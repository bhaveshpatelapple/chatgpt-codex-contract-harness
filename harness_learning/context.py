from dataclasses import dataclass
from .models import HarnessError, canonical_json, stable_id
from .retrieval import RetrievalQuery, retrieve

DEFAULTS={"L0":(2,2048),"L1":(4,2048),"L2":(4,3072),"L3":(8,4096),"L4":(4,3072),"L5":(3,3072)}

@dataclass(frozen=True)
class ContextRequest:
    text: str; task_kind: str; current_sequence: int; enable_l4: bool; enable_l5: bool; mandatory_layers: dict
@dataclass(frozen=True)
class LayerManifest:
    layer_type: str; enabled: bool; item_budget: int; byte_budget: int; used_items: int; used_bytes: int; selected_ids: tuple[str,...]; exclusion_reasons: dict
@dataclass(frozen=True)
class ContextManifest:
    query_id: str; total_byte_budget: int; used_bytes: int; ablations: dict; layers: dict

class ContextComposer:
    def __init__(self,total_byte_budget=16384,budgets=None): self.total_byte_budget=total_byte_budget; self.budgets=budgets or DEFAULTS
    def _mandatory(self,name,records):
        limit,bytes_limit=self.budgets[name]; chosen=tuple(records); used=len(canonical_json(chosen).encode())
        if len(chosen)>limit or used>bytes_limit: raise HarnessError("CONTEXT_MANDATORY_OVERFLOW",name)
        return LayerManifest(name,True,limit,bytes_limit,len(chosen),used,tuple(str(r["id"]) for r in chosen),{})
    def compose(self,request,references,episodes,skills):
        layers={name:self._mandatory(name,request.mandatory_layers.get(name,())) for name in ("L0","L1","L2")}
        used=sum(layer.used_bytes for layer in layers.values())
        for name,records,enabled,kind in (("L3",references,True,"reference"),("L4",episodes,request.enable_l4,"episode"),("L5",skills,request.enable_l5,"skill")):
            item_limit,byte_limit=self.budgets[name]
            if not enabled:
                layers[name]=LayerManifest(name,False,item_limit,byte_limit,0,0,(),{getattr(r,"id",str(i)):"ablated" for i,r in enumerate(records)}); continue
            if records:
                allowed=tuple(sorted({getattr(r,"kind",kind) for r in records}))
                result=retrieve(records,RetrievalQuery(request.text,request.task_kind,allowed,(),(),request.current_sequence,.2,item_limit,min(byte_limit,max(0,self.total_byte_budget-used))))
                ids=tuple(h.record_id for h in result.hits); layer_used=result.used_bytes; reasons=result.exclusion_reasons
            else: ids=(); layer_used=0; reasons={}
            layers[name]=LayerManifest(name,True,item_limit,byte_limit,len(ids),layer_used,ids,reasons); used+=layer_used
        return ContextManifest(stable_id("query",{"text":request.text,"kind":request.task_kind}),self.total_byte_budget,used,{"enable_l4":request.enable_l4,"enable_l5":request.enable_l5},layers)
