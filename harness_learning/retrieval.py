from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .models import VerificationStatus, canonical_json


def tokenize(text):
    return frozenset(re.findall(r"[\w]+", unicodedata.normalize("NFKC", text).lower()))


def _record_payload(record):
    to_dict = getattr(record, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    if isinstance(record, dict):
        return record
    raise TypeError(f"retrieval record {type(record).__name__} is not serializable")


@dataclass(frozen=True)
class RetrievalQuery:
    text: str; task_kind: str; allowed_kinds: tuple[str, ...]; required_tags: tuple[str, ...]
    excluded_ids: tuple[str, ...]; current_sequence: int; minimum_score: float
    item_limit: int; byte_limit: int


@dataclass(frozen=True)
class RetrievalHit:
    record_id: str; score: float; record: object


@dataclass(frozen=True)
class RetrievalResult:
    hits: tuple[RetrievalHit, ...]; used_bytes: int; exclusion_reasons: dict[str, str]


def retrieve(candidates, query):
    query_tokens = tokenize(query.text); excluded = {}; scored = []
    for record in candidates:
        reason = None
        if record.id in query.excluded_ids: reason = "excluded"
        elif record.kind not in query.allowed_kinds: reason = "kind"
        elif getattr(record, "verification_status", VerificationStatus.PASSED) != VerificationStatus.PASSED: reason = "verification_failed"
        elif getattr(record, "expiry_sequence", None) is not None and record.expiry_sequence < query.current_sequence: reason = "expired"
        elif not set(query.required_tags).issubset(record.tags): reason = "tags"
        else:
            overlap = len(query_tokens & tokenize(record.search_text)) / max(1, len(query_tokens))
            if not overlap: reason = "irrelevant"
            else:
                score = overlap + (.2 if record.task_kind == query.task_kind else 0) + (.1 if set(record.tags) & query_tokens else 0)
                score += max(0, .05 - max(0, query.current_sequence - record.created_sequence) * .001)
                if score < query.minimum_score: reason = "below_score"
                else: scored.append((score, record))
        if reason: excluded[record.id] = reason
    hits=[]; used=0
    for score, record in sorted(scored, key=lambda pair: (-pair[0], pair[1].id)):
        size = len(canonical_json({"id": record.id, "score": round(score, 6), "record": _record_payload(record)}).encode())
        if len(hits) >= query.item_limit: excluded[record.id] = "item_budget"; continue
        if used + size > query.byte_limit: excluded[record.id] = "byte_budget"; continue
        hits.append(RetrievalHit(record.id, score, record)); used += size
    return RetrievalResult(tuple(hits), used, excluded)
