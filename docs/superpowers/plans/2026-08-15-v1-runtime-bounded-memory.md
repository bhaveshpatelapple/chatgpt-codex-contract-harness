# V1 Runtime Enforcement and Bounded Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a separately locked V1 harness that runtime-enforces every lifecycle transition and restores execution from a tamper-evident journal plus deterministic bounded summaries.

**Architecture:** Preserve V0 unchanged and place V1 durable artifacts under `.harness/v1/`. Implement focused Python modules for the V1 contract, journal, summaries, runtime state, Git reconciliation, CLI, and recovery; the CLI composes these modules but does not own domain rules. Every authorization receipt is bound to a step attempt and Git identity, and every mutating command appends a hash-chained journal event.

**Tech Stack:** Python 3.11+, standard library (`argparse`, `dataclasses`, `hashlib`, `json`, `pathlib`, `subprocess`, `uuid`), PyYAML, `unittest`, Git CLI.

## Global Constraints

- Do not modify `.harness/contract.yaml`, `.harness/contract.lock`, `.harness/plan.yaml`, or the meaning of the completed V0 checkpoint.
- V1 is local and deterministic: no vector search, embeddings, RAG, cloud persistence, web UI, multi-agent runtime, Agents SDK, episodic memory, or self-evolving skills.
- Persist JSON using UTF-8, sorted keys for hashed payloads, two-space indentation for human-readable files, a trailing newline, and same-directory temporary-file replacement.
- Execute verification commands only as non-empty argument lists; never accept a shell command string.
- Never delete user files, reset Git, or advance state during recovery.
- Use stable diagnostic codes in the form `V1_<AREA>_<CONDITION>`.
- Each task ends with targeted tests, the full regression suite, `git diff --check`, diff review, and one focused commit.

## File Structure

- `.harness/v1/contract.yaml`: separately locked V1 scope and invariants.
- `.harness/v1/contract.lock`: SHA-256 digest of the exact V1 contract bytes.
- `.harness/v1/plan.yaml`: ordered V1 implementation plan with declared path scopes.
- `.harness/v1/state.json`: authoritative V1 lifecycle checkpoint.
- `.harness/v1/journal.json`: append-only logical journal represented as a JSON array and atomically replaced on append.
- `.harness/v1/summary.json`: bounded, derived recovery summary.
- `scripts/v1_contract.py`: V1 contract and baseline validation.
- `scripts/v1_io.py`: canonical JSON encoding and atomic persistence.
- `scripts/v1_journal.py`: hash-chained journal creation, append, and validation.
- `scripts/v1_memory.py`: deterministic bounded summary generation.
- `scripts/v1_runtime.py`: evidence-aware lifecycle transitions.
- `scripts/v1_git.py`: Git inspection, scope validation, commit, and checkpoint reconciliation.
- `scripts/harness_v1.py`: CLI adapter and structured diagnostics.
- `scripts/v1_recovery.py`: read-mostly recovery classification.
- `tests/test_v1_contract.py`: V1 contract and baseline tests.
- `tests/test_v1_journal.py`: journal integrity and atomicity tests.
- `tests/test_v1_memory.py`: count/byte bounds and pruning tests.
- `tests/test_v1_runtime.py`: attempt and receipt transition tests.
- `tests/test_v1_git.py`: temporary-repository Git reconciliation tests.
- `tests/test_v1_cli.py`: command interface and diagnostic tests.
- `tests/test_v1_recovery.py`: interruption/corruption recovery tests.
- `tests/test_v1_end_to_end.py`: complete V1 proof scenario.
- `V1_PROOF_REPORT.md`: final evidence report generated from verified results.

---

### Task 1: Lock the V1 contract and bootstrap durable state

**Files:**
- Create: `.harness/v1/contract.yaml`
- Create: `.harness/v1/contract.lock`
- Create: `.harness/v1/plan.yaml`
- Create: `.harness/v1/state.json`
- Create: `.harness/v1/journal.json`
- Create: `.harness/v1/summary.json`
- Create: `scripts/v1_io.py`
- Create: `scripts/v1_contract.py`
- Create: `tests/test_v1_contract.py`
- Modify: `README.md`

