from __future__ import annotations

from ...models import XContentItem
from ...validation import ValidationIssue
from ..shared.hype_phrase_catalog import HypePhraseCatalog
from ..shared.phrase_matcher import PhraseMatcher
from .x_rule import XRule


class XNoHypeRule(XRule):
    def __init__(self, catalog: HypePhraseCatalog, max_exclamations: int = 1) -> None:
        self._matcher = PhraseMatcher(catalog.phrases())
        self._max_exclamations = max_exclamations

    def evaluate(self, item: XContentItem) -> list[ValidationIssue]:
        for block in item.text_blocks:
            matches = self._matcher.find_matches(block)
            if matches:
                return [
                    ValidationIssue(
                        code="no_hype",
                        message="Hype language is not allowed.",
                        field="text",
                    )
                ]
            if block.count("!") > self._max_exclamations:
                return [
                    ValidationIssue(
                        code="no_hype",
                        message="Excessive exclamation is not allowed.",
                        field="text",
                    )
                ]
        return []
