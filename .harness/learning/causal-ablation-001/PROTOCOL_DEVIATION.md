# Protocol Deviation

The first execution attempt used `.harness/learning/real-world/run-001` as the
fixed learning store. That store contains the restart-contract skill
`skill_f534be3af4e257df00d7`, not the greeting-replacement skill required by the
pre-registered `wrong codex` → `hello codex` task.

Consequently, all three enabled units stopped with `SKILL_NOT_TRIGGERED` before
producing an outcome. Three disabled units emitted results, but they have no
valid treatment comparison and are excluded from analysis.

No causal conclusion is drawn from this failed protocol. The mismatch was a
design error in selecting the store, not evidence for or against L5.

