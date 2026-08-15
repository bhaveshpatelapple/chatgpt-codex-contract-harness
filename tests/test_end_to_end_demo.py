import tempfile
import unittest
from pathlib import Path

from examples.two_step_demo import run_demo


class TwoStepDemoTests(unittest.TestCase):
    def test_demo_proves_persistence_failure_blocking_and_recovery(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            events, final_state = run_demo(Path(temp_dir))
            artifact = (Path(temp_dir) / "message.txt").read_text(encoding="utf-8")

        self.assertEqual(
            events,
            [
                "step 1 verification PASSED",
                "step 1 checkpointed",
                "state reloaded",
                "step 2 verification FAILED",
                "step 2 completion BLOCKED",
                "step 2 verification PASSED",
                "step 2 checkpointed",
            ],
        )
        self.assertEqual(artifact, "hello world\n")
        self.assertEqual(final_state["completed_steps"], [1, 2])
        self.assertIsNone(final_state["active_step"])
        self.assertIsNone(final_state["next_step"])
        self.assertEqual(final_state["phase"], "CHECKPOINT")


if __name__ == "__main__":
    unittest.main()
