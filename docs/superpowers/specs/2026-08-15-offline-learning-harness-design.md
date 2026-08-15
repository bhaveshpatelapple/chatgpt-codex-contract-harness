# Deterministic Offline Learning Harness Design

## Status

Approved in conversation on 2026-08-15. This design extends the verified V0
baseline without weakening its contract lock, sequential verification gate, or
persistent execution state.

## Goal

Implement and verify L3 retrieval, L4 episodic memory, L5 learned skills, a
skill-evolution gate, permissioned multi-role orchestration, independent L4/L5
ablations, restart-safe persistence, and a controlled end-to-end learning
demonstration. The default implementation is deterministic and works offline.
Model-backed behavior may be supplied through an optional adapter, but no test
or core capability depends on network access or model output.

## Repository Layout

Production modules live in `harness_learning/` and expose small typed APIs:

- `models.py`: immutable records, enums, validation, canonical serialization,
  deterministic identifiers, and clock injection.
- `persistence.py`: repository-local versioned JSON/JSONL stores with atomic
  replacement, schema checks, and deterministic reload.
- `retrieval.py`: tokenization, weighted lexical scoring, filtering, stable
  tie-breaking, and bounded selection.
- `episodes.py`: verified-repair episode admission and L4 retrieval.
- `skills.py`: skill registry, trigger matching, candidate evaluation,
  rejection, deterministic duplicate merging, and promotion.
- `context.py`: L0-L5 composition, typed manifests, per-layer budgets, and a
  total encoded-byte budget.
- `roles.py`: planner, executor, verifier, repair, and memory roles with a
  capability-enforcing dispatcher.
- `orchestrator.py`: deterministic lifecycle coordination without bypassing
  verification or role permissions.
- `adapters.py`: offline default adapter and an optional model-adapter
  protocol. No OpenAI dependency is added to the core package.
- `demo.py`: the controlled learning proof used by tests and the command-line
  demonstration.

Persistent runtime data lives under `.harness/learning/`. Tests use temporary
directories and never mutate the checked-in runtime data.

## Data Model and Persistence

All persisted envelopes contain `schema_version`, `kind`, and `records`.
Records have deterministic IDs derived from canonical JSON of their stable
content. Volatile observation fields are not part of identity. JSON is emitted
with sorted keys and normalized newlines. Stores reject unknown schema versions,
invalid JSON, duplicate IDs with conflicting content, and incorrect record
kinds.

Writes create a same-directory temporary file, flush it, and replace the target
atomically. A failed validation or interrupted pre-replacement write cannot
alter the last valid store. Episodes and skills reload into fresh objects with
the same IDs, status, evidence, triggers, and evaluation results.

Checked-in configuration defines exact budgets, thresholds, and ablation
defaults. Generated episodes, skills, manifests, and run receipts are runtime
artifacts rather than required source-controlled state.

## L3 Retrieval

Retrieval normalizes Unicode text, lowercases it, and extracts alphanumeric
tokens. Candidates are scored deterministically using weighted token overlap,
exact task-kind match, explicit tags, verification quality, and bounded recency.
The API accepts candidate kinds, query text, task kind, required tags, excluded
IDs, minimum score, item limit, and encoded-byte limit.

Candidates with expired validity, mismatched required tags, disallowed kind,
failed verification, zero relevant overlap, or a score below the configured
minimum are excluded before selection. Results use descending score followed by
ascending deterministic ID. Selection stops before either the item or byte
budget would be exceeded. Growing the candidate store cannot grow the returned
selection beyond those bounds.

## L4 Episodes

An episode records the task signature, observed failure, repair, verification
evidence, reusable lesson, tags, creation sequence, and optional expiry
sequence. The store admits an episode only when verification status is `PASSED`,
the repair differs from the failure, and a nonempty reusable lesson exists.

L4 retrieval delegates to L3 and adds task-kind, expiry, and verified-only
filters. Stale, failed, irrelevant, or explicitly excluded episodes never enter
the composed context. Duplicate episodes with the same stable identity are
idempotent rather than creating extra records.

## L5 Skills and Evolution Gate

A skill contains a name, purpose, trigger tokens, procedure steps, source
episode IDs, evaluation cases, quality score, status, and revision. Triggering
requires both a configured minimum overlap and any required task-kind match.
Selection is deterministic, bounded, and returns no skill for unrelated input.

Candidates pass through these gates in order:

1. schema and nonempty-field validation;
2. source evidence references only verified episodes;
3. safety validation rejects procedures that request permission bypass,
   verification bypass, destructive broad operations, or contract mutation;
4. deterministic offline evaluation meets the configured pass ratio;
5. minimum quality score;
6. duplicate detection by normalized trigger/procedure similarity.

