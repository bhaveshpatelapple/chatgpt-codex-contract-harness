from dataclasses import asdict, dataclass, replace
import json, os
from pathlib import Path
from scripts.harness_verify import validate_contract
from .adapters import OfflineAdapter
from .context import ContextComposer
from .episodes import EpisodeStore
from .models import HarnessError, VerificationStatus, stable_id
from .roles import Capability, Role, RoleDispatcher
from .skills import SkillRegistry

@dataclass(frozen=True)
class Attempt: id:str; run_id:str; output:str; number:int
@dataclass(frozen=True)
class VerificationReceipt: id:str; run_id:str; attempt_id:str; status:VerificationStatus
@dataclass
class RunState: id:str; task:dict; active_attempt_id:str; attempts:list; status:str="ACTIVE"

class LearningOrchestrator:
    def __init__(self,root,contract_path,lock_path,adapter=None,composer=None,episode_store=None,skill_registry=None):
        self.root=Path(root); self.contract_path=Path(contract_path); self.lock_path=Path(lock_path); self.adapter=adapter or OfflineAdapter(); self.composer=composer or ContextComposer(); self.episode_store=episode_store or EpisodeStore(self.root/"episodes.json"); self.skill_registry=skill_registry or SkillRegistry(self.root/"skills.json"); self.dispatcher=RoleDispatcher(); self.run=None; self.last_receipt=None
    def _save(self):
        self.root.mkdir(parents=True,exist_ok=True); path=self.root/"runs.json"; temporary=path.with_suffix(".json.tmp")
        envelope={"schema_version":1,"kind":"runs","run":None if not self.run else {"id":self.run.id,"task":self.run.task,"active_attempt_id":self.run.active_attempt_id,"attempts":[asdict(a) for a in self.run.attempts],"status":self.run.status},"last_receipt":None if not self.last_receipt else {**asdict(self.last_receipt),"status":self.last_receipt.status.value}}
        with temporary.open("w",encoding="utf-8",newline="\n") as handle:
            handle.write(json.dumps(envelope,sort_keys=True,separators=(",",":"))+"\n"); handle.flush(); os.fsync(handle.fileno())
        temporary.replace(path)
    @classmethod
    def open(cls,root,contract_path,lock_path,adapter=None,composer=None,episode_store=None,skill_registry=None):
        obj=cls(root,contract_path,lock_path,adapter,composer,episode_store,skill_registry); obj._contract(); path=Path(root)/"runs.json"
        try: data=json.loads(path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError) as exc: raise HarnessError("STORE_CORRUPT",str(exc)) from exc
        if data.get("schema_version")!=1 or data.get("kind")!="runs": raise HarnessError("STORE_SCHEMA")
        if data["run"]:
            r=data["run"]; attempts=[Attempt(**a) for a in r["attempts"]]
            if r["active_attempt_id"] not in {a.id for a in attempts}: raise HarnessError("STORE_REFERENCE")
            obj.run=RunState(r["id"],r["task"],r["active_attempt_id"],attempts,r["status"])
        if data["last_receipt"]:
            v=dict(data["last_receipt"]); v["status"]=VerificationStatus(v["status"]); obj.last_receipt=VerificationReceipt(**v)
        return obj
    def record_receipt(self,receipt):
        return self.dispatcher.perform(Role.VERIFIER,Capability.WRITE_VERIFICATION,lambda:self._record_receipt(receipt))
    def _record_receipt(self,receipt): self.last_receipt=receipt; self._save(); return receipt
    def _contract(self):
        try: validate_contract(self.contract_path,self.lock_path)
        except (OSError,ValueError) as exc: raise HarnessError("CONTRACT_MISMATCH",str(exc)) from exc
    def start(self,task):
        self._contract(); plan=self.dispatcher.perform(Role.PLANNER,Capability.WRITE_PLAN,lambda:self.adapter.plan(task))
        run_id=stable_id("run",task); output=self.dispatcher.perform(Role.EXECUTOR,Capability.WRITE_ATTEMPT,lambda:self.adapter.execute(plan))
        attempt=Attempt(stable_id("attempt",{"run":run_id,"number":1,"output":output}),run_id,output,1)
        self.run=RunState(run_id,dict(task),attempt.id,[attempt]); self._save(); return self.run
    def verify(self,attempt_id,observed):
        if not self.run or attempt_id!=self.run.active_attempt_id: raise HarnessError("VERIFICATION_STALE")
        status=VerificationStatus.PASSED if observed==self.run.task["expected"] else VerificationStatus.FAILED
        return self.dispatcher.perform(Role.VERIFIER,Capability.WRITE_VERIFICATION,lambda:VerificationReceipt(stable_id("verification",{"run":self.run.id,"attempt":attempt_id,"status":status.value}),self.run.id,attempt_id,status))
    def advance(self,receipt):
        if not self.run or receipt.run_id!=self.run.id or receipt.attempt_id!=self.run.active_attempt_id: raise HarnessError("VERIFICATION_STALE")
        if receipt.status!=VerificationStatus.PASSED: raise HarnessError("ADVANCE_BLOCKED")
        self.run.status="COMPLETE"; self.last_receipt=receipt; self._save(); return self.run
    def repair(self,failed_receipt,repaired_output):
        if not self.run or failed_receipt.run_id!=self.run.id or failed_receipt.attempt_id!=self.run.active_attempt_id or failed_receipt.status!=VerificationStatus.FAILED: raise HarnessError("REPAIR_STALE")
        output=self.dispatcher.perform(Role.REPAIR,Capability.WRITE_ATTEMPT,lambda:self.adapter.repair(self.run.task,self.run.attempts[-1].output,repaired_output))
        attempt=Attempt(stable_id("attempt",{"run":self.run.id,"number":len(self.run.attempts)+1,"output":output}),self.run.id,output,len(self.run.attempts)+1)
        self.run.attempts.append(attempt); self.run.active_attempt_id=attempt.id; self._save(); return attempt
    def compose_context(self,role,request,references=(),*,enable_l4=None,enable_l5=None):
        ablated=replace(request,enable_l4=request.enable_l4 if enable_l4 is None else enable_l4,enable_l5=request.enable_l5 if enable_l5 is None else enable_l5)
        return self.dispatcher.perform(role,Capability.READ_CONTEXT,lambda:self.composer.compose(ablated,references,self.episode_store.all(),self.skill_registry.all()))
    def _verified_receipt(self):
        receipt=self.last_receipt
        if not self.run or self.run.status!="COMPLETE" or not receipt or receipt.run_id!=self.run.id or receipt.attempt_id!=self.run.active_attempt_id or receipt.status!=VerificationStatus.PASSED:
            raise HarnessError("MEMORY_UNVERIFIED")
        return receipt
    def admit_episode(self,role,task_kind,failure,repair,lesson,tags,created_sequence,expiry_sequence=None):
        receipt=self.dispatcher.perform(role,Capability.READ_VERIFIED_RUN,self._verified_receipt)
        return self.dispatcher.perform(role,Capability.WRITE_EPISODE,lambda:self.episode_store.admit(task_kind,failure,repair,lesson,tags,receipt.status,receipt.id,created_sequence,expiry_sequence))
    def propose_skill(self,role,candidate):
        self.dispatcher.perform(role,Capability.READ_VERIFIED_RUN,self._verified_receipt)
        return self.dispatcher.perform(role,Capability.PROPOSE_SKILL,lambda:self.skill_registry.evaluate_and_store(candidate,self.episode_store.all()))
