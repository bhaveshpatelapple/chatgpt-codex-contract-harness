import tempfile, unittest
from pathlib import Path
from harness_learning.episodes import EpisodeStore
from harness_learning.models import HarnessError, VerificationStatus
from harness_learning.retrieval import RetrievalQuery

class EpisodeStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.store=EpisodeStore(Path(self.tmp.name)/"episodes.json")
    def admit(self, n=1, lesson="replace greeting token", task="replace", expiry=None):
        return self.store.admit(task, f"wrong{n}", f"right{n}", lesson, (task,), VerificationStatus.PASSED, f"v{n}", n, expiry)
    def test_only_verified_repairs_are_admitted(self):
        with self.assertRaisesRegex(HarnessError,"EPISODE_UNVERIFIED"):
            self.store.admit("replace","wrong","right","lesson",("replace",),VerificationStatus.FAILED,"v",1)
        self.assertEqual((),self.store.all())
    def test_duplicate_admission_is_idempotent(self):
        self.assertEqual(self.admit().id,self.admit().id); self.assertEqual(1,len(self.store.all()))
    def test_retrieval_excludes_stale_and_unrelated(self):
        relevant=self.admit(); stale=self.admit(2,expiry=5); unrelated=self.admit(3,"invoice tax","math")
        q=RetrievalQuery("replace greeting token","replace",("episode",),(),(),10,.2,4,2048)
        result=self.store.retrieve(q)
        self.assertEqual((relevant.id,),tuple(h.record_id for h in result.hits))
        self.assertEqual("expired",result.exclusion_reasons[stale.id]); self.assertEqual("irrelevant",result.exclusion_reasons[unrelated.id])

if __name__=="__main__": unittest.main()
