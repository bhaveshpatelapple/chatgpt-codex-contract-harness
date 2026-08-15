# Real-World Reuse Checkpoint 002

## Fresh-session retrieval before planning

The fresh session loaded verified episode
`episode_0c72fe0dfc4caaeab4c1` and promoted skill
`skill_f534be3af4e257df00d7` from checkpoint 001. Query
`restart receipt integrity guard` triggered that skill before the repository
repair was planned.

Retrieved procedure:

`call the contract gate before reading persisted run state`

## Related repository task

Reject a persisted verification receipt when its run or attempt identity does
not match the active run restored after the contract gate.

The repair validates the deserialized receipt before exposing restored state.

## Reuse evidence

- Run: `run_bc73df8e3019341c5e6f`.
- Attempts: `1`.
- Verification: `PASSED`.
- No failed approach from checkpoint 001 was repeated.
- Triggered skill: `skill_f534be3af4e257df00d7`.
- Source episode: `episode_0c72fe0dfc4caaeab4c1`.

## Verification

- `python -m unittest tests.test_learning_restart -v`: 3 passed.
- `python -m unittest discover -s tests -v`: 49 passed.
- `python -m harness_learning.demo run`: passed.
- `git diff --check`: passed.

This checkpoint intentionally stops without beginning a third task.
