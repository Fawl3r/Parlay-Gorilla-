"""
Season state service: compute and cache IN_SEASON / POSTSEASON / PRESEASON / OFF_SEASON per sport.
Used for candidate window lookahead and refresh TTL.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_logger import log_event
from app.models.enums import SeasonState
from app.models.game import Game
from app.repositories.sport_season_state_repository import SportSeasonStateRepository
from app.utils.nfl_week import get_current_nfl_week

logger = logging.getLogger(__name__)

SEASON_STATE_TTL_SECONDS = 3600  # 1 hour
RECENT_FINAL_DAYS = 14
NEAR_SCHEDULED_DAYS = 10
POST_SCHEDULED_DAYS = 30


class SeasonStateService:
    """Compute and cache season state per sport."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._repo = SportSeasonStateRepository(db)

    async def get_season_state(
        self,
        sport: str,
        now_utc: datetime | None = None,
        use_cache: bool = True,
    ) -> SeasonState:
        """
        Return current season state for sport.
        Uses cached row if fresh (computed_at_utc within TTL); otherwise computes and upserts.
        """
        now = now_utc or datetime.now(timezone.utc)
        if use_cache:
            row = await self._repo.get(sport)
            if row and (now - row.computed_at_utc.replace(tzinfo=timezone.utc)).total_seconds() < SEASON_STATE_TTL_SECONDS:
                return SeasonState(row.state)
        return await self._compute_and_cache(sport, now)

    async def _compute_and_cache(self, sport: str, now_utc: datetime) -> SeasonState:
        """Count games in windows, determine state, upsert cache, log."""
        recent_start = now_utc - timedelta(days=RECENT_FINAL_DAYS)
        near_end = now_utc + timedelta(days=NEAR_SCHEDULED_DAYS)
        post_end = now_utc + timedelta(days=POST_SCHEDULED_DAYS)
        sport_upper = (sport or "NFL").upper()

        # recent finals: start_time in [recent_start, now], status final
        r_final = await self._db.execute(
            select(func.count(Game.id))
            .where(Game.sport == sport_upper)
            .where(Game.start_time >= recent_start)
            .where(Game.start_time <= now_utc)
            .where(func.lower(Game.status) == "final")
        )
        recent_final_count = r_final.scalar() or 0

        # near scheduled: start_time in [now, near_end], status scheduled or null
        scheduled_cond = or_(Game.status.is_(None), func.lower(Game.status).in_(("scheduled", "status_scheduled")))
        r_near = await self._db.execute(
            select(func.count(Game.id))
            .where(Game.sport == sport_upper)
            .where(Game.start_time >= now_utc)
            .where(Game.start_time <= near_end)
            .where(scheduled_cond)
        )
        near_scheduled_count = r_near.scalar() or 0

        # post scheduled: start_time in [now, post_end], status scheduled or null
        r_post = await self._db.execute(
            select(func.count(Game.id))
            .where(Game.sport == sport_upper)
            .where(Game.start_time >= now_utc)
            .where(Game.start_time <= post_end)
            .where(scheduled_cond)
        )
        post_scheduled_count = r_post.scalar() or 0

        # Determine state: NFL postseason if week >= 19; else by counts
        if sport_upper == "NFL":
            nfl_week = get_current_nfl_week(now_utc.year if now_utc.month > 3 else now_utc.year - 1)
            if nfl_week is not None and nfl_week >= 19:
                state = SeasonState.POSTSEASON
            elif near_scheduled_count > 0:
                state = SeasonState.IN_SEASON
            elif post_scheduled_count > 0:
                state = SeasonState.PRESEASON
            else:
                state = SeasonState.OFF_SEASON
        else:
            if near_scheduled_count > 0:
                state = SeasonState.IN_SEASON
            elif post_scheduled_count > 0:
                state = SeasonState.PRESEASON
            else:
                state = SeasonState.OFF_SEASON

        await self._repo.upsert(
            sport=sport_upper,
            state=state.value,
            recent_final_count=recent_final_count,
            near_scheduled_count=near_scheduled_count,
            post_scheduled_count=post_scheduled_count,
            computed_at_utc=now_utc,
        )

        log_event(
            logger,
            "season_state.compute",
            sport=sport_upper,
            state=state.value,
            recent_final_count=recent_final_count,
            near_scheduled_count=near_scheduled_count,
            post_scheduled_count=post_scheduled_count,
        )
        return state
