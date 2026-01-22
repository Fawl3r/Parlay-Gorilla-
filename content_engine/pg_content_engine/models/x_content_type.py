from __future__ import annotations

from .string_enum import StringEnum


class XContentType(StringEnum):
    POST = "post"
    THREAD = "thread"
    REPLY = "reply"
