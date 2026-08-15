import tempfile
import unittest
from pathlib import Path

from harness_learning.repository_ablation import (
    fixture_digest,
    prepare_controlled_store,
    run_trial,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT / ".harness" / "learning" / "causal-ablation-002" / "fixture"
)


class RepositoryCausalAblationTests(unittest.TestCase):
    def test_l5_intervention_changes_first_attempt_repository_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill_id = prepare_controlled_store(root / "store")
            pristine = fixture_digest(FIXTURE)
            enabled = run_trial(FIXTURE, root / "store", root / "enabled", True)
            disabled = run_trial(FIXTURE, root / "store", root / "disabled", False)

        self.assertEqual(pristine, enabled["pristine_digest"])
        self.assertEqual(pristine, disabled["pristine_digest"])
        self.assertEqual("PASSED", enabled["first_verification"])
        self.assertEqual(1, enabled["attempts"])
        self.assertEqual(skill_id, enabled["skill_id"])
        self.assertEqual("FAILED", disabled["first_verification"])
        self.assertEqual(2, disabled["attempts"])
        self.assertIsNone(disabled["skill_id"])
        self.assertEqual("PASSED", disabled["final_verification"])


if __name__ == "__main__":
    unittest.main()
