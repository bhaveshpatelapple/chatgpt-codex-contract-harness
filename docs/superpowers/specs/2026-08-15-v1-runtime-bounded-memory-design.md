# V1 Runtime Enforcement and Bounded Memory Design

## Status

Approved for specification on 2026-08-15. This document defines V1 only. The
completed V0 contract, plan, state, proof report, and Git history remain an
immutable baseline.

## Goal

Strengthen the contract-locked harness so repository transitions are enforced
by a runtime command layer and execution can resume from compact, deterministic,
file-backed context without relying on conversation history.

## Scope

V1 will add:

- a runtime command layer for starting, verifying, reviewing, committing,
  checkpointing, inspecting, and recovering one planned step;
- precondition checks that reconcile the locked contract, plan, state,
  verification receipt, worktree, and Git HEAD before every transition;
- durable, append-only execution journal entries written atomically;
- deterministic checkpoint summaries with configured entry-count and byte-size
  limits;
- deterministic pruning that preserves essential recovery context;
- explicit detection and blocking of stale receipts, corrupt state, interrupted
  writes, dirty-scope violations, and Git/state divergence;
- an end-to-end V1 proof covering failure, reload, pruning, repair, commit, and
  recovery;
- regression coverage that preserves every V0 behavior.

V1 will not add vector search, embeddings, RAG, cloud persistence, a web UI,
multi-agent orchestration, Agents SDK orchestration, episodic memory, or
self-evolving skills.

## Contract and Versioning

V0 remains locked and unchanged. V1 receives its own machine-readable contract,
lock digest, ordered plan, execution state, and proof report. V1 artifacts must
reference the V0 completion commit as their baseline. A V1 transition must fail
if that baseline identity cannot be reconciled with repository history.

The V1 contract will lock the runtime commands, required evidence, memory
limits, invariants, exclusions, and final proof obligations before feature
implementation begins.

## Architecture

### Runtime command layer

A single command-line entry point will expose narrowly scoped operations:

- `inspect`: report reconciled contract, plan, state, journal, and Git status;
- `start`: activate exactly the recorded next step;
- `verify`: run an argument-list verification command and persist its complete
  receipt;
- `review`: validate scope and record review evidence for the current diff;
- `commit`: create the focused step commit only after passing verification and
  review;
- `checkpoint`: reconcile the created commit with state and close the step;
- `recover`: rebuild the authoritative resumable view from valid durable
  artifacts without advancing execution.

The runtime command layer will call focused domain functions rather than embed
transition rules directly in command parsing. Existing V0 state behavior will
remain covered by regression tests while V1 introduces stricter evidence-aware
state transitions.

### Reconciliation engine

Before a mutating command, the reconciliation engine will validate:

1. the V1 contract is locked and its digest matches;
2. the plan is valid and the state describes an ordered prefix;
3. at most one step is active;
4. recorded evidence belongs to the active step and current attempt;
5. the worktree scope matches the active step's declared paths;
6. the recorded base and checkpoint commits exist in the current history;
7. Git HEAD agrees with the lifecycle phase;
8. journal sequence numbers and hashes form an unbroken chain.

Any disagreement produces a nonzero result and a structured diagnostic. The
engine never guesses, rewrites the contract, advances a step, or discards
evidence automatically.

### Evidence model

Each step attempt receives a stable attempt identifier. Verification, review,
commit, and checkpoint evidence include that identifier, the step ID, relevant
Git identity, command or operation, result, and timestamp. Evidence from an
older attempt or different HEAD is stale and cannot authorize progression.

Review evidence records the reviewed diff identity and scope result. Commit
evidence records the resulting commit and its parent. Checkpoint succeeds only
when those identities form the expected chain.

### Journal and bounded summaries

The journal is an append-only sequence of JSON records. Each record contains a
monotonic sequence number, previous-record hash, event type, step and attempt
identity when applicable, payload, and its own content hash. Appends use a
temporary file plus atomic replacement so interruption cannot expose a partial
record as valid.

Checkpoint summaries are derived artifacts, never a second source of truth.
They contain only:

- contract and plan identity;
- active or next step;
- latest valid checkpoint and Git HEAD;
- latest verification and review outcome;
- unresolved blocker, if present;
- the most recent journal events that fit the configured bounds.

Two independent limits apply: maximum retained event count and maximum encoded
byte size. Pruning removes the oldest nonessential events first. Essential
recovery fields listed above are never pruned. If essential fields alone exceed
the byte limit, summary generation fails explicitly instead of emitting an
invalid or silently truncated summary.

## Lifecycle

The enforced V1 lifecycle is:

```text
INSPECT -> START -> EXECUTE -> VERIFY -> REVIEW -> COMMIT -> CHECKPOINT
                           |                                |
                           +-- failure -> REPAIR -----------+
```

A failed verification leaves the same attempt and step active. Repair may
change only declared step scope. It must produce a new verification receipt;
the failed receipt remains in the journal. No review, commit, checkpoint, or
next-step activation is permitted from a failed or stale receipt.

Commit and checkpoint are intentionally separate. Commit creates Git history;
checkpoint verifies that history and records durable completion. If interruption
occurs between them, `recover` recognizes the matching uncheckpointed commit and
offers a deterministic checkpoint continuation without creating another commit.

## Recovery and Error Handling

Recovery is read-mostly and never broadens authority. It validates the contract,
state, evidence files, journal chain, and Git history, then selects one outcome:

- resume execution of the active step;
- repair after failed verification;
- repeat verification because the receipt is stale;
- continue checkpointing an already-created matching commit;
- stop for manual resolution because artifacts disagree or are corrupt.

Atomic files use same-directory temporary files and replacement. Invalid JSON,
missing required fields, broken journal hashes, unknown phases, missing commits,
and unexpected dirty paths are hard failures with stable diagnostic codes.
Recovery never deletes files or resets Git.

## Testing Strategy

Unit tests will cover contract validation, state transitions, attempt identity,
receipt freshness, diff-scope validation, journal hashing, atomic persistence,
summary bounds, deterministic pruning, and diagnostic codes.

Integration tests will use temporary Git repositories to prove:

- commands cannot be bypassed to advance an invalid state;
- failure blocks review, commit, checkpoint, and next-step activation;
- repair stays on the same attempt until fresh verification passes;
- a reviewed diff becoming stale blocks commit;
- a commit with the wrong parent or content blocks checkpoint;
- interruption before and after commit recovers deterministically;
- state and journal survive process and conversation loss;
- corrupt or partially written artifacts stop safely;
- bounded summaries respect both count and byte limits;
- pruning is deterministic and preserves essential recovery context.

The final end-to-end proof will execute at least two steps, deliberately fail
one verification, reload from disk, force summary pruning, repair the same step,
commit and checkpoint it, simulate an interrupted checkpoint, recover, and
finish with matching Git/state/journal identities and a clean worktree.

The final gate is the complete V0 and V1 regression suite plus a V1 proof report.

## Acceptance Criteria

V1 is complete only when:

- the separately locked V1 contract and ordered plan exist;
- every mutating lifecycle transition is runtime-enforced;
- verification, review, commit, and checkpoint evidence is attempt- and
  Git-bound;
- invalid, stale, corrupt, or out-of-scope state blocks progression;
- recovery handles supported interruption points without duplicate commits;
- journal integrity is independently verifiable;
- summaries enforce deterministic count and byte bounds;
- essential recovery context survives pruning and reload;
- the end-to-end V1 proof passes;
- all V0 and V1 regression tests pass;
- the repository finishes clean at a durable checkpoint;
- no excluded V1 capability has been introduced.
