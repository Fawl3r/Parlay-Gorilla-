"""
Per-sport API-Sports enrichment capabilities (single map, no one-off branching).

Defines which enrichment pieces are supported per sport and key stats profile for display.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# Sport slugs we support for enrichment (must have league ID in config)
SUPPORTED_ENRICHMENT_SLUGS = ("nfl", "nba", "wnba", "nhl", "mlb", "epl", "mls", "laliga", "ucl")

# Key stats profile: ordered list of (key, label) for key_team_stats table (sport-aware human labels)
BASKETBALL_KEY_STATS: List[Tuple[str, str]] = [
    ("points_for", "PPG"), ("points_against", "PAPG"), ("fg_pct", "FG%"), ("three_pct", "3P%"),
    ("ft_pct", "FT%"), ("rebounds", "REB"), ("assists", "AST"), ("turnovers", "TO"),
]
FOOTBALL_KEY_STATS: List[Tuple[str, str]] = [
    ("points_for", "PPG"), ("points_against", "PAPG"), ("total_yards", "Yds/G"),
    ("pass_yards", "Pass Yds/G"), ("rush_yards", "Rush Yds/G"), ("turnovers", "TO"),
]
HOCKEY_KEY_STATS: List[Tuple[str, str]] = [
    ("goals_for", "GF/G"), ("goals_against", "GA/G"), ("shots_for", "SF/G"), ("shots_against", "SA/G"),
    ("power_play_pct", "PP%"), ("penalty_kill_pct", "PK%"), ("save_pct", "Sv%"),
]
BASEBALL_KEY_STATS: List[Tuple[str, str]] = [
    ("runs_for", "R/G"), ("runs_against", "RA/G"), ("era", "ERA"), ("avg", "AVG"),
]
SOCCER_KEY_STATS: List[Tuple[str, str]] = [
    ("goals_for", "GF/G"), ("goals_against", "GA/G"), ("possession", "Poss%"), ("shots_on_target", "SoT/G"),
]


@dataclass(frozen=True)
class SportEnrichmentCapability:
    """What enrichment data we can fetch for this sport."""
    standings: bool = True
    team_stats: bool = True
    form: bool = True
    injuries: bool = True
    standings_key: str = "standings"
    games_key: str = "games"
    injuries_key: str = "injuries"
    key_stats_profile: List[Tuple[str, str]] = field(default_factory=list)


# Default: all capabilities on; can disable per sport if API doesn't support
DEFAULT_CAPABILITY = SportEnrichmentCapability(
    standings=True,
    team_stats=True,
    form=True,
    injuries=True,
    key_stats_profile=[],
)

# Sports where we know injuries or team_stats may be limited
CAPABILITIES: Dict[str, SportEnrichmentCapability] = {
    "nfl": SportEnrichmentCapability(
        standings=True, team_stats=True, form=True, injuries=True,
        key_stats_profile=FOOTBALL_KEY_STATS,
    ),
    "nba": SportEnrichmentCapability(
        standings=True, team_stats=True, form=True, injuries=True,
        key_stats_profile=BASKETBALL_KEY_STATS,
    ),
    "wnba": SportEnrichmentCapability(
        standings=True,
        team_stats=True,
        form=True,
        injuries=True,
        key_stats_profile=BASKETBALL_KEY_STATS,
    ),
    "nhl": SportEnrichmentCapability(
        standings=True, team_stats=True, form=True, injuries=True,
        key_stats_profile=HOCKEY_KEY_STATS,
    ),
    "mlb": SportEnrichmentCapability(
        standings=True, team_stats=True, form=True, injuries=True,
        key_stats_profile=BASEBALL_KEY_STATS,
    ),
    "epl": SportEnrichmentCapability(
        standings=True, team_stats=True, form=True, injuries=True,
        key_stats_profile=SOCCER_KEY_STATS,
    ),
    "mls": SportEnrichmentCapability(
        standings=True, team_stats=True, form=True, injuries=True,
        key_stats_profile=SOCCER_KEY_STATS,
    ),
    "laliga": SportEnrichmentCapability(
        standings=True, team_stats=True, form=True, injuries=True,
        key_stats_profile=SOCCER_KEY_STATS,
    ),
    "ucl": SportEnrichmentCapability(
        standings=True, team_stats=True, form=True, injuries=True,
        key_stats_profile=SOCCER_KEY_STATS,
    ),
}


def get_capability(sport_slug: str) -> SportEnrichmentCapability:
    """Return capability for sport; default to all-off if unknown."""
    slug = (sport_slug or "").lower().strip()
    return CAPABILITIES.get(slug) or SportEnrichmentCapability(
        standings=False,
        team_stats=False,
        form=False,
        injuries=False,
    )


def supports_standings(sport_slug: str) -> bool:
    return get_capability(sport_slug).standings


def supports_team_stats(sport_slug: str) -> bool:
    return get_capability(sport_slug).team_stats


def supports_form(sport_slug: str) -> bool:
    return get_capability(sport_slug).form


def supports_injuries(sport_slug: str) -> bool:
    return get_capability(sport_slug).injuries