**Interfaces:**
- Produces: `canonical_json(value: object) -> bytes`, `atomic_write_json(path: Path, value: object) -> None`.
- Produces: `validate_v1_contract(root: Path) -> dict`, raising `V1Error(code, message)` on invalid lock or baseline.
- Produces: state fields `version`, `phase`, `baseline_commit`, `active_step`, `attempt_id`, `completed_steps`, `next_step`, `verification`, `review`, `commit`.

- [ ] **Step 1: Write failing contract tests**

```python
class V1ContractTests(unittest.TestCase):
    def test_locked_contract_matches_digest_and_v0_baseline(self):
        contract = validate_v1_contract(ROOT)
        self.assertEqual(contract["version"], "1.0")
        self.assertEqual(contract["status"], "LOCKED")

    def test_contract_rejects_silent_change(self):
        with copied_harness(ROOT) as root:
            path = root / ".harness/v1/contract.yaml"
            path.write_text(path.read_text() + "\n# changed\n", encoding="utf-8")
            with self.assertRaisesRegex(V1Error, "V1_CONTRACT_DIGEST_MISMATCH"):
                validate_v1_contract(root)

    def test_contract_rejects_missing_v0_baseline_commit(self):
        with copied_harness(ROOT) as root:
            rewrite_baseline(root, "0" * 40)
            with self.assertRaisesRegex(V1Error, "V1_BASELINE_COMMIT_MISSING"):
                validate_v1_contract(root)
```

- [ ] **Step 2: Run the tests and confirm RED**

Run: `python -m unittest -v tests.test_v1_contract`

Expected: import failure for missing `scripts.v1_contract`.

- [ ] **Step 3: Implement canonical I/O and V1 contract validation**

```python
def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def atomic_write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)

def validate_v1_contract(root):
    contract_path = root / ".harness/v1/contract.yaml"
    lock_path = root / ".harness/v1/contract.lock"
    raw = contract_path.read_bytes()
    expected = lock_path.read_text(encoding="utf-8").strip()
    if expected != "sha256:" + hashlib.sha256(raw).hexdigest():
        raise V1Error("V1_CONTRACT_DIGEST_MISMATCH", "V1 contract differs from its lock")
    contract = yaml.safe_load(raw)
    require_locked_schema(contract)
    require_git_ancestor(root, contract["v0_baseline_commit"])
    return contract
```

Create a seven-step V1 plan matching Tasks 1–7 in this document, with each
step declaring its allowed paths. Initialize state at `CHECKPOINT` with no
active attempt, `completed_steps: [1]`, and `next_step: 2`. Initialize the
journal and summary with a V1 bootstrap event bound to the V0 baseline, V1
contract digest, and V1 plan digest. Do not attempt to embed Task 1's own commit
hash in files contained by that commit; later reconciliation establishes the
current checkpoint HEAD from Git history without a self-referential hash.

- [ ] **Step 4: Run targeted and regression tests**

Run: `python -m unittest -v tests.test_v1_contract`

Expected: all V1 contract tests pass.

Run: `python -m unittest discover -s tests -v`

Expected: all V0 and new V1 tests pass.

- [ ] **Step 5: Review and commit**

Run: `git diff --check`

Review the full diff and confirm V0 locked artifacts are unchanged.

```text
git add .harness/v1 README.md scripts/v1_io.py scripts/v1_contract.py tests/test_v1_contract.py
git commit -m "feat: lock V1 contract and bootstrap state"
```

---

### Task 2: Add the tamper-evident execution journal

**Files:**
- Create: `scripts/v1_journal.py`
- Create: `tests/test_v1_journal.py`
- Modify: `.harness/v1/state.json`
- Modify: `.harness/v1/journal.json`

**Interfaces:**
- Consumes: `canonical_json`, `atomic_write_json` from `scripts.v1_io`.
- Produces: `make_event(sequence: int, previous_hash: str | None, event_type: str, payload: dict, step_id: int | None = None, attempt_id: str | None = None) -> dict`.
- Produces: `append_event(path: Path, event_type: str, payload: dict, step_id: int | None = None, attempt_id: str | None = None) -> dict`.
- Produces: `validate_journal(events: list[dict]) -> list[dict]`.

- [ ] **Step 1: Write failing journal behavior tests**

