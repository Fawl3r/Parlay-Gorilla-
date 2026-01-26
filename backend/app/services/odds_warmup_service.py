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
        """
        Warm up odds for a sport by fetching games and odds from the API.
        
        Returns:
            True if warmup succeeded and games were fetched, False otherwise
        """
        if settings.environment == "testing":
            logger.debug("Odds warmup skipped (testing environment)")
            return False

        identifier = str(sport_identifier or "").strip()
        if not identifier:
            logger.warning("Odds warmup skipped: empty sport identifier")
            return False

        logger.info(f"Starting odds warmup for sport: {identifier}")
        
        try:
            config = get_sport_config(identifier)
            logger.info(f"Sport config resolved: {config.code} (slug: {config.slug})")
        except Exception as exc:
            logger.warning(f"Odds warmup skipped (unsupported sport={identifier}): {exc}")
            return False

        try:
            logger.info(f"Fetching games for {config.code} (slug: {config.slug})...")
            games = await self._fetcher.get_or_fetch_games(config.slug, force_refresh=False)
            
            if games:
                # Count games with markets/odds
                games_with_odds = sum(1 for g in games if getattr(g, "markets", None) and len(getattr(g, "markets", [])) > 0)
                total_markets = sum(len(getattr(g, "markets", []) or []) for g in games)
                logger.info(
                    f"Odds warmup completed for {config.code}: {len(games)} games fetched, "
                    f"{games_with_odds} games with markets, {total_markets} total markets"
                )
            else:
                logger.warning(f"Odds warmup completed for {config.code} but no games were returned")
            
            return len(games) > 0
        except Exception as exc:
            logger.error(f"Odds warmup failed for {config.code}: {exc}", exc_info=True)
            return False


