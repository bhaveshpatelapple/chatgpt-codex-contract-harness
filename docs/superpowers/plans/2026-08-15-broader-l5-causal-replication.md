# Broader L5 Causal Replication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove or refute that a validated L5 skill causes first-attempt success on an isolated multi-file nested-configuration repository repair.

**Architecture:** A committed broken Python fixture supplies the realistic task and its independent verifier. A focused repository-ablation module copies that fixture per unit, hashes the pristine copy, optionally retrieves and applies one promoted L5 procedure, runs the real fixture test suite, performs a deterministic fallback repair after failure, and returns structured evidence. A preregistered seeded six-unit experiment invokes the module in separate processes and stores raw outcomes without broadening the causal claim beyond the fixed fixture.

**Tech Stack:** Python 3.11+, standard-library `argparse`, `hashlib`, `json`, `shutil`, `subprocess`, `tempfile`, and `unittest`; existing `LearningOrchestrator`, `SkillRegistry`, and JSON persistence.

## Global Constraints

- Work only in the broader L5 causal-replication checkpoint described by `docs/superpowers/specs/2026-08-15-broader-l5-causal-replication-design.md`.
- Do not modify `.harness/contract.yaml` or `.harness/contract.lock`.
- Commit preregistration before collecting any experimental outcome.
- Use exactly three fresh-process units per condition in one seeded randomized order.
- Hold fixture bytes, task, verifier, store, interpreter, and base commit fixed across conditions.
- L5-disabled units must not query or apply a skill.
- Treat retrieved skill and attempted patch as mediators: record them, but do not adjust on them.
- Stop on a pre-run gate or protocol failure; do not interpret partial outcomes.
- Report only Pearl rung-2 evidence local to the deterministic fixture and current code revision.
- Stage exact paths only; never use `git add .` or `git add -A`.

---

## File map

- `.harness/learning/causal-ablation-002/fixture/fixture_app/config.py`: intentionally broken shallow configuration merge.
- `.harness/learning/causal-ablation-002/fixture/fixture_app/service.py`: consumer that exposes lost nested defaults.
- `.harness/learning/causal-ablation-002/fixture/tests/test_config.py`: merge invariants and input immutability.
- `.harness/learning/causal-ablation-002/fixture/tests/test_service.py`: cross-module consumer behavior.
- `.harness/learning/causal-ablation-002/PRE_REGISTRATION.md`: hypothesis, estimand, design, endpoints, and stopping rule.
- `.harness/learning/causal-ablation-002/causal-dag.md`: edges, missing-edge assumptions, identifiability, and rung.
- `.harness/learning/causal-ablation-002/randomization.md`: seed and exact six-unit condition allocation.
- `.harness/learning/causal-ablation-002/confound_analysis.csv`: confound, mediator, collider, and control audit.
- `harness_learning/repository_ablation.py`: fixture hashing/copying, controlled skill-store creation, trial execution, actual verification, repair, and JSON CLI.
- `tests/test_learning_repository_causal_ablation.py`: real integration coverage for the intervention and isolation contract.
- `.harness/learning/causal-ablation-002/base-store/*.json`: persisted controlled episode, skill, and verified run.
- `.harness/learning/causal-ablation-002/RESULTS.json`: exact raw unit outcomes and protocol metadata.
- `.harness/learning/causal-ablation-002/RESULTS.md`: preregistered sufficient statistics and bounded interpretation.
- `.harness/learning/causal-ablation-002/VERIFICATION.md`: fresh verification commands and results.

---

### Task 1: Commit the preregistered fixture and experiment allocation

