from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from .models import HarnessError
from .orchestrator import LearningOrchestrator
from .retrieval import RetrievalQuery
from .roles import Role
from .skills import EvaluationCase, SkillCandidate, SkillRegistry


ROOT = Path(__file__).resolve().parents[1]
TASK_TEXT = "repair nested configuration merge preserving default siblings"
TASK_KIND = "config_merge"
PROCEDURE_TOKEN = "recursive_non_mutating_merge"
REPAIRED_CONFIG = '''from copy import deepcopy


DEFAULTS = {
    "http": {
        "host": "127.0.0.1",
        "port": 8080,
        "timeouts": {"connect": 2, "read": 10},
    },
    "logging": {"level": "INFO", "json": False},
}


def merge_config(defaults: dict, overrides: dict) -> dict:
    merged = deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_config(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged
'''


def _query() -> RetrievalQuery:
    return RetrievalQuery(
        TASK_TEXT,
        TASK_KIND,
        ("skill",),
        (),
        (),
        2_000,
        0.2,
        1,
        3_072,
    )


def fixture_digest(path: Path) -> str:
    root = Path(path)
    digest = hashlib.sha256()
    files = sorted(
        candidate
        for candidate in root.rglob("*")
        if candidate.is_file()
        and "__pycache__" not in candidate.parts
        and candidate.suffix != ".pyc"
    )
    for candidate in files:
        relative = candidate.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        content = candidate.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def prepare_controlled_store(path: Path) -> str:
    root = Path(path)
    orchestrator = LearningOrchestrator(
        root,
        ROOT / ".harness" / "contract.yaml",
        ROOT / ".harness" / "contract.lock",
    )
    run = orchestrator.start(
        {"task_kind": TASK_KIND, "input": "shallow_merge", "expected": PROCEDURE_TOKEN}
    )
    failed = orchestrator.verify(run.active_attempt_id, "shallow_merge")
    orchestrator.record_receipt(failed)
    repaired = orchestrator.repair(failed, PROCEDURE_TOKEN)
    passed = orchestrator.verify(repaired.id, repaired.output)
    orchestrator.advance(passed)
    episode = orchestrator.admit_episode(
        Role.MEMORY,
        TASK_KIND,
        "nested override removed default siblings",
        PROCEDURE_TOKEN,
        "recursively merge mappings and deepcopy override leaves",
        ("nested", "configuration", "merge", "defaults"),
        20,
    )
    outcome = orchestrator.propose_skill(
        Role.MEMORY,
        SkillCandidate(
            "repair nested configuration merge",
            "preserve default siblings during nested configuration overrides",
            ("repair", "nested", "configuration", "merge", "default", "siblings"),
            (
                PROCEDURE_TOKEN,
                "recurse when both values are mappings",
                "deepcopy every override leaf",
            ),
            (episode.id,),
            (EvaluationCase(TASK_TEXT, PROCEDURE_TOKEN),),
            0.95,
            TASK_KIND,
        ),
    )
    if outcome.decision != "PROMOTED" or outcome.skill is None:
        raise HarnessError("SKILL_NOT_PROMOTED", outcome.reason)
    return outcome.skill.id


def _verify_fixture(work: Path) -> dict:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=work,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "status": "PASSED" if completed.returncode == 0 else "FAILED",
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _apply_repair(work: Path) -> str:
    relative = Path("fixture_app") / "config.py"
    (work / relative).write_text(REPAIRED_CONFIG, encoding="utf-8", newline="\n")
    return relative.as_posix()


def run_trial(fixture: Path, store: Path, work: Path, enable_l5: bool) -> dict:
    fixture = Path(fixture)
    store = Path(store)
    work = Path(work)
    if work.exists() and any(work.iterdir()):
        raise HarnessError("WORK_NOT_EMPTY")
    if work.exists():
        work.rmdir()
    pristine_digest = fixture_digest(fixture)
    shutil.copytree(fixture, work)
    if fixture_digest(work) != pristine_digest:
        raise HarnessError("FIXTURE_MISMATCH")

    skill_id = None
    changed_files: list[str] = []
    if enable_l5:
        hits = SkillRegistry(store / "skills.json").trigger(_query()).hits
        if not hits:
            raise HarnessError("SKILL_NOT_TRIGGERED")
        skill = hits[0].record
        if PROCEDURE_TOKEN not in skill.procedure:
            raise HarnessError("SKILL_PROCEDURE_MISMATCH")
        skill_id = skill.id
        changed_files.append(_apply_repair(work))

    first = _verify_fixture(work)
    final = first
    attempts = 1
    if first["status"] == "FAILED":
        repaired_path = _apply_repair(work)
        if repaired_path not in changed_files:
            changed_files.append(repaired_path)
        final = _verify_fixture(work)
        attempts = 2

    return {
        "condition": "enabled" if enable_l5 else "disabled",
        "pristine_digest": pristine_digest,
        "skill_id": skill_id,
        "changed_files": changed_files,
        "first_verification": first["status"],
        "first_exit_code": first["exit_code"],
        "final_verification": final["status"],
        "final_exit_code": final["exit_code"],
        "attempts": attempts,
        "first_stdout": first["stdout"],
        "first_stderr": first["stderr"],
        "final_stdout": final["stdout"],
        "final_stderr": final["stderr"],
    }


def gate(fixture: Path, store: Path) -> dict:
    skills = SkillRegistry(Path(store) / "skills.json").all()
    hits = SkillRegistry(Path(store) / "skills.json").trigger(_query()).hits
    ready = len(skills) == 1 and len(hits) == 1 and hits[0].record.id == skills[0].id
    return {
        "ready": ready,
        "fixture_digest": fixture_digest(Path(fixture)),
        "skill_id": skills[0].id if len(skills) == 1 else None,
        "enabled_retrieval_count": len(hits),
        "disabled_retrieval_count": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare-store")
    prepare.add_argument("store")
    check = subparsers.add_parser("gate")
    check.add_argument("fixture")
    check.add_argument("store")
    trial = subparsers.add_parser("trial")
    trial.add_argument("fixture")
    trial.add_argument("store")
    trial.add_argument("work")
    trial.add_argument("--condition", choices=("enabled", "disabled"), required=True)
    arguments = parser.parse_args()

    if arguments.command == "prepare-store":
        result = {"skill_id": prepare_controlled_store(Path(arguments.store))}
    elif arguments.command == "gate":
        result = gate(Path(arguments.fixture), Path(arguments.store))
        if not result["ready"]:
            raise HarnessError("GATE_FAILED")
    else:
        result = run_trial(
            Path(arguments.fixture),
            Path(arguments.store),
            Path(arguments.work),
            arguments.condition == "enabled",
        )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
