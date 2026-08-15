import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "harness_state.py"
CONTRACT = """\
version: "0.1"
status: LOCKED
goal: Build a harness.
required_features:
  - locked contract
workflow:
  - CONTRACT_LOCK
invariants:
  - contract cannot silently change
out_of_scope:
  - web UI
"""
PLAN = {"version": "0.1", "steps": [{"id": 1, "name": "Only step"}]}


def load_state_module():
    spec = importlib.util.spec_from_file_location("harness_state_contract", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checkpoint_state():
    return {
        "version": "0.1",
        "phase": "NEXT_STEP",
        "active_step": None,
        "completed_steps": [],
        "next_step": 1,
        "verification": None,
    }


class ContractRuntimeEnforcementTests(unittest.TestCase):
    def setUp(self):
        self.state_machine = load_state_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        self.contract_path = root / "contract.yaml"
        self.lock_path = root / "contract.lock"
        self.contract_path.write_text(CONTRACT, encoding="utf-8", newline="\n")
        digest = hashlib.sha256(CONTRACT.encode("utf-8")).hexdigest()
        self.lock_path.write_text(f"sha256:{digest}\n", encoding="utf-8")

    def contract_paths(self):
        return {
            "contract_path": self.contract_path,
            "lock_path": self.lock_path,
        }

    def test_silent_change_blocks_start_before_state_transition(self):
        self.contract_path.write_text(
            CONTRACT.replace("web UI", "cloud deployment"),
            encoding="utf-8",
            newline="\n",
        )

        with self.assertRaisesRegex(ValueError, "contract digest does not match lock"):
            self.state_machine.start_step(
                PLAN, checkpoint_state(), 1, **self.contract_paths()
            )

    def test_silent_change_blocks_verification_before_command_execution(self):
        marker = Path(self.temp_dir.name) / "command-ran"
        active = checkpoint_state()
        active["active_step"] = 1
        active["phase"] = "EXECUTE_ONE_STEP"
        self.contract_path.write_text(
            CONTRACT.replace("web UI", "cloud deployment"),
            encoding="utf-8",
            newline="\n",
        )

        with self.assertRaisesRegex(ValueError, "contract digest does not match lock"):
            self.state_machine.run_verification(
                PLAN,
                active,
                1,
                [sys.executable, "-c", f"open({str(marker)!r}, 'w').close()"],
                **self.contract_paths(),
            )

        self.assertFalse(marker.exists())

    def test_silent_change_blocks_completion_before_state_transition(self):
        verified = checkpoint_state()
        verified["active_step"] = 1
        verified["phase"] = "DIFF_REVIEW"
        verified["verification"] = {
            "step": 1,
            "status": "PASSED",
            "command": ["example"],
            "exit_code": 0,
        }
        self.contract_path.write_text(
            CONTRACT.replace("web UI", "cloud deployment"),
            encoding="utf-8",
            newline="\n",
        )

        with self.assertRaisesRegex(ValueError, "contract digest does not match lock"):
            self.state_machine.complete_step(
                PLAN, verified, 1, **self.contract_paths()
            )


if __name__ == "__main__":
    unittest.main()