**Files:**
- Create: `.harness/learning/causal-ablation-002/fixture/fixture_app/__init__.py`
- Create: `.harness/learning/causal-ablation-002/fixture/fixture_app/config.py`
- Create: `.harness/learning/causal-ablation-002/fixture/fixture_app/service.py`
- Create: `.harness/learning/causal-ablation-002/fixture/tests/__init__.py`
- Create: `.harness/learning/causal-ablation-002/fixture/tests/test_config.py`
- Create: `.harness/learning/causal-ablation-002/fixture/tests/test_service.py`
- Create: `.harness/learning/causal-ablation-002/PRE_REGISTRATION.md`
- Create: `.harness/learning/causal-ablation-002/causal-dag.md`
- Create: `.harness/learning/causal-ablation-002/randomization.md`
- Create: `.harness/learning/causal-ablation-002/confound_analysis.csv`

**Interfaces:**
- Consumes: approved design specification and existing exact-output verification policy.
- Produces: `merge_config(defaults: dict, overrides: dict) -> dict`, `service_settings(overrides: dict) -> dict`, pristine fixture bytes, and a committed condition order consumed by Task 3.

- [ ] **Step 1: Generate and record the random allocation without running outcomes**

Run this once and copy its literal output into `randomization.md`:

```powershell
python -c "import random; labels=['enabled']*3+['disabled']*3; random.Random(20260816).shuffle(labels); print(labels)"
```

Record seed `20260816`, the six numbered labels, and the rule that allocation cannot change after commit.

- [ ] **Step 2: Create the intentionally broken fixture implementation**

Use this shallow merge in `fixture_app/config.py`:

```python
from copy import deepcopy


DEFAULTS = {
    "http": {"host": "127.0.0.1", "port": 8080, "timeouts": {"connect": 2, "read": 10}},
    "logging": {"level": "INFO", "json": False},
}


def merge_config(defaults: dict, overrides: dict) -> dict:
    merged = deepcopy(defaults)
    merged.update(deepcopy(overrides))
    return merged
```

Use this consumer in `fixture_app/service.py`:

```python
from .config import DEFAULTS, merge_config


def service_settings(overrides: dict) -> dict:
    merged = merge_config(DEFAULTS, overrides)
    return {
        "bind": f'{merged["http"]["host"]}:{merged["http"]["port"]}',
        "read_timeout": merged["http"]["timeouts"]["read"],
        "log_level": merged["logging"]["level"],
    }
```

- [ ] **Step 3: Create independent fixture verification tests**

`tests/test_config.py` must use literal expectations and cover the defect plus non-mutation:

```python
import unittest
from fixture_app.config import DEFAULTS, merge_config


class MergeConfigTests(unittest.TestCase):
    def test_nested_override_preserves_default_siblings(self):
        merged = merge_config(DEFAULTS, {"http": {"port": 9090}})
        self.assertEqual("127.0.0.1", merged["http"]["host"])
        self.assertEqual(9090, merged["http"]["port"])
        self.assertEqual({"connect": 2, "read": 10}, merged["http"]["timeouts"])

    def test_merge_does_not_mutate_inputs(self):
        defaults = {"outer": {"kept": 1}}
        overrides = {"outer": {"added": 2}}
        merge_config(defaults, overrides)
        self.assertEqual({"outer": {"kept": 1}}, defaults)
        self.assertEqual({"outer": {"added": 2}}, overrides)
```

`tests/test_service.py` must prove the cross-module effect:

```python
import unittest
from fixture_app.service import service_settings


class ServiceSettingsTests(unittest.TestCase):
    def test_port_override_retains_required_http_defaults(self):
        self.assertEqual(
            {"bind": "127.0.0.1:9090", "read_timeout": 10, "log_level": "INFO"},
            service_settings({"http": {"port": 9090}}),
        )
```

- [ ] **Step 4: Verify the pristine fixture fails for the intended reason**

Run from the fixture directory:

```powershell
python -m unittest discover -s tests -v
```

Expected: nonzero exit; the preservation and service tests fail because `http.host` and `http.timeouts` disappear. The immutability test may pass. Any import or syntax error must be fixed before proceeding.

- [ ] **Step 5: Write the causal preregistration files**

`PRE_REGISTRATION.md` must state the hypothesis, two treatment levels, six units, allocation seed/order, the literal base commit returned by `git rev-parse HEAD`, primary endpoint, `3/3` versus `0/3` criterion, secondary endpoints, power limitation, and stop/exclusion rules.

