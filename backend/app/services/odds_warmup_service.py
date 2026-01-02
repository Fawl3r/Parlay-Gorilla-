from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.odds_fetcher import OddsFetcherService
from app.services.sports_config import get_sport_config

logger = logging.getLogger(__name__)


class OddsWarmupService:
    """
    Best-effort odds warmup used by parlay generation.

    Why:
    - Parlay generation requires games + odds in the DB.
    - If the scheduler hasn't populated the DB yet (or a cold start cleared caches),
      we can fetch/store odds on-demand once and retry candidate generation.

    Safety:
    - Disabled in tests to keep the suite offline/deterministic.
    - In production, `OddsFetcherService` is already protected by distributed caching
      and rate limiting to avoid credit drain.
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._fetcher = OddsFetcherService(db)

    async def warm_sport(self, sport_identifier: str) -> bool:
        if settings.environment == "testing":
            return False

        identifier = str(sport_identifier or "").strip()
        if not identifier:
            return False

        try:
            config = get_sport_config(identifier)
        except Exception as exc:
            logger.warning("Odds warmup skipped (unsupported sport=%s): %s", identifier, exc)
            return False

        try:
            games = await self._fetcher.get_or_fetch_games(config.slug, force_refresh=False)
            logger.info("Odds warmup completed for %s: %s games", config.code, len(games))
            return True
        except Exception as exc:
            logger.warning("Odds warmup failed for %s: %s", config.code, exc)
            return False


