import tempfile, unittest
from pathlib import Path
from harness_learning.demo import run_learning_demo

class EndToEndLearningTests(unittest.TestCase):
    def test_fail_repair_learn_restart_and_reuse(self):
        with tempfile.TemporaryDirectory() as tmp: proof=run_learning_demo(Path(tmp))
        self.assertEqual("FAILED",proof["initial_verification"]); self.assertTrue(proof["advancement_blocked"])
        self.assertEqual("PASSED",proof["repair_verification"]); self.assertEqual("PROMOTED",proof["skill_gate"])
        self.assertEqual("SAFETY",proof["bad_skill_rejection"]); self.assertEqual("EXACT_DUPLICATE",proof["duplicate_decision"])
        self.assertTrue(proof["permission_denied"]); self.assertTrue(proof["restart_ids_match"])
        self.assertTrue(proof["related_episode_retrieved"]); self.assertTrue(proof["unrelated_episode_excluded"])
        self.assertTrue(proof["related_skill_triggered"]); self.assertTrue(proof["unrelated_skill_not_triggered"])
        self.assertEqual("PASSED",proof["fresh_session_reuse"]); self.assertEqual(1,proof["fresh_session_attempts"])
        self.assertEqual(4,len(proof["ablations"])); self.assertEqual([10,100,1000],sorted(map(int,proof["bounded_context"])))
        self.assertTrue(all(x["used"]<=x["budget"] for x in proof["bounded_context"].values()))
if __name__=="__main__": unittest.main()
