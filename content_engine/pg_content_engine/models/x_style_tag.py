from __future__ import annotations

from .string_enum import StringEnum


class XStyleTag(StringEnum):
    AUTHORITY = "authority"
    WARNING = "warning"
    DISCIPLINE = "discipline"
    MISTAKE_BREAKDOWN = "mistake_breakdown"
