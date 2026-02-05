"""
Central sport availability resolver for parlay generation and API behavior.
Detects out-of-season sports to prevent AI parlay generation and empty-game errors.
IN_SEASON, PRESEASON, POSTSEASON → available; OFF_SEASON → blocked unless SPORT_FORCE_AVAILABLE.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import SeasonState
from app.services.season_state_service import SeasonStateService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SportAvailability:
    """Result of checking if a sport is available for parlay generation."""
    available: bool
    state: str
    message: str


class SportAvailabilityResolver:
    """
    Resolves whether a sport is in season and available for AI parlay generation.
    Ensures API calls are skipped for inactive sports and user-safe messaging is returned.
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._season_service = SeasonStateService(db)

    async def resolve(self, sport: str) -> SportAvailability:
        """
        Check if the sport is available for parlay generation (in season or preseason/postseason).
        OFF_SEASON → not available; IN_SEASON, PRESEASON, POSTSEASON → available.
        """
        sport_upper = (sport or "").strip().upper()
        if not sport_upper:
            return SportAvailability(
                available=False,
                state="unknown",
                message="No sport specified.",
            )
        # Safety override: force available for listed sports (e.g. MLB spring training, emergency)
        force_list = getattr(settings, "sport_force_available", None) or os.getenv("SPORT_FORCE_AVAILABLE") or ""
        if force_list and sport_upper in [s.strip().upper() for s in force_list.split(",") if s.strip()]:
            logger.info("SportAvailabilityResolver: %s force-available via SPORT_FORCE_AVAILABLE", sport_upper)
            return SportAvailability(available=True, state="force_available", message="")
        try:
            state = await self._season_service.get_season_state(sport_upper, use_cache=True)
        except Exception as e:
            logger.warning(
                "SportAvailabilityResolver: failed to get season state for %s: %s",
                sport_upper,
                e,
                exc_info=False,
            )
            # On error, allow attempt (avoid blocking on cache/DB issues)
            return SportAvailability(
                available=True,
                state="unknown",
                message="",
            )
        if state == SeasonState.OFF_SEASON:
            logger.info(
                "SportAvailabilityResolver: sport %s is OFF_SEASON; skipping parlay generation intentionally",
                sport_upper,
            )
            return SportAvailability(
                available=False,
                state=state.value,
                message=(
                    f"{sport_upper} is currently off season. "
                    "Parlay generation is available when games are in season. "
                    "Try another sport or check back when the season starts."
                ),
            )
        return SportAvailability(
            available=True,
            state=state.value,
            message="",
        )
