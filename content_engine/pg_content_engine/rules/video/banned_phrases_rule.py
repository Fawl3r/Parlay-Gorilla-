from __future__ import annotations

from ...models import VideoContentItem
from ...validation import ValidationIssue
from ..shared.banned_phrase_catalog import BannedPhraseCatalog
from ..shared.phrase_matcher import PhraseMatcher
from .video_rule import VideoRule


class VideoBannedPhrasesRule(VideoRule):
    def __init__(self, catalog: BannedPhraseCatalog) -> None:
        self._matcher = PhraseMatcher(catalog.phrases())

    def evaluate(self, item: VideoContentItem) -> list[ValidationIssue]:
        matches = self._matcher.find_matches(item.script)
        if matches:
            return [
                ValidationIssue(
                    code="banned_phrases",
                    message=f"Banned phrase found: {matches[0]}",
                    field="script",
                )
            ]
        return []
