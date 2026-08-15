from dataclasses import dataclass, replace
from .models import Skill, stable_id
from .persistence import JsonRecordStore
from .retrieval import retrieve, tokenize

@dataclass(frozen=True)
class EvaluationCase: input: str; expected_token: str
@dataclass(frozen=True)
class SkillCandidate:
    name: str; purpose: str; trigger_tokens: tuple[str,...]; procedure: tuple[str,...]
    source_episode_ids: tuple[str,...]; evaluation_cases: tuple[EvaluationCase,...]; quality: float; task_kind: str
@dataclass(frozen=True)
class GateOutcome: decision: str; reason: str|None=None; skill: Skill|None=None

class SkillRegistry:
    def __init__(self,path): self.store=JsonRecordStore(path,"skill",Skill.from_dict)
    def all(self): return self.store.load()
    def trigger(self,query): return retrieve(self.all(),query)
    def evaluate_and_store(self,candidate,episodes):
        verified={e.id for e in episodes}
        if not set(candidate.source_episode_ids).issubset(verified): return GateOutcome("REJECTED","SOURCE_UNVERIFIED")
        text=" ".join(candidate.procedure).lower()
        if any(term in text for term in ("bypass permission","skip verification","disable contract","rm -rf","delete repository")): return GateOutcome("REJECTED","SAFETY")
        ratio=sum(case.expected_token.lower() in text for case in candidate.evaluation_cases)/max(1,len(candidate.evaluation_cases))
        if ratio < .8: return GateOutcome("REJECTED","EVALUATION")
        if candidate.quality < .7: return GateOutcome("REJECTED","QUALITY")
        stable={"name":candidate.name,"purpose":candidate.purpose,"triggers":sorted(set(candidate.trigger_tokens)),"procedure":candidate.procedure,"sources":sorted(set(candidate.source_episode_ids)),"task_kind":candidate.task_kind}
        skill=Skill(stable_id("skill",stable),candidate.name,candidate.purpose,tuple(sorted(set(candidate.trigger_tokens))),candidate.procedure,tuple(sorted(set(candidate.source_episode_ids))),candidate.quality,candidate.task_kind)
        for existing in self.all():
            if existing.id==skill.id: return GateOutcome("REJECTED","EXACT_DUPLICATE",existing)
            a,b=set(existing.trigger_tokens),set(skill.trigger_tokens); similarity=len(a&b)/max(1,len(a|b))
            if existing.task_kind==skill.task_kind and similarity>=.8:
                if not (set(existing.procedure).issubset(skill.procedure) or set(skill.procedure).issubset(existing.procedure)):
                    return GateOutcome("REJECTED","DUPLICATE_CONFLICT",existing)
                merged=replace(existing,procedure=tuple(dict.fromkeys((*existing.procedure,*skill.procedure))),source_episode_ids=tuple(sorted(set(existing.source_episode_ids)|set(skill.source_episode_ids))),quality=max(existing.quality,skill.quality),revision=existing.revision+1)
                self.store.replace(tuple(merged if x.id==existing.id else x for x in self.all()))
                return GateOutcome("MERGED",skill=merged)
        self.store.upsert(skill); return GateOutcome("PROMOTED",skill=skill)
