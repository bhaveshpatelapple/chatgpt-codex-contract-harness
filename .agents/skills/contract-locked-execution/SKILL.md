---
name: contract-locked-execution
description: Use when a repository contains .harness/contract.yaml, .harness/plan.yaml, and .harness/state.json, or when asked to resume, execute, verify, checkpoint, or advance a contract-locked implementation step.
---

# Contract-Locked Execution

## Overview

Execute exactly one planned repository step while preserving the locked scope
and durable checkpoint. Treat the contract, plan, state, verification result,
diff, and commit as one ordered chain.

## Procedure

1. Read `AGENTS.md`, `.harness/contract.yaml`, `.harness/plan.yaml`, and
   `.harness/state.json` before changing files.
2. Run `python scripts/harness_verify.py`. Stop if the contract is invalid,
   unlocked, or differs from `.harness/contract.lock`.
3. Load and validate plan/state with `scripts.harness_state`. Confirm there is
   no active step and the requested step equals `next_step`.
4. Call `start_step(plan, state, step_id)` and persist it with `save_state`.
5. Implement only that step. Use the repository's required implementation and
   test workflow.
6. Call `run_verification(plan, state, step_id, command)` with an argument list,
   never a shell command string. Persist the returned state.
7. If verification records `FAILED` or a nonzero exit code, leave the step
   active, report the failure, and stop. Do not review for approval, commit,
   mark complete, or start another step.
8. If verification passes, inspect the complete diff for scope, correctness,
   generated files, and whitespace errors.
9. After diff approval, call `complete_step`, persist the checkpoint, rerun the
   relevant verification, and create one focused commit containing the step
   and checkpoint.
10. Confirm a clean worktree and report the commit hash, verification evidence,
    files changed, diff review, and recorded `next_step`. Stop.

## Transition Example

```python
from scripts.harness_state import (
    complete_step,
    load_plan,
    load_state,
    run_verification,
    save_state,
    start_step,
)

plan = load_plan(".harness/plan.yaml")
state = start_step(plan, load_state(".harness/state.json"), 5)
save_state(".harness/state.json", state)

state = run_verification(
    plan,
    state,
    5,
    ["python", "-m", "unittest", "discover", "-s", "tests", "-v"],
)
save_state(".harness/state.json", state)
if state["verification"]["status"] == "PASSED":
    state = complete_step(plan, state, 5)
    save_state(".harness/state.json", state)
```

## Quick Reference

| Condition | Required action |
|---|---|
| Contract check fails | Stop; do not change the contract silently |
| Another step is active | Resume it; do not start a second step |
| Requested step is not `next_step` | Stop and report the state mismatch |
| Verification exits nonzero | Persist `VERIFY_FAILED` and stop |
| Verification passes | Review the full diff before completion |
| Commit succeeds | Confirm checkpoint and stop before the next step |

## Common Mistakes

- Editing `contract.yaml` and regenerating its digest as part of implementation.
- Running more than one plan step in a single commit.
- Calling `complete_step` before verification and diff review.
- Treating a flaky or environment-specific failure as a pass without evidence.
- Advancing state without including the checkpoint in the step commit.
- Continuing into `next_step` instead of stopping at the checkpoint.
