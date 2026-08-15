import unittest

from harness_learning.models import Episode, HarnessError, VerificationStatus, stable_id


class LearningModelTests(unittest.TestCase):
    def test_stable_id_ignores_mapping_order(self):
        self.assertEqual(stable_id("episode", {"a": 1, "b": 2}), stable_id("episode", {"b": 2, "a": 1}))

    def test_episode_requires_passed_verification(self):
        with self.assertRaisesRegex(HarnessError, "EPISODE_UNVERIFIED"):
            Episode.create("replace", "wrong", "right", "use right", ("replace",), VerificationStatus.FAILED, "v1", 1)


if __name__ == "__main__":
    unittest.main()
