from __future__ import annotations

import re
from typing import Optional


class OddsConverter:
    """Best-effort odds conversion helpers (American <-> decimal)."""

    @staticmethod
    def american_to_decimal(american_odds: str) -> float:
        """
        Convert American odds to decimal odds.

        Accepts strings like "+150", "-110", "150", "-145".
        """
        value = OddsConverter._parse_american(american_odds)
        if value is None or value == 0:
            # Fallback to -110 (~1.909)
            return 1.909
        if value > 0:
            return (value / 100.0) + 1.0
        return (100.0 / abs(value)) + 1.0

    @staticmethod
    def decimal_to_american(decimal_odds: float) -> str:
        """Convert decimal odds to American odds (rounded to nearest int)."""
        try:
            dec = float(decimal_odds)
        except Exception:
            return "+100"
        if dec <= 1.0:
            return "+100"
        if dec >= 2.0:
            american = int(round((dec - 1.0) * 100.0))
            return f"+{american}"
        american = int(round(-100.0 / (dec - 1.0)))
        return str(american)

    @staticmethod
    def implied_prob_from_decimal(decimal_odds: float) -> float:
        try:
            dec = float(decimal_odds)
        except Exception:
            return 0.5
        if dec <= 0:
            return 0.5
        return 1.0 / dec

    @staticmethod
    def extract_point(outcome: str) -> Optional[float]:
        """Extract the first signed float from an outcome string (e.g., '+3.5', '44.5')."""
        if not outcome:
            return None
        match = re.search(r"[+-]?\d+(?:\.\d+)?", str(outcome))
        if not match:
            return None
        try:
            return float(match.group(0))
        except Exception:
            return None

    @staticmethod
    def _parse_american(american_odds: str) -> Optional[int]:
        if american_odds is None:
            return None
        s = str(american_odds).strip()
        if not s:
            return None
        s = s.replace("−", "-")  # handle unicode minus
        s = s.replace("+", "")
        try:
            return int(float(s))
        except Exception:
            return None




