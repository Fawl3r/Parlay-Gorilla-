"""
Infer season phase (preseason / regular / postseason) from provider text.

Used by Odds API data store and APISports adapter. Never infer from date alone;
only when provider supplies explicit flag or stage/round/description text.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

# Case-insensitive keywords that indicate postseason (playoffs)
_POSTSEASON_KEYWORDS = (
    "playoff",
    "playoffs",
    "postseason",
    "wild card",
    "wildcard",
    "quarterfinal",
    "semifinal",
    "semi-final",
    "final",
    "finals",
    "conference finals",
    "championship",
    "bowl",
    "super bowl",
    "stanley cup",
    "world series",
)

_PRESEASON_KEYWORDS = ("preseason", "pre-season", "exhibition")


def infer_season_phase_from_text(text: Optional[str]) -> Optional[str]:
    """
    Infer season_phase from provider text. Returns "postseason", "preseason", "regular", or None.

    Only returns postseason if one of _POSTSEASON_KEYWORDS appears (substring, case-insensitive).
    Only returns preseason if one of _PRESEASON_KEYWORDS appears.
    Returns "regular" when we have text that clearly is not postseason/preseason; else None.
    """
    if not text or not isinstance(text, str):
        return None
    lower = text.strip().lower()
    if not lower:
        return None
    for kw in _POSTSEASON_KEYWORDS:
        if kw in lower:
            return "postseason"
    for kw in _PRESEASON_KEYWORDS:
        if kw in lower:
            return "preseason"
    # If text looks like a round label (e.g. "Regular Season - 12") we could return "regular"
    if "regular" in lower and "season" in lower:
        return "regular"
    return None


def extract_stage_and_round(
    stage_text: Optional[str],
    round_text: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """Return (stage, round) for DB. Normalize empty to None."""
    stage = (stage_text or "").strip() or None
    round_val = (round_text or "").strip() or None
    return (stage, round_val)
