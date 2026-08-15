# Broader L5 Causal Replication — Pre-registration

## Hypothesis

For the fixed isolated nested-configuration repository repair, intervening to
enable the validated L5 skill causes the complete fixture suite to pass on the
first attempt. With L5 disabled, the identical deterministic baseline leaves
the shallow-merge defect in place on attempt one and requires one repair.

## Fixed evidence regime

- Base commit: `91a4d59773fa2a77ec2e59bb0492e40289711e19`.
- Fixture: committed `fixture/` tree in this evidence directory.
- Task: preserve nested defaults while applying overrides without mutating
  either input.
- Verifier: `python -m unittest discover -s tests -v`, run from the copied
  fixture root.
- Store: one controlled promoted skill generated before the pre-run gate.
- Interpreter: the same `sys.executable` for every unit.

## Factors and levels

| Factor | Levels | Role |
|---|---|---|
| L5 availability | enabled, disabled | treatment |
| Fixture, task, verifier, store, code | fixed | blocking |
| Process and work copy | fresh per unit | isolated nuisance |

## Design and allocation

- Type: randomized complete block comparison.
- Replicates: three separate-process units per condition; six total.
- Randomization seed: `20260816`.
- Fixed order: enabled, disabled, enabled, enabled, disabled, disabled.
- Each unit receives a new byte-identical fixture copy and the same store.
- Enabled units may retrieve and apply the matching L5 procedure.
- Disabled units must not query or apply L5.
- After a valid first-attempt failure, deterministic repair is allowed so final
  completion is independently verified.

The system is deterministic, so classical sampling variance and a conventional
power calculation are not meaningful. Three units per condition test process
and copy isolation; they do not estimate population variance.

## Endpoints and decision rule

Primary endpoint: complete fixture-suite success on attempt one. The sufficient
statistics are passes and total units per condition.

Confirmatory criterion: enabled `3/3` first-attempt passes and disabled `0/3`.
Report the success-rate difference directly.

Secondary endpoints are attempts required, final verification, retrieved skill
ID, changed files, test exit codes, and pristine fixture digest agreement.
Secondary endpoints cannot replace the primary endpoint after execution.

## Protocol gates and stopping

Before outcomes, the gate must prove that the store contains exactly one
intended skill, the enabled query retrieves it, the disabled path performs no
query, and a fresh copy matches the committed pristine digest. Any gate failure
stops execution without interpreting partial outcomes.

An unexpected CLI error, digest mismatch, missing final pass, or changed fixed
input is a protocol failure. Document and commit the deviation before any new
run; exclude a failed protocol in full. A disabled first-attempt test failure is
the preregistered outcome and is not a deviation.

## Analysis boundary

Report ordered raw unit records, primary counts, success-rate difference, mean
attempts, final passes, skill IDs, changed files, and digest agreement. Do not
report a p-value or confidence interval because repetitions are deterministic
isolation checks. The strongest permitted conclusion is Pearl rung 2 for this
fixed fixture, skill, runner, verifier, interpreter, and code revision—not
general repository performance or autonomous reasoning.
