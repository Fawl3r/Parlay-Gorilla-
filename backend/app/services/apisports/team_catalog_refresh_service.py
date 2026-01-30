"""
Team catalog refresh: fetch and cache teams per sport/league/season (TTL-based).

Called from SportsRefreshService only. No live API from request path.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.apisports_team_repository import ApisportsTeamRepository
from app.services.apisports.client import get_apisports_client

logger = logging.getLogger(__name__)

DEFAULT_TTL_TEAM_CATALOG_SECONDS = 86400 * 7  # 7 days


class TeamCatalogRefreshService:
    """Fetch teams for league/season and upsert into apisports_teams. Skips when fresh (TTL)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = ApisportsTeamRepository(db)
        self._client = get_apisports_client()

    def _ttl_seconds(self) -> int:
        from app.core.config import settings
        return getattr(settings, "apisports_ttl_team_catalog_seconds", DEFAULT_TTL_TEAM_CATALOG_SECONDS)

    async def refresh_teams(
        self,
        sport: str,
        league_id: int,
        season: str,
        *,
        force: bool = False,
    ) -> int:
        """
        Fetch teams for (sport, league_id, season) and upsert. Returns number upserted.
        Skips if we already have fresh data for this (sport, league_id, season) unless force=True.
        """
        if not self._client.is_configured():
            return 0

        existing = await self._repo.get_teams_by_sport_league_season(
            sport=sport, league_id=league_id, season=season
        )
        if not force and existing:
            any_fresh = any(
                ApisportsTeamRepository.is_fresh(row.last_fetched_at, self._ttl_seconds())
                for row in existing
            )
            if any_fresh:
                logger.debug(
                    "TeamCatalogRefresh: skip %s league %s season %s (fresh)",
                    sport, league_id, season,
                )
                return 0

        data = await self._client.get_teams(
            league_id=league_id,
            season=season,
            sport=sport,
        )
        if not data or not isinstance(data.get("response"), list):
            return 0

        count = 0
        for item in data["response"]:
            if not isinstance(item, dict):
                continue
            team_obj = item.get("team") if isinstance(item.get("team"), dict) else item
            team_id = team_obj.get("id") if team_obj else None
            name = team_obj.get("name") if team_obj else None
            if team_id is None:
                continue
            await self._repo.upsert_team(
                sport=sport,
                team_id=team_id,
                payload=item,
                league_id=league_id,
                season=season,
                name=name,
                stale_after_seconds=self._ttl_seconds(),
            )
            count += 1

        if count > 0:
            logger.info(
                "TeamCatalogRefresh: upserted %s teams for %s league %s season %s",
                count, sport, league_id, season,
            )
        return count
