from __future__ import annotations

from ...models import XContentItem
from ...validation import ValidationIssue
from .x_rule import XRule


class XLengthRule(XRule):
    def __init__(self, max_length: int = 280) -> None:
        self._max_length = max_length

    def evaluate(self, item: XContentItem) -> list[ValidationIssue]:
        for index, block in enumerate(item.text_blocks, start=1):
            if len(block) > self._max_length:
                return [
                    ValidationIssue(
                        code="length_limit",
                        message=f"Text block {index} exceeds {self._max_length} characters.",
                        field="text",
                    )
                ]
        return []
