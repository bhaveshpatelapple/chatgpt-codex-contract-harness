import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "harness_state.py"
PLAN = {
    "version": "0.1",
    "steps": [
        {"id": 1, "name": "Setup"},
        {"id": 2, "name": "Verification gate"},
    ],
}


def load_state_module():
    spec = importlib.util.spec_from_file_location("harness_state_gate", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def active_state():
    return {
        "version": "0.1",
        "phase": "EXECUTE_ONE_STEP",
        "active_step": 2,
        "completed_steps": [1],
        "next_step": 2,
        "verification": None,
    }


class VerificationGateTests(unittest.TestCase):
    def setUp(self):
        self.state_machine = load_state_module()

    def test_failed_verification_is_persisted_and_blocks_completion(self):
        failed = self.state_machine.run_verification(
            PLAN,
            active_state(),
            2,
            [sys.executable, "-c", "raise SystemExit(7)"],
        )

        self.assertEqual(failed["verification"]["status"], "FAILED")
        self.assertEqual(failed["verification"]["exit_code"], 7)
        self.assertEqual(failed["phase"], "VERIFY_FAILED")
        with self.assertRaisesRegex(ValueError, "verification must pass"):
            self.state_machine.complete_step(PLAN, failed, 2)

    def test_verification_output_is_persisted_for_reload_evidence(self):
        failed = self.state_machine.run_verification(
            PLAN,
            active_state(),
            2,
            [
                sys.executable,
                "-c",
                "import sys; print('observed mismatch'); print('details', file=sys.stderr); raise SystemExit(1)",
            ],
        )

        self.assertEqual(failed["verification"]["stdout"], "observed mismatch\n")
        self.assertEqual(failed["verification"]["stderr"], "details\n")

    def test_passed_verification_allows_completion(self):
        passed = self.state_machine.run_verification(
            PLAN,
            active_state(),
            2,
            [sys.executable, "-c", "raise SystemExit(0)"],
        )

        self.assertEqual(passed["verification"]["status"], "PASSED")
        self.assertEqual(passed["phase"], "DIFF_REVIEW")
        completed = self.state_machine.complete_step(PLAN, passed, 2)
        self.assertEqual(completed["completed_steps"], [1, 2])

    def test_verification_must_target_the_active_step(self):
        with self.assertRaisesRegex(ValueError, "step 1 is not active"):
            self.state_machine.run_verification(
                PLAN,
                active_state(),
                1,
                [sys.executable, "-c", "raise SystemExit(0)"],
            )

    def test_nonzero_exit_code_cannot_be_labeled_as_passed(self):
        inconsistent = active_state()
        inconsistent["verification"] = {
            "step": 2,
            "status": "PASSED",
            "command": ["example"],
            "exit_code": 7,
        }

        with self.assertRaisesRegex(ValueError, "verification must pass"):
            self.state_machine.complete_step(PLAN, inconsistent, 2)


if __name__ == "__main__":
    unittest.main()