```python
def test_append_builds_monotonic_hash_chain(self):
    append_event(self.path, "STEP_STARTED", {"head": "a"}, 2, "attempt-1")
    second = append_event(self.path, "VERIFY_FAILED", {"exit_code": 1}, 2, "attempt-1")
    events = json.loads(self.path.read_text(encoding="utf-8"))
    self.assertEqual([event["sequence"] for event in events], [1, 2])
    self.assertEqual(second["previous_hash"], events[0]["hash"])
    self.assertEqual(validate_journal(events), events)

def test_validation_rejects_modified_payload(self):
    event = append_event(self.path, "STEP_STARTED", {"head": "a"})
    event["payload"]["head"] = "b"
    with self.assertRaisesRegex(V1Error, "V1_JOURNAL_HASH_MISMATCH"):
        validate_journal([event])

def test_failed_replace_preserves_previous_valid_journal(self):
    append_event(self.path, "BOOTSTRAP", {})
    before = self.path.read_bytes()
    with mock.patch("pathlib.Path.replace", side_effect=OSError("interrupted")):
        with self.assertRaises(OSError):
            append_event(self.path, "STEP_STARTED", {})
    self.assertEqual(self.path.read_bytes(), before)
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `python -m unittest -v tests.test_v1_journal`

Expected: import failure for missing `scripts.v1_journal`.

- [ ] **Step 3: Implement hash construction, validation, and atomic append**

```python
def event_hash(event):
    unhashed = {key: value for key, value in event.items() if key != "hash"}
    return hashlib.sha256(canonical_json(unhashed)).hexdigest()

def validate_journal(events):
    previous = None
    for index, event in enumerate(events, start=1):
        if event["sequence"] != index:
            raise V1Error("V1_JOURNAL_SEQUENCE_INVALID", f"expected journal sequence {index}")
        if event["previous_hash"] != previous or event["hash"] != event_hash(event):
            raise V1Error("V1_JOURNAL_HASH_MISMATCH", f"invalid journal event {index}")
        previous = event["hash"]
    return events
```

`append_event` must load and validate the existing list, create the next event, validate the combined list, and call `atomic_write_json` once. Timestamps are evidence metadata but never participate in pruning order; sequence controls order.

- [ ] **Step 4: Run targeted and regression tests**

Run: `python -m unittest -v tests.test_v1_journal`

Expected: all journal tests pass.

Run: `python -m unittest discover -s tests -v`

Expected: full suite passes.

- [ ] **Step 5: Update checkpoint, review, and commit**

Record Task 2 verification in V1 state and append `STEP_CHECKPOINTED` to the journal.

Run: `git diff --check`

```text
git add .harness/v1/state.json .harness/v1/journal.json scripts/v1_journal.py tests/test_v1_journal.py
git commit -m "feat: add tamper-evident execution journal"
```

---

### Task 3: Generate deterministic bounded recovery summaries

**Files:**
- Create: `scripts/v1_memory.py`
- Create: `tests/test_v1_memory.py`
- Modify: `.harness/v1/state.json`
- Modify: `.harness/v1/journal.json`
- Modify: `.harness/v1/summary.json`

**Interfaces:**
- Consumes: validated journal events and canonical JSON encoding.
- Produces: `build_summary(state: dict, events: list[dict], max_events: int, max_bytes: int) -> dict`.
- Produces: `write_summary(path: Path, summary: dict) -> None`.

- [ ] **Step 1: Write failing bounds and pruning tests**

```python
def test_summary_keeps_latest_events_within_both_limits(self):
    events = chained_events(8, payload_size=20)
    summary = build_summary(active_state(), events, max_events=3, max_bytes=900)
    self.assertEqual([event["sequence"] for event in summary["recent_events"]], [6, 7, 8])
    self.assertLessEqual(len(canonical_json(summary)), 900)

def test_pruning_is_deterministic(self):
    first = build_summary(active_state(), chained_events(20), 5, 1200)
    second = build_summary(active_state(), chained_events(20), 5, 1200)
    self.assertEqual(canonical_json(first), canonical_json(second))

def test_essential_context_over_limit_fails_explicitly(self):
    with self.assertRaisesRegex(V1Error, "V1_SUMMARY_ESSENTIAL_TOO_LARGE"):
        build_summary(state_with_blocker("x" * 1000), [], 2, 100)
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `python -m unittest -v tests.test_v1_memory`

Expected: import failure for missing `scripts.v1_memory`.

- [ ] **Step 3: Implement essential projection and oldest-first pruning**

