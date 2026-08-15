import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".agents" / "skills" / "contract-locked-execution"


class ContractLockedSkillTests(unittest.TestCase):
    def test_skill_metadata_is_discoverable_and_complete(self):
        skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        _, frontmatter, body = skill_text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)

        self.assertEqual(set(metadata), {"name", "description"})
        self.assertEqual(metadata["name"], "contract-locked-execution")
        self.assertTrue(metadata["description"].startswith("Use when "))
        self.assertNotIn("TODO", body)

    def test_ui_metadata_invokes_the_skill_by_name(self):
        metadata = yaml.safe_load(
            (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
        )

        self.assertIn(
            "$contract-locked-execution",
            metadata["interface"]["default_prompt"],
        )


if __name__ == "__main__":
    unittest.main()
