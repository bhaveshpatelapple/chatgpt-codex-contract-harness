# Deterministic Offline Learning Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and prove a deterministic, repository-local learning harness with bounded L3 retrieval, verified L4 episodes, selective L5 skills, a gated skill-evolution lifecycle, permissioned role orchestration, independent ablations, restart persistence, and a fresh-session learning demonstration.

**Architecture:** Focused Python modules under `harness_learning/` exchange immutable dataclasses and persist canonical, versioned JSON envelopes beneath `.harness/learning/`. A bounded context composer consumes deterministic retrieval results, while a capability dispatcher and orchestrator enforce role and verification boundaries. The offline adapter provides reproducible plans, attempts, repairs, and skill candidates; an optional protocol permits later model integration without affecting core tests.

**Tech Stack:** Python 3.11+, standard library (`dataclasses`, `enum`, `hashlib`, `json`, `pathlib`, `tempfile`, `typing`, `unittest`) and existing PyYAML 6.x dependency.

## Global Constraints

- Preserve the locked V0 contract, history, tests, and behavior.
- Core behavior and the full acceptance suite must run without network access or credentials.
- Runtime state uses versioned JSON/JSONL beneath `.harness/learning/`; tests use temporary directories.
- Every production behavior is introduced by a test that is observed failing for the expected reason.
- Every task ends with targeted tests, full regression tests, diff review, and one focused commit.
- L4 and L5 reads are independently ablatable; ablation never deletes stored knowledge.
- No matrix row is complete without direct behavioral verification.

---

## File Map

- `harness_learning/__init__.py`: stable public imports only.
- `harness_learning/models.py`: enums, errors, immutable records, canonical JSON, deterministic IDs.
- `harness_learning/persistence.py`: validated atomic JSON record stores.
- `harness_learning/retrieval.py`: lexical scoring, exclusions, stable bounded selection.
- `harness_learning/episodes.py`: verified episode admission and L4 retrieval facade.
- `harness_learning/skills.py`: skill registry, trigger selection, evaluation, rejection, merge, promotion.
- `harness_learning/context.py`: budgets, L0-L5 composition, typed manifest.
- `harness_learning/roles.py`: roles, capabilities, permission dispatcher.
- `harness_learning/adapters.py`: deterministic offline adapter and optional adapter protocol.
- `harness_learning/orchestrator.py`: run lifecycle and verification-bound advancement.
- `harness_learning/demo.py`: controlled proof runner and JSON CLI output.
- `.harness/learning/config.json`: checked-in schema version, thresholds, and budgets.
- `tests/test_learning_models.py`: identity and validation.
- `tests/test_learning_persistence.py`: atomic save, reload, corruption rejection.
- `tests/test_learning_retrieval.py`: relevance, staleness, ordering, item/byte bounds.
- `tests/test_learning_episodes.py`: admission, idempotency, exclusion.
- `tests/test_learning_skills.py`: triggers and every evolution decision.
- `tests/test_learning_context.py`: typed manifests, long-run bounds, ablations.
- `tests/test_learning_roles.py`: permission boundaries.
- `tests/test_learning_orchestrator.py`: lifecycle, mismatch and stale-receipt blocking.
- `tests/test_learning_restart.py`: fresh-object and fresh-process reload.
- `tests/test_learning_end_to_end.py`: complete fail-to-fresh-session-reuse proof.

### Task 1: Canonical records and atomic persistence

**Files:**
- Create: `harness_learning/__init__.py`
- Create: `harness_learning/models.py`
- Create: `harness_learning/persistence.py`
- Create: `tests/test_learning_models.py`
- Create: `tests/test_learning_persistence.py`

**Interfaces:**
- Produces: `canonical_json(value) -> str`, `stable_id(kind, value) -> str`, `HarnessError(code, message)`, `VerificationStatus`, `Episode`, `Skill`, `JsonRecordStore(path, kind, decoder)`.
- `JsonRecordStore.load() -> tuple[T, ...]`, `upsert(record) -> T`, and `replace(records) -> None` validate before mutation and write an envelope with `schema_version`, `kind`, and `records`.

- [ ] **Step 1: Write failing identity and validation tests**

