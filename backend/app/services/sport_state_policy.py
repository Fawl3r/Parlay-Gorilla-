"""
Per-sport state policies for cadence vs event-based leagues.

Cadence leagues (NFL, NBA, NHL, MLB, NCAAF, NCAAB, etc.) use tight windows.
Event-based sports (boxing, MMA) use larger windows so sparse schedules
don't incorrectly trigger offseason.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SportStateMode = Literal["cadence", "event_based"]


@dataclass(frozen=True)
class SportStatePolicy:
    """Policy controlling sport state windows and listing horizons."""

    mode: SportStateMode = "cadence"
    in_season_window_days: int = 10
    preseason_window_days: int = 60
    recent_window_days: int = 10
    preseason_enable_days: int = 14
    max_future_sanity_days: int = 330
    max_past_sanity_days: int = 365
    break_max_next_days: int = 60
    listing_in_season_days: int = 10
    listing_preseason_days: int = 60


# Event-based: sparse events, larger windows so we don't mark offseason too early
EVENT_BASED_POLICY = SportStatePolicy(
    mode="event_based",
    in_season_window_days=30,
    preseason_window_days=90,
    recent_window_days=30,
    preseason_enable_days=30,
    max_future_sanity_days=400,
    max_past_sanity_days=365,
    break_max_next_days=90,
    listing_in_season_days=30,
    listing_preseason_days=90,
)

# Cadence default (matches existing config defaults)
CADENCE_DEFAULT_POLICY = SportStatePolicy()


_EVENT_BASED_SPORT_CODES: frozenset[str] = frozenset({"BOXING", "UFC", "MMA"})


def get_policy_for_sport(sport_code: str) -> SportStatePolicy:
    """Return the policy for the given sport. Cadence by default; event_based for boxing/MMA."""
    if not sport_code:
        return CADENCE_DEFAULT_POLICY
    normalized = (sport_code or "").strip().upper()
    if normalized in _EVENT_BASED_SPORT_CODES:
        return EVENT_BASED_POLICY
    return CADENCE_DEFAULT_POLICY
