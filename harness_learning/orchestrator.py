from dataclasses import dataclass
from pathlib import Path
from scripts.harness_verify import validate_contract
from .adapters import OfflineAdapter
from .models import HarnessError, VerificationStatus, stable_id
from .roles import Capability, Role, RoleDispatcher

@dataclass(frozen=True)
class Attempt: id:str; run_id:str; output:str; number:int
@dataclass(frozen=True)
class VerificationReceipt: id:str; run_id:str; attempt_id:str; status:VerificationStatus
@dataclass
class RunState: id:str; task:dict; active_attempt_id:str; attempts:list; status:str="ACTIVE"

class LearningOrchestrator:
    def __init__(self,root,contract_path,lock_path,adapter=None):
        self.root=Path(root); self.contract_path=Path(contract_path); self.lock_path=Path(lock_path); self.adapter=adapter or OfflineAdapter(); self.dispatcher=RoleDispatcher(); self.run=None
    def _contract(self):
        try: validate_contract(self.contract_path,self.lock_path)
        except (OSError,ValueError) as exc: raise HarnessError("CONTRACT_MISMATCH",str(exc)) from exc
    def start(self,task):
        self._contract(); plan=self.dispatcher.perform(Role.PLANNER,Capability.WRITE_PLAN,lambda:self.adapter.plan(task))
        run_id=stable_id("run",task); output=self.dispatcher.perform(Role.EXECUTOR,Capability.WRITE_ATTEMPT,lambda:self.adapter.execute(plan))
        attempt=Attempt(stable_id("attempt",{"run":run_id,"number":1,"output":output}),run_id,output,1)
        self.run=RunState(run_id,dict(task),attempt.id,[attempt]); return self.run
    def verify(self,attempt_id,observed):
        if not self.run or attempt_id!=self.run.active_attempt_id: raise HarnessError("VERIFICATION_STALE")
        status=VerificationStatus.PASSED if observed==self.run.task["expected"] else VerificationStatus.FAILED
        return self.dispatcher.perform(Role.VERIFIER,Capability.WRITE_VERIFICATION,lambda:VerificationReceipt(stable_id("verification",{"run":self.run.id,"attempt":attempt_id,"status":status.value}),self.run.id,attempt_id,status))
    def advance(self,receipt):
        if not self.run or receipt.run_id!=self.run.id or receipt.attempt_id!=self.run.active_attempt_id: raise HarnessError("VERIFICATION_STALE")
        if receipt.status!=VerificationStatus.PASSED: raise HarnessError("ADVANCE_BLOCKED")
        self.run.status="COMPLETE"; return self.run
    def repair(self,failed_receipt,repaired_output):
        if not self.run or failed_receipt.run_id!=self.run.id or failed_receipt.attempt_id!=self.run.active_attempt_id or failed_receipt.status!=VerificationStatus.FAILED: raise HarnessError("REPAIR_STALE")
        output=self.dispatcher.perform(Role.REPAIR,Capability.WRITE_ATTEMPT,lambda:self.adapter.repair(self.run.task,self.run.attempts[-1].output,repaired_output))
        attempt=Attempt(stable_id("attempt",{"run":self.run.id,"number":len(self.run.attempts)+1,"output":output}),self.run.id,output,len(self.run.attempts)+1)
        self.run.attempts.append(attempt); self.run.active_attempt_id=attempt.id; return attempt
