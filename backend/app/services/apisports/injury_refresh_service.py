"""
Injury refresh: fetch and cache injuries per league/season, store by team. Quota-aware.

Called from SportsRefreshService only. Uses get_injuries(league_id, season); groups by team_id.
No live API from request path.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.apisports_injury_repository import ApisportsInjuryRepository
from app.services.apisports.client import get_apisports_client
from app.services.apisports.quota_manager import get_quota_manager
from app.services.apisports.season_resolver import get_season_int_for_sport

logger = logging.getLogger(__name__)


class InjuryRefreshService:
    """
    Refresh injuries for (sport, league_id, season). One API call; upsert per team.
    TTL-skip if all teams fresh; respects quota reserve.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = ApisportsInjuryRepository(db)
        self._client = get_apisports_client()
        self._quota = get_quota_manager()

    def _reserve(self) -> int:
        return getattr(settings, "apisports_budget_reserve", 5)

    def _ttl_seconds(self) -> int:
        return getattr(settings, "apisports_ttl_injuries_seconds", 21600)

    async def refresh_injuries(
        self,
        sport: str,
        league_id: int,
        season: str,
    ) -> int:
        """
        Call API-Sports get_injuries(league_id, season); group by team_id; upsert each team.
        Returns number of teams updated. Skips if quota <= reserve.
        """
        if not self._client.is_configured():
            return 0

        reserve = self._reserve()
        if await self._quota.remaining_async(sport) <= reserve:
            logger.debug("InjuryRefresh: skip (quota <= reserve)")
            return 0

        try:
            season_int = int(season.split("-")[0]) if season and "-" in season else int(season or "0")
        except (TypeError, ValueError):
            season_int = get_season_int_for_sport(sport)

        data = await self._client.get_injuries(
            league_id=league_id,
            season=season_int,
            sport=sport,
        )
        if not data or not isinstance(data.get("response"), list):
            return 0

        # Group by team_id: payload per team = list of injury items for that team
        by_team: dict[int, List[dict[str, Any]]] = defaultdict(list)
        for item in data["response"]:
            if not isinstance(item, dict):
                continue
            team = item.get("team")
            if isinstance(team, dict) and team.get("id") is not None:
                tid = int(team["id"])
                by_team[tid].append(item)
            elif isinstance(team, (int, float)):
                tid = int(team)
                by_team[tid].append(item)

        ttl = self._ttl_seconds()
        updated = 0
        for team_id, payload_list in by_team.items():
            if await self._quota.remaining_async(sport) <= reserve:
                break
            payload = {"response": payload_list}
            await self._repo.upsert_team_injury(
                sport=sport,
                league_id=league_id,
                team_id=team_id,
                payload=payload,
                stale_after_seconds=ttl,
            )
            updated += 1

        if updated:
            logger.info(
                "InjuryRefreshService: refreshed injuries for %s league %s (%s teams)",
                sport, league_id, updated,
            )
        return updated
