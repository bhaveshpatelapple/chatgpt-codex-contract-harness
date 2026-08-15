from enum import Enum
from .models import HarnessError

class Role(str,Enum): PLANNER="planner"; EXECUTOR="executor"; VERIFIER="verifier"; REPAIR="repair"; MEMORY="memory"
class Capability(str,Enum):
    READ_CONTEXT="read_context"; WRITE_PLAN="write_plan"; READ_PLAN="read_plan"; WRITE_ATTEMPT="write_attempt"
    READ_ATTEMPT="read_attempt"; WRITE_VERIFICATION="write_verification"; READ_FAILURE="read_failure"
    READ_VERIFIED_RUN="read_verified_run"; WRITE_EPISODE="write_episode"; PROPOSE_SKILL="propose_skill"
class PermissionDenied(HarnessError):
    def __init__(self,role,capability): super().__init__("PERMISSION_DENIED",f"{role.value}:{capability.value}")
PERMISSIONS={Role.PLANNER:{Capability.READ_CONTEXT,Capability.WRITE_PLAN},Role.EXECUTOR:{Capability.READ_PLAN,Capability.WRITE_ATTEMPT},Role.VERIFIER:{Capability.READ_ATTEMPT,Capability.WRITE_VERIFICATION},Role.REPAIR:{Capability.READ_FAILURE,Capability.READ_CONTEXT,Capability.WRITE_ATTEMPT},Role.MEMORY:{Capability.READ_VERIFIED_RUN,Capability.WRITE_EPISODE,Capability.PROPOSE_SKILL}}
class RoleDispatcher:
    def perform(self,role,capability,operation):
        if capability not in PERMISSIONS[role]: raise PermissionDenied(role,capability)
        return operation()
