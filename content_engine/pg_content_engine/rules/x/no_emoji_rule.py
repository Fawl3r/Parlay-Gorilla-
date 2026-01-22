from __future__ import annotations

from ...models import XContentItem
from ...validation import ValidationIssue
from ..shared.emoji_detector import EmojiDetector
from .x_rule import XRule


class XNoEmojiRule(XRule):
    def __init__(self, detector: EmojiDetector) -> None:
        self._detector = detector

    def evaluate(self, item: XContentItem) -> list[ValidationIssue]:
        for block in item.text_blocks:
            if self._detector.contains_emoji(block):
                return [ValidationIssue(code="no_emojis", message="Emojis are not allowed.", field="text")]
        return []