```python
def test_stable_id_ignores_mapping_order():
    self.assertEqual(stable_id("episode", {"a": 1, "b": 2}),
                     stable_id("episode", {"b": 2, "a": 1}))

def test_episode_requires_passed_verification():
    with self.assertRaisesRegex(HarnessError, "EPISODE_UNVERIFIED"):
        Episode.create(task_kind="replace", failure="x", repair="y",
                       lesson="replace x with y", tags=("replace",),
                       verification_status=VerificationStatus.FAILED,
                       verification_id="verify-1", created_sequence=1)
```

- [ ] **Step 2: Run and observe the expected missing-module failure**

Run: `python -m unittest tests.test_learning_models -v`

Expected: import failure for `harness_learning.models`.

- [ ] **Step 3: Implement canonical models minimally**

Define frozen dataclasses with `to_dict`/`from_dict`, tuple normalization, stable IDs prefixed `episode_` or `skill_`, and `HarnessError.code`. Reject empty semantic fields, non-passing episode evidence, identical failure/repair, invalid scores outside `0.0..1.0`, and unknown statuses.

- [ ] **Step 4: Run model tests and observe them pass**

Run: `python -m unittest tests.test_learning_models -v`

- [ ] **Step 5: Write failing persistence tests**

```python
def test_store_round_trips_with_same_identity(self):
    store = JsonRecordStore(self.path, "episode", Episode.from_dict)
    stored = store.upsert(self.episode)
    reloaded = JsonRecordStore(self.path, "episode", Episode.from_dict).load()
    self.assertEqual((stored,), reloaded)

def test_conflicting_duplicate_does_not_replace_valid_store(self):
    store = JsonRecordStore(self.path, "episode", Episode.from_dict)
    store.upsert(self.episode)
    before = self.path.read_bytes()
    with self.assertRaisesRegex(HarnessError, "STORE_ID_CONFLICT"):
        store.replace((self.episode, conflicting_record_with_same_id()))
    self.assertEqual(before, self.path.read_bytes())
```

- [ ] **Step 6: Run persistence tests and observe the expected missing-class failure**

Run: `python -m unittest tests.test_learning_persistence -v`

- [ ] **Step 7: Implement validated atomic persistence minimally**

Use `path.with_suffix(path.suffix + ".tmp")`, write canonical JSON plus newline, flush and `os.fsync`, then `Path.replace`. Validate the complete envelope before replacement. Reject invalid JSON as `STORE_CORRUPT`, schema mismatches as `STORE_SCHEMA`, kind mismatches as `STORE_KIND`, and conflicting IDs as `STORE_ID_CONFLICT`.

- [ ] **Step 8: Verify Task 1 and commit**

Run: `python -m unittest tests.test_learning_models tests.test_learning_persistence -v`

Run: `python -m unittest discover -s tests -v`

Run: `git diff --check`

Commit: `git commit -am "feat: add learning records and atomic persistence"` after explicitly adding new files.

### Task 2: L3 deterministic bounded retrieval

**Files:**
- Create: `harness_learning/retrieval.py`
- Create: `tests/test_learning_retrieval.py`
- Modify: `harness_learning/__init__.py`

**Interfaces:**
- Consumes records exposing `id`, `search_text`, `task_kind`, `tags`, `verification_status`, `created_sequence`, and `expiry_sequence`.
- Produces `RetrievalQuery`, `RetrievalHit`, `RetrievalResult`, `tokenize(text)`, and `retrieve(candidates, query) -> RetrievalResult`.

- [ ] **Step 1: Write failing relevance and exclusion tests**

```python
def test_retrieval_excludes_stale_failed_and_irrelevant_records():
    result = retrieve(self.candidates, RetrievalQuery(
        text="replace greeting token", task_kind="replace",
        allowed_kinds=("episode",), required_tags=(), excluded_ids=(),
        current_sequence=20, minimum_score=0.2, item_limit=4,
        byte_limit=2048))
    self.assertEqual([self.relevant.id], [hit.record_id for hit in result.hits])
    self.assertEqual({"expired", "verification_failed", "irrelevant"},
                     set(result.exclusion_reasons.values()))
```

