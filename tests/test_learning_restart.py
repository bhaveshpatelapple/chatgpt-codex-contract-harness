import shutil, tempfile, unittest
from pathlib import Path
from harness_learning.models import HarnessError, VerificationStatus
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

    def test_open_rejects_contract_mismatch_before_loading_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); contract=root/"contract.yaml"; lock=root/"contract.lock"
            shutil.copyfile(ROOT/".harness/contract.yaml",contract); shutil.copyfile(ROOT/".harness/contract.lock",lock)
            original=LearningOrchestrator(root,contract,lock)
            original.start({"task_kind":"replace","input":"wrong","expected":"right"})
            before=(root/"runs.json").read_bytes()
            contract.write_text(contract.read_text(encoding="utf-8")+"\n# tampered\n",encoding="utf-8")

            with self.assertRaisesRegex(HarnessError,"CONTRACT_MISMATCH"):
                LearningOrchestrator.open(root,contract,lock)

            self.assertEqual(before,(root/"runs.json").read_bytes())
if __name__=="__main__": unittest.main()
