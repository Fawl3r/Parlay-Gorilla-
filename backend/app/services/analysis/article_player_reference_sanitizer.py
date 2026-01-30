"""Deterministic sanitizer for player-name references in full-article text.

Removes or generalizes common patterns where the model may have mentioned
specific player names (e.g. "led by Geno Smith") so that legacy or
hallucinated content does not show incorrect player/team associations.
Preserves markdown headings (## / ###) used by the frontend parser.
"""

from __future__ import annotations

import re


# Pattern: "led by <Name>" where Name is 2+ title-case words (e.g. "Geno Smith")
_LED_BY_NAME = re.compile(
    r"\bled by ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b",
    re.IGNORECASE,
)
_REPLACEMENT_LED_BY = "led by its core playmakers"

# Pattern: "quarterback <Name>" or "QB <Name>" (optional comma/dash before name)
_QB_NAME = re.compile(
    r"\b(quarterback|QB)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b",
    re.IGNORECASE,
)
_REPLACEMENT_QB = r"\1"

# Pattern: "running back <Name>", "RB <Name>", "wide receiver <Name>", "WR <Name>"
_RB_WR_NAME = re.compile(
    r"\b(running back|RB|wide receiver|WR|tight end|TE)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b",
    re.IGNORECASE,
)
_REPLACEMENT_RB_WR = r"\1"

# Pattern: "star <Name>", "leading scorer <Name>", "go-to <Name>"
_STAR_NAME = re.compile(
    r"\b(star|leading scorer|go-to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b",
    re.IGNORECASE,
)
_REPLACEMENT_STAR = r"\1"

# Pattern: "<Name> will" at start of sentence or after role (conservative: 2–3 title-case words)
_NAME_WILL = re.compile(
    r"\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+will\b",
)
# We replace "Name will" with "The unit will" to keep the sentence structure
_REPLACEMENT_NAME_WILL = "The unit will"


class ArticlePlayerReferenceSanitizer:
    """
    Transform full-article text to remove or generalize player-name references.

    Single responsibility: apply a fixed set of regex substitutions so that
    phrases like "led by Geno Smith" or "quarterback Patrick Mahomes" become
    generic. Does not touch markdown headings (## / ###).
    """

    def sanitize(self, text: str) -> str:
        if not text or not isinstance(text, str):
            return str(text or "")

        cleaned = text

        # "led by <Name>" -> "led by its core playmakers"
        cleaned = _LED_BY_NAME.sub(_REPLACEMENT_LED_BY, cleaned)

        # "quarterback <Name>" / "QB <Name>" -> "quarterback" / "QB"
        cleaned = _QB_NAME.sub(_REPLACEMENT_QB, cleaned)

        # "RB <Name>", "WR <Name>", etc. -> "RB", "WR"
        cleaned = _RB_WR_NAME.sub(_REPLACEMENT_RB_WR, cleaned)

        # "star <Name>", "leading scorer <Name>" -> "star", "leading scorer"
        cleaned = _STAR_NAME.sub(_REPLACEMENT_STAR, cleaned)

        # "<Name> will" -> "The unit will" (conservative: only 2–3 word names)
        cleaned = _NAME_WILL.sub(_REPLACEMENT_NAME_WILL, cleaned)

        return cleaned
