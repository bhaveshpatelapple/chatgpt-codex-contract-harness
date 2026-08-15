import unittest
from harness_learning.context import ContextComposer, ContextRequest
from harness_learning.models import Episode, Skill, VerificationStatus

def episode(n): return Episode.create("replace",f"w{n}",f"r{n}","replace greeting token",("replace",),VerificationStatus.PASSED,f"v{n}",n)
def skill(n=1): return Skill(f"skill_{n}","replace","replace greeting token",("replace","greeting","token"),("replace greeting token",),("e",),.9,"replace")

class ContextTests(unittest.TestCase):
    def setUp(self): self.composer=ContextComposer(); self.base={"L0":({"id":"contract","text":"locked contract"},),"L1":({"id":"policy","text":"verify before advance"},),"L2":({"id":"task","text":"replace greeting token"},)}
    def request(self,l4=True,l5=True): return ContextRequest("replace greeting token","replace",10,l4,l5,self.base)
    def test_manifest_records_all_typed_layers_and_budgets(self):
        manifest=self.composer.compose(self.request(),(),(episode(1),),(skill(),))
        self.assertEqual(tuple(f"L{i}" for i in range(6)),tuple(manifest.layers))
        for name,layer in manifest.layers.items():
            self.assertEqual(name,layer.layer_type); self.assertLessEqual(layer.used_items,layer.item_budget); self.assertLessEqual(layer.used_bytes,layer.byte_budget)
        self.assertLessEqual(manifest.used_bytes,manifest.total_byte_budget)
    def test_long_histories_remain_bounded(self):
        for size in (10,100,1000):
            m=self.composer.compose(self.request(),(),tuple(episode(n) for n in range(1,size+1)),(skill(),))
            self.assertLessEqual(m.layers["L4"].used_items,4); self.assertLessEqual(m.used_bytes,16384)
    def test_l4_l5_ablations_are_independent(self):
        manifests={(a,b):self.composer.compose(self.request(a,b),(),(episode(1),),(skill(),)) for a in (False,True) for b in (False,True)}
        self.assertEqual(0,manifests[(False,True)].layers["L4"].used_items); self.assertGreater(manifests[(False,True)].layers["L5"].used_items,0)
        self.assertGreater(manifests[(True,False)].layers["L4"].used_items,0); self.assertEqual(0,manifests[(True,False)].layers["L5"].used_items)
        self.assertEqual(manifests[(False,False)].layers["L3"].selected_ids,manifests[(True,True)].layers["L3"].selected_ids)

if __name__=="__main__": unittest.main()