```python
def build_summary(state, events, max_events, max_bytes):
    essential = project_essential_state(state)
    summary = {
        **essential,
        "limits": {"max_events": max_events, "max_bytes": max_bytes},
        "recent_events": events[-max_events:],
    }
    while summary["recent_events"] and len(canonical_json(summary)) > max_bytes:
        summary["recent_events"].pop(0)
    if len(canonical_json(summary)) > max_bytes:
        raise V1Error("V1_SUMMARY_ESSENTIAL_TOO_LARGE", "essential recovery context exceeds max_bytes")
    return summary
```

Essential projection must include contract/plan identity, phase, active/next
step, attempt, checkpoint HEAD, latest verification/review outcome, and blocker.

- [ ] **Step 4: Run targeted and regression tests**

Run: `python -m unittest -v tests.test_v1_memory`

Expected: count, bytes, deterministic pruning, and essential overflow tests pass.

Run: `python -m unittest discover -s tests -v`

Expected: full suite passes.

- [ ] **Step 5: Update durable artifacts, review, and commit**

Generate `.harness/v1/summary.json` using the locked V1 limits, record the passing receipt, append the checkpoint journal event, and run `git diff --check`.

```text
git add .harness/v1/state.json .harness/v1/journal.json .harness/v1/summary.json scripts/v1_memory.py tests/test_v1_memory.py
git commit -m "feat: add deterministic bounded recovery summaries"
```

---

### Task 4: Enforce attempt-bound runtime transitions

**Files:**
- Create: `scripts/v1_runtime.py`
- Create: `tests/test_v1_runtime.py`
- Modify: `.harness/v1/state.json`
- Modify: `.harness/v1/journal.json`
- Modify: `.harness/v1/summary.json`

**Interfaces:**
- Produces: `start_step(plan: dict, state: dict, step_id: int, head: str, attempt_id: str) -> dict`.
- Produces: `record_verification(plan: dict, state: dict, command: list[str], result: CompletedProcess, head: str, diff_hash: str) -> dict`.
- Produces: `record_review(plan: dict, state: dict, head: str, diff_hash: str, paths: list[str]) -> dict`.
- Produces: `authorize_commit(plan: dict, state: dict, head: str, diff_hash: str) -> None`.
- Produces: `record_commit(plan: dict, state: dict, parent: str, commit: str) -> dict`.
- Produces: `checkpoint_step(plan: dict, state: dict, head: str) -> dict`.

- [ ] **Step 1: Write failing transition tests**

```python
def test_failed_verification_blocks_every_later_transition(self):
    failed = verified_state(exit_code=1, attempt_id="a1", head="h1", diff_hash="d1")
    for operation in (record_review, authorize_commit, record_commit, checkpoint_step):
        with self.subTest(operation=operation.__name__):
            with self.assertRaisesRegex(V1Error, "V1_VERIFY_REQUIRED"):
                invoke(operation, failed)

def test_changed_diff_makes_verification_stale(self):
    passed = verified_state(exit_code=0, attempt_id="a1", head="h1", diff_hash="d1")
    with self.assertRaisesRegex(V1Error, "V1_VERIFICATION_STALE"):
        record_review(PLAN, passed, "h1", "different", ["allowed.txt"])

def test_checkpoint_requires_recorded_commit_at_head(self):
    committed = committed_state(commit="c1", parent="h1")
    with self.assertRaisesRegex(V1Error, "V1_CHECKPOINT_HEAD_MISMATCH"):
        checkpoint_step(PLAN, committed, "c2")
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `python -m unittest -v tests.test_v1_runtime`

Expected: import failure for missing `scripts.v1_runtime`.

- [ ] **Step 3: Implement immutable evidence-aware transitions**

```python
def record_review(plan, state, head, diff_hash, paths):
    require_phase(state, "VERIFIED")
    receipt = state["verification"]
    if receipt["attempt_id"] != state["attempt_id"] or receipt["head"] != head or receipt["diff_hash"] != diff_hash:
        raise V1Error("V1_VERIFICATION_STALE", "verification does not match current attempt and diff")
    require_allowed_paths(plan, state["active_step"], paths)
    updated = copy.deepcopy(state)
    updated["review"] = {"attempt_id": state["attempt_id"], "head": head, "diff_hash": diff_hash, "paths": sorted(paths)}
    updated["phase"] = "REVIEWED"
    return updated
