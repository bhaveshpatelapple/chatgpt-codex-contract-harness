# ChatGPT/Codex Contract-Locked Harness

V0 is a repository harness for executing an agreed implementation contract one
verified, reviewed, and committed step at a time.

Step 1 establishes the locked V0 scope, repository-wide execution policy, and
minimal Python test scaffolding. Later harness behavior is intentionally not
implemented yet.

## Verify Step 1

Requires Python 3.11 or newer. From the repository root, run:

```text
python -m unittest discover -s tests -v
```

Validate that the locked contract has the required schema and has not changed:

```text
python scripts/harness_verify.py
```

The ordered V0 plan lives in `.harness/plan.yaml`; resumable progress lives in
`.harness/state.json`. State transitions are implemented in
`scripts/harness_state.py` and permit only one ordered step at a time.

Each active step must run a verification command through the state machine.
Only a recorded zero exit code permits completion; a nonzero exit code leaves
the step active in `VERIFY_FAILED` and blocks progression.

Codex can follow the repo-local `contract-locked-execution` skill under
`.agents/skills/` to operate this workflow consistently.

Run the temporary two-step demonstration without changing repository state:

```text
python -m examples.two_step_demo
```

## Deterministic learning harness

The offline learning pipeline adds bounded L3 retrieval, verified L4 episodes,
selective L5 skills, a skill-evolution gate, permissioned role orchestration,
independent L4/L5 ablations, and atomic restart persistence.

Run its controlled fail-repair-learn-restart-reuse proof with:

```text
python -m harness_learning.demo run
```

The proof uses temporary storage unless a target directory is supplied. Core
behavior is deterministic and requires no network access or API credentials.