- [ ] **Step 2: Run and observe failure because retrieval is absent**

Run: `python -m unittest tests.test_learning_retrieval -v`

- [ ] **Step 3: Implement normalized scoring and stable selection**

Tokenize with Unicode normalization and the expression `[\w]+`. Score token intersection divided by query-token count, plus `0.20` task-kind match, `0.10` tag overlap, and at most `0.05` recency. Exclude before sorting. Sort by `(-score, record_id)`. Measure each selected record as UTF-8 bytes of its canonical hit JSON and never exceed item or byte limits.

- [ ] **Step 4: Add and observe failing growth-bound test**

```python
def test_selection_stays_bounded_as_history_grows():
    for size in (10, 100, 1000):
        result = retrieve(make_relevant_candidates(size), self.query)
        self.assertLessEqual(len(result.hits), self.query.item_limit)
        self.assertLessEqual(result.used_bytes, self.query.byte_limit)
```

- [ ] **Step 5: Complete byte-budget accounting and verify**

Run: `python -m unittest tests.test_learning_retrieval -v`

Run: `python -m unittest discover -s tests -v`

Run: `git diff --check`

Commit: `git commit -am "feat: add bounded deterministic retrieval"` after explicitly adding new files.

### Task 3: L4 verified episodic memory

**Files:**
- Create: `harness_learning/episodes.py`
- Create: `tests/test_learning_episodes.py`
- Modify: `harness_learning/__init__.py`

**Interfaces:**
- Consumes `JsonRecordStore[Episode]`, `RetrievalQuery`, and `retrieve`.
- Produces `EpisodeStore.admit(...) -> Episode`, `EpisodeStore.all()`, and `EpisodeStore.retrieve(query) -> RetrievalResult`.

- [ ] **Step 1: Write failing episode admission tests**

```python
def test_only_verified_repairs_are_admitted():
    with self.assertRaisesRegex(HarnessError, "EPISODE_UNVERIFIED"):
        self.store.admit(task_kind="replace", failure="wrong", repair="right",
                         lesson="use right", tags=("replace",),
                         verification_status=VerificationStatus.FAILED,
                         verification_id="v1", created_sequence=1)
    self.assertEqual((), self.store.all())

def test_duplicate_admission_is_idempotent():
    first = self.admit_verified()
    second = self.admit_verified()
    self.assertEqual(first.id, second.id)
    self.assertEqual(1, len(self.store.all()))
```

- [ ] **Step 2: Run and observe failure because `EpisodeStore` is absent**

Run: `python -m unittest tests.test_learning_episodes -v`

- [ ] **Step 3: Implement admission and retrieval facade**

Construct `Episode` only after all invariants pass, then upsert. Map episodes into retrieval candidates without weakening verified-only or expiry filters.

- [ ] **Step 4: Add direct stale and unrelated exclusion assertions**

Create one relevant, one expired, and one unrelated episode; assert only the relevant ID is returned and both exclusions are recorded.

- [ ] **Step 5: Verify Task 3 and commit**

Run: `python -m unittest tests.test_learning_episodes -v`

Run: `python -m unittest discover -s tests -v`

Run: `git diff --check`

Commit: `git commit -am "feat: add verified episodic memory"` after explicitly adding new files.

### Task 4: L5 skills and evolution gate

**Files:**
- Create: `harness_learning/skills.py`
- Create: `tests/test_learning_skills.py`
- Modify: `harness_learning/models.py`
- Modify: `harness_learning/__init__.py`

**Interfaces:**
- Produces `SkillCandidate`, `EvaluationCase`, `GateDecision`, `GateOutcome`, `SkillRegistry.evaluate_and_store(candidate, episodes)`, and `SkillRegistry.trigger(query) -> RetrievalResult`.
- Gate outcomes are `PROMOTED`, `MERGED`, and `REJECTED`, with stable reason codes.

- [ ] **Step 1: Write failing trigger-selectivity tests**

```python
def test_skill_triggers_for_related_task_but_not_unrelated_task():
    self.registry.add_promoted(self.skill)
    related = self.registry.trigger(self.query("replace greeting token", "replace"))
    unrelated = self.registry.trigger(self.query("calculate invoice tax", "math"))
    self.assertEqual([self.skill.id], [hit.record_id for hit in related.hits])
    self.assertEqual((), unrelated.hits)
```

