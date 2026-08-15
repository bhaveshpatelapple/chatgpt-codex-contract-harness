import tempfile, unittest
from pathlib import Path
from harness_learning.models import HarnessError, VerificationStatus
from harness_learning.orchestrator import LearningOrchestrator

ROOT=Path(__file__).resolve().parents[1]
class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.o=LearningOrchestrator(Path(self.tmp.name),ROOT/".harness/contract.yaml",ROOT/".harness/contract.lock")
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
if __name__=="__main__": unittest.main()
