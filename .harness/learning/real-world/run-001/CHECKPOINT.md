# Real-World Learning Checkpoint 001

## Repository task

Prevent `LearningOrchestrator.open()` from loading persisted run state before
the locked contract has been validated.

Base commit: `b612f3703e2454d9b27db24d08ded39086f3e1a7`.

## Execution evidence

- Initial attempt: `attempt_d9588d22bc020b92e3f2`.
- Initial verification: `FAILED`; advancement raised `ADVANCE_BLOCKED`.
- Repaired attempt: `attempt_13a02c243b8e5f1fb925`.
- Repair verification: `verification_26637242d3d5a1c53044`, `PASSED`.
- Run: `run_4f267bd4c0b5f5d84672`, reopened with identical identity.

## Learned evidence

- Verified episode: `episode_0c72fe0dfc4caaeab4c1`.
- Promoted skill: `skill_f534be3af4e257df00d7`.
- Fresh orchestrator retrieval returned the episode.
- Fresh orchestrator triggering returned the skill.

## Verification

- `python -m unittest tests.test_learning_restart -v`: 2 passed.
- `python -m unittest discover -s tests -v`: 48 passed.
- `python -m harness_learning.demo run`: passed.
- `git diff --check`: passed.

This checkpoint intentionally stops after the first real repository repair and
does not begin a second task.