- [ ] **Step 2: Run and observe failure because the registry is absent**

Run: `python -m unittest tests.test_learning_skills -v`

- [ ] **Step 3: Implement promoted-skill storage and trigger matching**

Require task-kind equality when configured and minimum trigger overlap `0.5`. Delegate bounded ordering to L3 retrieval; never return rejected candidates.

- [ ] **Step 4: Write failing evolution-gate tests**

Cover these exact outcomes: missing source episode → `REJECTED/SOURCE_UNVERIFIED`; destructive or bypass procedure → `REJECTED/SAFETY`; evaluation pass ratio below `0.8` → `REJECTED/EVALUATION`; quality below `0.7` → `REJECTED/QUALITY`; valid candidate → `PROMOTED`; exact duplicate → `REJECTED/EXACT_DUPLICATE`; compatible overlap at or above `0.8` → `MERGED`; conflicting procedure at the same trigger similarity → `REJECTED/DUPLICATE_CONFLICT`.

- [ ] **Step 5: Run and observe failures for missing gate behavior**

Run: `python -m unittest tests.test_learning_skills -v`

- [ ] **Step 6: Implement ordered gates and deterministic merge**

Safety-match normalized procedure text against `bypass permission`, `skip verification`, `disable contract`, `rm -rf`, and `delete repository`. Offline evaluation counts cases whose expected tokens are all present in the candidate procedure. Merge sorted unique evidence IDs and evaluation cases, increment revision once, retain the greater quality, and persist atomically.

- [ ] **Step 7: Verify Task 4 and commit**

Run: `python -m unittest tests.test_learning_skills -v`

Run: `python -m unittest discover -s tests -v`

Run: `git diff --check`

Commit: `git commit -am "feat: add selective skills and evolution gate"` after explicitly adding new files.

### Task 5: Bounded L0-L5 context manifests and ablations

**Files:**
- Create: `harness_learning/context.py`
- Create: `.harness/learning/config.json`
- Create: `tests/test_learning_context.py`
- Modify: `harness_learning/__init__.py`

**Interfaces:**
- Produces `LayerBudget`, `ContextConfig.from_path`, `ContextRequest`, `ContextManifest`, and `ContextComposer.compose(request, references, episodes, skills)`.
- Manifests expose `layers["L0"]` through `layers["L5"]`, total budget/usage, query ID, and `{enable_l4, enable_l5}`.

- [ ] **Step 1: Write failing typed-manifest test**

```python
def test_manifest_records_all_typed_layers_and_budgets():
    manifest = self.composer.compose(self.request, self.refs, self.episodes, self.skills)
    self.assertEqual([f"L{i}" for i in range(6)], list(manifest.layers))
    for name, layer in manifest.layers.items():
        self.assertEqual(name, layer.layer_type)
        self.assertLessEqual(layer.used_items, layer.item_budget)
        self.assertLessEqual(layer.used_bytes, layer.byte_budget)
    self.assertLessEqual(manifest.used_bytes, manifest.total_byte_budget)
```

- [ ] **Step 2: Run and observe failure because composer is absent**

Run: `python -m unittest tests.test_learning_context -v`

- [ ] **Step 3: Implement budgets and manifest composition**

Use checked-in defaults: total `16384` bytes; L0 `2/2048`; L1 `4/2048`; L2 `4/3072`; L3 `8/4096`; L4 `4/3072`; L5 `3/3072`. Mandatory L0-L2 overflow raises `CONTEXT_MANDATORY_OVERFLOW`; optional L3-L5 records are omitted before overflow and their IDs receive `layer_budget` or `total_budget` exclusion reasons.

- [ ] **Step 4: Add failing long-history and four-way ablation tests**

For histories of 10, 100, and 1000 records, assert identical upper bounds and typed manifests. Exercise `(L4,L5)` values `(on,on)`, `(off,on)`, `(on,off)`, `(off,off)` and assert only the selected layers change while L0-L3 IDs stay identical.

