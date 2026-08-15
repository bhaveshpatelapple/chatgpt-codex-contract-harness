# Deterministic Learning Harness Proof Report

## Scope

This proof covers L3 retrieval, L4 verified episodes, L5 selective skills, the
skill-evolution gate, multi-role permission enforcement, independent L4/L5
ablations, restart persistence, and the controlled learning lifecycle.

## Controlled flow

The offline demonstration deliberately produced `wrong value`, received a
`FAILED` verifier receipt, and observed `ADVANCE_BLOCKED`. Repair remained on
the same run, produced `hello world`, and received a `PASSED` receipt. Only that
verified repair was admitted as episode
`episode_fca3a09c386ef2d8db47`.

The episode generated skill `skill_8efb8f860b7499a01208`. The evolution gate
promoted it, rejected an unsafe candidate with `SAFETY`, and rejected an exact
duplicate with `EXACT_DUPLICATE`. Unit coverage also proves compatible
near-duplicate merging and conflicting-duplicate rejection.

After all in-memory stores and orchestration objects were destroyed, fresh
instances reloaded identical run, episode, and skill IDs. A related task
retrieved the episode, triggered the skill, and passed on its first attempt.
Unrelated episode and skill queries returned neither learned artifact.

## Bounds and ablations

Synthetic L4 histories of 10, 100, and 1,000 records each selected four items
and produced a 347-byte manifest against the 16,384-byte total budget. Every
manifest records typed L0-L5 layer item and byte budgets.

The observed ablation matrix was:

| L4 | L5 | L4 selected | L5 selected |
|---|---|---:|---:|
| off | off | 0 | 0 |
| off | on | 0 | 1 |
| on | off | 1 | 0 |
| on | on | 1 | 1 |

The L0-L3 selection was unchanged across ablations. Disabling a layer did not
delete its persisted records.

## Enforcement

The planner was denied the memory-only `WRITE_EPISODE` capability before its
operation executed. The complete role/capability cross-product is covered by
tests. A stale verification receipt cannot advance a run. A contract digest
mismatch blocks run creation before state is written.

## Verification commands

The final committed-tree evidence must be refreshed before release with:

```text
python scripts/harness_verify.py
python -m unittest discover -s tests -v
python -m harness_learning.demo run
git diff --check
git status --short --branch
```
