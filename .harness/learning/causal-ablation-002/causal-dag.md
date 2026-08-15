# Causal DAG and Identifiability

## Question and rung

- Cause: `do(L5 availability = enabled)` versus `do(L5 availability = disabled)`.
- Effect: complete fixture-suite success on attempt one.
- Estimand: condition-level first-attempt success-rate difference.
- Evidence rung: Pearl rung 2, direct intervention.

## Graph

```text
fixture bytes ---------------------------> first-attempt result
task and verifier ------------------------> first-attempt result
base code and interpreter ----------------> first-attempt result
L5 intervention -> retrieved procedure --> attempted patch --> first-attempt result
```

## Edges

- Fixture bytes determine the defect and tests presented to each unit.
- Task and verifier define the requested repair and accepted outcome.
- Base code and interpreter determine runner and execution semantics.
- L5 availability determines whether retrieval is permitted.
- A retrieved procedure determines whether the intended patch is attempted.
- The attempted patch and fixed inputs determine the first verification result.

## Missing-edge assumptions

- Assignment does not change fixture bytes, task text, verifier, store, base
  code, or interpreter.
- Process order does not affect later units because no work copy is reused.
- Disabled execution cannot access L5 through another path.
- The fallback repair occurs only after the primary endpoint is recorded.

## Identifiability and conditioning

Direct randomized intervention makes the local average treatment effect
identifiable without adjustment: fixed inputs and fresh copies block backdoor
paths between treatment and outcome. Treatment is the only conditioned
variable. Retrieved procedure and attempted patch are mediators; they are
recorded but not adjusted for. No collider or post-treatment selection variable
is introduced.

## Sensitivity

The material unmeasured-confounder risk is imperfect isolation, such as mutable
files leaking between units. A digest over sorted fixture paths and bytes is
checked before each trial, and every unit uses a new process and destination.
Any mismatch invalidates the protocol. Unknown host-level differences remain
possible, but the deterministic functional outcome and identical interpreter
make timing and performance variation irrelevant to the endpoint.

The resulting claim remains local. It cannot establish an effect across other
defects, repositories, skill qualities, models, or stochastic environments.
