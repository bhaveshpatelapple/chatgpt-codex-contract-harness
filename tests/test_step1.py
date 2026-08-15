import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StepOneRepositoryTests(unittest.TestCase):
    def test_required_step_one_files_exist(self):
        required_files = {
            "AGENTS.md",
            "README.md",
            "pyproject.toml",
            ".harness/contract.yaml",
        }

        missing = sorted(path for path in required_files if not (ROOT / path).is_file())

        self.assertEqual(missing, [])

if __name__ == "__main__":
    unittest.main()
