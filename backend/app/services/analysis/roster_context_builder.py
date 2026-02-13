"""
Build roster allowlist for a game: allowed player names from cached rosters.

The allowlist contains ONLY current roster players for the two matchup teams
(home + away) for the game's season. Call ensure_rosters_for_game() before
get_allowed_player_names() so cached data reflects current rosters (post-trades,
moves). Used by full-article generation.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.repositories.apisports_roster_repository import ApisportsRosterRepository
from app.services.apisports.roster_refresh_service import RosterRefreshService
from app.services.apisports.season_resolver import get_season_for_sport_at_date
from app.services.apisports.team_id_resolver import resolve_team_id_async

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


async def _game_team_ids_and_season(db: AsyncSession, game: Game) -> tuple[str, List[int], str]:
    """Return (sport, team_ids, season) for the game. Uses DB-first resolution; empty team_ids if unmapped."""
    sport = (game.sport or "").strip()
    if not sport:
        return sport, [], ""
    game_date = getattr(game, "start_time", None) or datetime.now(timezone.utc)
    if game_date and getattr(game_date, "tzinfo", None) is None:
        game_date = game_date.replace(tzinfo=timezone.utc)
    season = get_season_for_sport_at_date(sport, game_date)
    team_ids: List[int] = []
    for team_name in (getattr(game, "home_team", None), getattr(game, "away_team", None)):
        if not team_name:
            continue
        tid = await resolve_team_id_async(db, str(team_name).strip(), sport=sport)
        if tid is not None:
            team_ids.append(tid)
    return sport, team_ids, season


class RosterContextBuilder:
    """
    Build allowed_player_names for a Game from cached apisports_team_rosters.

    The allowlist is ONLY current roster players for the two matchup teams
    (home + away) for the game's season. Call ensure_rosters_for_game() before
    get_allowed_player_names() so data reflects current rosters (post-trades).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._roster_repo = ApisportsRosterRepository(db)

    async def ensure_rosters_for_game(self, game: Game) -> None:
        """
        Refresh rosters for the game's two teams (game's season) so the cache
        reflects current rosters. Call before get_allowed_player_names() so
        only current players are allowed in matchup analysis.
        """
        sport, team_ids, season = await _game_team_ids_and_season(self._db, game)
        if not team_ids:
            return
        try:
            roster_svc = RosterRefreshService(self._db)
            refreshed = await roster_svc.refresh_rosters_for_team_ids(sport, team_ids, season)
            if refreshed > 0:
                logger.info(
                    "RosterContextBuilder: refreshed %s rosters for game (sport=%s season=%s)",
                    refreshed, sport, season,
                )
        except Exception as e:  # quota, API errors; continue with existing cache
            logger.warning(
                "RosterContextBuilder: roster refresh failed for game (sport=%s): %s",
                sport, e,
            )
        # Log roster freshness (home=first, away=second) for debugging: high redaction_count + stale → refresh cadence; high + fresh → model overreaching
        now = datetime.now(timezone.utc)

        def _age_seconds(last_fetched: Optional[datetime]) -> Optional[float]:
            if last_fetched is None:
                return None
            ts = last_fetched if last_fetched.tzinfo else last_fetched.replace(tzinfo=timezone.utc)
            return (now - ts).total_seconds()

        home_age: Optional[float] = None
        away_age: Optional[float] = None
        if len(team_ids) >= 1:
            row_h = await self._roster_repo.get_roster(sport, team_ids[0], season)
            home_age = _age_seconds(getattr(row_h, "last_fetched_at", None) if row_h else None)
        if len(team_ids) >= 2:
            row_a = await self._roster_repo.get_roster(sport, team_ids[1], season)
            away_age = _age_seconds(getattr(row_a, "last_fetched_at", None) if row_a else None)
        logger.info(
            "RosterContextBuilder: roster ages home_roster_age_seconds=%s away_roster_age_seconds=%s sport=%s",
            home_age, away_age, sport,
        )

    async def get_allowed_player_names(
        self,
        game: Game,
        *,
        max_names: int = MAX_ALLOWED_NAMES,
    ) -> List[str]:
        """
        Return list of allowed player names for this game (from cached rosters).
        Only players on the current rosters of the two matchup teams (game's
        season) are included. Empty list if rosters missing or teams not resolved.
        Bounded by max_names.
        """
        sport, team_ids, season = await _game_team_ids_and_season(self._db, game)
        if not sport or not team_ids:
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
