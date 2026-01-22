from __future__ import annotations

from ...models import XContentItem
from ...validation import ValidationIssue
from ..shared.uppercase_token_detector import UppercaseTokenDetector
from .x_rule import XRule


class XAllCapsRule(XRule):
    def __init__(self, detector: UppercaseTokenDetector) -> None:
        self._detector = detector

    def evaluate(self, item: XContentItem) -> list[ValidationIssue]:
        for block in item.text_blocks:
            tokens = self._detector.find_uppercase_tokens(block)
            if tokens:
                return [
                    ValidationIssue(
                        code="no_all_caps",
                        message="ALL CAPS emphasis is not allowed.",
                        field="text",
                    )
                ]
        return []
