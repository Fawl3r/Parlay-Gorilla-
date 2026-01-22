from __future__ import annotations

from ...models import VideoContentItem
from ...validation import ValidationIssue
from ..shared.certainty_phrase_catalog import CertaintyPhraseCatalog
from ..shared.phrase_matcher import PhraseMatcher
from .video_rule import VideoRule


class VideoOutcomeCertaintyRule(VideoRule):
    def __init__(self, catalog: CertaintyPhraseCatalog) -> None:
        self._matcher = PhraseMatcher(catalog.phrases(), catalog.regex_patterns())

    def evaluate(self, item: VideoContentItem) -> list[ValidationIssue]:
        matches = self._matcher.find_matches(item.script)
        if matches:
            return [
                ValidationIssue(
                    code="outcome_certainty",
                    message="Outcome certainty language is not allowed.",
                    field="script",
                )
            ]
        return []
