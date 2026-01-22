from __future__ import annotations

import math

from ...models import VideoContentItem
from ...validation import ValidationIssue
from ..shared.word_counter import WordCounter
from .video_rule import VideoRule


class VideoDurationRule(VideoRule):
    def __init__(
        self,
        counter: WordCounter,
        min_seconds: int = 15,
        max_seconds: int = 30,
        words_per_minute: int = 150,
    ) -> None:
        self._counter = counter
        self._min_seconds = min_seconds
        self._max_seconds = max_seconds
        self._words_per_minute = words_per_minute

    def evaluate(self, item: VideoContentItem) -> list[ValidationIssue]:
        word_count = self._counter.count_words(item.script)
        min_words = math.ceil(self._min_seconds * self._words_per_minute / 60)
        max_words = math.floor(self._max_seconds * self._words_per_minute / 60)
        if word_count < min_words or word_count > max_words:
            return [
                ValidationIssue(
                    code="duration_range",
                    message=(
                        f"Script word count {word_count} is outside the allowed range "
                        f"({min_words}-{max_words} words)."
                    ),
                    field="script",
                )
            ]
        return []
