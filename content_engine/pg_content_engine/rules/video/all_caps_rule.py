from __future__ import annotations

from ...models import VideoContentItem
from ...validation import ValidationIssue
from ..shared.uppercase_token_detector import UppercaseTokenDetector
from .video_rule import VideoRule


class VideoAllCapsRule(VideoRule):
    def __init__(self, detector: UppercaseTokenDetector) -> None:
        self._detector = detector

    def evaluate(self, item: VideoContentItem) -> list[ValidationIssue]:
        tokens = self._detector.find_uppercase_tokens(item.script)
        if tokens:
            return [
                ValidationIssue(
                    code="no_all_caps",
                    message="ALL CAPS emphasis is not allowed.",
                    field="script",
                )
            ]
        return []
