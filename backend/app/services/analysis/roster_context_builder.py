"""
Build roster allowlist for a game: allowed player names from cached rosters.

Used by full-article generation. No live API; reads from apisports_team_rosters only.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.repositories.apisports_roster_repository import ApisportsRosterRepository
from app.services.apisports.season_resolver import get_season_for_sport_at_date
from app.services.apisports.team_mapper import get_team_mapper

logger = logging.getLogger(__name__)

MAX_ALLOWED_NAMES = 300  # cap for prompt size


def _normalize_name(name: str) -> str:
    """Return trimmed title-case 'First Last' for allowlist matching."""
    if not name or not isinstance(name, str):
        return ""
    return " ".join(name.split()).strip()


def _extract_names_from_payload(payload: dict) -> Set[str]:
    """Extract player names from roster payload_json (sport-agnostic)."""
    out: Set[str] = set()
    if not isinstance(payload, dict):
        return out
    players = payload.get("players") or payload.get("response") or []
    if not isinstance(players, list):
        return out
    for p in players:
        if not isinstance(p, dict):
            continue
        name = p.get("name")
        if name:
            out.add(_normalize_name(str(name)))
            continue
        first = p.get("firstname") or p.get("first_name") or ""
        last = p.get("lastname") or p.get("last_name") or ""
        if first or last:
            out.add(_normalize_name(f"{first} {last}".strip()))
    return out


class RosterContextBuilder:
    """
    Build allowed_player_names for a Game from cached apisports_team_rosters.

    Resolves game home/away team names to API-Sports team IDs via team_mapper,
    then loads rosters for those teams and the game's season (date-aware).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._roster_repo = ApisportsRosterRepository(db)
        self._team_mapper = get_team_mapper()

    async def get_allowed_player_names(
        self,
        game: Game,
        *,
        max_names: int = MAX_ALLOWED_NAMES,
    ) -> List[str]:
        """
        Return list of allowed player names for this game (from cached rosters).
        Empty list if rosters missing or teams not resolved. Bounded by max_names.
        """
        sport = (game.sport or "").strip()
        if not sport:
            return []

        game_date = getattr(game, "start_time", None) or datetime.now(timezone.utc)
        if game_date and getattr(game_date, "tzinfo", None) is None:
            game_date = game_date.replace(tzinfo=timezone.utc)
        season = get_season_for_sport_at_date(sport, game_date)

        team_ids: List[int] = []
        for team_name in (getattr(game, "home_team", None), getattr(game, "away_team", None)):
            if not team_name:
                continue
            tid = self._team_mapper.get_team_id(str(team_name).strip(), sport=sport)
            if tid is not None:
                team_ids.append(tid)

        if not team_ids:
            logger.debug("RosterContextBuilder: no API-Sports team IDs for game %s", getattr(game, "id", ""))
            return []

        rosters = await self._roster_repo.get_rosters_for_team_ids(sport, team_ids, season)
        names: Set[str] = set()
        for row in rosters:
            names |= _extract_names_from_payload(row.payload_json or {})

        result = sorted(names)[:max_names]
        if result:
            logger.debug("RosterContextBuilder: %s allowed names for game", len(result))
        return result
