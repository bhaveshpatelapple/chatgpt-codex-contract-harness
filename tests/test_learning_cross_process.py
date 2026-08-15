import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CrossProcessLearningTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, "-m", "harness_learning.demo", *map(str, arguments)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )

    def test_separate_process_reloads_and_reuses_learned_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = Path(temp_dir) / "learning"
            learned = json.loads(self.run_cli("run", store).stdout)
            inspected = json.loads(self.run_cli("inspect", store).stdout)
            reused = json.loads(
                self.run_cli("reuse", store, "wrong codex", "hello codex").stdout
            )

        self.assertIn(learned["episode_id"], inspected["episode_ids"])
        self.assertIn(learned["skill_id"], inspected["skill_ids"])
        self.assertEqual("PASSED", reused["verification"])
        self.assertEqual(1, reused["attempts"])
        self.assertEqual(learned["skill_id"], reused["skill_id"])


if __name__ == "__main__":
    unittest.main()
