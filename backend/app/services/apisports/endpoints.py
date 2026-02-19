"""
Single source of truth for API-Sports team stats endpoints per sport family.

Client methods call get_team_stats_endpoint(sport_slug) for path and params;
base URL is resolved via base_url_resolver using the returned sport key.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class TeamStatsEndpoint:
    """Team season stats endpoint: path and required query param names."""
    path: str
    required_params: List[str]
    sport_key: str  # passed to base_url_resolver for host


# Sport slug -> endpoint config. Soccer uses different path.
_TEAM_STATS_ENDPOINTS: dict[str, TeamStatsEndpoint] = {
    "nba": TeamStatsEndpoint(path="/statistics", required_params=["league", "season", "team"], sport_key="nba"),
    "wnba": TeamStatsEndpoint(path="/statistics", required_params=["league", "season", "team"], sport_key="wnba"),
    "nfl": TeamStatsEndpoint(path="/statistics", required_params=["league", "season", "team"], sport_key="nfl"),
    "nhl": TeamStatsEndpoint(path="/statistics", required_params=["league", "season", "team"], sport_key="nhl"),
    "mlb": TeamStatsEndpoint(path="/statistics", required_params=["league", "season", "team"], sport_key="mlb"),
    "epl": TeamStatsEndpoint(path="/teams/statistics", required_params=["league", "season", "team"], sport_key="football"),
    "mls": TeamStatsEndpoint(path="/teams/statistics", required_params=["league", "season", "team"], sport_key="football"),
    "laliga": TeamStatsEndpoint(path="/teams/statistics", required_params=["league", "season", "team"], sport_key="football"),
    "ucl": TeamStatsEndpoint(path="/teams/statistics", required_params=["league", "season", "team"], sport_key="football"),
}


def get_team_stats_endpoint(sport_slug: str) -> Optional[TeamStatsEndpoint]:
    """
    Return team stats endpoint config for the given sport slug, or None if unsupported.

    Returns:
        TeamStatsEndpoint with path, required_params, sport_key for base URL resolution.
    """
    slug = (sport_slug or "").lower().strip()
    return _TEAM_STATS_ENDPOINTS.get(slug)