```

All transition functions return copies and never write files. Use phases `CHECKPOINT`, `EXECUTING`, `VERIFY_FAILED`, `VERIFIED`, `REVIEWED`, and `COMMITTED`. Starting a step clears prior receipts and accepts an injected UUID so tests remain deterministic.

- [ ] **Step 4: Run targeted and regression tests**

Run: `python -m unittest -v tests.test_v1_runtime`

Expected: transition and stale-evidence tests pass.

Run: `python -m unittest discover -s tests -v`

Expected: full suite passes.

- [ ] **Step 5: Update checkpoint, review, and commit**

Persist Task 4 receipt/journal/summary using the already-tested modules, run `git diff --check`, and review all paths.

```text
git add .harness/v1/state.json .harness/v1/journal.json .harness/v1/summary.json scripts/v1_runtime.py tests/test_v1_runtime.py
git commit -m "feat: enforce attempt-bound V1 transitions"
```

---

### Task 5: Reconcile Git and expose the enforced CLI

**Files:**
- Create: `scripts/v1_git.py`
- Create: `scripts/harness_v1.py`
- Create: `tests/test_v1_git.py`
- Create: `tests/test_v1_cli.py`
- Modify: `.harness/v1/state.json`
- Modify: `.harness/v1/journal.json`
- Modify: `.harness/v1/summary.json`
- Modify: `README.md`

**Interfaces:**
- Produces: `git_head(root: Path) -> str`, `changed_paths(root: Path) -> list[str]`, `diff_hash(root: Path) -> str`, `create_commit(root: Path, subject: str, paths: list[str]) -> str`.
- Produces: `reconcile(root: Path, contract: dict, plan: dict, state: dict, events: list[dict]) -> Reconciliation`.
- Produces CLI operations `inspect`, `start`, `verify -- <argv...>`, `review`, `commit -m SUBJECT`, and `checkpoint`.

- [ ] **Step 1: Write failing Git and CLI tests**

```python
def test_review_rejects_path_outside_step_scope(self):
    repo = initialized_repo(plan_scope=["allowed.txt"])
    (repo / "forbidden.txt").write_text("change", encoding="utf-8")
    result = run_cli(repo, "review")
    self.assertEqual(result.returncode, 2)
    self.assertEqual(json.loads(result.stderr)["code"], "V1_SCOPE_VIOLATION")

def test_commit_rejects_diff_changed_after_review(self):
    repo = repo_at_reviewed_state()
    (repo / "allowed.txt").write_text("changed again", encoding="utf-8")
    result = run_cli(repo, "commit", "-m", "step commit")
    self.assertEqual(json.loads(result.stderr)["code"], "V1_REVIEW_STALE")

def test_valid_cli_sequence_creates_one_commit_then_checkpoints(self):
    repo = initialized_repo(plan_scope=["allowed.txt"])
    run_valid_start_verify_review(repo)
    before = git_count(repo)
    self.assertEqual(run_cli(repo, "commit", "-m", "complete step").returncode, 0)
    self.assertEqual(git_count(repo), before + 1)
    self.assertEqual(run_cli(repo, "checkpoint").returncode, 0)
    self.assertEqual(load_state(repo)["phase"], "CHECKPOINT")
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `python -m unittest -v tests.test_v1_git tests.test_v1_cli`

Expected: imports fail for missing Git and CLI modules.

- [ ] **Step 3: Implement Git inspection and structured CLI dispatch**

```python
def diff_hash(root):
    unstaged = git_bytes(root, "diff", "--binary")
    staged = git_bytes(root, "diff", "--cached", "--binary")
    untracked = canonical_untracked_bytes(root)
    return hashlib.sha256(unstaged + b"\0" + staged + b"\0" + untracked).hexdigest()

def emit_error(error):
    print(json.dumps({"status": "error", "code": error.code, "message": str(error)}, sort_keys=True), file=sys.stderr)
    return 2
```

Each mutating CLI operation must: load and validate contract/plan/state/journal; reconcile Git; call one domain transition; atomically persist state; append exactly one event; regenerate the bounded summary. `commit` stages only declared paths plus V1 durable artifacts, creates one commit, and records its parent/result. `checkpoint` never creates a commit.

- [ ] **Step 4: Run targeted and regression tests**

