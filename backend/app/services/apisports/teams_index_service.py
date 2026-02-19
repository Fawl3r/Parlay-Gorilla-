"""
Cached teams index per league+season: map Odds API team names -> API-Sports team IDs.

Fetches teams list once per 24h; normalizes names (lowercase, strip punctuation);
supports alias overrides for known mismatches. Used by enrichment to resolve home/away.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from app.services.apisports.enrichment_cache import get_cached, set_cached, TTL_TEAMS
from app.services.apisports.team_aliases import get_team_alias


def normalize_team_name(name: str) -> str:
    """Normalize for lookup: lowercase, collapse spaces, strip punctuation."""
    if not name:
        return ""
    s = (name or "").lower().strip()
    s = re.sub(r"[.\-,']", "", s)
    s = " ".join(s.split())
    return s


# Known Odds API name -> normalized key overrides (add as mismatches are found)
TEAM_ALIAS_OVERRIDES: Dict[str, str] = {}


async def get_teams_index(
    client: Any,
    sport_key: str,
    league_id: int,
    season: str,
    sport_slug: str = "",
) -> Dict[str, Dict[str, Any]]:
    """
    Get name_lower -> {id, name} from cache or API. Cache 24h.
    Uses normalized names for keys; alias overrides applied when resolving.
    """
    cached = await get_cached("teams", sport_key, league_id, season)
    if cached is not None and isinstance(cached, dict):
        return cached
    try:
        from app.services.apisports.telemetry_helpers import inc_cache_miss, inc_call_made
        inc_cache_miss("teams_index")
    except Exception:
        pass
    raw = await client.get_teams(league_id=league_id, season=season, sport=sport_key)
    try:
        from app.services.apisports.telemetry_helpers import inc_call_made
        inc_call_made("teams_index", sport_slug or sport_key)
    except Exception:
        pass
    if not raw or not isinstance(raw.get("response"), list):
        return {}
    index: Dict[str, Dict[str, Any]] = {}
    for item in raw["response"]:
        if not isinstance(item, dict):
            continue
        team = item.get("team") or item
        tid = team.get("id") if isinstance(team, dict) else None
        name = (team.get("name") or item.get("name") or "").strip() if isinstance(team, dict) else (item.get("name") or "").strip()
        if tid and name:
            key = normalize_team_name(name)
            index[key] = {"id": tid, "name": name}
    await set_cached("teams", sport_key, league_id, season, index)
    return index


def resolve_team_id(
    teams_index: Dict[str, Dict[str, Any]],
    odds_team_name: str,
) -> Optional[int]:
    """Resolve Odds API team name to API-Sports team ID; check alias map before fuzzy normalization."""
    if not odds_team_name or not teams_index:
        return None
    normalized = normalize_team_name(odds_team_name)
    lookup = TEAM_ALIAS_OVERRIDES.get(normalized) or get_team_alias(normalized) or normalized
    if lookup in teams_index:
        return teams_index[lookup].get("id")
    if normalized in teams_index:
        return teams_index[normalized].get("id")
    for key, val in teams_index.items():
        if key in normalized or normalized in key:
            return val.get("id")
    return None
