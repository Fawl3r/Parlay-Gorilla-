"""Sport configuration helpers for multi-sport support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class SportConfig:
    """Static configuration describing how to fetch and store a sport."""

    slug: str  # internal identifier (lowercase, e.g., "nfl")
    code: str  # stored in DB (e.g., "NFL")
    odds_key: str  # The Odds API sport key
    display_name: str
    default_markets: List[str]
    supported_markets: List[str]
    premium_markets: List[str] = field(default_factory=list)  # Premium-only markets (e.g., player_props)
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
        supported_markets=["h2h", "spreads", "totals", "player_props"],
        premium_markets=["player_props"],
        lookahead_days=14,
        past_hours=4,
        max_full_games=50,
        max_quick_games=30,
    ),
    "nba": SportConfig(
        slug="nba",
        code="NBA",
        odds_key="basketball_nba",
        display_name="NBA",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "spreads", "totals", "player_props"],
        premium_markets=["player_props"],
        lookahead_days=10,
        past_hours=6,
        max_full_games=100,
        max_quick_games=50,
    ),
    "wnba": SportConfig(
        slug="wnba",
        code="WNBA",
        odds_key="basketball_wnba",
        display_name="WNBA",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "spreads", "totals"],
        lookahead_days=10,
        past_hours=6,
        max_full_games=50,
        max_quick_games=30,
    ),
    "nhl": SportConfig(
        slug="nhl",
        code="NHL",
        odds_key="icehockey_nhl",
        display_name="NHL",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "spreads", "totals", "player_props"],
        premium_markets=["player_props"],
        lookahead_days=10,
        past_hours=6,
        max_full_games=100,
        max_quick_games=50,
    ),
    "mlb": SportConfig(
        slug="mlb",
        code="MLB",
        odds_key="baseball_mlb",
        display_name="MLB",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "spreads", "totals", "player_props"],
        premium_markets=["player_props"],
        lookahead_days=5,
        past_hours=6,
        max_full_games=30,
        max_quick_games=20,
    ),
    # College Football
    "ncaaf": SportConfig(
        slug="ncaaf",
        code="NCAAF",
        odds_key="americanfootball_ncaaf",
        display_name="College Football",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "spreads", "totals"],
        lookahead_days=7,
        past_hours=6,
        # Bowl season + regular season slates can exceed 50 games.
        max_full_games=300,
        max_quick_games=150,
    ),
    # College Basketball
    "ncaab": SportConfig(
        slug="ncaab",
        code="NCAAB",
        odds_key="basketball_ncaab",
        display_name="College Basketball",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "spreads", "totals"],
        lookahead_days=5,
        past_hours=6,
        # College hoops can have very large daily slates.
        max_full_games=400,
        max_quick_games=200,
    ),
    # Soccer - MLS (Major League Soccer)
    "mls": SportConfig(
        slug="mls",
        code="MLS",
        odds_key="soccer_usa_mls",
        display_name="MLS",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "totals", "spreads"],
        lookahead_days=7,
        past_hours=8,
        max_full_games=30,
        max_quick_games=20,
    ),
    # Soccer - English Premier League
    "epl": SportConfig(
        slug="epl",
        code="EPL",
        odds_key="soccer_epl",
        display_name="Premier League",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "totals", "spreads"],
        lookahead_days=7,
        past_hours=8,
        max_full_games=30,
        max_quick_games=20,
    ),
    # Soccer - La Liga
    "laliga": SportConfig(
        slug="laliga",
        code="LALIGA",
        odds_key="soccer_spain_la_liga",
        display_name="La Liga",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "totals", "spreads"],
        lookahead_days=7,
        past_hours=8,
        max_full_games=30,
        max_quick_games=20,
    ),
    # Soccer - UEFA Champions League
    "ucl": SportConfig(
        slug="ucl",
        code="UCL",
        odds_key="soccer_uefa_champs_league",
        display_name="Champions League",
        default_markets=["h2h", "spreads", "totals"],
        supported_markets=["h2h", "totals", "spreads"],
        lookahead_days=14,
        past_hours=8,
        max_full_games=20,
        max_quick_games=15,
    ),
    # Legacy soccer config (keep for backwards compatibility)
    "soccer": SportConfig(
        slug="soccer",
        code="SOCCER",
        odds_key="soccer_epl",
        display_name="Soccer",
        default_markets=["h2h", "spreads", "totals"],
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
    # NFL
    "nfl": "nfl",
    "americanfootball_nfl": "nfl",
    "football": "nfl",
    # NBA
    "nba": "nba",
    "basketball": "nba",
    "basketball_nba": "nba",
    # WNBA
    "wnba": "wnba",
    "basketball_wnba": "wnba",
    # NHL
    "nhl": "nhl",
    "icehockey_nhl": "nhl",
    "hockey": "nhl",
    # MLB
    "mlb": "mlb",
    "baseball": "mlb",
    "baseball_mlb": "mlb",
    # College Football
    "ncaaf": "ncaaf",
    "americanfootball_ncaaf": "ncaaf",
    "college football": "ncaaf",
    "cfb": "ncaaf",
    # College Basketball
    "ncaab": "ncaab",
    "basketball_ncaab": "ncaab",
    "college basketball": "ncaab",
    "cbb": "ncaab",
    # Soccer - MLS
    "mls": "mls",
    "soccer_usa_mls": "mls",
    "major league soccer": "mls",
    # Soccer - EPL
    "epl": "epl",
    "soccer_epl": "epl",
    "premier league": "epl",
    "english premier league": "epl",
    # Soccer - La Liga
    "laliga": "laliga",
    "la liga": "laliga",
    "soccer_spain_la_liga": "laliga",
    # Soccer - Champions League
    "ucl": "ucl",
    "soccer_uefa_champs_league": "ucl",
    "champions league": "ucl",
    # Legacy soccer
    "soccer": "soccer",
    # UFC
    "ufc": "ufc",
    "mma": "ufc",
    "mma_mixed_martial_arts": "ufc",
    # Boxing
    "boxing": "boxing",
    "boxing_boxing": "boxing",
}

# Also map the uppercase codes for convenience
for _config in SPORT_CONFIGS.values():
    _SPORT_ALIAS_MAP[_config.code.lower()] = _config.slug

# Backend-owned visibility: which sports appear in listing APIs (no frontend policy import).
HIDDEN_SPORT_SLUGS: frozenset[str] = frozenset({"ucl"})
COMING_SOON_SPORT_SLUGS: frozenset[str] = frozenset({"ufc", "boxing"})


def is_sport_visible(cfg: SportConfig) -> bool:
    """True if this sport should appear in /api/sports and ops availability-contract (not hidden)."""
    slug = (cfg.slug or "").lower().strip()
    return slug not in HIDDEN_SPORT_SLUGS


def apply_sport_visibility_overrides(item: Dict[str, Any], slug: str) -> Dict[str, Any]:
    """Apply coming-soon overrides so frontend (is_enabled primary) stays consistent."""
    slug_norm = (slug or "").lower().strip()
    if slug_norm in COMING_SOON_SPORT_SLUGS:
        item["in_season"] = False
        item["status_label"] = "Coming Soon"
        item["is_enabled"] = False
        item["sport_state"] = "OFFSEASON"
        item["state_reason"] = "coming_soon_override"
    return item


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

