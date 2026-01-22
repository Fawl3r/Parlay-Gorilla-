from __future__ import annotations

from .string_enum import StringEnum


class ContentStatus(StringEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
