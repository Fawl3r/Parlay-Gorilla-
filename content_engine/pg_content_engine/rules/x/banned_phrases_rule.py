from __future__ import annotations

from ...models import XContentItem
from ...validation import ValidationIssue
from ..shared.banned_phrase_catalog import BannedPhraseCatalog
from ..shared.phrase_matcher import PhraseMatcher
from .x_rule import XRule


class XBannedPhrasesRule(XRule):
    def __init__(self, catalog: BannedPhraseCatalog) -> None:
        self._matcher = PhraseMatcher(catalog.phrases())

    def evaluate(self, item: XContentItem) -> list[ValidationIssue]:
        for block in item.text_blocks:
            matches = self._matcher.find_matches(block)
            if matches:
                return [
                    ValidationIssue(
                        code="banned_phrases",
                        message=f"Banned phrase found: {matches[0]}",
                        field="text",
                    )
                ]
        return []
