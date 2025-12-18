"""Timezone normalization utilities to keep datetimes consistent."""

from datetime import datetime, timezone
from typing import Optional


class TimezoneNormalizer:
    """Normalize datetimes to UTC-aware values for consistent serialization."""

    @staticmethod
    def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
        """
        Ensure a datetime is timezone-aware in UTC.

        - If dt is None, returns None.
        - If dt is naive, assumes it is UTC and attaches timezone info.
        - If dt has a timezone, converts to UTC.
        """
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def isoformat_utc(dt: Optional[datetime]) -> Optional[str]:
        """Return an ISO-8601 string in UTC (or None)."""
        normalized = TimezoneNormalizer.ensure_utc(dt)
        return normalized.isoformat() if normalized else None

