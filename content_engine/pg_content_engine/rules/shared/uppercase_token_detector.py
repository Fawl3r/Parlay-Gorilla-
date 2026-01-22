from __future__ import annotations

import re


class UppercaseTokenDetector:
    _TOKEN_PATTERN = re.compile(r"\b[A-Z]{3,}\b")

    def find_uppercase_tokens(self, text: str) -> list[str]:
        return self._TOKEN_PATTERN.findall(text)
