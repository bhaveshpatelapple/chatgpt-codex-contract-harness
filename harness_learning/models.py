from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum


class HarnessError(ValueError):
    def __init__(self, code: str, message: str = ""):
        self.code = code
        super().__init__(f"{code}: {message}" if message else code)


class VerificationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_id(kind: str, value) -> str:
    return f"{kind}_{hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()[:20]}"


@dataclass(frozen=True)
class Episode:
    id: str
    task_kind: str
    failure: str
    repair: str
    lesson: str
    tags: tuple[str, ...]
    verification_status: VerificationStatus
    verification_id: str
    created_sequence: int
    expiry_sequence: int | None = None
    kind: str = "episode"

    @property
    def search_text(self): return " ".join((self.task_kind, self.failure, self.repair, self.lesson, *self.tags))

    @classmethod
    def create(cls, task_kind, failure, repair, lesson, tags, verification_status, verification_id, created_sequence, expiry_sequence=None):
        if verification_status != VerificationStatus.PASSED:
            raise HarnessError("EPISODE_UNVERIFIED")
        if not all((task_kind.strip(), failure.strip(), repair.strip(), lesson.strip(), verification_id.strip())) or failure == repair:
            raise HarnessError("EPISODE_INVALID")
        stable = {"task_kind": task_kind, "failure": failure, "repair": repair, "lesson": lesson, "tags": sorted(set(tags)), "verification_id": verification_id}
        return cls(stable_id("episode", stable), task_kind, failure, repair, lesson, tuple(sorted(set(tags))), verification_status, verification_id, created_sequence, expiry_sequence)

    def to_dict(self):
        data = asdict(self); data["verification_status"] = self.verification_status.value; data["tags"] = list(self.tags); return data

    @classmethod
    def from_dict(cls, data):
        data = dict(data); data["tags"] = tuple(data["tags"]); data["verification_status"] = VerificationStatus(data["verification_status"]); return cls(**data)

@dataclass(frozen=True)
class Skill:
    id: str; name: str; purpose: str; trigger_tokens: tuple[str,...]; procedure: tuple[str,...]
    source_episode_ids: tuple[str,...]; quality: float; task_kind: str; revision: int = 1
    status: str = "PROMOTED"; kind: str = "skill"
    verification_status: VerificationStatus = VerificationStatus.PASSED
    created_sequence: int = 0; expiry_sequence: int|None = None
    @property
    def tags(self): return self.trigger_tokens
    @property
    def search_text(self): return " ".join((self.name,self.purpose,*self.trigger_tokens,*self.procedure))
    def to_dict(self):
        d=asdict(self); d["trigger_tokens"]=list(self.trigger_tokens); d["procedure"]=list(self.procedure); d["source_episode_ids"]=list(self.source_episode_ids); d["verification_status"]=self.verification_status.value; return d
    @classmethod
    def from_dict(cls,data):
        d=dict(data)
        for key in ("trigger_tokens","procedure","source_episode_ids"): d[key]=tuple(d[key])
        d["verification_status"]=VerificationStatus(d["verification_status"]); return cls(**d)
