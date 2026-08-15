# V0 End-to-End Proof Report

## Steps 1–5 prerequisite audit

Each commit was checked out independently and its complete available test suite passed. Contract verification also passed for Steps 2–5.

| Step | Commit | Verification |
|---|---|---|
| 1 | `8b0b8b67886315387dbd18e90f7820e0ae3dafbd` | 1/1 tests passed |
| 2 | `f63c438a893237e5d711cdb90cccdbb12afe26e4` | 5/5 tests passed; contract locked and unchanged |
| 3 | `1f9b58d76b4efc42e4e9a352b73d9b6f6d0ffcfd` | 11/11 tests passed; contract locked and unchanged |
| 4 | `2c39c8b0e50066c126fc6002c09537782355fde5` | 15/15 tests passed; contract locked and unchanged |
| 5 | `7ca81b7e9942790a1c61d85f4309b7740f49fd2d` | 17/17 tests passed; contract locked and unchanged |

## Step 6 controlled proof

The canonical demo repository used setup commit `820cdb65c3838bf0191c01275a983df1ca721e3d`, Step 1 commit `9aa04d61ac69f068ea2195a8accb18049ee4c294`, and Step 2 commit `f5d4eaf6e4b8adf0045c4e683e79a0acc03a4ec0`.

- Step 1: activated, produced `hello\n`, verified with exit code 0, passed `git diff --check`, committed, checkpointed, and reloaded.
- Intentional Step 2 failure: expected `hello world\n`, observed `wrong value\n`, exit code 1. Reloaded state remained `VERIFY_FAILED` with `active_step: 2`, `completed_steps: [1]`, and the complete command/stdout/stderr evidence.
- Blocked transitions: completion, the Git commit wrapper, checkpoint, and another step activation all raised the harness gate. `HEAD` remained exactly the Step 1 commit (`9aa04d6`) throughout the failed phase.
- Repair: only Step 2 remained active; changing the artifact to `hello world\n` verified with exit code 0, passed diff review, committed, and checkpointed.
- Sequential invariant: the observed maximum number of active steps was exactly one.
- Git/state agreement: the two implementation commits are ordered Step 1 then Step 2; the final demo state is `CHECKPOINT`, `completed_steps: [1, 2]`, `active_step: null`, `next_step: null`, with persisted passing verification. The demo worktree is clean.

## Final V0 verification

- Contract integrity: `python scripts/harness_verify.py` reported `contract 0.1 is LOCKED and unchanged`; the contract Git blob stayed `d8fc80a0af6c9ae253eac10bc61077df8935e1d4`.
- Full regression suite: `python -m unittest discover -s tests -v` ran 20 tests with 20 passing and zero failures.
- Main harness state: `CHECKPOINT`, completed Steps `[1, 2, 3, 4, 5, 6]`, no active or next step, and Step 6 verification `PASSED` with exit code 0.
- Final repository status: clean after the single final Step 6 harness/report commit.

V0 passes. No V1 or bounded-memory work was started.