`causal-dag.md` must include the design DAG, every edge, missing-edge assumptions, direct-intervention identifiability, mediator handling, imperfect-isolation sensitivity, and explicit Pearl rung 2.

`confound_analysis.csv` must have columns `variable,role,control,uncontrolled_consequence` and rows for fixture bytes, task text, verifier command, base store, base code, interpreter, process state, process order, retrieved skill, and attempted patch.

- [ ] **Step 6: Review and commit the preregistration gate**

Run:

```powershell
git diff --check
git status --short
git diff --stat
```

Confirm only the ten Task 1 paths are present, then stage those exact paths and commit:

```powershell
git commit -m "test: preregister broader L5 causal replication"
```

Do not run an enabled or disabled experimental unit before this commit exists.

---

### Task 2: Build the isolated repository trial runner with TDD

**Files:**
- Create: `tests/test_learning_repository_causal_ablation.py`
- Create: `harness_learning/repository_ablation.py`
- Create: `.harness/learning/causal-ablation-002/base-store/episodes.json`
- Create: `.harness/learning/causal-ablation-002/base-store/runs.json`
- Create: `.harness/learning/causal-ablation-002/base-store/skills.json`

**Interfaces:**
- Consumes: `SkillRegistry.trigger(RetrievalQuery)`, the committed fixture, contract files, and a fresh destination directory.
- Produces: `fixture_digest(path: Path) -> str`, `prepare_controlled_store(path: Path) -> str`, `run_trial(fixture: Path, store: Path, work: Path, enable_l5: bool) -> dict`, and CLI commands `prepare-store`, `gate`, and `trial`.

- [ ] **Step 1: Write the failing integration test first**

The production mutation caught by this test is either querying L5 in the disabled branch, failing to isolate fixture copies, or failing to turn the retrieved procedure into a first-attempt verified repair.

```python
import tempfile
import unittest
from pathlib import Path

from harness_learning.repository_ablation import (
    fixture_digest,
    prepare_controlled_store,
    run_trial,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / ".harness" / "learning" / "causal-ablation-002" / "fixture"


class RepositoryCausalAblationTests(unittest.TestCase):
    def test_l5_intervention_changes_first_attempt_repository_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill_id = prepare_controlled_store(root / "store")
            pristine = fixture_digest(FIXTURE)
            enabled = run_trial(FIXTURE, root / "store", root / "enabled", True)
            disabled = run_trial(FIXTURE, root / "store", root / "disabled", False)

        self.assertEqual(pristine, enabled["pristine_digest"])
        self.assertEqual(pristine, disabled["pristine_digest"])
        self.assertEqual("PASSED", enabled["first_verification"])
        self.assertEqual(1, enabled["attempts"])
        self.assertEqual(skill_id, enabled["skill_id"])
        self.assertEqual("FAILED", disabled["first_verification"])
        self.assertEqual(2, disabled["attempts"])
        self.assertIsNone(disabled["skill_id"])
        self.assertEqual("PASSED", disabled["final_verification"])
```

- [ ] **Step 2: Run the test and observe the correct red state**

Run:

```powershell
python -m unittest tests.test_learning_repository_causal_ablation -v
```

Expected: import failure for missing `harness_learning.repository_ablation`. This proves the test demands the new production boundary.

- [ ] **Step 3: Implement deterministic hashing, copying, and real verification**

Implement `fixture_digest` as SHA-256 over each sorted relative file path plus its bytes, excluding `__pycache__` and `.pyc` files. `run_trial` must reject a pre-existing non-empty work directory, copy the fixture, assert the copied pristine digest equals the source digest, and execute this command with the copy as its working directory:

```python
[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
```

Return `PASSED` only for exit code zero; preserve stdout/stderr and exit code in the structured result.

- [ ] **Step 4: Implement the controlled store and treatment branches**

