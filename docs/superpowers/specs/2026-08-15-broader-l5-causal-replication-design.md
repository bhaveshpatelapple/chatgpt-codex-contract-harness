# Broader L5 Causal Replication Design

## Goal and checkpoint boundary

Test whether a validated L5 skill causes first-attempt success on a realistic,
multi-file repository repair while every other relevant input is held fixed.
This checkpoint covers one isolated nested-configuration defect, its controlled
experiment, verification evidence, and one final commit. It does not add a
general benchmark framework or begin another learning checkpoint.

## Repository fixture

The experiment creates a small standalone Python repository under the causal
evidence directory. The repository contains:

- `fixture_app/config.py`, which merges application defaults with overrides;
- `fixture_app/service.py`, which consumes values from the merged structure;
- `tests/test_config.py`, which verifies nested override and preservation
  behavior; and
- `tests/test_service.py`, which verifies the consumer-visible configuration.

The seeded defect is a shallow dictionary update. Overriding one nested key
replaces its entire parent mapping and removes required sibling defaults. The
repair must implement a non-mutating recursive merge that:

1. recursively combines two mappings;
2. lets override leaf values win;
3. preserves default siblings not mentioned by the override; and
4. does not mutate either input.

This is non-trivial relative to the greeting demonstration because the failure
crosses module boundaries, requires preserving an invariant rather than
replacing a token, and is accepted only by the fixture's complete test suite.

## L5 skill and execution interface

A controlled base learning store contains one promoted skill derived from a
verified episode for the nested-merge repair. Its trigger is specific to the
fixture task, and its procedure identifies the recursive, non-mutating merge
invariant.

Each experimental unit receives a fresh byte-for-byte copy of the same broken
fixture. A deterministic repository-task runner accepts the copy, task text,
expected test command, controlled store, and L5 condition. With L5 enabled, it
may retrieve the matching skill and apply its procedure. With L5 disabled, it
must neither query nor apply L5. The runner records the retrieved skill ID,
changed files, first-attempt test result, attempts, and final test result.

The disabled condition represents the harness's fixed baseline executor. It
does not independently invent the recursive repair on its first attempt. After
a failed first attempt, the same deterministic repair operation may be applied
so both conditions can demonstrate final verified completion.

## Causal analysis

### Question and rung

- Cause: intervention setting L5 availability to enabled rather than disabled.
- Effect: whether the fresh fixture passes its full test suite on attempt one.
- Required and targeted evidence: Pearl rung 2, intervention.
- Estimand: first-attempt success-rate difference between conditions for this
  fixed fixture, runner, skill, verifier, and code revision.

### Causal graph

```text
fixture bytes ---------------------------> first-attempt result
task and verifier ------------------------> first-attempt result
base code and interpreter ----------------> first-attempt result
L5 intervention -> retrieved procedure --> attempted patch --> first-attempt result
```

Edges are based on the repository execution path. Missing-edge assumptions are
that treatment assignment does not alter fixture bytes, task text, verifier,
interpreter, base code, or repair fallback; process order has no carry-over
because every unit uses a new process and repository copy.

The effect is identifiable by direct random intervention: all backdoor paths
from L5 condition to outcome are blocked by construction. Treatment is the only
conditioned variable. Retrieved procedure and attempted patch are mediators and
will be recorded but not adjusted for. No post-treatment variable is used for
selection.

The main unmeasured-confounder risk is imperfect isolation, such as a trial
reusing mutable files. Hashing the pristine fixture, copying it per unit, and
checking the hash before execution controls that risk. The claim remains local
to this deterministic fixture and cannot establish cross-task performance.

## Experimental design

### Factors and controls

| Factor | Levels | Role |
|---|---|---|
| L5 availability | enabled, disabled | treatment |
| Fixture | identical broken nested-merge repository | blocked |
| Task and verifier | identical task and full test command | blocked |
| Base learning store | identical persisted store | blocked |
| Process and work copy | fresh per unit | isolated nuisance |

The design is a randomized complete block comparison. It uses three independent
process units per condition, six total. A fixed seed, recorded before execution,
randomizes three enabled and three disabled labels. The exact allocation and
base commit are committed in the preregistration before any outcomes are run.

The harness is deterministic, so prior sampling variance is zero and a
classical power calculation is not meaningful. Three units per condition test
process and copy isolation. They do not estimate population variance.

### Endpoints and decision rule

The primary endpoint is full fixture-suite success on the first attempt. The
sufficient statistics are first-attempt passes and total units per condition.
The preregistered confirmatory criterion is enabled `3/3` and disabled `0/3`.
The reported effect is the difference in first-attempt success rates.

Secondary endpoints are attempts required, final full-suite status, retrieved
skill ID, changed-file set, and pristine-fixture hash agreement. These cannot
replace the primary endpoint after outcomes are observed. No p-value or
confidence interval will be reported because these deterministic repetitions
are isolation checks rather than population samples.

## Failure handling and protocol integrity

Before collecting outcomes, a pre-run gate must prove that the controlled store
contains exactly the intended skill, the enabled query retrieves it, the
disabled path performs no retrieval, and every unit starts with the recorded
pristine hash. Any gate failure stops the experiment without interpreting
partial outcomes.

Unexpected protocol deviations are documented and committed before a restart.
Failed or partial protocols are excluded in full. A first-attempt test failure
inside a valid disabled unit is an outcome, not a protocol failure; it proceeds
to deterministic repair and final verification.

## Testing and verification

Implementation follows red-green TDD. A new integration test must fail first
because the broader repository-task runner does not exist. The production
change that makes it pass is the runner that isolates fixture copies, enforces
the L5 intervention, executes the actual fixture tests, and returns structured
evidence.

Verification gates are:

1. the fixture tests fail on the pristine defect and pass after the intended
   recursive-merge repair;
2. targeted broader-ablation and prior cross-process tests pass;
3. the full learning-harness regression suite passes;
4. the six preregistered separate-process units complete in seeded order;
5. stored raw results reproduce the reported sufficient statistics;
6. diff review finds only fixture, runner, test, and causal evidence files; and
7. `git diff --check` passes before the final checkpoint commit.

## Deliverables

- committed preregistration, causal graph, randomization, and confound audit;
- isolated broken fixture and deterministic task runner;
- a test that proves the enabled and disabled execution paths;
- raw per-unit outcomes plus an analysis bounded to Pearl rung 2;
- verification transcript summary and one focused checkpoint commit.
