"""
Fallback return dates for offseason sports when the DB has no next game.

Used so the UI can show "Returns 8/29/2026" etc. when the odds/DB don't yet
have next season's games. Dates are approximate (typical season openers).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

# (month, day) of typical season opener — we return next occurrence on or after now
_OFFSEASON_OPENER: dict[str, tuple[int, int]] = {
    "NFL": (9, 5),       # ~ first Thursday Sept
    "NCAAF": (8, 29),    # last Saturday Aug / Labor Day weekend
    "NCAAB": (11, 4),    # early November
    "NBA": (10, 18),     # mid October
    "NHL": (10, 4),      # early October
    "MLB": (3, 28),      # late March
    "WNBA": (5, 14),     # mid May
    "MLS": (2, 22),      # late February
    "EPL": (8, 16),      # mid August
    "LALIGA": (8, 16),   # mid August
}


def get_offseason_fallback_return_date(
    sport_code: str,
    now: Optional[datetime] = None,
) -> Optional[datetime]:
    """
    Return an approximate next-season start date for the sport when in offseason.

    Used only when DB has no next game (next_game_at is None). Returns None
    for sports without a configured opener (e.g. UFC, Boxing).
    """
    if not sport_code:
        return None
    key = (sport_code or "").strip().upper()
    opener = _OFFSEASON_OPENER.get(key)
    if not opener:
        return None
    month, day = opener
    now = now or datetime.now(timezone.utc)
    # Ensure we have tz-aware for comparison
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    year = now.year
    try:
        candidate = datetime(year, month, day, 12, 0, 0, tzinfo=timezone.utc)
    except ValueError:
        return None
    if candidate < now:
        try:
            candidate = datetime(year + 1, month, day, 12, 0, 0, tzinfo=timezone.utc)
        except ValueError:
            return None
    return candidate
