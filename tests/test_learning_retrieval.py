import unittest

from harness_learning.models import Episode, VerificationStatus
from harness_learning.retrieval import RetrievalQuery, retrieve


def ep(n, lesson, task="replace", expiry=None):
    return Episode.create(task, f"wrong{n}", f"right{n}", lesson, (task,), VerificationStatus.PASSED, f"v{n}", n, expiry)


class RetrievalTests(unittest.TestCase):
    def query(self, item_limit=4, byte_limit=2048):
        return RetrievalQuery("replace greeting token", "replace", ("episode",), (), (), 20, .2, item_limit, byte_limit)

    def test_excludes_stale_and_irrelevant_records(self):
        relevant = ep(1, "replace greeting token safely")
        stale = ep(2, "replace greeting token", expiry=10)
        irrelevant = ep(3, "calculate invoice tax", task="math")
        result = retrieve((relevant, stale, irrelevant), self.query())
        self.assertEqual((relevant.id,), tuple(hit.record_id for hit in result.hits))
        self.assertEqual("expired", result.exclusion_reasons[stale.id])
        self.assertEqual("irrelevant", result.exclusion_reasons[irrelevant.id])

    def test_selection_stays_bounded_as_history_grows(self):
        for size in (10, 100, 1000):
            result = retrieve(tuple(ep(n, "replace greeting token") for n in range(1, size + 1)), self.query(3, 800))
            self.assertLessEqual(len(result.hits), 3)
            self.assertLessEqual(result.used_bytes, 800)


if __name__ == "__main__": unittest.main()
