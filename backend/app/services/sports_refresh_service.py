"""
API-Sports refresh pipeline: quota-aware, DB-first.

Runs in background only. Never call from user-facing endpoints.
Budget: fixtures 60, team_stats 25, standings 10, reserve 5 (configurable).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import AsyncSessionLocal
from app.models.apisports_fixture import ApisportsFixture
from app.repositories.sports_data_repository import SportsDataRepository
from app.services.apisports.client import get_apisports_client
from app.services.apisports.quota_manager import get_quota_manager
from app.services.sports_config import list_supported_sports

logger = logging.getLogger(__name__)

# API-Sports football league IDs (configurable later)
DEFAULT_LEAGUE_IDS: dict[str, List[int]] = {
    "americanfootball_nfl": [1],   # placeholder; API-Sports uses different sport keys
    "basketball_nba": [12],
    "icehockey_nhl": [57],
    "baseball_mlb": [1],
}

# Map our sport keys to API-Sports "sport" and league IDs (football example)
APISPORTS_SPORT_LEAGUES: dict[str, List[int]] = {
    "football": [39, 40, 61, 78, 135, 140, 203],  # top European leagues
    "basketball_nba": [12],
    "icehockey_nhl": [57],
    "baseball_mlb": [1],
}


class SportsRefreshService:
    """
    Consolidated refresh: fixtures for today+tomorrow, team stats for teams playing soon,
    standings once/day. Stops when remaining quota < reserve.
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._repo = SportsDataRepository(db)
        self._client = get_apisports_client()
        self._quota = get_quota_manager()

    def _reserve(self) -> int:
        return getattr(settings, "apisports_budget_reserve", 5)

    def _ttl_fixtures(self) -> int:
        return getattr(settings, "apisports_ttl_fixtures_seconds", 900)

    def _ttl_team_stats(self) -> int:
        return getattr(settings, "apisports_ttl_team_stats_seconds", 86400)

    def _ttl_standings(self) -> int:
        return getattr(settings, "apisports_ttl_standings_seconds", 86400)

    async def remaining_quota(self) -> int:
        return await self._quota.remaining_async()

    async def _active_sports_for_next_48h(self) -> List[str]:
        """Sports that have games in next 48h or are in configured list."""
        # API-Sports base URL is football; support football first
        sport_configs = list_supported_sports()
        active: List[str] = []
        for sc in sport_configs:
            ok = getattr(sc, "odds_key", None) or getattr(sc, "slug", "")
            if ok in APISPORTS_SPORT_LEAGUES:
                active.append(ok)
        if not active:
            active = ["football"]
        return active

    async def run_refresh(self) -> dict[str, Any]:
        """
        Run full refresh pipeline. Returns summary: used, remaining, refreshed entities.
        """
        if not self._client.is_configured():
            logger.info("SportsRefreshService: API-Sports not configured, skip")
            return {"used": 0, "remaining": await self.remaining_quota(), "refreshed": {}}

        remaining = await self.remaining_quota()
        reserve = self._reserve()
        if remaining <= reserve:
            logger.warning("SportsRefreshService: remaining quota %s <= reserve %s, skip", remaining, reserve)
            return {"used": 0, "remaining": remaining, "refreshed": {}}

        used = 0
        refreshed: dict[str, Any] = {"fixtures": 0, "team_stats": 0, "standings": 0}

        # 1) Fixtures for today + tomorrow (1 call per active sport/league)
        active_sports = await self._active_sports_for_next_48h()
        now = datetime.now(timezone.utc)
        from_date = now.strftime("%Y-%m-%d")
        to_dt = now + timedelta(days=2)
        to_date = to_dt.strftime("%Y-%m-%d")

        for sport in active_sports:
            if await self.remaining_quota() <= reserve:
                break
            league_ids = APISPORTS_SPORT_LEAGUES.get(sport, [39])
            for league_id in league_ids[:2]:  # max 2 leagues per sport per run to save quota
                if await self.remaining_quota() <= reserve:
                    break
                data = await self._client.get_fixtures(league_id=league_id, from_date=from_date, to_date=to_date)
                if data and isinstance(data.get("response"), list):
                    count = await self._repo.upsert_fixtures(
                        sport=sport,
                        fixtures=data["response"],
                        stale_after_seconds=self._ttl_fixtures(),
                    )
                    refreshed["fixtures"] += count
                    used += 1
                    logger.info("SportsRefreshService: refreshed %s fixtures for %s league %s", count, sport, league_id)

        # 2) Teams playing in next 48h from DB
        team_ids: Set[int] = set()
        from_ts = now
        to_ts = now + timedelta(days=2)
        result = await self._db.execute(
            select(ApisportsFixture).where(
                ApisportsFixture.sport.in_(active_sports),
                ApisportsFixture.date >= from_ts,
                ApisportsFixture.date <= to_ts,
            )
        )
        for row in result.scalars().all():
            if row.home_team_id:
                team_ids.add(row.home_team_id)
            if row.away_team_id:
                team_ids.add(row.away_team_id)

        # 3) Team stats for those teams (bounded by remaining - reserve)
        for tid in list(team_ids)[: (await self.remaining_quota() - reserve)]:
            if await self.remaining_quota() <= reserve:
                break
            # API-Sports team statistics are per fixture; we use standings or a generic stats endpoint if available
            # For now skip per-team stats call to avoid burning quota (1 call per team). Use standings instead.
            break

        # 4) Standings once/day per active sport
        for sport in active_sports:
            if await self.remaining_quota() <= reserve:
                break
            league_ids = APISPORTS_SPORT_LEAGUES.get(sport, [39])
            for league_id in league_ids[:1]:
                if await self.remaining_quota() <= reserve:
                    break
                season = str(now.year)
                data = await self._client.get_standings(league_id=league_id, season=int(season))
                if data and isinstance(data.get("response"), list) and len(data["response"]) > 0:
                    standings_list = data["response"]
                    payload = standings_list[0] if isinstance(standings_list[0], dict) else {"response": standings_list}
                    await self._repo.upsert_standings(
                        sport=sport,
                        league_id=league_id,
                        standings=payload,
                        season=season,
                        stale_after_seconds=self._ttl_standings(),
                    )
                    refreshed["standings"] += 1
                    used += 1
                    logger.info("SportsRefreshService: refreshed standings for %s league %s", sport, league_id)

        remaining_after = await self.remaining_quota()
        logger.info(
            "SportsRefreshService: used=%s remaining=%s refreshed=%s",
            used,
            remaining_after,
            refreshed,
        )
        return {"used": used, "remaining": remaining_after, "refreshed": refreshed}


async def run_apisports_refresh() -> dict[str, Any]:
    """Entrypoint for scheduler: run refresh in a new DB session."""
    async with AsyncSessionLocal() as db:
        service = SportsRefreshService(db)
        return await service.run_refresh()
