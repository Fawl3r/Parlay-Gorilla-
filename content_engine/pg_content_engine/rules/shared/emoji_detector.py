from __future__ import annotations

import re


class EmojiDetector:
    _EMOJI_PATTERN = re.compile(
        "["  # based on common emoji unicode blocks
        "\U0001F300-\U0001F5FF"
        "\U0001F600-\U0001F64F"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "\U00002600-\U000026FF"
        "\U00002700-\U000027BF"
        "]",
        flags=re.UNICODE,
    )

    def contains_emoji(self, text: str) -> bool:
        return bool(self._EMOJI_PATTERN.search(text))
