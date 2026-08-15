import json
import subprocess
import sys
import tempfile
from pathlib import Path

from scripts.harness_state import (
    complete_step,
    load_state,
    run_verification,
    save_state,
    start_step,
)


PLAN = {
    "version": "0.1",
    "steps": [
        {"id": 1, "name": "Create a greeting"},
        {"id": 2, "name": "Expand the greeting"},
    ],
}
INITIAL_STATE = {
    "version": "0.1",
    "phase": "NEXT_STEP",
    "active_step": None,
    "completed_steps": [],
    "next_step": 1,
    "verification": None,
}
CHECK_TEXT = (
    "import pathlib,sys; expected=sys.argv[2]; "
    "actual=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'); "
    "print(f'expected={expected!r} actual={actual!r}'); "
    "raise SystemExit(0 if actual == expected else 1)"
)


def verification_command(artifact, expected):
    return [sys.executable, "-c", CHECK_TEXT, str(artifact), expected]


def git(repo, *args):
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def reviewed_commit(repo, state_path, artifact, state, subject):
    save_state(state_path, state)
    git(repo, "diff", "--check")
    if not git(repo, "status", "--short"):
        raise AssertionError("demo step produced no diff to review")
    git(repo, "add", artifact.name, state_path.name, "failure-evidence.json")
    git(repo, "commit", "-m", subject)
    return git(repo, "rev-parse", "HEAD")


def commit_step(repo, state_path, artifact, plan, state, step_id, subject):
    checkpoint = complete_step(plan, state, step_id)
    commit = reviewed_commit(repo, state_path, artifact, checkpoint, subject)
    return checkpoint, commit


def run_demo(workspace):
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    state_path = workspace / "state.json"
    artifact = workspace / "message.txt"
    evidence_path = workspace / "failure-evidence.json"
    events = []
    active_counts = []

    git(workspace, "init", "-q")
    git(workspace, "config", "user.name", "V0 Harness Demo")
    git(workspace, "config", "user.email", "harness@example.invalid")
    save_state(state_path, INITIAL_STATE)
    artifact.write_text("", encoding="utf-8", newline="\n")
    evidence_path.write_text("{}\n", encoding="utf-8", newline="\n")
    git(workspace, "add", ".")
    git(workspace, "commit", "-m", "demo: initialize controlled task")

    state = start_step(PLAN, load_state(state_path), 1)
    save_state(state_path, state)
    active_counts.append(1)
    events.append("step 1 active")
    artifact.write_text("hello\n", encoding="utf-8", newline="\n")
    state = run_verification(
        PLAN, state, 1, verification_command(artifact, "hello\n")
    )
    events.append("step 1 verification PASSED")
    git(workspace, "diff", "--check")
    events.append("step 1 diff reviewed")
    state, step_1_commit = commit_step(
        workspace,
        state_path,
        artifact,
        PLAN,
        state,
        1,
        "demo: complete step 1",
    )
    events.extend(["step 1 committed", "step 1 checkpointed"])

    state = load_state(state_path)
    events.append("state reloaded")
    state = start_step(PLAN, state, 2)
    save_state(state_path, state)
    active_counts.append(1)
    events.append("step 2 active")
    artifact.write_text("wrong value\n", encoding="utf-8", newline="\n")
    state = run_verification(
        PLAN, state, 2, verification_command(artifact, "hello world\n")
    )
    save_state(state_path, state)
    failure = dict(state["verification"])
    evidence_path.write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
    failed_state = load_state(state_path)
    events.append("step 2 verification FAILED")
    head_during_failure = git(workspace, "rev-parse", "HEAD")

    for label in ("completion", "checkpoint"):
        try:
            complete_step(PLAN, failed_state, 2)
        except ValueError:
            events.append(f"step 2 {label} BLOCKED")
        else:
            raise AssertionError(f"failed verification allowed {label}")
    try:
        commit_step(
            workspace,
            state_path,
            artifact,
            PLAN,
            failed_state,
            2,
            "demo: forbidden failed commit",
        )
    except ValueError:
        events.insert(events.index("step 2 checkpoint BLOCKED"), "step 2 commit BLOCKED")
    else:
        raise AssertionError("failed verification allowed commit")
    try:
        start_step(PLAN, failed_state, 2)
    except ValueError:
        events.append("next-step activation BLOCKED")
    else:
        raise AssertionError("failed verification allowed another activation")
    if git(workspace, "rev-parse", "HEAD") != step_1_commit:
        raise AssertionError("Git history advanced after failed verification")

    state = load_state(state_path)
    active_counts.append(1)
    if state["active_step"] != 2:
        raise AssertionError("repair did not remain on step 2")
    events.append("step 2 repair stayed active")
    artifact.write_text("hello world\n", encoding="utf-8", newline="\n")
    state = run_verification(
        PLAN, state, 2, verification_command(artifact, "hello world\n")
    )
    events.append("step 2 verification PASSED")
    git(workspace, "diff", "--check")
    events.append("step 2 diff reviewed")
    state, step_2_commit = commit_step(
        workspace,
        state_path,
        artifact,
        PLAN,
        state,
        2,
        "demo: complete step 2",
    )
    events.extend(["step 2 committed", "step 2 checkpointed"])

    final_state = load_state(state_path)
    subjects = git(workspace, "log", "-2", "--reverse", "--format=%s").splitlines()
    if git(workspace, "status", "--porcelain"):
        raise AssertionError("demo repository is not clean")
    return {
        "events": events,
        "artifact": artifact.read_text(encoding="utf-8"),
        "intentional_failure": failure,
        "failed_state": failed_state,
        "head_during_failure": head_during_failure,
        "step_1_commit": step_1_commit,
        "step_2_commit": step_2_commit,
        "commit_subjects": subjects,
        "final_state": final_state,
        "maximum_active_steps": max(active_counts),
    }


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        proof = run_demo(Path(temp_dir))
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
