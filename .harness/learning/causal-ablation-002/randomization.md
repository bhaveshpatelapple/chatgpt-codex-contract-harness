# Randomization Record

- RNG: Python `random.Random`.
- Seed: `20260816`.
- Input multiset: three `enabled` labels and three `disabled` labels.
- Command: `python -c "import random; labels=['enabled']*3+['disabled']*3; random.Random(20260816).shuffle(labels); print(labels)"`
- Generated allocation: `['enabled', 'disabled', 'enabled', 'enabled', 'disabled', 'disabled']`.

| Unit | Condition |
|---:|---|
| 1 | enabled |
| 2 | disabled |
| 3 | enabled |
| 4 | enabled |
| 5 | disabled |
| 6 | disabled |

This allocation is immutable after this preregistration commit. No outcome was
collected before it was generated or recorded.
