"""
Resolve internal sport slug to API-Sports league ID.

Used by analysis enrichment to fetch standings/team stats/form/injuries.
If league ID is not configured, enrichment is skipped (graceful fallback).
"""

from __future__ import annotations

from typing import Optional

from app.core.config import settings

_SPORT_LEAGUE_ATTRS = {
    "nba": "apisports_league_id_nba",
    "wnba": "apisports_league_id_wnba",
    "nfl": "apisports_league_id_nfl",
    "nhl": "apisports_league_id_nhl",
    "mlb": "apisports_league_id_mlb",
    "epl": "apisports_league_id_epl",
}


def get_league_id_for_sport(sport_slug: str) -> Optional[int]:
    """
    Return API-Sports league ID for the given sport slug, or None if not configured.
    """
    if not sport_slug:
        return None
    slug = (sport_slug or "").lower().strip()
    attr = _SPORT_LEAGUE_ATTRS.get(slug)
    if not attr:
        return None
    return getattr(settings, attr, None)


def is_enrichment_supported_for_sport(sport_slug: str) -> bool:
    """True if we have a league ID and can attempt API-Sports enrichment for this sport."""
    return get_league_id_for_sport(sport_slug) is not None
