from __future__ import annotations

from ...models import VideoContentItem
from ...validation import ValidationIssue
from ..shared.hype_phrase_catalog import HypePhraseCatalog
from ..shared.phrase_matcher import PhraseMatcher
from .video_rule import VideoRule


class VideoNoHypeRule(VideoRule):
    def __init__(self, catalog: HypePhraseCatalog, max_exclamations: int = 1) -> None:
        self._matcher = PhraseMatcher(catalog.phrases())
        self._max_exclamations = max_exclamations

    def evaluate(self, item: VideoContentItem) -> list[ValidationIssue]:
        matches = self._matcher.find_matches(item.script)
        if matches:
            return [
                ValidationIssue(
                    code="no_hype",
                    message="Hype language is not allowed.",
                    field="script",
                )
            ]
        if item.script.count("!") > self._max_exclamations:
            return [
                ValidationIssue(
                    code="no_hype",
                    message="Excessive exclamation is not allowed.",
                    field="script",
                )
            ]
        return []
