"""
API-Sports per-sport base URL resolver.

Resolves sport key to the correct API-Sports host. Soccer uses the default
(apisports_base_url); NFL/NBA/NHL/MLB use their v1 hosts unless overridden.
"""

from __future__ import annotations

from typing import Optional

from app.core.config import settings
from app.services.apisports.team_mapper import (
    SPORT_KEY_FOOTBALL,
    SPORT_KEY_NBA,
    SPORT_KEY_NFL,
    SPORT_KEY_NHL,
    SPORT_KEY_MLB,
)

# Default API-Sports hosts per sport (plan defaults)
DEFAULT_BASE_URL_FOOTBALL = "https://v3.football.api-sports.io"
DEFAULT_BASE_URL_NFL = "https://v1.american-football.api-sports.io"
DEFAULT_BASE_URL_NBA = "https://v1.basketball.api-sports.io"
DEFAULT_BASE_URL_NHL = "https://v1.hockey.api-sports.io"
DEFAULT_BASE_URL_MLB = "https://v1.baseball.api-sports.io"


def get_base_url_for_sport(sport: str) -> str:
    """
    Return API-Sports base URL for the given sport key.

    Args:
        sport: Sport key (e.g. football, americanfootball_nfl, basketball_nba).

    Returns:
        Base URL without trailing slash.
    """
    sport_lower = (sport or "").lower().strip()
    base = getattr(settings, "apisports_base_url", DEFAULT_BASE_URL_FOOTBALL) or DEFAULT_BASE_URL_FOOTBALL

    if sport_lower in (SPORT_KEY_FOOTBALL, "soccer", "football_soccer", "epl", "mls", "laliga"):
        return (base or DEFAULT_BASE_URL_FOOTBALL).rstrip("/")
    if sport_lower in (SPORT_KEY_NFL, "nfl", "americanfootball_nfl", "americanfootball"):
        override = getattr(settings, "apisports_base_url_nfl", None)
        return (override or DEFAULT_BASE_URL_NFL).rstrip("/")
    if sport_lower in (SPORT_KEY_NBA, "nba", "basketball_nba", "basketball"):
        override = getattr(settings, "apisports_base_url_nba", None)
        return (override or DEFAULT_BASE_URL_NBA).rstrip("/")
    if sport_lower in (SPORT_KEY_NHL, "nhl", "icehockey_nhl", "icehockey", "hockey"):
        override = getattr(settings, "apisports_base_url_nhl", None)
        return (override or DEFAULT_BASE_URL_NHL).rstrip("/")
    if sport_lower in (SPORT_KEY_MLB, "mlb", "baseball_mlb", "baseball"):
        override = getattr(settings, "apisports_base_url_mlb", None)
        return (override or DEFAULT_BASE_URL_MLB).rstrip("/")

    # Default to soccer/football base
    return (base or DEFAULT_BASE_URL_FOOTBALL).rstrip("/")
