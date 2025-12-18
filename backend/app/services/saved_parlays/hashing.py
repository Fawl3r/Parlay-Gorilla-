"""Deterministic hashing helpers for Saved Parlays.

We use canonical JSON serialization + sha256 hex digests to create stable hashes
across processes and database reads/writes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import is_dataclass, asdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID


class CanonicalJsonSerializer:
    """Serialize JSON-like data deterministically (stable keys, consistent scalars)."""

    def serialize(self, value: Any) -> str:
        normalized = self._normalize(value)
        return json.dumps(
            normalized,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def _normalize(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (str, int, bool)):
            return value
        if isinstance(value, float):
            # Avoid platform-specific float repr quirks by formatting explicitly.
            # Keep enough precision for betting lines while remaining stable.
            return format(value, ".10g")
        if isinstance(value, Decimal):
            return format(value, "f")
        if isinstance(value, (datetime, date)):
            if isinstance(value, datetime) and value.tzinfo is not None:
                return value.isoformat()
            # Treat naive datetimes as UTC by convention.
            if isinstance(value, datetime):
                return value.replace(tzinfo=None).isoformat() + "Z"
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if is_dataclass(value):
            return self._normalize(asdict(value))
        if hasattr(value, "model_dump"):
            # Pydantic v2 models.
            return self._normalize(value.model_dump())
        if isinstance(value, Mapping):
            # Sort keys later via json.dumps(sort_keys=True); normalize values here.
            out: dict[str, Any] = {}
            for k, v in value.items():
                if v is None:
                    # Prefer omitting null-ish optional fields to reduce accidental hash churn.
                    continue
                out[str(k)] = self._normalize(v)
            return out
        if isinstance(value, (list, tuple)):
            return [self._normalize(v) for v in value]
        if isinstance(value, set):
            # Sets are unordered; sort by string form for deterministic output.
            return [self._normalize(v) for v in sorted(value, key=lambda x: str(x))]
        # Fallback: best-effort stringification.
        return str(value)


class Sha256HexHasher:
    """Compute sha256 hex digests."""

    def hash_text(self, text: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return digest


canonical_json = CanonicalJsonSerializer()
sha256_hex = Sha256HexHasher()


