from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PhrasePattern:
    label: str
    pattern: re.Pattern[str]


class PhraseMatcher:
    def __init__(self, phrases: Iterable[str], regex_patterns: Iterable[str] | None = None) -> None:
        self._patterns = self._build_patterns(list(phrases), list(regex_patterns or []))

    def find_matches(self, text: str) -> list[str]:
        matches: list[str] = []
        for phrase_pattern in self._patterns:
            if phrase_pattern.pattern.search(text):
                matches.append(phrase_pattern.label)
        return matches

    def _build_patterns(self, phrases: list[str], regex_patterns: list[str]) -> list[PhrasePattern]:
        patterns: list[PhrasePattern] = []
        for phrase in phrases:
            patterns.append(PhrasePattern(label=phrase, pattern=self._compile_phrase(phrase)))
        for regex_pattern in regex_patterns:
            patterns.append(
                PhrasePattern(
                    label=regex_pattern,
                    pattern=re.compile(regex_pattern, flags=re.IGNORECASE),
                )
            )
        return patterns

    @staticmethod
    def _compile_phrase(phrase: str) -> re.Pattern[str]:
        escaped = re.escape(phrase)
        return re.compile(rf"\b{escaped}\b", flags=re.IGNORECASE)
