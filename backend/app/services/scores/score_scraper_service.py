"""Score scraper service with multi-source fallback."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.models.parlay_feed_event import ParlayFeedEvent
from app.models.system_heartbeat import SystemHeartbeat
from app.services.scores.normalizer import ScoreNormalizer
from app.services.scores.sources.espn import ESPNScraper
from app.services.scores.sources.yahoo import YahooScraper

logger = logging.getLogger(__name__)


def backfill_start_time_if_missing(existing_game: Game, update) -> None:
    """Backfill existing_game.start_time from update only when existing is None (does not overwrite)."""
    if existing_game.start_time is None and getattr(update, "start_time", None) is not None:
        existing_game.start_time = update.start_time


class ScoreScraperService:
    """Service for scraping and updating game scores with multi-source fallback."""
    
    STALENESS_THRESHOLD_MINUTES = 5  # Mark as stale if LIVE game not updated in 5 minutes
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._normalizer = ScoreNormalizer()
        self._espn_scraper = ESPNScraper()
        self._yahoo_scraper = YahooScraper()
    
    async def close(self):
        """Close scraper sessions."""
        await self._espn_scraper.close()
        await self._yahoo_scraper.close()
    
    async def scrape_and_update_games(self, sport: str, window_days: int = 1) -> int:
        """Scrape and update games for a sport.
        
        Args:
            sport: Sport code (NFL, NBA, etc.)
            window_days: Number of days to look back/forward (default 1)
            
        Returns:
            Number of games updated
        """
        updated_count = 0
        yesterday = datetime.utcnow() - timedelta(days=window_days)
        tomorrow = datetime.utcnow() + timedelta(days=window_days)
        
        # Try ESPN first
        games_updated = await self._try_scrape_source(
            scraper=self._espn_scraper,
            sport=sport,
            start_date=yesterday,
            end_date=tomorrow,
        )
        
        if games_updated == 0:
            # Fallback to Yahoo
            logger.info(f"ESPN returned no games for {sport}, trying Yahoo...")
            games_updated = await self._try_scrape_source(
                scraper=self._yahoo_scraper,
                sport=sport,
                start_date=yesterday,
                end_date=tomorrow,
            )
        
        updated_count = games_updated
        
        # Mark stale games
        await self._mark_stale_games(sport)
        
        # Update heartbeat
        await self._update_heartbeat("scraper_worker", {"games_updated": updated_count, "sport": sport})
        
        return updated_count
    
    async def _try_scrape_source(
        self,
        scraper: ESPNScraper | YahooScraper,
        sport: str,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Try scraping from a source and update games."""
        updated_count = 0
        current_date = start_date
        
        while current_date <= end_date:
            try:
                game_updates = await scraper.fetch_scoreboard(sport, current_date)
                if game_updates is None:
                    game_updates = []

                for update in game_updates:
                    try:
                        updated = await self._upsert_game(update, sport)
                        if updated:
                            updated_count += 1
                    except Exception as e:
                        logger.error(f"Error upserting game {update.external_game_key}: {e}")
                        continue
                
                # Small delay between date requests
                import asyncio
                await asyncio.sleep(0.5)
            
            except Exception as e:
                logger.error(f"Error scraping {scraper.__class__.__name__} for {sport} on {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        return updated_count
    
    async def _upsert_game(self, update, sport: str) -> bool:
        """Upsert a game with score data."""
        try:
            # Try to find existing game by external_game_key first
            result = await self.db.execute(
                select(Game).where(
                    and_(
                        Game.external_game_key == update.external_game_key,
                        Game.sport == sport,
                    )
                )
            )
            existing_game = result.scalar_one_or_none()
            
            # If not found by external key, try to match by teams and date
            if not existing_game:
                # Normalize team names for matching
                home_norm = self._normalizer.normalize_team_name(update.home_team)
                away_norm = self._normalizer.normalize_team_name(update.away_team)
                
                # Find games with matching teams and start time within 1 hour
                time_window_start = update.start_time - timedelta(hours=1)
                time_window_end = update.start_time + timedelta(hours=1)
                
                result = await self.db.execute(
                    select(Game).where(
                        and_(
                            Game.sport == sport,
                            Game.start_time >= time_window_start,
                            Game.start_time <= time_window_end,
                        )
                    )
                )
                
                for game in result.scalars().all():
                    game_home_norm = self._normalizer.normalize_team_name(game.home_team)
                    game_away_norm = self._normalizer.normalize_team_name(game.away_team)
                    
                    if (game_home_norm == home_norm and game_away_norm == away_norm) or \
                       (game_home_norm == away_norm and game_away_norm == home_norm):
                        existing_game = game
                        break
            
            # Track status changes for feed events
            old_status = existing_game.status if existing_game else None
            new_status = update.status
            
            # Update or create game
            if existing_game:
                existing_game.home_score = update.home_score
                existing_game.away_score = update.away_score
                existing_game.status = update.status
                existing_game.period = update.period
                existing_game.clock = update.clock
                existing_game.last_scraped_at = datetime.utcnow()
                existing_game.data_source = update.data_source
                existing_game.is_stale = False

                backfill_start_time_if_missing(existing_game, update)

                if not existing_game.external_game_key:
                    existing_game.external_game_key = update.external_game_key
                
                await self.db.flush()
                
                # Create feed events for status changes
                await self._create_status_change_events(existing_game, old_status, new_status)
                
                return True
            else:
                # Create new game (shouldn't happen often, but handle it)
                new_game = Game(
                    external_game_id=f"{sport}_{update.external_game_key}",
                    external_game_key=update.external_game_key,
                    sport=sport,
                    home_team=update.home_team,
                    away_team=update.away_team,
                    start_time=update.start_time,
                    status=update.status,
                    home_score=update.home_score,
                    away_score=update.away_score,
                    period=update.period,
                    clock=update.clock,
                    last_scraped_at=datetime.utcnow(),
                    data_source=update.data_source,
                    is_stale=False,
                )
                self.db.add(new_game)
                await self.db.flush()
                
                # Create feed event for new game going live
                if new_status == "LIVE":
                    await self._create_game_live_event(new_game)
                
                return True
        
        except Exception as e:
            logger.error(f"Error in _upsert_game: {e}")
            return False
    
    async def _create_status_change_events(self, game: Game, old_status: Optional[str], new_status: str):
        """Create feed events when game status changes."""
        try:
            # SCHEDULED -> LIVE
            if old_status != "LIVE" and new_status == "LIVE":
                await self._create_game_live_event(game)
            
            # LIVE -> FINAL
            if old_status == "LIVE" and new_status == "FINAL":
                await self._create_game_final_event(game)
        
        except Exception as e:
            logger.error(f"Error creating status change events: {e}")
    
    async def _create_game_live_event(self, game: Game):
        """Create GAME_LIVE feed event."""
        try:
            summary = f"LIVE: {game.away_team} @ {game.home_team}"
            if game.home_score is not None and game.away_score is not None:
                summary = f"LIVE: {game.away_team} {game.away_score or 0}–{game.home_score or 0} {game.home_team}"
                if game.period:
                    summary += f" ({game.period})"
                if game.clock:
                    summary += f" {game.clock}"
            
            event = ParlayFeedEvent(
                event_type="GAME_LIVE",
                sport=game.sport,
                summary=summary,
                event_metadata={
                    "game_id": str(game.id),
                    "home_team": game.home_team,
                    "away_team": game.away_team,
                    "home_score": game.home_score,
                    "away_score": game.away_score,
                    "period": game.period,
                    "clock": game.clock,
                },
            )
            self.db.add(event)
            await self.db.flush()
        
        except Exception as e:
            logger.error(f"Error creating GAME_LIVE event: {e}")
    
    async def _create_game_final_event(self, game: Game):
        """Create GAME_FINAL feed event."""
        try:
            summary = f"FINAL: {game.away_team} {game.away_score or 0}–{game.home_score or 0} {game.home_team}"
            
            event = ParlayFeedEvent(
                event_type="GAME_FINAL",
                sport=game.sport,
                summary=summary,
                event_metadata={
                    "game_id": str(game.id),
                    "home_team": game.home_team,
                    "away_team": game.away_team,
                    "home_score": game.home_score,
                    "away_score": game.away_score,
                },
            )
            self.db.add(event)
            await self.db.flush()
        
        except Exception as e:
            logger.error(f"Error creating GAME_FINAL event: {e}")
    
    async def _mark_stale_games(self, sport: str):
        """Mark games as stale if LIVE but not updated recently."""
        try:
            threshold = datetime.utcnow() - timedelta(minutes=self.STALENESS_THRESHOLD_MINUTES)
            
            result = await self.db.execute(
                select(Game).where(
                    and_(
                        Game.sport == sport,
                        Game.status == "LIVE",
                        or_(
                            Game.last_scraped_at.is_(None),
                            Game.last_scraped_at < threshold,
                        ),
                    )
                )
            )
            
            stale_games = result.scalars().all()
            for game in stale_games:
                game.is_stale = True
            
            await self.db.flush()
        
        except Exception as e:
            logger.error(f"Error marking stale games: {e}")
    
    async def _update_heartbeat(self, worker_name: str, meta: dict):
        """Update system heartbeat."""
        try:
            result = await self.db.execute(
                select(SystemHeartbeat).where(SystemHeartbeat.name == worker_name)
            )
            heartbeat = result.scalar_one_or_none()
            
            if heartbeat:
                heartbeat.last_beat_at = datetime.utcnow()
                heartbeat.meta = meta
            else:
                heartbeat = SystemHeartbeat(
                    name=worker_name,
                    last_beat_at=datetime.utcnow(),
                    meta=meta,
                )
                self.db.add(heartbeat)
            
            await self.db.flush()
        
        except Exception as e:
            logger.error(f"Error updating heartbeat: {e}")
