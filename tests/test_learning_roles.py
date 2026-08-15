import unittest
from harness_learning.roles import Capability, PermissionDenied, Role, RoleDispatcher

class RoleTests(unittest.TestCase):
    def test_exact_permission_matrix_is_enforced_before_operation(self):
        allowed={Role.PLANNER:{Capability.READ_CONTEXT,Capability.WRITE_PLAN},Role.EXECUTOR:{Capability.READ_PLAN,Capability.WRITE_ATTEMPT},
        Role.VERIFIER:{Capability.READ_ATTEMPT,Capability.WRITE_VERIFICATION},Role.REPAIR:{Capability.READ_FAILURE,Capability.READ_CONTEXT,Capability.WRITE_ATTEMPT},
        Role.MEMORY:{Capability.READ_VERIFIED_RUN,Capability.WRITE_EPISODE,Capability.PROPOSE_SKILL}}
        dispatcher=RoleDispatcher(); called=[]
        for role in Role:
            for cap in Capability:
                if cap in allowed[role]: self.assertEqual("ok",dispatcher.perform(role,cap,lambda:"ok"))
                else:
                    with self.assertRaisesRegex(PermissionDenied,"PERMISSION_DENIED"): dispatcher.perform(role,cap,lambda:called.append(1))
        self.assertEqual([],called)
if __name__=="__main__": unittest.main()
