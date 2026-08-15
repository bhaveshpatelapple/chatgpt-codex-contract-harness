import tempfile
import unittest
from pathlib import Path

from examples.two_step_demo import run_demo


class TwoStepDemoTests(unittest.TestCase):
    def test_demo_proves_git_backed_failure_blocking_and_recovery(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proof = run_demo(Path(temp_dir))

        self.assertEqual(
            proof["events"],
            [
                "step 1 active",
                "step 1 verification PASSED",
                "step 1 diff reviewed",
                "step 1 committed",
                "step 1 checkpointed",
                "state reloaded",
                "step 2 active",
                "step 2 verification FAILED",
                "step 2 completion BLOCKED",
                "step 2 commit BLOCKED",
                "step 2 checkpoint BLOCKED",
                "next-step activation BLOCKED",
                "step 2 repair stayed active",
                "step 2 verification PASSED",
                "step 2 diff reviewed",
                "step 2 committed",
                "step 2 checkpointed",
            ],
        )
        self.assertEqual(proof["artifact"], "hello world\n")
        self.assertEqual(proof["intentional_failure"]["exit_code"], 1)
        self.assertEqual(proof["intentional_failure"]["status"], "FAILED")
        self.assertEqual(proof["failed_state"]["phase"], "VERIFY_FAILED")
        self.assertEqual(proof["failed_state"]["active_step"], 2)
        self.assertEqual(proof["failed_state"]["completed_steps"], [1])
        self.assertEqual(proof["head_during_failure"], proof["step_1_commit"])
        self.assertNotEqual(proof["step_1_commit"], proof["step_2_commit"])
        self.assertEqual(
            proof["commit_subjects"],
            ["demo: complete step 1", "demo: complete step 2"],
        )
        final_state = proof["final_state"]
        self.assertEqual(final_state["completed_steps"], [1, 2])
        self.assertIsNone(final_state["active_step"])
        self.assertIsNone(final_state["next_step"])
        self.assertEqual(final_state["phase"], "CHECKPOINT")
        self.assertEqual(final_state["verification"]["status"], "PASSED")

    def test_demo_never_has_more_than_one_active_step(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proof = run_demo(Path(temp_dir))

        self.assertEqual(proof["maximum_active_steps"], 1)


if __name__ == "__main__":
    unittest.main()