Run: `python -m unittest -v tests.test_v1_git tests.test_v1_cli`

Expected: scope, stale review, ordered commit, checkpoint, and diagnostic tests pass.

Run: `python -m unittest discover -s tests -v`

Expected: full suite passes.

- [ ] **Step 5: Update checkpoint, review, and commit**

Run `python scripts/harness_v1.py inspect` and confirm reconciled output, then run `git diff --check` and review the complete diff.

```text
git add .harness/v1 README.md scripts/v1_git.py scripts/harness_v1.py tests/test_v1_git.py tests/test_v1_cli.py
git commit -m "feat: enforce V1 lifecycle through runtime CLI"
```

---

### Task 6: Recover safely from interruption and corruption

**Files:**
- Create: `scripts/v1_recovery.py`
- Create: `tests/test_v1_recovery.py`
- Modify: `scripts/harness_v1.py`
- Modify: `.harness/v1/state.json`
- Modify: `.harness/v1/journal.json`
- Modify: `.harness/v1/summary.json`

**Interfaces:**
- Produces: `classify_recovery(root: Path, contract: dict, plan: dict, state: dict, events: list[dict]) -> RecoveryResult`.
- Adds CLI operation `recover`, which reports or persists only a supported continuation classification; it never advances a step.
- Recovery actions: `RESUME_EXECUTION`, `REPAIR_ACTIVE_STEP`, `REVERIFY_STALE`, `CONTINUE_CHECKPOINT`, `MANUAL_RESOLUTION`.

- [ ] **Step 1: Write failing recovery tests**

```python
def test_recovery_finds_matching_uncheckpointed_commit(self):
    repo = repo_interrupted_after_commit()
    result = classify_recovery_from_disk(repo)
    self.assertEqual(result.action, "CONTINUE_CHECKPOINT")
    self.assertEqual(result.commit, git_head(repo))

def test_recovery_never_duplicates_existing_commit(self):
    repo = repo_interrupted_after_commit()
    before = git_count(repo)
    self.assertEqual(run_cli(repo, "recover").returncode, 0)
    self.assertEqual(git_count(repo), before)

def test_broken_journal_requires_manual_resolution(self):
    repo = repo_with_modified_journal_payload()
    result = run_cli(repo, "recover")
    self.assertEqual(json.loads(result.stdout)["action"], "MANUAL_RESOLUTION")
    self.assertEqual(json.loads(result.stdout)["code"], "V1_JOURNAL_HASH_MISMATCH")
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `python -m unittest -v tests.test_v1_recovery`

Expected: import failure for missing `scripts.v1_recovery`.

- [ ] **Step 3: Implement ordered recovery classification**

```python
def classify_recovery(root, contract, plan, state, events):
    try:
        validate_journal(events)
        reconciliation = reconcile(root, contract, plan, state, events)
    except V1Error as error:
        return RecoveryResult("MANUAL_RESOLUTION", error.code, None)
    if state["phase"] == "COMMITTED" and reconciliation.head == state["commit"]["commit"]:
        return RecoveryResult("CONTINUE_CHECKPOINT", None, reconciliation.head)
    if state["phase"] == "VERIFY_FAILED":
        return RecoveryResult("REPAIR_ACTIVE_STEP", None, None)
    if reconciliation.receipt_stale:
        return RecoveryResult("REVERIFY_STALE", "V1_VERIFICATION_STALE", None)
    return RecoveryResult("RESUME_EXECUTION", None, None)
