import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from harness_learning.models import Episode, HarnessError, VerificationStatus
from harness_learning.persistence import JsonRecordStore


class LearningPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "episodes.json"
        self.episode = Episode.create("replace", "wrong", "right", "use right", ("replace",), VerificationStatus.PASSED, "v1", 1)

    def test_store_round_trips_with_same_identity(self):
        store = JsonRecordStore(self.path, "episode", Episode.from_dict)
        store.upsert(self.episode)
        self.assertEqual((self.episode,), JsonRecordStore(self.path, "episode", Episode.from_dict).load())

    def test_conflicting_duplicate_does_not_replace_valid_store(self):
        store = JsonRecordStore(self.path, "episode", Episode.from_dict); store.upsert(self.episode)
        before = self.path.read_bytes()
        with self.assertRaisesRegex(HarnessError, "STORE_ID_CONFLICT"):
            store.replace((self.episode, replace(self.episode, lesson="conflict")))
        self.assertEqual(before, self.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
