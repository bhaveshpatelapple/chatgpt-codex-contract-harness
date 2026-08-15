import tempfile, unittest
from pathlib import Path
from harness_learning.episodes import EpisodeStore
from harness_learning.models import VerificationStatus
from harness_learning.retrieval import RetrievalQuery
from harness_learning.skills import EvaluationCase, SkillCandidate, SkillRegistry

class SkillTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); root=Path(self.tmp.name)
        es=EpisodeStore(root/"episodes.json")
        self.episode=es.admit("replace","wrong","right","replace greeting token safely",("replace",),VerificationStatus.PASSED,"v1",1)
        self.registry=SkillRegistry(root/"skills.json")
    def candidate(self, procedure=("replace greeting token safely",), quality=.9, source=None):
        return SkillCandidate("safe replace","replace greeting token",("replace","greeting","token"),procedure,(source or self.episode.id,),
            (EvaluationCase("replace greeting","replace"),),quality,"replace")
    def query(self,text,kind): return RetrievalQuery(text,kind,("skill",),(),(),10,.2,3,2048)
    def test_promoted_skill_triggers_selectively(self):
        outcome=self.registry.evaluate_and_store(self.candidate(),(self.episode,)); self.assertEqual("PROMOTED",outcome.decision)
        self.assertEqual(1,len(self.registry.trigger(self.query("replace greeting token","replace")).hits))
        self.assertEqual(0,len(self.registry.trigger(self.query("calculate invoice tax","math")).hits))
    def test_gate_rejects_unverified_unsafe_evaluation_and_quality(self):
        cases=[(self.candidate(source="missing"),"SOURCE_UNVERIFIED"),(self.candidate(("skip verification",)),"SAFETY"),
               (self.candidate(("unrelated action",)),"EVALUATION"),(self.candidate(quality=.2),"QUALITY")]
        for candidate,reason in cases:
            with self.subTest(reason=reason): self.assertEqual(reason,self.registry.evaluate_and_store(candidate,(self.episode,)).reason)
    def test_duplicate_rejects_exact_and_merges_compatible(self):
        self.assertEqual("PROMOTED",self.registry.evaluate_and_store(self.candidate(),(self.episode,)).decision)
        self.assertEqual("EXACT_DUPLICATE",self.registry.evaluate_and_store(self.candidate(),(self.episode,)).reason)
        merged=self.registry.evaluate_and_store(self.candidate(("replace greeting token safely","confirm replace"),quality=.95),(self.episode,))
        self.assertEqual("MERGED",merged.decision); self.assertEqual(2,merged.skill.revision)

if __name__=="__main__": unittest.main()
