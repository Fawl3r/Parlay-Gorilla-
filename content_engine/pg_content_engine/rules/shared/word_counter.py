from __future__ import annotations

import re


class WordCounter:
    _WORD_PATTERN = re.compile(r"[A-Za-z0-9']+")

    def count_words(self, text: str) -> int:
        return len(self._WORD_PATTERN.findall(text))
