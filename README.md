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
