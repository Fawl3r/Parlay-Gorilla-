"""
API-Sports injuries cache (DB-first).

Read/write apisports_injuries. Used by injury refresh and by get_injury_report.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.apisports_injury import ApisportsInjury


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ApisportsInjuryRepository:
    """CRUD for apisports_injuries (injury payload per team)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @staticmethod
    def is_fresh(
        last_fetched_at: Optional[datetime],
        stale_after_seconds: Optional[int],
    ) -> bool:
        """Return True if row is still fresh (not past stale_after_seconds)."""
        if last_fetched_at is None:
            return False
        if stale_after_seconds is None or stale_after_seconds <= 0:
            return True
        ts = last_fetched_at
        if getattr(ts, "tzinfo", None) is None:
            ts = ts.replace(tzinfo=timezone.utc)
        delta = (_utc_now() - ts).total_seconds()
        return delta < stale_after_seconds

    async def get_latest_for_team(
        self,
        sport: str,
        team_id: int,
    ) -> Optional[ApisportsInjury]:
        """Return latest injury row for (sport, team_id)."""
        result = await self._db.execute(
            select(ApisportsInjury).where(
                ApisportsInjury.sport == sport,
                ApisportsInjury.team_id == team_id,
            ).order_by(ApisportsInjury.updated_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def upsert_team_injury(
        self,
        sport: str,
        league_id: int,
        team_id: int,
        payload: dict[str, Any],
        stale_after_seconds: Optional[int] = None,
    ) -> None:
        """Upsert one injury row by (sport, team_id)."""
        now = _utc_now()
        result = await self._db.execute(
            select(ApisportsInjury).where(
                ApisportsInjury.sport == sport,
                ApisportsInjury.team_id == team_id,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.payload_json = payload
            row.league_id = league_id
            row.last_fetched_at = now
            row.stale_after_seconds = stale_after_seconds
        else:
            row = ApisportsInjury(
                sport=sport,
                team_id=team_id,
                league_id=league_id,
                payload_json=payload,
                source="api_sports",
                last_fetched_at=now,
                stale_after_seconds=stale_after_seconds,
            )
            self._db.add(row)
        await self._db.commit()
