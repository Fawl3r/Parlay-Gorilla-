from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .compliance_flags import ComplianceFlags
from .content_status import ContentStatus
from .parse_error import ContentItemParseError
from .schedule import Schedule
from .video_content_type import VideoContentType
from .video_format_tag import VideoFormatTag


@dataclass(frozen=True)
class VideoContentItem:
    content_id: str
    content_type: VideoContentType
    topic: str
    script: str
    format_tag: VideoFormatTag
    compliance: ComplianceFlags
    schedule: Schedule
    status: ContentStatus

    @classmethod
    def from_dict(cls, data: Any) -> "VideoContentItem":
        if not isinstance(data, dict):
            raise ContentItemParseError("Video item must be an object.")
        content_id = cls._get_required_str(data, "id")
        topic = cls._get_required_str(data, "topic")
        content_type = cls._parse_enum(VideoContentType, data.get("type"), "type")
        format_tag = cls._parse_enum(VideoFormatTag, data.get("format_tag"), "format_tag")
        status = cls._parse_enum(ContentStatus, data.get("status"), "status")
        script = cls._parse_script(data.get("script"))
        compliance = cls._parse_compliance(data.get("compliance"))
        schedule = cls._parse_schedule(data.get("schedule"))
        return cls(
            content_id=content_id,
            content_type=content_type,
            topic=topic,
            script=script,
            format_tag=format_tag,
            compliance=compliance,
            schedule=schedule,
            status=status,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.content_id,
            "type": self.content_type.value,
            "topic": self.topic,
            "script": self.script,
            "format_tag": self.format_tag.value,
            "compliance": self.compliance.to_dict(),
            "schedule": self.schedule.to_dict(),
            "status": self.status.value,
        }

    @staticmethod
    def _get_required_str(data: dict[str, Any], field: str) -> str:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ContentItemParseError(f"Video item field '{field}' must be a string.", field)
        return value.strip()

    @staticmethod
    def _parse_enum(enum_type: type, value: Any, field: str) -> Any:
        if not isinstance(value, str):
            raise ContentItemParseError(f"Video item field '{field}' must be a string.", field)
        try:
            return enum_type.from_value(value)
        except ValueError as exc:
            raise ContentItemParseError(str(exc), field) from exc

    @staticmethod
    def _parse_script(script: Any) -> str:
        if not isinstance(script, str) or not script.strip():
            raise ContentItemParseError("Script must be a non-empty string.", "script")
        return script.strip()

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
