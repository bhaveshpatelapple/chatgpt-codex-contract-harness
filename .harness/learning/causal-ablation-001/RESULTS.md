# Controlled L5 Causal Ablation — Results

## Protocol accounting

The original execution used a mismatched persisted skill and produced no valid
enabled outcomes. Its three disabled outputs were excluded in full. The reason
and timing are recorded in `PROTOCOL_DEVIATION.md`; amendment 1 was committed
before the valid comparison ran.

## Pre-registered comparison

| Condition | First-attempt passes | Mean attempts | Final passes | Skill triggered |
|---|---:|---:|---:|---:|
| L5 enabled | 3/3 | 1.0 | 3/3 | 3/3 |
| L5 disabled | 0/3 | 2.0 | 3/3 | 0/3 |

- First-attempt success-rate difference: `1.0` (100 percentage points).
- Mean-attempt difference, enabled minus disabled: `-1.0`.
- Every unit followed the seeded order in `RESULTS.json`.
- Enabled units triggered `skill_8efb8f860b7499a01208`.
- Disabled units did not query or apply L5 and reported no skill ID.

## Causal interpretation

This is an intervention result at Pearl rung 2. Within this deterministic
harness, fixed generated store, fixed greeting task, exact-output verifier, and
current code version, enabling L5 caused first-attempt success; disabling L5
caused a failed first attempt followed by deterministic repair.

The result does not estimate performance across different repositories, tasks,
skills, models, or stochastic environments. Replication here checks process
isolation and persistence consistency; it is not population sampling, so no
p-value or confidence interval is reported.

## Verification target

- Targeted causal and cross-process tests must pass.
- The complete repository suite must pass.
- The deterministic learning proof must pass.
- `git diff --check` must pass.
