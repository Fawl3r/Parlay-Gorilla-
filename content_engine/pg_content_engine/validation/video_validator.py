from __future__ import annotations

from ..models import VideoContentItem
from ..rules.video.video_rule import VideoRule
from .validation_result import ValidationResult


class VideoValidator:
    def __init__(self, rules: list[VideoRule]) -> None:
        self._rules = rules

    def validate(self, item: VideoContentItem) -> ValidationResult:
        result = ValidationResult()
        for rule in self._rules:
            result.extend(rule.evaluate(item))
        return result
