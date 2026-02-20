"""
Season state service: single source of truth for IN_SEASON / POSTSEASON / PRESEASON / OFF_SEASON.

Delegates to sport_state_service.get_sport_state so API listing, parlay/candidate window,
and ops use the same DB-driven logic. Caches result with TTL for performance.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_logger import log_event
from app.models.enums import SeasonState
from app.repositories.sport_season_state_repository import SportSeasonStateRepository
from app.services.sport_state_service import SportState, get_sport_state

logger = logging.getLogger(__name__)

SEASON_STATE_TTL_SECONDS = 3600  # 1 hour

_SPORT_STATE_TO_SEASON_STATE = {
    SportState.IN_SEASON: SeasonState.IN_SEASON,
    SportState.POSTSEASON: SeasonState.POSTSEASON,
    SportState.PRESEASON: SeasonState.PRESEASON,
    SportState.OFFSEASON: SeasonState.OFF_SEASON,
    SportState.IN_BREAK: SeasonState.OFF_SEASON,  # no games soon; use OFF_SEASON lookahead
}


class SeasonStateService:
    """Compute and cache season state per sport (unified with get_sport_state)."""

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
        Uses cached row if fresh (within TTL); otherwise delegates to get_sport_state and caches.
        """
        now = now_utc or datetime.now(timezone.utc)
        sport_upper = (sport or "").strip().upper()
        if not sport_upper:
            return SeasonState.OFF_SEASON

        if use_cache:
            row = await self._repo.get(sport_upper)
            if row and row.computed_at_utc is not None:
                computed = row.computed_at_utc
                if computed.tzinfo is None:
                    computed = computed.replace(tzinfo=timezone.utc)
                age = (now - computed).total_seconds()
            else:
                age = float("inf")
            if row and age < SEASON_STATE_TTL_SECONDS:
                return SeasonState(row.state)
        return await self._compute_and_cache(sport_upper, now)

    async def _compute_and_cache(self, sport: str, now_utc: datetime) -> SeasonState:
        """Get state from get_sport_state (single source of truth), map to SeasonState, cache."""
        result = await get_sport_state(self._db, sport, now=now_utc)
        sport_state_str = result.get("sport_state") or "OFFSEASON"
        try:
            sport_state = SportState(sport_state_str)
        except ValueError:
            sport_state = SportState.OFFSEASON
        state = _SPORT_STATE_TO_SEASON_STATE.get(sport_state, SeasonState.OFF_SEASON)
        upcoming = result.get("upcoming_soon_count") or 0
        recent = result.get("recent_count") or 0
        # post_scheduled not in get_sport_state; use 0 for cache shape
        await self._repo.upsert(
            sport=sport,
            state=state.value,
            recent_final_count=recent,
            near_scheduled_count=upcoming,
            post_scheduled_count=0,
            computed_at_utc=now_utc,
        )
        log_event(
            logger,
            "season_state.compute",
            sport=sport,
            state=state.value,
            recent_final_count=recent,
            near_scheduled_count=upcoming,
            post_scheduled_count=0,
        )
        return state
