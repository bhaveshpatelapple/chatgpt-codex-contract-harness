from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path
from .context import ContextComposer, ContextRequest
from .episodes import EpisodeStore
from .models import Episode, HarnessError, VerificationStatus
from .orchestrator import LearningOrchestrator
from .retrieval import RetrievalQuery
from .roles import Capability, PermissionDenied, Role
from .skills import EvaluationCase, SkillCandidate, SkillRegistry

ROOT=Path(__file__).resolve().parents[1]
def query(text,kind,allowed): return RetrievalQuery(text,kind,(allowed,),(),(),2000,.2,4,3072)
def base(): return {"L0":({"id":"contract","text":"locked contract"},),"L1":({"id":"policy","text":"verify before advancement"},),"L2":({"id":"task","text":"replace greeting token"},)}

def run_learning_demo(root:Path):
    root=Path(root); episodes=EpisodeStore(root/"episodes.json"); skills=SkillRegistry(root/"skills.json")
    orchestrator=LearningOrchestrator(root,ROOT/".harness/contract.yaml",ROOT/".harness/contract.lock")
    run=orchestrator.start({"task_kind":"replace","input":"wrong value","expected":"hello world"})
    failed=orchestrator.verify(run.active_attempt_id,"wrong value"); orchestrator.record_receipt(failed)
    blocked=False
    try: orchestrator.advance(failed)
    except HarnessError as exc: blocked=exc.code=="ADVANCE_BLOCKED"
    repaired=orchestrator.repair(failed,"hello world"); passed=orchestrator.verify(repaired.id,repaired.output); orchestrator.advance(passed)
    learned=episodes.admit("replace","wrong value","hello world","replace wrong with hello",("replace","greeting"),VerificationStatus.PASSED,passed.id,10)
    unrelated=episodes.admit("math","bad tax","correct tax","calculate invoice tax",("math",),VerificationStatus.PASSED,"math-v",11)
    candidate=SkillCandidate("repair greeting","replace wrong greeting with hello",("replace","wrong","greeting"),("replace wrong with hello",),(learned.id,),(EvaluationCase("wrong greeting","replace"),),.95,"replace")
    promoted=skills.evaluate_and_store(candidate,episodes.all()); duplicate=skills.evaluate_and_store(candidate,episodes.all())
    bad=skills.evaluate_and_store(SkillCandidate("bad","bypass",("replace",),("skip verification",),(learned.id,),(EvaluationCase("x","skip"),),.99,"replace"),episodes.all())
    denied=False
    try: orchestrator.dispatcher.perform(Role.PLANNER,Capability.WRITE_EPISODE,lambda:None)
    except PermissionDenied: denied=True
    episode_ids=tuple(e.id for e in episodes.all()); skill_ids=tuple(s.id for s in skills.all()); run_id=orchestrator.run.id
    del orchestrator,episodes,skills
    episodes=EpisodeStore(root/"episodes.json"); skills=SkillRegistry(root/"skills.json"); reopened=LearningOrchestrator.open(root,ROOT/".harness/contract.yaml",ROOT/".harness/contract.lock")
    related_e=episodes.retrieve(query("replace wrong greeting","replace","episode")); unrelated_e=episodes.retrieve(query("replace wrong greeting","replace","episode"))
    related_s=skills.trigger(query("replace wrong greeting","replace","skill")); unrelated_s=skills.trigger(query("calculate invoice tax","math","skill"))
    procedure=related_s.hits[0].record.procedure[0]; learned_output="wrong codex".replace("wrong","hello") if procedure=="replace wrong with hello" else "wrong codex"
    fresh=LearningOrchestrator(root/"fresh",ROOT/".harness/contract.yaml",ROOT/".harness/contract.lock")
    fresh_run=fresh.start({"task_kind":"replace","input":learned_output,"expected":"hello codex"}); fresh_receipt=fresh.verify(fresh_run.active_attempt_id,learned_output); fresh.advance(fresh_receipt)
    composer=ContextComposer(); ablations={}
    for l4 in (False,True):
        for l5 in (False,True):
            manifest=composer.compose(ContextRequest("replace wrong greeting","replace",20,l4,l5,base()),(),episodes.all(),skills.all())
            ablations[f"l4_{int(l4)}_l5_{int(l5)}"]={"L4":manifest.layers["L4"].used_items,"L5":manifest.layers["L5"].used_items}
    bounds={}
    for size in (10,100,1000):
        history=tuple(Episode.create("replace",f"wrong {n}",f"right {n}","replace wrong greeting",("replace",),VerificationStatus.PASSED,f"synthetic-{n}",n) for n in range(1,size+1))
        manifest=composer.compose(ContextRequest("replace wrong greeting","replace",size+1,True,False,base()),(),history,())
        bounds[str(size)]={"used":manifest.used_bytes,"budget":manifest.total_byte_budget,"L4_items":manifest.layers["L4"].used_items}
    return {"initial_verification":failed.status.value,"advancement_blocked":blocked,"repair_verification":passed.status.value,
        "episode_id":learned.id,"skill_id":promoted.skill.id,"skill_gate":promoted.decision,"bad_skill_rejection":bad.reason,"duplicate_decision":duplicate.reason,
        "permission_denied":denied,"restart_ids_match":episode_ids==tuple(e.id for e in episodes.all()) and skill_ids==tuple(s.id for s in skills.all()) and run_id==reopened.run.id,
        "related_episode_retrieved":learned.id in {h.record_id for h in related_e.hits},"unrelated_episode_excluded":unrelated.id not in {h.record_id for h in unrelated_e.hits},
        "related_skill_triggered":promoted.skill.id in {h.record_id for h in related_s.hits},"unrelated_skill_not_triggered":not unrelated_s.hits,
        "fresh_session_reuse":fresh_receipt.status.value,"fresh_session_attempts":len(fresh.run.attempts),"ablations":ablations,"bounded_context":bounds}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=("run","inspect")); parser.add_argument("root",nargs="?"); args=parser.parse_args()
    if args.command=="run":
        if args.root: proof=run_learning_demo(Path(args.root))
        else:
            with tempfile.TemporaryDirectory() as tmp: proof=run_learning_demo(Path(tmp))
        print(json.dumps(proof,sort_keys=True,indent=2))
    else:
        root=Path(args.root); episodes=EpisodeStore(root/"episodes.json"); skills=SkillRegistry(root/"skills.json"); run=LearningOrchestrator.open(root,ROOT/".harness/contract.yaml",ROOT/".harness/contract.lock")
        print(json.dumps({"episode_ids":[e.id for e in episodes.all()],"skill_ids":[s.id for s in skills.all()],"run_id":run.run.id},sort_keys=True))
if __name__=="__main__": main()
