import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CausalAblationTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, "-m", "harness_learning.demo", *map(str, arguments)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )

    def test_l5_intervention_changes_first_attempt_outcome(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = Path(temp_dir) / "learning"
            learned = json.loads(self.run_cli("run", store).stdout)
            enabled = json.loads(
                self.run_cli("reuse", store, "wrong codex", "hello codex").stdout
            )
            disabled = json.loads(
                self.run_cli(
                    "reuse", store, "wrong codex", "hello codex", "--disable-l5"
                ).stdout
            )

        self.assertEqual("PASSED", enabled["first_verification"])
        self.assertEqual("PASSED", enabled["final_verification"])
        self.assertEqual(1, enabled["attempts"])
        self.assertEqual(learned["skill_id"], enabled["skill_id"])
        self.assertEqual("FAILED", disabled["first_verification"])
        self.assertEqual("PASSED", disabled["final_verification"])
        self.assertEqual(2, disabled["attempts"])
        self.assertIsNone(disabled["skill_id"])


if __name__ == "__main__":
    unittest.main()