`prepare_controlled_store` must use `LearningOrchestrator` to create a failed nested-merge run, verify and advance the recursive repair, admit one episode, and promote exactly one `SkillCandidate` whose procedure includes the literal invariant token `recursive_non_mutating_merge`.

`run_trial` must query that store only when `enable_l5` is true. An enabled matching procedure replaces only `fixture_app/config.py` with the minimal recursive implementation:

```python
from copy import deepcopy


DEFAULTS = {
    "http": {"host": "127.0.0.1", "port": 8080, "timeouts": {"connect": 2, "read": 10}},
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
```

The disabled branch runs the broken fixture unchanged first. After any valid first failure, apply the same repair, rerun the full suite, and record two attempts. Never silently repair an enabled retrieval failure; raise `HarnessError("SKILL_NOT_TRIGGERED")`.

- [ ] **Step 5: Add the JSON CLI and pre-run gate**

Support:

```powershell
python -m harness_learning.repository_ablation prepare-store .harness/learning/causal-ablation-002/base-store
python -m harness_learning.repository_ablation gate .harness/learning/causal-ablation-002/fixture .harness/learning/causal-ablation-002/base-store
python -m harness_learning.repository_ablation trial .harness/learning/causal-ablation-002/fixture .harness/learning/causal-ablation-002/base-store work/enabled-smoke --condition enabled
python -m harness_learning.repository_ablation trial .harness/learning/causal-ablation-002/fixture .harness/learning/causal-ablation-002/base-store work/disabled-smoke --condition disabled
```

The gate succeeds only when the store has exactly one skill, the fixed task query retrieves that skill, a copied fixture has the source digest, and the disabled configuration is represented without performing a registry query. Emit sorted JSON on stdout and nonzero exit on failure.

- [ ] **Step 6: Run green and regression verification**

Run:

```powershell
python -m unittest tests.test_learning_repository_causal_ablation tests.test_learning_causal_ablation tests.test_learning_cross_process -v
python -m unittest discover -s tests -v
python -m harness_learning.repository_ablation prepare-store .harness/learning/causal-ablation-002/base-store
python -m harness_learning.repository_ablation gate .harness/learning/causal-ablation-002/fixture .harness/learning/causal-ablation-002/base-store
git diff --check
```

Expected: 3 targeted tests pass; the full suite passes with one new test; store creation reports one skill ID; gate reports `ready: true`; diff check is clean.

- [ ] **Step 7: Mutation-check the causal branch manually**

Temporarily change the enabled condition to skip applying the procedure and rerun the targeted repository-ablation test. It must fail on enabled first verification. Restore the implementation and rerun the test to green. Do not commit the mutation.

- [ ] **Step 8: Review and commit the runner gate**

Inspect `git diff`, `git status --short`, generated base-store JSON, and the exact staged names. Confirm no experiment work directories or outcome results exist. Commit exact Task 2 paths:

```powershell
git commit -m "test: add isolated L5 repository ablation runner"
```

---

### Task 3: Execute, analyze, and checkpoint the preregistered experiment

**Files:**
- Create: `.harness/learning/causal-ablation-002/units/unit-01/**` through `unit-06/**`
- Create: `.harness/learning/causal-ablation-002/RESULTS.json`
- Create: `.harness/learning/causal-ablation-002/RESULTS.md`
- Create: `.harness/learning/causal-ablation-002/VERIFICATION.md`

**Interfaces:**
- Consumes: committed allocation, fixture, controlled store, and `repository_ablation trial` CLI.
- Produces: immutable per-unit work copies and sufficient-statistic evidence for the local rung-2 claim.

- [ ] **Step 1: Re-run the pre-run gate from the committed tree**

Run:

```powershell
git status --short
python -m harness_learning.repository_ablation gate .harness/learning/causal-ablation-002/fixture .harness/learning/causal-ablation-002/base-store
```

Expected: clean worktree and `ready: true`. Record the fixture digest, skill ID, Python version, and `git rev-parse HEAD`. Stop if any differs from preregistration.