- [ ] **Step 5: Implement independent ablation behavior and verify**

Disabled layers have `enabled: false`, zero usage, no selected IDs, and exclusion reason `ablated`. They do not modify stores or the other optional layer.

Run: `python -m unittest tests.test_learning_context -v`

Run: `python -m unittest discover -s tests -v`

Run: `git diff --check`

Commit: `git commit -am "feat: compose bounded context with independent ablations"` after explicitly adding new files.

### Task 6: Permissioned multi-role orchestration

**Files:**
- Create: `harness_learning/roles.py`
- Create: `harness_learning/adapters.py`
- Create: `harness_learning/orchestrator.py`
- Create: `tests/test_learning_roles.py`
- Create: `tests/test_learning_orchestrator.py`
- Modify: `harness_learning/__init__.py`

**Interfaces:**
- Produces `Role`, `Capability`, `PermissionDenied`, `RoleDispatcher.perform(role, capability, operation)`, `OfflineAdapter`, `ModelAdapter` protocol, `RunState`, `Attempt`, `VerificationReceipt`, and `LearningOrchestrator`.
- `advance(receipt)` accepts only a verifier-produced passing receipt whose `run_id` and `attempt_id` equal the active state.

- [ ] **Step 1: Write failing permission-matrix tests**

Define the exact matrix: planner `{READ_CONTEXT, WRITE_PLAN}`; executor `{READ_PLAN, WRITE_ATTEMPT}`; verifier `{READ_ATTEMPT, WRITE_VERIFICATION}`; repair `{READ_FAILURE, READ_CONTEXT, WRITE_ATTEMPT}`; memory `{READ_VERIFIED_RUN, WRITE_EPISODE, PROPOSE_SKILL}`. For every role/capability pair, assert allowed pairs execute and denied pairs raise `PERMISSION_DENIED` without calling the operation.

- [ ] **Step 2: Run and observe failure because role dispatch is absent**

Run: `python -m unittest tests.test_learning_roles -v`

- [ ] **Step 3: Implement immutable permission sets and dispatcher**

Check permission before evaluating the supplied zero-argument operation. Include role and capability in the stable diagnostic.

- [ ] **Step 4: Write failing lifecycle enforcement tests**

```python
def test_failed_verification_blocks_advancement_and_allows_repair():
    run = self.orchestrator.start(self.task)
    failed = self.orchestrator.verify(run.active_attempt.id, expected="hello world")
    self.assertEqual(VerificationStatus.FAILED, failed.status)
    with self.assertRaisesRegex(HarnessError, "ADVANCE_BLOCKED"):
        self.orchestrator.advance(failed)
    repaired = self.orchestrator.repair(failed)
    self.assertEqual(run.id, repaired.run_id)

def test_stale_or_foreign_receipt_cannot_advance():
    with self.assertRaisesRegex(HarnessError, "VERIFICATION_STALE"):
        self.orchestrator.advance(dataclasses.replace(self.passed, attempt_id="other"))
```

Also mutate a temporary contract without updating its lock and assert `start` raises `CONTRACT_MISMATCH` before any run record is written.

- [ ] **Step 5: Run and observe lifecycle failures**

Run: `python -m unittest tests.test_learning_orchestrator -v`

- [ ] **Step 6: Implement offline adapter and verification-bound lifecycle**

The adapter deterministically maps a plan to an attempt, a failed receipt to a repaired attempt, and a verified episode to a skill candidate. Orchestrator construction receives contract/lock paths, composer, episode store, skill registry, and adapter. `start` calls the existing contract validator before creating state. Only dispatcher-authorized methods mutate the active run.

- [ ] **Step 7: Verify Task 6 and commit**

Run: `python -m unittest tests.test_learning_roles tests.test_learning_orchestrator -v`

Run: `python -m unittest discover -s tests -v`

Run: `git diff --check`

Commit: `git commit -am "feat: enforce permissioned learning orchestration"` after explicitly adding new files.

### Task 7: Restart-safe learning state

**Files:**
- Create: `tests/test_learning_restart.py`
- Modify: `harness_learning/orchestrator.py`
- Modify: `harness_learning/persistence.py`

