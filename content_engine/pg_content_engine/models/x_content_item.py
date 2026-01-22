from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .compliance_flags import ComplianceFlags
from .content_status import ContentStatus
from .parse_error import ContentItemParseError
from .schedule import Schedule
from .x_content_type import XContentType
from .x_style_tag import XStyleTag


@dataclass(frozen=True)
class XContentItem:
    content_id: str
    content_type: XContentType
    topic: str
    text_blocks: list[str]
    style_tag: XStyleTag
    compliance: ComplianceFlags
    hashtags: list[str]
    schedule: Schedule
    status: ContentStatus

    @classmethod
    def from_dict(cls, data: Any) -> "XContentItem":
        if not isinstance(data, dict):
            raise ContentItemParseError("X item must be an object.")
        content_id = cls._get_required_str(data, "id")
        topic = cls._get_required_str(data, "topic")
        content_type = cls._parse_enum(XContentType, data.get("type"), "type")
        style_tag = cls._parse_enum(XStyleTag, data.get("style_tag"), "style_tag")
        status = cls._parse_enum(ContentStatus, data.get("status"), "status")
        text_blocks = cls._parse_text_blocks(data.get("text"), content_type)
        compliance = cls._parse_compliance(data.get("compliance"))
        schedule = cls._parse_schedule(data.get("schedule"))
        hashtags = cls._parse_hashtags(data.get("hashtags"))
        return cls(
            content_id=content_id,
            content_type=content_type,
            topic=topic,
            text_blocks=text_blocks,
            style_tag=style_tag,
            compliance=compliance,
            hashtags=hashtags,
            schedule=schedule,
            status=status,
        )

    def to_dict(self) -> dict[str, Any]:
        text: str | list[str]
        if self.content_type == XContentType.THREAD:
            text = list(self.text_blocks)
        else:
            text = self.text_blocks[0] if self.text_blocks else ""
        return {
            "id": self.content_id,
            "type": self.content_type.value,
            "topic": self.topic,
            "text": text,
            "style_tag": self.style_tag.value,
            "compliance": self.compliance.to_dict(),
            "hashtags": list(self.hashtags),
            "schedule": self.schedule.to_dict(),
            "status": self.status.value,
        }

    @staticmethod
    def _get_required_str(data: dict[str, Any], field: str) -> str:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ContentItemParseError(f"X item field '{field}' must be a string.", field)
        return value.strip()

    @staticmethod
    def _parse_enum(enum_type: type, value: Any, field: str) -> Any:
        if not isinstance(value, str):
            raise ContentItemParseError(f"X item field '{field}' must be a string.", field)
        try:
            return enum_type.from_value(value)
        except ValueError as exc:
            raise ContentItemParseError(str(exc), field) from exc

    @staticmethod
    def _parse_text_blocks(text_value: Any, content_type: XContentType) -> list[str]:
        if content_type == XContentType.THREAD:
            return XContentItem._parse_thread_blocks(text_value)
        return [XContentItem._parse_single_text(text_value)]

    @staticmethod
    def _parse_thread_blocks(text_value: Any) -> list[str]:
        if not isinstance(text_value, list) or not text_value:
            raise ContentItemParseError("Thread text must be a non-empty list.", "text")
        blocks: list[str] = []
        for entry in text_value:
            blocks.append(XContentItem._parse_single_text(entry))
        return blocks

    @staticmethod
    def _parse_single_text(text_value: Any) -> str:
        if not isinstance(text_value, str) or not text_value.strip():
            raise ContentItemParseError("Text must be a non-empty string.", "text")
        return text_value.strip()

    @staticmethod
    def _parse_compliance(value: Any) -> ComplianceFlags:
        try:
            return ComplianceFlags.from_dict(value)
        except ValueError as exc:
            raise ContentItemParseError(str(exc), "compliance") from exc

    @staticmethod
    def _parse_schedule(value: Any) -> Schedule:
        try:
            return Schedule.from_dict(value)
        except ValueError as exc:
            raise ContentItemParseError(str(exc), "schedule") from exc

    @staticmethod
    def _parse_hashtags(value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ContentItemParseError("Hashtags must be an array of strings.", "hashtags")
        return XContentItem._validate_hashtag_entries(value)

    @staticmethod
    def _validate_hashtag_entries(entries: Iterable[Any]) -> list[str]:
        hashtags: list[str] = []
        for entry in entries:
            if not isinstance(entry, str) or not entry.strip():
                raise ContentItemParseError("Hashtags must be non-empty strings.", "hashtags")
            hashtags.append(entry.strip())
        return hashtags
