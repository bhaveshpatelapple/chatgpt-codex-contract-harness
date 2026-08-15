from __future__ import annotations

import json
import os
from pathlib import Path

from .models import HarnessError, canonical_json


class JsonRecordStore:
    def __init__(self, path: Path, kind: str, decoder):
        self.path, self.kind, self.decoder = Path(path), kind, decoder

    def load(self):
        if not self.path.exists(): return ()
        try: envelope = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc: raise HarnessError("STORE_CORRUPT", str(exc)) from exc
        if envelope.get("schema_version") != 1: raise HarnessError("STORE_SCHEMA")
        if envelope.get("kind") != self.kind: raise HarnessError("STORE_KIND")
        try: records = tuple(self.decoder(item) for item in envelope["records"])
        except (KeyError, TypeError, ValueError) as exc: raise HarnessError("STORE_CORRUPT", str(exc)) from exc
        self._validate(records)
        return records

    def _validate(self, records):
        seen = {}
        for record in records:
            if getattr(record, "kind", None) != self.kind: raise HarnessError("STORE_KIND")
            if record.id in seen and seen[record.id] != record: raise HarnessError("STORE_ID_CONFLICT")
            seen[record.id] = record

    def replace(self, records):
        records = tuple(records); self._validate(records)
        unique = {record.id: record for record in records}
        envelope = {"schema_version": 1, "kind": self.kind, "records": [unique[key].to_dict() for key in sorted(unique)]}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(envelope) + "\n"); handle.flush(); os.fsync(handle.fileno())
        temporary.replace(self.path)

    def upsert(self, record):
        records = list(self.load())
        for existing in records:
            if existing.id == record.id:
                if existing != record: raise HarnessError("STORE_ID_CONFLICT")
                return existing
        records.append(record); self.replace(records); return record
