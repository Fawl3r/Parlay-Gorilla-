"""
API-Sports team catalog repository (DB-first).

Read/write apisports_teams. Used by team catalog refresh; no live API from request path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.apisports_team import ApisportsTeam


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ApisportsTeamRepository:
    """CRUD for apisports_teams (team catalog per sport/league/season)."""

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

    async def upsert_team(
        self,
        sport: str,
        team_id: int,
        payload: dict[str, Any],
        league_id: Optional[int] = None,
        season: Optional[str] = None,
        name: Optional[str] = None,
        normalized_name: Optional[str] = None,
        source: str = "api_sports",
        stale_after_seconds: Optional[int] = None,
    ) -> None:
        """Upsert one team row by (sport, team_id, season)."""
        now = _utc_now()
        q = select(ApisportsTeam).where(
            ApisportsTeam.sport == sport,
            ApisportsTeam.team_id == team_id,
        )
        if season is not None:
            q = q.where(ApisportsTeam.season == season)
        else:
            q = q.where(ApisportsTeam.season.is_(None))
        result = await self._db.execute(q)
        row = result.scalar_one_or_none()
        if row:
            row.payload_json = payload
            row.last_fetched_at = now
            row.stale_after_seconds = stale_after_seconds
            row.league_id = league_id
            row.name = name or row.name
            if normalized_name is not None:
                row.normalized_name = normalized_name
        else:
            row = ApisportsTeam(
                sport=sport,
                league_id=league_id,
                team_id=team_id,
                season=season,
                name=name,
                normalized_name=normalized_name,
                payload_json=payload,
                source=source,
                last_fetched_at=now,
                stale_after_seconds=stale_after_seconds,
            )
            self._db.add(row)
        await self._db.commit()

    async def find_team_id_by_name(
        self,
        sport: str,
        normalized_name: str,
        league_id: Optional[int] = None,
    ) -> Optional[int]:
        """Return team_id for (sport, normalized_name), optional league_id filter."""
        if not (sport and normalized_name):
            return None
        key = (sport or "").strip().lower()
        norm = (normalized_name or "").strip().lower()
        if not norm:
            return None
        q = (
            select(ApisportsTeam.team_id)
            .where(ApisportsTeam.sport == key)
            .where(ApisportsTeam.normalized_name == norm)
        )
        if league_id is not None:
            q = q.where(ApisportsTeam.league_id == league_id)
        result = await self._db.execute(q.limit(1))
        row = result.scalar_one_or_none()
        return int(row) if row is not None else None

    async def find_team_id_by_name_fuzzy(
        self,
        sport: str,
        normalized_name: str,
        league_id: Optional[int] = None,
    ) -> Optional[int]:
        """Fallback: return first team whose normalized_name contains or is contained in the given name."""
        if not (sport and normalized_name):
            return None
        key = (sport or "").strip().lower()
        norm = (normalized_name or "").strip().lower()
        if not norm:
            return None
        q = select(ApisportsTeam).where(ApisportsTeam.sport == key)
        if league_id is not None:
            q = q.where(ApisportsTeam.league_id == league_id)
        result = await self._db.execute(q)
        for row in result.scalars().all():
            if not row.normalized_name:
                continue
            nn = (row.normalized_name or "").strip().lower()
            if norm == nn or norm in nn or nn in norm:
                return row.team_id
        return None

    async def get_team(
        self,
        sport: str,
        team_id: int,
        season: Optional[str] = None,
    ) -> Optional[ApisportsTeam]:
        """Return team for (sport, team_id, season)."""
        q = select(ApisportsTeam).where(
            ApisportsTeam.sport == sport,
            ApisportsTeam.team_id == team_id,
        )
        if season is not None:
            q = q.where(ApisportsTeam.season == season)
        result = await self._db.execute(q.order_by(ApisportsTeam.last_fetched_at.desc()).limit(1))
        return result.scalar_one_or_none()

    async def get_teams_by_sport_league_season(
        self,
        sport: str,
        league_id: Optional[int] = None,
        season: Optional[str] = None,
    ) -> List[ApisportsTeam]:
        """Return teams for sport, optional league and season."""
        q = select(ApisportsTeam).where(ApisportsTeam.sport == sport)
        if league_id is not None:
            q = q.where(ApisportsTeam.league_id == league_id)
        if season is not None:
            q = q.where(ApisportsTeam.season == season)
        result = await self._db.execute(q)
        return list(result.scalars().all())

    async def get_team_ids_for_sport_season(
        self,
        sport: str,
        season: str,
        league_id: Optional[int] = None,
    ) -> List[int]:
        """Return list of team_id for sport/season (and optional league)."""
        q = select(ApisportsTeam.team_id).where(
            ApisportsTeam.sport == sport,
            ApisportsTeam.season == season,
        )
        if league_id is not None:
            q = q.where(ApisportsTeam.league_id == league_id)
        result = await self._db.execute(q)
        return list(result.scalars().all())
