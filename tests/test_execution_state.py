import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "harness_state.py"


def load_state_module():
    spec = importlib.util.spec_from_file_location("harness_state", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PLAN = {
    "version": "0.1",
    "steps": [
        {"id": 1, "name": "Repository skeleton"},
        {"id": 2, "name": "Contract validation"},
        {"id": 3, "name": "Execution state"},
        {"id": 4, "name": "Verification gate"},
    ],
}


def checkpoint_state():
    return {
        "version": "0.1",
        "phase": "NEXT_STEP",
        "active_step": None,
        "completed_steps": [1, 2],
        "next_step": 3,
    }


class ExecutionStateTests(unittest.TestCase):
    def setUp(self):
        self.state_machine = load_state_module()

    def test_starts_only_the_recorded_next_step(self):
        result = self.state_machine.start_step(PLAN, checkpoint_state(), 3)

        self.assertEqual(result["active_step"], 3)
        self.assertEqual(result["phase"], "EXECUTE_ONE_STEP")

    def test_rejects_a_second_active_step(self):
        state = self.state_machine.start_step(PLAN, checkpoint_state(), 3)

        with self.assertRaisesRegex(ValueError, "step 3 is already active"):
            self.state_machine.start_step(PLAN, state, 4)

    def test_rejects_starting_a_step_out_of_order(self):
        with self.assertRaisesRegex(ValueError, "next step is 3"):
            self.state_machine.start_step(PLAN, checkpoint_state(), 4)

    def test_completes_the_active_step_and_advances(self):
        active = self.state_machine.start_step(PLAN, checkpoint_state(), 3)

        result = self.state_machine.complete_step(PLAN, active, 3)

        self.assertEqual(result["completed_steps"], [1, 2, 3])
        self.assertIsNone(result["active_step"])
        self.assertEqual(result["next_step"], 4)
        self.assertEqual(result["phase"], "CHECKPOINT")

    def test_rejects_completing_a_step_that_is_not_active(self):
        with self.assertRaisesRegex(ValueError, "step 3 is not active"):
            self.state_machine.complete_step(PLAN, checkpoint_state(), 3)

    def test_state_round_trips_through_json(self):
        state = self.state_machine.start_step(PLAN, checkpoint_state(), 3)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state.json"

            self.state_machine.save_state(path, state)
            loaded = self.state_machine.load_state(path)

            serialized = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(loaded, state)
        self.assertEqual(serialized, state)


if __name__ == "__main__":
    unittest.main()
