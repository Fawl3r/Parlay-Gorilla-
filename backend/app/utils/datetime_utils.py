"""
Datetime helpers.

SQLite (used in tests) can return naive datetimes even when timezone=True is set on columns.
To keep comparisons safe and consistent, we normalize datetimes to UTC when needed.
"""

from __future__ import annotations

from datetime import datetime, timezone


def coerce_utc(dt: datetime) -> datetime:
    """Ensure `dt` is timezone-aware and in UTC (treat naive datetimes as UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def now_utc() -> datetime:
    """Timezone-aware UTC 'now'."""
    return datetime.now(timezone.utc)


