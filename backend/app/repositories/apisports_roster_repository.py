"""
API-Sports roster repository (DB-first).

Read/write apisports_team_rosters. Used by roster refresh; no live API from request path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.apisports_team_roster import ApisportsTeamRoster


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ApisportsRosterRepository:
    """CRUD for apisports_team_rosters (players per team/season)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @staticmethod
    def is_fresh(last_fetched_at: Optional[datetime], stale_after_seconds: Optional[int]) -> bool:
        """Return True if entity is still fresh (not past stale_after_seconds)."""
        if last_fetched_at is None:
            return False
        if stale_after_seconds is None or stale_after_seconds <= 0:
            return True
        delta = (_utc_now() - last_fetched_at).total_seconds()
        return delta < stale_after_seconds

    async def upsert_roster(
        self,
        sport: str,
        team_id: int,
        season: str,
        payload: dict[str, Any],
        source: str = "api_sports",
        stale_after_seconds: Optional[int] = None,
    ) -> None:
        """Upsert one roster row by (sport, team_id, season)."""
        now = _utc_now()
        result = await self._db.execute(
            select(ApisportsTeamRoster).where(
                ApisportsTeamRoster.sport == sport,
                ApisportsTeamRoster.team_id == team_id,
                ApisportsTeamRoster.season == season,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.payload_json = payload
            row.last_fetched_at = now
            row.stale_after_seconds = stale_after_seconds
        else:
            row = ApisportsTeamRoster(
                sport=sport,
                team_id=team_id,
                season=season,
                payload_json=payload,
                source=source,
                last_fetched_at=now,
                stale_after_seconds=stale_after_seconds,
            )
            self._db.add(row)
        await self._db.commit()

    async def get_roster(
        self,
        sport: str,
        team_id: int,
        season: str,
    ) -> Optional[ApisportsTeamRoster]:
        """Return roster for (sport, team_id, season)."""
        result = await self._db.execute(
            select(ApisportsTeamRoster).where(
                ApisportsTeamRoster.sport == sport,
                ApisportsTeamRoster.team_id == team_id,
                ApisportsTeamRoster.season == season,
            )
        )
        return result.scalar_one_or_none()

    async def get_rosters_for_team_ids(
        self,
        sport: str,
        team_ids: List[int],
        season: str,
    ) -> List[ApisportsTeamRoster]:
        """Return roster rows for given sport, team_ids, and season."""
        if not team_ids:
            return []
        result = await self._db.execute(
            select(ApisportsTeamRoster).where(
                ApisportsTeamRoster.sport == sport,
                ApisportsTeamRoster.team_id.in_(team_ids),
                ApisportsTeamRoster.season == season,
            )
        )
        return list(result.scalars().all())
