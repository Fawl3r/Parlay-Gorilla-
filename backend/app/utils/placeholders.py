"""Placeholder team name detection (AFC, NFC, TBD, Winner of, etc.)."""

import re
from typing import Optional

PLACEHOLDER_LITERALS = frozenset({"AFC", "NFC", "TBD", "TBA", "TBC", "TO BE DETERMINED", "TO BE ANNOUNCED"})
WINNER_LOSER_PATTERN = re.compile(r"(winner\s+of|loser\s+of)", re.IGNORECASE)


def is_placeholder_team(name: Optional[str]) -> bool:
    """
    Return True if the team name is a placeholder (AFC, NFC, TBD, TBA, or contains Winner of / Loser of).
    """
    if not name or not isinstance(name, str):
        return False
    stripped = name.strip().upper()
    if stripped in PLACEHOLDER_LITERALS:
        return True
    if "TBD" in stripped or "TBA" in stripped:
        return True
    if WINNER_LOSER_PATTERN.search(name):
        return True
    return False