A failed gate records a rejection reason and cannot promote the candidate. An
exact duplicate is rejected idempotently. A compatible near-duplicate merges
source evidence and evaluation cases into the existing skill, increments its
revision, and retains the higher quality score. A materially conflicting
near-duplicate is rejected. Only accepted or merged skills are selectable.

## Context Composer and Manifest

The composer accepts typed sources for:

- L0: locked contract identity and immutable invariants;
- L1: active policy and role permissions;
- L2: current task and execution state;
- L3: bounded retrieved reference records;
- L4: bounded relevant episodes;
- L5: bounded triggered skills.

Each layer has an item limit and encoded-byte limit, and the complete manifest
has a total encoded-byte limit. L0-L2 reserve their configured budgets before
optional L3-L5 content is selected. If mandatory content alone exceeds its
budget, composition fails explicitly. Optional records are selected in stable
priority order and omitted before they can exceed a layer or total budget.

The emitted `context_manifest` records schema version, query identity, ablation
settings, total budget and usage, and for every L0-L5 layer: type, enabled
state, item budget, byte budget, used item count, used bytes, selected record
IDs, scores where applicable, and exclusion reasons. Synthetic histories of
increasing size must produce manifests that remain within identical configured
bounds.

## Multi-Role Orchestration and Permissions

The five roles are:

- planner: reads contract, policy, state, and context; writes a bounded plan;
- executor: reads the approved plan and task state; writes an attempt result;
- verifier: reads the attempt and expected outcome; writes verification only;
- repair: reads failed verification and context; writes a repaired attempt;
- memory: reads only verified run evidence; writes episodes and proposes skills.

Capabilities are explicit enum values checked by a central dispatcher before
every operation. Roles cannot acquire capabilities from their input. Planner,
executor, repair, and memory cannot mark verification as passed or advance the
workflow. Verifier cannot alter attempts, episodes, skills, or state. Memory
cannot learn from failed or unverified evidence. Unauthorized operations raise
a stable `PermissionDenied` error and produce no mutation.

The orchestrator advances only after a verifier-produced passing receipt bound
to the current run and attempt. Failure retains the same run, blocks advancement,
and permits a repair attempt. All role inputs and outputs are bounded records.

## Ablations

`enable_l4` and `enable_l5` are independent settings accepted by the composer
and orchestrator. Disabling L4 prevents episode retrieval and records L4 as
disabled without changing L5 behavior. Disabling L5 prevents skill triggering
and records L5 as disabled without changing L4 behavior. Disabling both leaves
L0-L3 unchanged. Ablations affect reads and reuse, not deletion or corruption
of persisted records.

## Controlled End-to-End Proof

The deterministic demonstration performs this complete flow:

1. start with empty temporary episode and skill stores;
2. plan and execute a task using an intentionally wrong first strategy;
3. verify failure and prove advancement is blocked;
4. compose bounded repair context and execute a successful repair;
5. verify success and admit a verified repair episode;
6. generate a candidate skill from that episode;
7. evaluate and promote the skill through the evolution gate;
8. destroy all in-memory harness objects;
9. create a fresh harness instance from the same persisted directory;
10. retrieve the relevant episode and trigger the promoted skill;
11. reuse the learned procedure to succeed on a related task without repair;
12. emit a proof receipt containing IDs, manifests, gate decisions,
    verification receipts, ablation checks, and persistence identities.

The proof separately demonstrates unrelated episode exclusion, unrelated skill
non-triggering, duplicate and bad-skill rejection or merge, permission denial,
contract-lock checking before orchestration, bounded context under growing
synthetic history, and independent L4/L5 ablations.

## Error Handling

Public operations fail closed with stable exceptions for invalid schema,
budget overflow, corrupt persistence, permission denial, stale verification,
contract mismatch, and invalid lifecycle transitions. A failing operation does
not partially mutate persisted stores or orchestration state. Errors include a
machine-readable code and concise diagnostic; they do not silently repair or
discard evidence.

## Verification Strategy

Every production behavior is introduced test-first. Unit tests cover canonical
identity, atomic persistence, scoring and filtering, episode admission, skill
triggering, every evolution gate, duplicate merge behavior, byte and item
budgets, manifest typing, permission enforcement, and lifecycle transitions.
Integration tests use temporary directories and fresh processes or objects for
restart verification. Ablation tests exercise all four L4/L5 combinations.
The end-to-end test asserts every numbered proof stage and receipt identity.

The final gate is:

- the unchanged V0 contract validator;
- all existing V0 regression tests;
- the complete learning-harness unit and integration suite;
- the controlled end-to-end demonstration;
- `git diff --check` and a clean worktree after focused commits.

No row in the completion matrix may be marked complete without a direct test
or demonstration result for its stated acceptance properties.
