"""Repository for sport_season_state cache."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sport_season_state import SportSeasonState


class SportSeasonStateRepository:
    """Read/write cached season state per sport."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get(self, sport: str) -> Optional[SportSeasonState]:
        """Return cached row for sport or None."""
        result = await self._db.execute(
            select(SportSeasonState).where(SportSeasonState.sport == sport)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        sport: str,
        state: str,
        recent_final_count: int,
        near_scheduled_count: int,
        post_scheduled_count: int,
        computed_at_utc: Optional[datetime] = None,
    ) -> None:
        """Insert or update cached state for sport."""
        from datetime import timezone
        now = computed_at_utc or datetime.now(timezone.utc)
        stmt = insert(SportSeasonState).values(
            sport=sport,
            state=state,
            computed_at_utc=now,
            recent_final_count=recent_final_count,
            near_scheduled_count=near_scheduled_count,
            post_scheduled_count=post_scheduled_count,
        ).on_conflict_do_update(
            index_elements=["sport"],
            set_=dict(
                state=state,
                computed_at_utc=now,
                recent_final_count=recent_final_count,
                near_scheduled_count=near_scheduled_count,
                post_scheduled_count=post_scheduled_count,
            ),
        )
        await self._db.execute(stmt)
