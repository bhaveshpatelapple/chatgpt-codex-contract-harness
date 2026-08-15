import tempfile, unittest
from pathlib import Path
from harness_learning.models import VerificationStatus
from harness_learning.orchestrator import LearningOrchestrator

ROOT=Path(__file__).resolve().parents[1]
class RestartTests(unittest.TestCase):
    def test_failed_run_reloads_and_repairs_with_same_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); o=LearningOrchestrator(root,ROOT/".harness/contract.yaml",ROOT/".harness/contract.lock")
            run=o.start({"task_kind":"replace","input":"wrong","expected":"right"}); failed=o.verify(run.active_attempt_id,"wrong"); o.record_receipt(failed)
            before=(root/"runs.json").read_bytes()
            reopened=LearningOrchestrator.open(root,ROOT/".harness/contract.yaml",ROOT/".harness/contract.lock")
            self.assertEqual(run.id,reopened.run.id); self.assertEqual(failed,reopened.last_receipt); self.assertEqual(before,(root/"runs.json").read_bytes())
            repaired=reopened.repair(reopened.last_receipt,"right")
            self.assertEqual(run.id,repaired.run_id); self.assertNotEqual(failed.attempt_id,repaired.id)
if __name__=="__main__": unittest.main()
