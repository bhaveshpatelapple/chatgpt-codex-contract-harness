# Pre-registration Amendment 1

This amendment is recorded after the store/task mismatch and before any valid
enabled outcome is observed.

## Changed blocking variable

Replace “persisted learning store: checkpoint 001” with one controlled base
store generated once by `python -m harness_learning.demo run <store>`. That
store contains the validated greeting-replacement skill used by the fixed task.
All six units use this same store.

## Unchanged design

- Hypothesis, intervention, task, endpoints, decision criterion, replicate
  count, seed `20260815`, randomized order, and analysis plan are unchanged.
- Order remains: enabled, disabled, enabled, disabled, disabled, enabled.
- Each unit remains a separate Python process.
- The failed protocol attempt is excluded in full and reported separately.

## Additional protocol gate

Before executing units, `inspect` must confirm exactly one persisted skill and
an enabled dry-run query must return that skill. The dry-run may inspect the
trigger only; it must not execute or verify the task outcome.
