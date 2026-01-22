from __future__ import annotations

from ...models import XContentItem
from ...validation import ValidationIssue
from ..shared.hashtag_extractor import HashtagExtractor
from .x_rule import XRule


class XHashtagRule(XRule):
    def __init__(self, extractor: HashtagExtractor, max_hashtags: int = 2) -> None:
        self._extractor = extractor
        self._max_hashtags = max_hashtags

    def evaluate(self, item: XContentItem) -> list[ValidationIssue]:
        normalized_list = self._normalize_hashtags(item.hashtags)
        if len(normalized_list) > self._max_hashtags:
            return [
                ValidationIssue(
                    code="hashtags_limit",
                    message="Hashtags array exceeds the allowed limit.",
                    field="hashtags",
                )
            ]
        inline_hashtags = self._extract_inline_hashtags(item.text_blocks)
        if inline_hashtags != normalized_list:
            return [
                ValidationIssue(
                    code="hashtags_mismatch",
                    message="Hashtags list must match hashtags in the text.",
                    field="hashtags",
                )
            ]
        return []

    def _extract_inline_hashtags(self, blocks: list[str]) -> list[str]:
        inline: list[str] = []
        for block in blocks:
            inline.extend(self._extractor.extract(block))
        return self._normalize_hashtags(inline)

    @staticmethod
    def _normalize_hashtags(values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            tag = value.strip()
            if not tag:
                continue
            if not tag.startswith("#"):
                tag = f"#{tag}"
            normalized.append(tag.lower())
        return sorted(set(normalized))
