"""Sport configuration helpers for multi-sport support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class SportConfig:
    """Static configuration describing how to fetch and store a sport."""

    slug: str  # internal identifier (lowercase, e.g., "nfl")
    code: str  # stored in DB (e.g., "NFL")
    odds_key: str  # The Odds API sport key
    display_name: str
    default_markets: List[str]
    supported_markets: List[str]
    lookahead_days: int = 7
    past_hours: int = 2
    max_full_games: int = 30
    max_quick_games: int = 20


SPORT_CONFIGS: Dict[str, SportConfig] = {
    "nfl": SportConfig(
        slug="nfl",
        code="NFL",
        odds_key="americanfootball_nfl",
        display_name="NFL",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "spreads", "totals"],
        lookahead_days=7,
        past_hours=4,
        max_full_games=30,
        max_quick_games=20,
    ),
    "nba": SportConfig(
        slug="nba",
        code="NBA",
        odds_key="basketball_nba",
        display_name="NBA",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "spreads", "totals"],
        lookahead_days=5,
        past_hours=6,
        max_full_games=40,
        max_quick_games=25,
    ),
    "nhl": SportConfig(
        slug="nhl",
        code="NHL",
        odds_key="icehockey_nhl",
        display_name="NHL",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "spreads", "totals"],
        lookahead_days=5,
        past_hours=6,
        max_full_games=30,
        max_quick_games=20,
    ),
    "mlb": SportConfig(
        slug="mlb",
        code="MLB",
        odds_key="baseball_mlb",
        display_name="MLB",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "spreads", "totals"],
        lookahead_days=5,
        past_hours=6,
        max_full_games=30,
        max_quick_games=20,
    ),
    "soccer": SportConfig(
        slug="soccer",
        code="SOCCER",
        odds_key="soccer_epl",
        display_name="Soccer",
        default_markets=["h2h", "totals"],
        supported_markets=["h2h", "totals", "spreads"],
        lookahead_days=7,
        past_hours=8,
        max_full_games=40,
        max_quick_games=25,
    ),
    "ufc": SportConfig(
        slug="ufc",
        code="UFC",
        odds_key="mma_mixed_martial_arts",
        display_name="UFC",
        default_markets=["h2h"],
        supported_markets=["h2h"],
        lookahead_days=14,
        past_hours=24,
        max_full_games=15,
        max_quick_games=10,
    ),
    "boxing": SportConfig(
        slug="boxing",
        code="BOXING",
        odds_key="boxing_boxing",
        display_name="Boxing",
        default_markets=["h2h"],
        supported_markets=["h2h"],
        lookahead_days=21,
        past_hours=48,
        max_full_games=15,
        max_quick_games=10,
    ),
}


_SPORT_ALIAS_MAP: Dict[str, str] = {
    "nfl": "nfl",
    "americanfootball_nfl": "nfl",
    "football": "nfl",
    "nba": "nba",
    "basketball": "nba",
    "basketball_nba": "nba",
    "nhl": "nhl",
    "icehockey_nhl": "nhl",
    "hockey": "nhl",
    "mlb": "mlb",
    "baseball": "mlb",
    "baseball_mlb": "mlb",
    "soccer": "soccer",
    "soccer_epl": "soccer",
    "ufc": "ufc",
    "mma": "ufc",
    "mma_mixed_martial_arts": "ufc",
    "boxing": "boxing",
    "boxing_boxing": "boxing",
}

# Also map the uppercase codes for convenience
for _config in SPORT_CONFIGS.values():
    _SPORT_ALIAS_MAP[_config.code.lower()] = _config.slug


def get_sport_config(identifier: str) -> SportConfig:
    """Resolve any supported identifier (slug, code, Odds API key) to a SportConfig."""
    if not identifier:
        raise ValueError("Sport identifier is required")
    
    key = identifier.lower()
    slug = _SPORT_ALIAS_MAP.get(key, key)
    config = SPORT_CONFIGS.get(slug)
    if not config:
        raise ValueError(f"Unsupported sport: {identifier}")
    return config


def list_supported_sports() -> List[SportConfig]:
    """Return SportConfig objects for all supported sports."""
    return list(SPORT_CONFIGS.values())

