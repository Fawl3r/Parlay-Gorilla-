from __future__ import annotations

import re


class HashtagExtractor:
    _HASHTAG_PATTERN = re.compile(r"#\w+")

    def extract(self, text: str) -> list[str]:
        return self._HASHTAG_PATTERN.findall(text)
