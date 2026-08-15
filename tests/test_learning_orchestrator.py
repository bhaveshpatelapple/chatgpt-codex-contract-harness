import tempfile, unittest
from pathlib import Path
from harness_learning.context import ContextComposer, ContextRequest
from harness_learning.episodes import EpisodeStore
from harness_learning.models import Episode, HarnessError, Skill, VerificationStatus
from harness_learning.orchestrator import LearningOrchestrator
from harness_learning.roles import PermissionDenied, Role
from harness_learning.skills import EvaluationCase, SkillCandidate, SkillRegistry

ROOT=Path(__file__).resolve().parents[1]
class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.episodes=EpisodeStore(root/"episodes.json"); self.skills=SkillRegistry(root/"skills.json")
        self.o=LearningOrchestrator(root,ROOT/".harness/contract.yaml",ROOT/".harness/contract.lock",composer=ContextComposer(),episode_store=self.episodes,skill_registry=self.skills)
    def test_failed_verification_blocks_and_repair_stays_on_run(self):
        run=self.o.start({"task_kind":"replace","input":"wrong value","expected":"hello world"})
        failed=self.o.verify(run.active_attempt_id,"wrong value")
        self.assertEqual(VerificationStatus.FAILED,failed.status)
        with self.assertRaisesRegex(HarnessError,"ADVANCE_BLOCKED"): self.o.advance(failed)
        repaired=self.o.repair(failed,"hello world"); self.assertEqual(run.id,repaired.run_id)
    def test_stale_receipt_and_contract_mismatch_block_execution(self):
        run=self.o.start({"task_kind":"replace","input":"x","expected":"y"}); passed=self.o.verify(run.active_attempt_id,"y")
        with self.assertRaisesRegex(HarnessError,"VERIFICATION_STALE"): self.o.advance(passed.__class__(passed.id,passed.run_id,"other",passed.status))
        contract=Path(self.tmp.name)/"contract.yaml"; contract.write_text((ROOT/".harness/contract.yaml").read_text()+"\n# changed\n",encoding="utf-8")
        bad=LearningOrchestrator(Path(self.tmp.name)/"bad",contract,ROOT/".harness/contract.lock")
        with self.assertRaisesRegex(HarnessError,"CONTRACT_MISMATCH"): bad.start({"task_kind":"x","input":"x","expected":"x"})

    def test_context_and_memory_operations_are_permissioned(self):
        base={"L0":({"id":"contract","text":"locked"},),"L1":({"id":"policy","text":"verify"},),"L2":({"id":"task","text":"replace"},)}
        request=ContextRequest("replace greeting token","replace",10,True,True,base)
        self.assertEqual((),self.o.compose_context(Role.PLANNER,request).selected_records["L4"])
        with self.assertRaisesRegex(PermissionDenied,"PERMISSION_DENIED"):
            self.o.compose_context(Role.EXECUTOR,request)

        run=self.o.start({"task_kind":"replace","input":"wrong","expected":"right"})
        passed=self.o.verify(run.active_attempt_id,"right"); self.o.advance(passed)
        episode=self.o.admit_episode(Role.MEMORY,"replace","wrong","right","replace greeting token",("replace",),10)
        candidate=SkillCandidate("replace","replace greeting token",("replace","greeting","token"),("replace greeting token",),(episode.id,),(EvaluationCase("wrong","replace"),),.9,"replace")
        self.assertEqual("PROMOTED",self.o.propose_skill(Role.MEMORY,candidate).decision)
        before=self.episodes.all()
        with self.assertRaisesRegex(PermissionDenied,"PERMISSION_DENIED"):
            self.o.admit_episode(Role.PLANNER,"replace","a","b","replace a",("replace",),11)
        self.assertEqual(before,self.episodes.all())

    def test_memory_cannot_learn_from_failed_run(self):
        run=self.o.start({"task_kind":"replace","input":"wrong","expected":"right"})
        failed=self.o.verify(run.active_attempt_id,"wrong"); self.o.record_receipt(failed)
        with self.assertRaisesRegex(HarnessError,"MEMORY_UNVERIFIED"):
            self.o.admit_episode(Role.MEMORY,"replace","wrong","right","replace greeting token",("replace",),10)
        self.assertEqual((),self.episodes.all())

    def test_orchestrator_applies_independent_read_only_ablations(self):
        episode=Episode.create("replace","wrong","right","replace greeting token",("replace",),VerificationStatus.PASSED,"v1",1)
        skill=Skill("skill_1","replace","replace greeting token",("replace","greeting","token"),("replace greeting token",),(episode.id,),.9,"replace")
        self.episodes.store.upsert(episode); self.skills.store.upsert(skill)
        base={"L0":({"id":"contract","text":"locked"},),"L1":({"id":"policy","text":"verify"},),"L2":({"id":"task","text":"replace"},)}
        request=ContextRequest("replace greeting token","replace",10,True,True,base)

        manifests={(l4,l5):self.o.compose_context(Role.PLANNER,request,enable_l4=l4,enable_l5=l5) for l4 in (False,True) for l5 in (False,True)}

        self.assertEqual((0,0),(manifests[(False,False)].layers["L4"].used_items,manifests[(False,False)].layers["L5"].used_items))
        self.assertEqual((0,1),(manifests[(False,True)].layers["L4"].used_items,manifests[(False,True)].layers["L5"].used_items))
        self.assertEqual((1,0),(manifests[(True,False)].layers["L4"].used_items,manifests[(True,False)].layers["L5"].used_items))
        self.assertEqual((1,1),(manifests[(True,True)].layers["L4"].used_items,manifests[(True,True)].layers["L5"].used_items))
        baseline=manifests[(True,True)]
        for manifest in manifests.values():
            for layer in ("L0","L1","L2","L3"):
                self.assertEqual(baseline.layers[layer].selected_ids,manifest.layers[layer].selected_ids)
        self.assertEqual((episode,),self.episodes.all()); self.assertEqual((skill,),self.skills.all())
if __name__=="__main__": unittest.main()
