# Broader L5 Causal Replication — Results

## Protocol accounting

All six units ran once in the committed seeded order. The pre-run gate passed,
every CLI process exited successfully, every unit began with digest
`0b6e9c397b247f233b5707499862713c9df4bc9d7348572833909850f6004f5b`,
and no unit was excluded. There were no protocol deviations.

## Pre-registered comparison

| Condition | First-attempt passes | Mean attempts | Final passes | Expected skill ID |
|---|---:|---:|---:|---:|
| L5 enabled | 3/3 | 1.0 | 3/3 | 3/3 |
| L5 disabled | 0/3 | 2.0 | 3/3 | 0/3 |

- First-attempt success-rate difference: `1.0` (100 percentage points).
- Mean-attempt difference, enabled minus disabled: `-1.0`.
- Digest agreement: `6/6`.
- Changed-file agreement: `6/6` changed only `fixture_app/config.py`.
- Enabled units retrieved `skill_f1973ba3647400dcb483`.
- Disabled units reported a null skill ID and performed no L5 retrieval.
- All final fixture suites passed all three tests.

The primary confirmatory criterion—enabled `3/3` and disabled `0/3` on the
first attempt—was met exactly.

## Causal interpretation

This is Pearl rung-2 intervention evidence. Within the committed fixture,
controlled skill, deterministic runner, full fixture verifier, Python 3.14.4,
and base commit `233e7f12fb8c24c154a11d638391c625346b8bde`, enabling L5 caused
first-attempt success; disabling it caused the shallow nested-merge failure and
one subsequent deterministic repair.

The comparison is broader than the earlier token-replacement ablation: the
repair crosses modules, preserves nested invariants, avoids input mutation, and
must pass an independent three-test repository suite. It still does not
estimate performance across unseen repositories, defect classes, skills,
models, or stochastic agent behavior. The three replicates per condition test
process and copy isolation, not population variance, so no p-value or
confidence interval is reported.
