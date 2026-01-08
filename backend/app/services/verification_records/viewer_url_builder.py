"""Verification record viewer URL builder.

We intentionally default to returning a *relative* viewer path so frontend links
stay on the current origin (avoids www/apex mismatches in production).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True, slots=True)
class VerificationRecordViewerUrlBuilder:
    """Builds verification record viewer URLs/paths in a consistent way."""

    def build(self, record_id: str, *, absolute: bool = False) -> str:
        record_id_clean = str(record_id or "").strip()
        path = f"/verification-records/{record_id_clean}" if record_id_clean else "/verification-records"

        if not absolute:
            return path

        base = str(getattr(settings, "frontend_url", "") or "").rstrip("/")
        if not base:
            base = "http://localhost:3000"
        return f"{base}{path}"


