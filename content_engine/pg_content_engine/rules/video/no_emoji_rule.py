from __future__ import annotations

from ...models import VideoContentItem
from ...validation import ValidationIssue
from ..shared.emoji_detector import EmojiDetector
from .video_rule import VideoRule


class VideoNoEmojiRule(VideoRule):
    def __init__(self, detector: EmojiDetector) -> None:
        self._detector = detector

    def evaluate(self, item: VideoContentItem) -> list[ValidationIssue]:
        if self._detector.contains_emoji(item.script):
            return [ValidationIssue(code="no_emojis", message="Emojis are not allowed.", field="script")]
        return []