**Interfaces:**
- Produces `LearningOrchestrator.open(root, contract_path, lock_path, adapter)` and persisted `runs.json`, `episodes.json`, and `skills.json` envelopes under the supplied root.

- [ ] **Step 1: Write failing fresh-object reload test**

Persist one run, episode, promoted skill, and failed receipt; discard all objects; reopen from the same directory; assert identical IDs/statuses and that repair resumes the same run and creates a new attempt ID.

- [ ] **Step 2: Run and observe failure because reopen is absent**

Run: `python -m unittest tests.test_learning_restart -v`

- [ ] **Step 3: Implement `open` and run-state serialization**

Validate all envelopes before constructing the orchestrator. Reject a run referencing a missing attempt, episode, or skill as `STORE_REFERENCE`. Do not rewrite valid files during a read-only open.

- [ ] **Step 4: Add fresh-process persistence test**

Use `subprocess.run([sys.executable, "-m", "harness_learning.demo", "inspect", root], ...)` against a temporary persisted proof directory and assert returned episode/skill/run IDs match the parent process.

- [ ] **Step 5: Verify Task 7 and commit**

Run: `python -m unittest tests.test_learning_restart -v`

Run: `python -m unittest discover -s tests -v`

Run: `git diff --check`

Commit: `git commit -am "feat: reload learning state across restarts"` after explicitly adding new files.

### Task 8: Controlled end-to-end learning proof

**Files:**
- Create: `harness_learning/demo.py`
- Create: `tests/test_learning_end_to_end.py`
- Create: `LEARNING_HARNESS_PROOF_REPORT.md`
- Modify: `README.md`
- Modify: `harness_learning/__init__.py`

**Interfaces:**
- Produces `run_learning_demo(root) -> dict` and CLI commands `python -m harness_learning.demo run [root]` and `inspect <root>`.

- [ ] **Step 1: Write failing end-to-end acceptance test**

Assert the returned proof contains, in order: initial failure; blocked advancement; repaired passing receipt; admitted episode ID; promoted skill ID; bad candidate rejection; duplicate decision; permission denial; pre/post-restart identical IDs; related episode retrieval; unrelated episode exclusion; related skill trigger; unrelated skill non-trigger; successful fresh-session reuse without repair; four ablation manifests; and context sizes within bounds for synthetic histories of 10, 100, and 1000.

- [ ] **Step 2: Run and observe failure because the demo is absent**

Run: `python -m unittest tests.test_learning_end_to_end -v`

- [ ] **Step 3: Implement the minimal proof runner**

Use a replace-text task whose first attempt returns `wrong value\n`; repair returns `hello world\n`; the learned episode lesson and promoted skill teach replacement of the wrong token. Reopen all stores and orchestration objects before a related `hello codex\n` task. The offline adapter must choose the learned skill procedure and pass on its first attempt. Emit canonical JSON proof data only.

- [ ] **Step 4: Run the focused proof and inspect every assertion**

Run: `python -m unittest tests.test_learning_end_to_end -v`

Run: `python -m harness_learning.demo run`

- [ ] **Step 5: Produce the proof report from observed evidence**

Document exact test counts, command exits, manifest budgets/usages, exclusion reasons, gate outcomes, role-denial result, restart identity checks, ablation matrix, and learning-flow IDs. Do not copy expected values without matching them to the fresh demo output.

- [ ] **Step 6: Run the final acceptance gate**

Run: `python scripts/harness_verify.py`

Run: `python -m unittest discover -s tests -v`

Run: `python -m harness_learning.demo run`

Run: `git diff --check`

Run: `git status --short --branch`

Expected: contract unchanged; all tests pass with zero failures; demo exits zero and contains all proof stages; diff check passes; only Task 8 intended files are pending before commit.

- [ ] **Step 7: Commit the proof and documentation**

Commit: `git commit -am "test: prove deterministic learning harness end to end"` after explicitly adding new files.

- [ ] **Step 8: Re-run verification from the committed tree**

Run all four final acceptance commands again. Record the committed `HEAD`, commit chain, and final clean Git status in the completion matrix. Mark a row complete only if its direct tests and proof evidence passed in this fresh run.
