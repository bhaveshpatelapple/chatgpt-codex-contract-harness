# Broader L5 Causal Replication — Verification

Verified at `2026-08-15T23:56:35.8845307+05:30` in the isolated worktree on
Python 3.14.4.

## Stored-result consistency

The PowerShell consistency check parsed `RESULTS.json` and returned:

```json
{"EnabledFirstPass":3,"EnabledN":3,"DisabledFirstPass":0,"DisabledN":3,"FinalPass":6,"DigestAgreement":6,"EnabledSkill":3,"DisabledNullSkill":3}
```

Exit code: `0`.

## Targeted verification

Command:

```text
python -m unittest tests.test_learning_repository_causal_ablation tests.test_learning_causal_ablation tests.test_learning_cross_process -v
```

Result: `3` tests passed, `0` failures, exit code `0`.

## Full regression verification

Command:

```text
python -m unittest discover -s tests -v
```

Result: `52` tests passed, `0` failures, exit code `0`.

## Controlled pre-run gate

Command:

```text
python -m harness_learning.repository_ablation gate .harness/learning/causal-ablation-002/fixture .harness/learning/causal-ablation-002/base-store
```

Result: exit code `0`, with:

```json
{"disabled_retrieval_count":0,"enabled_retrieval_count":1,"fixture_digest":"0b6e9c397b247f233b5707499862713c9df4bc9d7348572833909850f6004f5b","ready":true,"skill_id":"skill_f1973ba3647400dcb483"}
```

## Diff integrity

Command: `git diff --check`.

Result: no whitespace errors, exit code `0` before this verification record was
written. The check is rerun after staging and after the final commit.

## TDD and adversarial check

Before `harness_learning.repository_ablation` existed, the new integration test
failed with `ModuleNotFoundError`. After minimal implementation, it passed. A
temporary mutation that skipped the enabled L5 patch made the same test fail
because enabled first verification changed from `PASSED` to `FAILED`; restoring
the treatment branch returned the test to green. The mutation was not committed.