- [ ] **Step 2: Run six separate processes in the committed seeded order**

Invoke these commands in the committed seeded order (`enabled`, `disabled`,
`enabled`, `enabled`, `disabled`, `disabled`), with one unique work directory
per process:

```powershell
python -m harness_learning.repository_ablation trial .harness/learning/causal-ablation-002/fixture .harness/learning/causal-ablation-002/base-store .harness/learning/causal-ablation-002/units/unit-01 --condition enabled
python -m harness_learning.repository_ablation trial .harness/learning/causal-ablation-002/fixture .harness/learning/causal-ablation-002/base-store .harness/learning/causal-ablation-002/units/unit-02 --condition disabled
python -m harness_learning.repository_ablation trial .harness/learning/causal-ablation-002/fixture .harness/learning/causal-ablation-002/base-store .harness/learning/causal-ablation-002/units/unit-03 --condition enabled
python -m harness_learning.repository_ablation trial .harness/learning/causal-ablation-002/fixture .harness/learning/causal-ablation-002/base-store .harness/learning/causal-ablation-002/units/unit-04 --condition enabled
python -m harness_learning.repository_ablation trial .harness/learning/causal-ablation-002/fixture .harness/learning/causal-ablation-002/base-store .harness/learning/causal-ablation-002/units/unit-05 --condition disabled
python -m harness_learning.repository_ablation trial .harness/learning/causal-ablation-002/fixture .harness/learning/causal-ablation-002/base-store .harness/learning/causal-ablation-002/units/unit-06 --condition disabled
```

Capture each complete JSON object without editing. If the CLI errors, fixture digest differs, or an outcome lacks final `PASSED`, stop and document a protocol deviation before any rerun.

- [ ] **Step 3: Write raw results and preregistered analysis**

`RESULTS.json` must include protocol version, base commit, fixture digest, skill ID, seed, exact ordered unit objects, and no discarded units. Compute directly from those units:

- enabled first-attempt passes / enabled total;
- disabled first-attempt passes / disabled total;
- success-rate difference;
- mean attempts by condition;
- final passes by condition; and
- digest agreement count.

`RESULTS.md` must compare the primary result with the `3/3` versus `0/3` rule, report secondary endpoints, disclose every deviation, and state that the conclusion is Pearl rung 2 only for the deterministic fixture. Do not claim performance on unseen repositories or autonomous model reasoning.

- [ ] **Step 4: Run fresh verification and record it**

Run:

```powershell
python -m unittest tests.test_learning_repository_causal_ablation tests.test_learning_causal_ablation tests.test_learning_cross_process -v
python -m unittest discover -s tests -v
python -m harness_learning.repository_ablation gate .harness/learning/causal-ablation-002/fixture .harness/learning/causal-ablation-002/base-store
git diff --check
```

In `VERIFICATION.md`, record each exact command, exit code, passed-test count, gate identifiers, and timestamp. Then rerun `git diff --check` after writing the file.

- [ ] **Step 5: Perform final causal and scope audit**

Confirm:

- treatment alone changed between paired conditions;
- every unit began with the same fixture digest;
- enabled units retrieved the preregistered skill;
- disabled units report a null skill ID;
- raw units reproduce every number in `RESULTS.md`;
- no unit was selected or excluded post-treatment;
- all final fixture suites and harness regressions pass; and
- the diff contains only Task 3 evidence and generated unit files.

- [ ] **Step 6: Commit and stop at the checkpoint**

Stage only Task 3 paths, review `git diff --cached --name-status`, run `git diff --cached --check`, and commit:

```powershell
git commit -m "test: replicate L5 causality on repository repair"
```

After committing, rerun the targeted tests, full suite, gate, commit-range diff check, and `git status --short`. Report the design, preregistration, runner, and result commit hashes, before/after causal status, files changed, exact verification results, protocol deviations, remaining generalization gap, and the next dependency-ordered checkpoint. Do not start it.
