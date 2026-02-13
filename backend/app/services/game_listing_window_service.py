"""
Listing window for games/analysis by sport state.

Clamps what games are shown so OFFSEASON does not show far-future schedules
(e.g. August NCAAF in February). Uses per-sport policy when provided.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.sport_state_policy import SportStatePolicy

# Align with cadence default policy (backward compatibility when no policy passed)
IN_SEASON_WINDOW_DAYS = 10
PRESEASON_WINDOW_DAYS = 60
RECENT_WINDOW_DAYS = 10


@dataclass(frozen=True)
class ListingWindow:
    """Time window [start_utc, end_utc] for listing games. None means show no games (OFFSEASON)."""

    start_utc: datetime
    end_utc: datetime

    @property
    def is_empty(self) -> bool:
        return self.start_utc > self.end_utc


def get_listing_window_for_sport_state(
    sport_state: str,
    now: Optional[datetime] = None,
    in_season_days: Optional[int] = None,
    preseason_days: Optional[int] = None,
    past_days: float = 1.0,
    policy: Optional["SportStatePolicy"] = None,
) -> Optional[ListingWindow]:
    """
    Return the listing window for the given sport state.

    - IN_SEASON / POSTSEASON: [now - past_days, now + listing_in_season_days]
    - IN_BREAK: [now - past_days, now + listing_preseason_days]
    - PRESEASON: [now - past_days, now + listing_preseason_days]
    - OFFSEASON: None

    When policy is provided, uses policy.listing_in_season_days and
    policy.listing_preseason_days. Otherwise uses in_season_days/preseason_days
    with module defaults (cadence 10/60).
    """
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(days=past_days)

    if policy is not None:
        in_season_days = in_season_days if in_season_days is not None else policy.listing_in_season_days
        preseason_days = preseason_days if preseason_days is not None else policy.listing_preseason_days
    if in_season_days is None:
        in_season_days = IN_SEASON_WINDOW_DAYS
    if preseason_days is None:
        preseason_days = PRESEASON_WINDOW_DAYS

    if sport_state in ("IN_SEASON", "POSTSEASON"):
        end = now + timedelta(days=in_season_days)
        return ListingWindow(start_utc=start, end_utc=end)
    if sport_state == "IN_BREAK":
        end = now + timedelta(days=preseason_days)
        return ListingWindow(start_utc=start, end_utc=end)
    if sport_state == "PRESEASON":
        end = now + timedelta(days=preseason_days)
        return ListingWindow(start_utc=start, end_utc=end)
    return None