```

`recover` may refresh the derived summary and append a `RECOVERY_CLASSIFIED` event only when the existing journal validates. It must not modify tracked implementation files, create commits, clear blockers, or checkpoint automatically.

- [ ] **Step 4: Run targeted and regression tests**

Run: `python -m unittest -v tests.test_v1_recovery`

Expected: interruption, stale evidence, corrupt journal, and no-duplicate-commit tests pass.

Run: `python -m unittest discover -s tests -v`

Expected: full suite passes.

- [ ] **Step 5: Update checkpoint, review, and commit**

Persist Task 6 evidence, run `git diff --check`, and inspect the full diff.

```text
git add .harness/v1 scripts/v1_recovery.py scripts/harness_v1.py tests/test_v1_recovery.py
git commit -m "feat: add deterministic V1 recovery"
```

---

### Task 7: Prove V1 end to end and close the checkpoint

**Files:**
- Create: `tests/test_v1_end_to_end.py`
- Create: `V1_PROOF_REPORT.md`
- Modify: `.harness/v1/state.json`
- Modify: `.harness/v1/journal.json`
- Modify: `.harness/v1/summary.json`
- Modify: `README.md`

**Interfaces:**
- Consumes all V1 modules and CLI operations.
- Produces the final V1 checkpoint and proof report; no reusable production API is introduced.

- [ ] **Step 1: Write the failing end-to-end proof test**

```python
def test_v1_proves_failure_pruning_recovery_and_git_state_agreement(self):
    repo = create_v1_demo_repo(max_events=4, max_bytes=1800)
    proof = run_v1_demo(repo, interrupt_after_step_2_commit=True)
    self.assertEqual(proof["failed_exit_code"], 1)
    self.assertEqual(proof["head_during_failure"], proof["step_1_commit"])
    self.assertEqual(proof["recovery_action"], "CONTINUE_CHECKPOINT")
    self.assertEqual(proof["commit_subjects"], ["demo: step 1", "demo: step 2"])
    self.assertLessEqual(proof["summary_event_count"], 4)
    self.assertLessEqual(proof["summary_bytes"], 1800)
    self.assertTrue(proof["journal_chain_valid"])
    self.assertEqual(proof["final_state"]["phase"], "CHECKPOINT")
    self.assertEqual(proof["final_head"], proof["final_state"]["checkpoint_head"])
    self.assertEqual(proof["worktree_status"], "")
```

- [ ] **Step 2: Run the proof test and confirm RED**

Run: `python -m unittest -v tests.test_v1_end_to_end`

Expected: failure because the V1 demo fixture/proof orchestration is not yet implemented.

- [ ] **Step 3: Implement the minimum controlled proof orchestration**

Keep demo helpers inside `tests/test_v1_end_to_end.py` unless a helper is also needed by users. Use a temporary Git repository, real CLI subprocesses, literal expected events, and locked small bounds that force pruning. Capture commit hashes and verification output from the run; do not hardcode ephemeral hashes.

The scenario must: initialize; complete Step 1; reload; start Step 2; fail verification; prove review/commit/checkpoint/activation blocked; repair Step 2; pass verification/review; create one commit; simulate interruption before checkpoint; invoke recovery; continue checkpoint; validate journal; validate summary bounds; validate Git/state agreement and a clean worktree.

- [ ] **Step 4: Run all final verification commands**

Run: `python scripts/harness_verify.py`

Expected: `contract 0.1 is LOCKED and unchanged`.

Run: `python -m unittest -v tests.test_v1_end_to_end`

Expected: end-to-end V1 proof passes.

Run: `python -m unittest discover -s tests -v`

Expected: every V0 and V1 test passes with zero failures and errors.

Run: `python scripts/harness_v1.py inspect`

Expected: locked V1 contract, valid journal chain, bounded summary, completed plan, `CHECKPOINT`, no active/next step, and matching HEAD.

Run: `git diff --check`

Expected: no output and exit code 0.

- [ ] **Step 5: Generate and review the proof report**

Write `V1_PROOF_REPORT.md` from the fresh outputs. Include the V0 baseline, V1 commit chain, intentional failure receipt, blocked-transition evidence, pruning limits/results, interruption/recovery result, journal terminal hash, final test count, Git/state identity, and excluded-capability audit. Do not claim a result that is absent from captured evidence.

- [ ] **Step 6: Checkpoint and commit V1 completion**

Update V1 state to completed Steps `[1, 2, 3, 4, 5, 6, 7]`,
`active_step: null`, `next_step: null`, and `phase: CHECKPOINT`; append the
terminal checkpoint event and regenerate the summary. Re-run the full suite
after these durable artifacts are final.

```text
git add .harness/v1 README.md tests/test_v1_end_to_end.py V1_PROOF_REPORT.md
git commit -m "test: complete V1 runtime and bounded memory proof"
```

- [ ] **Step 7: Verify final repository integrity**

Run: `python scripts/harness_verify.py`

Run: `python -m unittest discover -s tests -v`

Run: `python scripts/harness_v1.py inspect`

Run: `git status --short --branch`

Expected: both contracts validate, the full suite passes, V1 is at its final checkpoint, and the worktree is clean. Stop without starting a later version.
