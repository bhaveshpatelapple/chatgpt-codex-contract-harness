# Contract-Locked Execution Policy

This policy applies to the entire repository.

## Source of truth

- `.harness/contract.yaml` is the locked V0 contract.
- Work must remain within its goal, required features, workflow, invariants,
  and exclusions.
- Do not alter a locked contract silently. A requested contract change must be
  identified explicitly and handled as a separate, reviewed change.

## Sequential execution

Follow this lifecycle in order:

1. `CONTRACT_LOCK`
2. `PLAN`
3. `EXECUTE_ONE_STEP`
4. `VERIFY`
5. `DIFF_REVIEW`
6. `COMMIT`
7. `CHECKPOINT`
8. `NEXT_STEP`
9. `FINAL_VERIFY`

Only one implementation step may be active at a time. Do not begin the next
step until the current step has passed verification, its diff has been
reviewed, and its changes have been committed.

## Verification and commits

- Run the verification specified for the active step after implementation.
- A failed verification blocks diff approval, commit, and progression.
- Review the complete diff for scope, correctness, and accidental files.
- Create one focused commit only after verification passes.
- Record completed work through Git; do not mark an uncommitted step complete.

## Scope discipline

- Implement only the active plan step.
- Do not add features from later steps early.
- Preserve persistent harness files so execution can resume without chat
  history.
- Stop and report the blocker when contract, plan, and repository state
  disagree; do not guess or silently rewrite them.

## V0 step boundaries

- Step 1: repository skeleton and this repository-wide policy.
- Step 2: contract schema and lock validation.
- Step 3: plan and persistent execution-state machine.
- Step 4: verification gate that prevents progression after failure.
- Step 5: Codex skill for operating the harness.
- Step 6: end-to-end two-step demonstration.
