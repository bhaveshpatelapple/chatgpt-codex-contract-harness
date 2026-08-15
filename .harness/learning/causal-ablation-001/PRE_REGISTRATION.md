# Controlled L5 Causal Ablation — Pre-registration

## Hypothesis

For the fixed related task `wrong codex` → `hello codex`, intervening to make
the validated L5 skill available causes successful completion on the first
attempt. With L5 disabled, the same deterministic executor fails its first
attempt and requires one repair.

## Causal graph and rung

```text
persisted validated skill -> L5 intervention -> triggered procedure -> first-attempt output
fixed task ----------------------------------------------------------> first-attempt output
fixed code/base commit ----------------------------------------------> first-attempt output
```

The intervention sets L5 availability; task, persisted store, code, interpreter,
and verification rule are held fixed. This targets Pearl rung 2
(`P(outcome | do(L5))`), not a cross-task observational association.

## Factors and levels

| Factor | Levels | Role |
|---|---|---|
| L5 availability | enabled, disabled | treatment |
| Task/input/expected output | fixed | blocking |
| Persisted learning store | checkpoint 001 | blocking |
| Process | new Python process per unit | nuisance, isolated |

## Design

- Type: paired randomized complete block design.
- Replicates: 3 independent processes per condition; 6 total units.
- Randomization seed: `20260815`.
- Execution order is generated once from three enabled and three disabled labels.
- Every unit receives input `wrong codex` and expected output `hello codex`.
- Enabled units may retrieve and apply L5. Disabled units must not query or apply L5.
- A failed first attempt is repaired deterministically so final completion can
  also be checked.

## Power and limits

The harness is deterministic, so classical variance-based power is not
estimable from prior data. Three process replicates per condition are required
as a persistence/isolation check, not as population sampling. The causal claim
is limited to this fixed harness, store, task, and code version.

## Primary endpoint

- Metric: first-attempt success (`PASSED` = 1, otherwise 0).
- Sufficient statistic: successes and total units per condition.
- Decision criterion: enabled `3/3` first-attempt successes and disabled `0/3`.

## Secondary endpoints

- Attempts required for final success.
- Final verification status.
- Triggered skill ID: present only when enabled.

## Confound audit

| Potential confound | Control |
|---|---|
| Different tasks | identical input and expected output |
| Different learned stores | same checkpoint-001 store |
| Residual in-memory state | separate process per unit |
| Code drift | one base commit for all units |
| Order effects | fixed seeded random order |
| Verifier differences | identical exact-output verifier |

## Analysis plan

Report condition-level counts, first-attempt success-rate difference, attempts
per unit, triggered skill IDs, and final verification. No p-value will be used;
the deterministic effect and its narrow evidence regime will be stated directly.
Any changed endpoint or condition after execution is exploratory and cannot
support the pre-registered claim.
