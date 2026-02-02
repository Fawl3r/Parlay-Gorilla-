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
from app.services.apisports.data_adapter import ApiSportsDataAdapter
from app.services.apisports.quota_manager import get_quota_manager
from app.services.apisports.injury_refresh_service import InjuryRefreshService
from app.services.apisports.roster_refresh_service import RosterRefreshService
from app.services.apisports.season_resolver import get_season_int_for_sport, get_season_for_sport
from app.services.apisports.team_catalog_refresh_service import TeamCatalogRefreshService
from app.services.apisports.team_mapper import get_team_mapper
from app.services.sports_config import list_supported_sports

logger = logging.getLogger(__name__)

# API-Sports football league IDs (configurable later)
DEFAULT_LEAGUE_IDS: dict[str, List[int]] = {
    "americanfootball_nfl": [1],   # placeholder; API-Sports uses different sport keys
    "basketball_nba": [12],
    "icehockey_nhl": [57],
    "baseball_mlb": [1],
}

# Map our sport keys to API-Sports league IDs (all target sports)
APISPORTS_SPORT_LEAGUES: dict[str, List[int]] = {
    "football": [39, 40, 61, 78, 135, 140, 203],  # soccer: top European leagues
    "americanfootball_nfl": [1],  # NFL
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

    def _ttl_injuries(self) -> int:
        return getattr(settings, "apisports_ttl_injuries_seconds", 21600)

    async def remaining_quota(self, sport: Optional[str] = None) -> int:
        """Return remaining quota for sport (or 'default' if no sport)."""
        return await self._quota.remaining_async(sport or "default")

    async def _active_sports_for_next_48h(self) -> List[str]:
        """Sports we refresh (all API-Sports target sports)."""
        sport_configs = list_supported_sports()
        active: List[str] = []
        for sc in sport_configs:
            ok = getattr(sc, "odds_key", None) or getattr(sc, "slug", "")
            if ok in APISPORTS_SPORT_LEAGUES:
                active.append(ok)
        if not active:
            active = list(APISPORTS_SPORT_LEAGUES.keys())
        return active

    async def run_refresh(self) -> dict[str, Any]:
        """
        Run full refresh pipeline. Returns summary: used, remaining, refreshed entities.
        """
        if not self._client.is_configured():
            logger.info("SportsRefreshService: API-Sports not configured, skip")
            return {"used": 0, "remaining": await self.remaining_quota(), "refreshed": {}}

        reserve = self._reserve()
        remaining = await self.remaining_quota()
        if remaining <= reserve:
            logger.warning("SportsRefreshService: remaining quota %s <= reserve %s, skip", remaining, reserve)
            return {"used": 0, "remaining": remaining, "refreshed": {}}

        used = 0
        refreshed: dict[str, Any] = {"fixtures": 0, "team_stats": 0, "standings": 0, "teams": 0, "rosters": 0, "injuries": 0}

        active_sports = await self._active_sports_for_next_48h()

        # 1) Fixtures for today + tomorrow (1 call per active sport/league)
        now = datetime.now(timezone.utc)
        from_date = now.strftime("%Y-%m-%d")
        to_dt = now + timedelta(days=2)
        to_date = to_dt.strftime("%Y-%m-%d")

        for sport in active_sports:
            if await self.remaining_quota(sport) <= reserve:
                break
            league_ids = APISPORTS_SPORT_LEAGUES.get(sport, [39])
            for league_id in league_ids[:2]:
                if await self.remaining_quota(sport) <= reserve:
                    break
                data = await self._client.get_fixtures(
                    league_id=league_id,
                    from_date=from_date,
                    to_date=to_date,
                    sport=sport,
                )
                if data and isinstance(data.get("response"), list):
                    count = await self._repo.upsert_fixtures(
                        sport=sport,
                        fixtures=data["response"],
                        stale_after_seconds=self._ttl_fixtures(),
                    )
                    refreshed["fixtures"] += count
                    used += 1
                    logger.info("SportsRefreshService: refreshed %s fixtures for %s league %s", count, sport, league_id)

        # 2) Team catalog refresh (TTL-based, one league per sport)
        team_catalog_svc = TeamCatalogRefreshService(self._db)
        for sport in active_sports:
            if await self.remaining_quota(sport) <= reserve:
                break
            league_ids = APISPORTS_SPORT_LEAGUES.get(sport, [39])
            season_str = get_season_for_sport(sport)
            for league_id in league_ids[:1]:
                if await self.remaining_quota(sport) <= reserve:
                    break
                n = await team_catalog_svc.refresh_teams(sport, league_id, season_str)
                if n > 0:
                    used += 1
                    refreshed["teams"] = refreshed.get("teams", 0) + n

        # 3) Teams playing in next 48h from DB (for roster refresh)
        team_ids: Set[int] = set()
        sport_to_team_ids: dict[str, Set[int]] = {s: set() for s in active_sports}
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
                sport_to_team_ids.setdefault(row.sport, set()).add(row.home_team_id)
            if row.away_team_id:
                team_ids.add(row.away_team_id)
                sport_to_team_ids.setdefault(row.sport, set()).add(row.away_team_id)

        # 4) Roster refresh for those team IDs (quota-aware)
        roster_svc = RosterRefreshService(self._db)
        for sport in active_sports:
            if await self.remaining_quota(sport) <= reserve:
                break
            sport_team_ids = list(sport_to_team_ids.get(sport, set()))[:20]
            if sport_team_ids:
                season_str = get_season_for_sport(sport)
                n = await roster_svc.refresh_rosters_for_team_ids(sport, sport_team_ids, season_str)
                refreshed["rosters"] = refreshed.get("rosters", 0) + n
                if n > 0:
                    used += n

        # 5) Team stats for those teams (bounded by remaining - reserve)
        for tid in list(team_ids)[: max(0, await self.remaining_quota() - reserve)]:
            if await self.remaining_quota() <= reserve:
                break
            # API-Sports team statistics are per fixture; we use standings or a generic stats endpoint if available
            # For now skip per-team stats call to avoid burning quota (1 call per team). Use standings instead.
            break

        # 6) Standings once/day per active sport (TTL-skip if fresh)
        ttl_standings = self._ttl_standings()
        for sport in active_sports:
            if await self.remaining_quota() <= reserve:
                break
            league_ids = APISPORTS_SPORT_LEAGUES.get(sport, [39])
            for league_id in league_ids[:1]:
                if await self.remaining_quota() <= reserve:
                    break
                existing = await self._repo.get_standings(sport=sport, league_id=league_id)
                if existing:
                    row = existing[0] if existing else None
                    if row and SportsDataRepository.is_fresh(row.last_fetched_at, ttl_standings):
                        logger.debug("SportsRefreshService: standings fresh for %s league %s, skip", sport, league_id)
                        continue
                season_int = get_season_int_for_sport(sport)
                data = await self._client.get_standings(
                    league_id=league_id,
                    season=season_int,
                    sport=sport,
                )
                if data and isinstance(data.get("response"), list) and len(data["response"]) > 0:
                    standings_list = data["response"]
                    payload = standings_list[0] if isinstance(standings_list[0], dict) else {"response": standings_list}
                    await self._repo.upsert_standings(
                        sport=sport,
                        league_id=league_id,
                        standings=payload,
                        season=str(season_int),
                        stale_after_seconds=ttl_standings,
                    )
                    refreshed["standings"] += 1
                    used += 1
                    logger.info("SportsRefreshService: refreshed standings for %s league %s", sport, league_id)
                    # Derive normalized per-team stats and upsert (no extra API calls)
                    normalized = ApiSportsDataAdapter.standings_to_normalized_team_stats(
                        payload, sport, league_id, season=str(season_int)
                    )
                    mapper = get_team_mapper()
                    for team_stat in normalized:
                        team_id = team_stat.get("team_id")
                        team_name = team_stat.get("team_name")
                        if not team_id:
                            continue
                        if team_name:
                            mapper.add_mapping(team_name, team_id, sport)
                        await self._repo.upsert_team_stats(
                            sport=sport,
                            team_id=team_id,
                            stats=team_stat,
                            league_id=league_id,
                            season=str(season_int),
                            source="standings_derived",
                            stale_after_seconds=self._ttl_team_stats(),
                        )
                    if normalized:
                        refreshed["team_stats"] = refreshed.get("team_stats", 0) + len(normalized)

        # 7) Injuries once per active sport (1 league per sport; quota-protected)
        injury_svc = InjuryRefreshService(self._db)
        for sport in active_sports:
            if await self.remaining_quota() <= reserve:
                break
            league_ids = APISPORTS_SPORT_LEAGUES.get(sport, [39])
            for league_id in league_ids[:1]:
                if await self.remaining_quota() <= reserve:
                    break
                season_str = get_season_for_sport(sport)
                n = await injury_svc.refresh_injuries(sport, league_id, season_str)
                refreshed["injuries"] = refreshed.get("injuries", 0) + n
                if n > 0:
                    used += 1
                    logger.info("SportsRefreshService: refreshed injuries for %s league %s", sport, league_id)
                break

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
