"""
Roster refresh: fetch and cache rosters for team IDs (upcoming games). Quota-aware.

Called from SportsRefreshService only. Uses team IDs from apisports_fixtures (next 48h).
No live API from request path.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.apisports_roster_repository import ApisportsRosterRepository
from app.services.apisports.client import get_apisports_client
from app.services.apisports.quota_manager import get_quota_manager

logger = logging.getLogger(__name__)

DEFAULT_TTL_ROSTER_SECONDS = 86400 * 2  # 2 days
MAX_ROSTER_PAGES = 2  # cap pages per team to limit quota


class RosterRefreshService:
    """
    Refresh rosters for given (sport, team_ids, season). Skips stale check per team.
    Respects quota reserve; does not call API when remaining <= reserve.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = ApisportsRosterRepository(db)
        self._client = get_apisports_client()
        self._quota = get_quota_manager()

    def _reserve(self) -> int:
        return getattr(settings, "apisports_budget_reserve", 5)

    def _ttl_seconds(self) -> int:
        return getattr(settings, "apisports_ttl_roster_seconds", DEFAULT_TTL_ROSTER_SECONDS)

    def _is_soccer(self, sport: str) -> bool:
        return (sport or "").lower().strip() in ("football", "soccer", "epl", "mls", "laliga", "ucl")

    async def refresh_rosters_for_team_ids(
        self,
        sport: str,
        team_ids: List[int],
        season: str,
    ) -> int:
        """
        Refresh roster for each team_id (sport, season). Skips if roster is fresh.
        Returns number of rosters refreshed. Stops when remaining quota <= reserve.
        """
        if not self._client.is_configured() or not team_ids:
            return 0

        reserve = self._reserve()
        ttl = self._ttl_seconds()
        refreshed = 0
        seen: Set[int] = set()

        for team_id in team_ids:
            if team_id in seen:
                continue
            seen.add(team_id)

            if await self._quota.remaining_async(sport) <= reserve:
                logger.debug("RosterRefresh: stop (quota reserve)")
                break

            row = await self._repo.get_roster(sport=sport, team_id=team_id, season=season)
            if row and ApisportsRosterRepository.is_fresh(row.last_fetched_at, ttl):
                continue

            if self._is_soccer(sport):
                data = await self._client.get_players_squads(
                    team_id=team_id,
                    season=season,
                    sport=sport,
                )
                if data and isinstance(data.get("response"), list) and len(data["response"]) > 0:
                    squad = data["response"][0] if isinstance(data["response"][0], dict) else {}
                    players = squad.get("players", []) if isinstance(squad.get("players"), list) else []
                    payload = {"players": players, "raw": data.get("response")}
                    await self._repo.upsert_roster(
                        sport=sport,
                        team_id=team_id,
                        season=season,
                        payload=payload,
                        stale_after_seconds=ttl,
                    )
                    refreshed += 1
            else:
                all_players: List[dict[str, Any]] = []
                for page in range(1, MAX_ROSTER_PAGES + 1):
                    if await self._quota.remaining_async(sport) <= reserve:
                        break
                    data = await self._client.get_players(
                        team_id=team_id,
                        season=season,
                        page=page,
                        sport=sport,
                    )
                    if not data or not isinstance(data.get("response"), list):
                        break
                    page_players = data["response"]
                    if not page_players:
                        break
                    all_players.extend(p for p in page_players if isinstance(p, dict))
                if all_players:
                    await self._repo.upsert_roster(
                        sport=sport,
                        team_id=team_id,
                        season=season,
                        payload={"players": all_players},
                        stale_after_seconds=ttl,
                    )
                    refreshed += 1

        if refreshed > 0:
            logger.info(
                "RosterRefresh: refreshed %s rosters for %s season %s (teams checked %s)",
                refreshed, sport, season, len(seen),
            )
        return refreshed
