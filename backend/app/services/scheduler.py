"""Background job scheduler using APScheduler"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from typing import Optional
import asyncio

from app.database.session import AsyncSessionLocal
from app.services.cache_manager import CacheManager
from app.services.parlay_tracker import ParlayTrackerService
from app.services.sports_config import list_supported_sports


class BackgroundScheduler:
    """Manages background jobs for the application"""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
    
    def start(self):
        """Start the scheduler"""
        if self.scheduler and self.scheduler.running:
            return
        
        self.scheduler = AsyncIOScheduler()
        
        # Schedule cache cleanup (daily at 2 AM)
        self.scheduler.add_job(
            self._cleanup_expired_cache,
            CronTrigger(hour=2, minute=0),
            id="cleanup_cache",
            name="Cleanup expired cache entries"
        )
        
        # Schedule parlay resolution (every 6 hours)
        self.scheduler.add_job(
            self._auto_resolve_parlays,
            IntervalTrigger(hours=6),
            id="resolve_parlays",
            name="Auto-resolve completed parlays"
        )
        
        # Schedule cache warmup (hourly for common requests)
        self.scheduler.add_job(
            self._warmup_cache,
            IntervalTrigger(hours=1),
            id="warmup_cache",
            name="Warmup cache for common parlay requests"
        )
        
        # Schedule games refresh for all supported sports (every 2 hours for fresh data)
        self.scheduler.add_job(
            self._refresh_games,
            IntervalTrigger(hours=2),
            id="refresh_games",
            name="Refresh games from API"
        )
        
        # Schedule cleanup of old games (daily at 3 AM)
        self.scheduler.add_job(
            self._cleanup_old_games,
            CronTrigger(hour=3, minute=0),
            id="cleanup_old_games",
            name="Cleanup old/completed games"
        )
        
        # Also run cleanup every 6 hours to keep database clean
        self.scheduler.add_job(
            self._cleanup_old_games,
            IntervalTrigger(hours=6),
            id="cleanup_old_games_interval",
            name="Cleanup old games (interval)"
        )
        
        self.scheduler.start()
        print("Background scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
            self.scheduler = None
            print("Background scheduler stopped")
    
    async def _cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        async with AsyncSessionLocal() as db:
            try:
                cache_manager = CacheManager(db)
                deleted_count = await cache_manager.clear_expired_cache()
                print(f"Cleaned up {deleted_count} expired cache entries")
            except Exception as e:
                print(f"Error cleaning up cache: {e}")
    
    async def _auto_resolve_parlays(self):
        """Automatically resolve parlays that have completed"""
        async with AsyncSessionLocal() as db:
            try:
                tracker = ParlayTrackerService(db)
                resolved_count = await tracker.auto_resolve_parlays()
                print(f"Auto-resolved {resolved_count} parlays")
            except Exception as e:
                print(f"Error auto-resolving parlays: {e}")
    
    async def _warmup_cache(self):
        """Pre-generate cache for common parlay requests"""
        async with AsyncSessionLocal() as db:
            try:
                # Common combinations to pre-cache
                common_requests = [
                    (5, "balanced"),
                    (3, "conservative"),
                    (7, "balanced"),
                    (10, "degen"),
                ]
                
                cache_manager = CacheManager(db)
                from app.services.parlay_builder import ParlayBuilderService
                
                for num_legs, risk_profile in common_requests:
                    # Check if cache exists and is fresh
                    cached = await cache_manager.get_cached_parlay(
                        num_legs=num_legs,
                        risk_profile=risk_profile,
                        max_age_hours=4
                    )
                    
                    if not cached:
                        # Generate and cache
                        try:
                            builder = ParlayBuilderService(db)
                            parlay_data = await builder.build_parlay(
                                num_legs=num_legs,
                                risk_profile=risk_profile
                            )
                            await cache_manager.set_cached_parlay(
                                num_legs=num_legs,
                                risk_profile=risk_profile,
                                parlay_data=parlay_data,
                                ttl_hours=6
                            )
                            print(f"Warmed up cache for {num_legs}-leg {risk_profile} parlay")
                        except Exception as e:
                            print(f"Error warming up cache for {num_legs}-leg {risk_profile}: {e}")
            except Exception as e:
                print(f"Error in cache warmup: {e}")
    
    async def _refresh_games(self):
        """Refresh games in the background for all supported sports."""
        async with AsyncSessionLocal() as db:
            try:
                from app.services.odds_fetcher import OddsFetcherService
                fetcher = OddsFetcherService(db)
                for config in list_supported_sports():
                    try:
                        games = await fetcher.get_or_fetch_games(config.slug, force_refresh=True)
                        print(f"[SCHEDULER] Refreshed {len(games)} {config.display_name} games")
                    except Exception as sport_error:
                        print(f"[SCHEDULER] Error refreshing {config.display_name} games: {sport_error}")
            except Exception as e:
                print(f"[SCHEDULER] Error refreshing games: {e}")
    
    async def _cleanup_old_games(self):
        """Remove old and completed games from the database."""
        from datetime import datetime, timedelta
        from sqlalchemy import delete, and_
        from app.models.game import Game
        
        async with AsyncSessionLocal() as db:
            try:
                # Remove games that are more than 48 hours old and completed
                cutoff_time = datetime.utcnow() - timedelta(hours=48)
                
                # Delete old completed games
                result = await db.execute(
                    delete(Game).where(
                        and_(
                            Game.start_time < cutoff_time,
                            Game.status.in_(["completed", "final", "closed"])
                        )
                    )
                )
                deleted_completed = result.rowcount
                
                # Also delete games that are more than 7 days old regardless of status
                old_cutoff = datetime.utcnow() - timedelta(days=7)
                result2 = await db.execute(
                    delete(Game).where(Game.start_time < old_cutoff)
                )
                deleted_old = result2.rowcount
                
                await db.commit()
                total_deleted = deleted_completed + deleted_old
                print(f"[SCHEDULER] Cleaned up {total_deleted} old games ({deleted_completed} completed, {deleted_old} old)")
            except Exception as e:
                await db.rollback()
                print(f"[SCHEDULER] Error cleaning up old games: {e}")
    
    async def _initial_refresh(self):
        """Run initial refresh on startup if games are stale."""
        import asyncio
        # Wait 10 seconds after startup to let database and everything initialize
        await asyncio.sleep(10)
        
        try:
            async with AsyncSessionLocal() as db:
                try:
                    from datetime import datetime, timedelta
                    from sqlalchemy import select, func
                    from app.models.game import Game
                    
                    # Check if we have recent games (within last 12 hours)
                    cutoff = datetime.utcnow() - timedelta(hours=12)
                    result = await db.execute(
                        select(func.count(Game.id)).where(Game.start_time >= cutoff)
                    )
                    recent_count = result.scalar() or 0
                    
                    if recent_count == 0:
                        print("[SCHEDULER] No recent games found, running initial refresh...")
                        # Use a fresh session for the refresh
                        await self._refresh_games()
                    else:
                        print(f"[SCHEDULER] Found {recent_count} recent games, skipping initial refresh")
                except Exception as e:
                    print(f"[SCHEDULER] Error in initial refresh check: {e}")
                    import traceback
                    traceback.print_exc()
        except Exception as outer_error:
            print(f"[SCHEDULER] Error creating session for initial refresh: {outer_error}")
            import traceback
            traceback.print_exc()


# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler

