from __future__ import annotations

from ...models import XContentItem
from ...validation import ValidationIssue
from ..shared.certainty_phrase_catalog import CertaintyPhraseCatalog
from ..shared.phrase_matcher import PhraseMatcher
from .x_rule import XRule


class XOutcomeCertaintyRule(XRule):
    def __init__(self, catalog: CertaintyPhraseCatalog) -> None:
        self._matcher = PhraseMatcher(catalog.phrases(), catalog.regex_patterns())

    def evaluate(self, item: XContentItem) -> list[ValidationIssue]:
        for block in item.text_blocks:
            matches = self._matcher.find_matches(block)
            if matches:
                return [
                    ValidationIssue(
                        code="outcome_certainty",
                        message="Outcome certainty language is not allowed.",
                        field="text",
                    )
                ]
        return []
