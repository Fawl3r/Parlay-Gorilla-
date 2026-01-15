"""Background job scheduler using APScheduler"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from typing import Optional
import asyncio
import logging

from app.database.session import AsyncSessionLocal
from app.services.cache_manager import CacheManager
from app.services.parlay_tracker import ParlayTrackerService
from app.services.sports_config import list_supported_sports
from app.services.verification_service import VerificationService
from app.services.scheduler_leader_lock import SchedulerLeaderLock
from app.services.scheduler_jobs.ats_ou_trends_job import AtsOuTrendsJob
from app.services.scheduler_jobs.game_results_sync_job import GameResultsSyncJob
from app.services.scheduler_jobs.saved_parlay_resolution_job import SavedParlayResolutionJob
from app.services.scheduler_jobs.arcade_points_award_job import ArcadePointsAwardJob

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """Manages background jobs for the application"""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._leader_lock: Optional[SchedulerLeaderLock] = None
    
    async def start(self):
        """Start the scheduler"""
        if self.scheduler and self.scheduler.running:
            return

        # Leader election (Redis). Prevents multiple replicas / dev reloads from
        # running duplicate background jobs.
        self._leader_lock = SchedulerLeaderLock()
        if self._leader_lock.is_available():
            acquired = await self._leader_lock.try_acquire()
            if not acquired:
                print("[SCHEDULER] Skipping start: another instance is leader")
                return
            print("[SCHEDULER] Leader lock acquired")
        else:
            # In dev/test, running schedulers without Redis can easily burn credits
            # due to reloads. Prefer explicit enabling via proper infra.
            from app.core.config import settings

            if settings.environment != "production":
                print("[SCHEDULER] Redis not configured; skipping background scheduler in non-production")
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
        
        # Schedule analysis generation for upcoming games (daily at 6 AM)
        self.scheduler.add_job(
            self._generate_upcoming_analyses,
            CronTrigger(hour=6, minute=0),
            id="generate_analyses",
            name="Generate analyses for upcoming games"
        )
        
        # Schedule cleanup of expired analyses (daily at 4 AM)
        self.scheduler.add_job(
            self._cleanup_expired_analyses,
            CronTrigger(hour=4, minute=0),
            id="cleanup_expired_analyses",
            name="Cleanup expired analyses"
        )
        
        # Schedule cleanup of expired verification tokens (daily at 5 AM)
        self.scheduler.add_job(
            self._cleanup_expired_tokens,
            CronTrigger(hour=5, minute=0),
            id="cleanup_expired_tokens",
            name="Cleanup expired verification tokens"
        )
        
        # Schedule odds sync (every 24 hours; also triggered when analytics update)
        from app.core.config import settings
        if settings.enable_background_jobs:
            self.scheduler.add_job(
                self._sync_odds,
                IntervalTrigger(minutes=settings.odds_sync_interval_minutes),
                id="sync_odds",
                name="Sync odds from The Odds API (24h interval)"
            )
            
            # Schedule scraper worker (daily at 1 AM to update injuries and stats)
            # This runs the full scrape: team stats, ATS/O/U trends, and injuries
            self.scheduler.add_job(
                self._run_scraper,
                CronTrigger(hour=1, minute=0),
                id="run_scraper",
                name="Scrape team stats and injuries (daily at 1 AM)"
            )
            
            # Schedule ATS/O/U trend calculation (daily at 1 AM, after games complete)
            # Note: This is also included in the scraper worker, but kept separate for redundancy
            self.scheduler.add_job(
                self._calculate_ats_ou_trends,
                CronTrigger(hour=1, minute=0),
                id="calculate_ats_ou",
                name="Calculate ATS and Over/Under trends"
            )
            
            # Schedule AI model trainer (daily at 2 AM)
            self.scheduler.add_job(
                self._train_ai_model,
                CronTrigger(hour=2, minute=0),
                id="train_ai_model",
                name="Train AI model on recent results"
            )
            
            # Schedule subscription expiration check (daily at 3:30 AM)
            self.scheduler.add_job(
                self._check_expired_subscriptions,
                CronTrigger(hour=3, minute=30),
                id="check_expired_subscriptions",
                name="Check and expire subscriptions past period end"
            )
            
            # Schedule affiliate commission processing (daily at 4:00 AM)
            # Moves PENDING commissions to READY status when hold period expires
            self.scheduler.add_job(
                self._process_ready_commissions,
                CronTrigger(hour=4, minute=0),
                id="process_ready_commissions",
                name="Process affiliate commissions ready for payout"
            )
            
            # Schedule game results sync from ESPN (every 2 hours)
            self.scheduler.add_job(
                self._sync_game_results,
                IntervalTrigger(hours=2),
                id="sync_game_results",
                name="Sync completed game results from ESPN"
            )
            
            # Schedule saved parlay resolution (every 6 hours)
            self.scheduler.add_job(
                self._resolve_saved_parlays,
                IntervalTrigger(hours=6),
                id="resolve_saved_parlays",
                name="Auto-resolve saved parlay outcomes"
            )
            
            # Schedule arcade points award (every 3 hours)
            self.scheduler.add_job(
                self._award_arcade_points,
                IntervalTrigger(hours=3),
                id="award_arcade_points",
                name="Award arcade points for verified wins"
            )
        
        self.scheduler.start()
        print("Background scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
            self.scheduler = None
            print("Background scheduler stopped")

        if self._leader_lock is not None:
            try:
                await self._leader_lock.release()
            except Exception:
                pass
            self._leader_lock = None
    
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
                        # Conserve credits: do not force API refresh in the background.
                        # OddsSyncWorker already keeps odds updated with rate limiting.
                        games = await fetcher.get_or_fetch_games(config.slug, force_refresh=False)
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
    
    async def _generate_upcoming_analyses(self):
        """Generate analyses for upcoming games"""
        from datetime import datetime, timedelta
        from sqlalchemy import or_, select
        from app.models.game import Game
        from app.models.game_analysis import GameAnalysis
        from app.services.sports_config import list_supported_sports
        from app.services.analysis import AnalysisOrchestratorService
        from app.core.config import settings
        
        async with AsyncSessionLocal() as db:
            try:
                now = datetime.utcnow()
                future_cutoff = now + timedelta(days=7)  # Generate for next 7 days
                
                generated_count = 0
                skipped_count = 0
                
                for config in list_supported_sports():
                    # Get upcoming games without analyses OR with expired analyses.
                    result = await db.execute(
                        select(Game, GameAnalysis)
                        .outerjoin(
                            GameAnalysis,
                            (Game.id == GameAnalysis.game_id) & (GameAnalysis.league == config.code),
                        )
                        .where(
                            Game.sport == config.code,
                            Game.start_time >= now,
                            Game.start_time <= future_cutoff,
                            # Skip placeholder games (common during postseason before matchups are set).
                            Game.home_team != "TBD",
                            Game.away_team != "TBD",
                            ~Game.home_team.ilike("tbd"),
                            ~Game.away_team.ilike("tbd"),
                            or_(
                                GameAnalysis.id.is_(None),
                                (GameAnalysis.expires_at.is_not(None) & (GameAnalysis.expires_at <= now)),
                            ),
                        )
                        .limit(20)  # Limit to 20 per sport to avoid rate limits
                    )
                    orchestrator = AnalysisOrchestratorService(db)
                    
                    for game, analysis in result.all():
                        try:
                            is_expired = bool(analysis is not None and analysis.expires_at is not None and analysis.expires_at <= now)
                            await orchestrator.ensure_core_for_game(
                                game=game,
                                core_timeout_seconds=settings.analysis_core_timeout_seconds,
                                force_regenerate=is_expired,
                            )
                            generated_count += 1
                        except Exception as e:
                            print(f"[SCHEDULER] Error generating analysis for game {game.id}: {e}")
                            skipped_count += 1
                            continue

                print(f"[SCHEDULER] Generated {generated_count} analyses, skipped {skipped_count}")

                # Best-effort: send a single Web Push notification for the batch.
                try:
                    if generated_count > 0:
                        from app.services.notifications.analysis_generation_notifier import AnalysisGenerationNotifier
                        await AnalysisGenerationNotifier(db).notify_batch(generated_count=generated_count)
                except Exception as notify_exc:
                    print(f"[SCHEDULER] Web push notify failed: {notify_exc}")
                
            except Exception as e:
                await db.rollback()
                print(f"[SCHEDULER] Error generating analyses: {e}")
                import traceback
                traceback.print_exc()
    
    async def _cleanup_expired_analyses(self):
        """Clean up expired analyses"""
        from datetime import datetime, timedelta
        from sqlalchemy import delete
        from app.models.game_analysis import GameAnalysis
        
        async with AsyncSessionLocal() as db:
            try:
                now = datetime.utcnow()
                
                # Delete analyses that expired more than 24 hours ago
                result = await db.execute(
                    delete(GameAnalysis).where(
                        GameAnalysis.expires_at < now - timedelta(hours=24)
                    )
                )
                deleted_count = result.rowcount
                
                await db.commit()
                print(f"[SCHEDULER] Cleaned up {deleted_count} expired analyses")
                
            except Exception as e:
                await db.rollback()
                print(f"[SCHEDULER] Error cleaning up expired analyses: {e}")
    
    async def _cleanup_expired_tokens(self):
        """Clean up expired verification tokens"""
        async with AsyncSessionLocal() as db:
            try:
                verification_service = VerificationService(db)
                deleted_count = await verification_service.cleanup_expired_tokens()
                if deleted_count > 0:
                    logger.info(f"[SCHEDULER] Cleaned up {deleted_count} expired verification tokens")
            except Exception as e:
                logger.error(f"[SCHEDULER] Error cleaning up expired tokens: {e}")
    
    async def _sync_odds(self):
        """Sync odds from The Odds API"""
        try:
            from app.workers.odds_sync_worker import OddsSyncWorker
            worker = OddsSyncWorker()
            await worker.sync_all_sports()
        except Exception as e:
            print(f"[SCHEDULER] Error syncing odds: {e}")
    
    async def trigger_odds_sync(self):
        """Trigger odds sync on demand (e.g., when analytics update)"""
        if self.scheduler and self.scheduler.running:
            # Run the sync job immediately
            await self._sync_odds()
        else:
            logger.warning("[SCHEDULER] Cannot trigger odds sync: scheduler not running")
    
    async def _run_scraper(self):
        """Run scraper worker for team stats"""
        try:
            from app.workers.scraper_worker import ScraperWorker
            worker = ScraperWorker()
            await worker.run_full_scrape()
        except Exception as e:
            print(f"[SCHEDULER] Error running scraper: {e}")
    
    async def _train_ai_model(self):
        """Train AI model on recent results"""
        try:
            from app.workers.ai_model_trainer import AIModelTrainer
            trainer = AIModelTrainer()
            await trainer.analyze_performance()
            await trainer.train_on_game_results()
        except Exception as e:
            print(f"[SCHEDULER] Error training AI model: {e}")
    
    async def _calculate_ats_ou_trends(self):
        """Calculate ATS and Over/Under trends for all sports"""
        await AtsOuTrendsJob().run()
    
    async def _sync_game_results(self):
        """Sync completed game results from ESPN scoreboard"""
        await GameResultsSyncJob().run()
    
    async def _resolve_saved_parlays(self):
        """Auto-resolve saved parlay outcomes"""
        await SavedParlayResolutionJob().run()
    
    async def _award_arcade_points(self):
        """Award arcade points for eligible verified wins"""
        await ArcadePointsAwardJob().run()
    
    async def _check_expired_subscriptions(self):
        """Check and expire subscriptions past their period end"""
        from app.services.payment_service import PaymentService
        
        async with AsyncSessionLocal() as db:
            try:
                payment_service = PaymentService(db)
                expired_count = await payment_service.check_expired_subscriptions()
                if expired_count > 0:
                    print(f"[SCHEDULER] Expired {expired_count} subscriptions")
            except Exception as e:
                print(f"[SCHEDULER] Error checking expired subscriptions: {e}")
    
    async def _process_ready_commissions(self):
        """Process affiliate commissions that are ready for payout"""
        async with AsyncSessionLocal() as db:
            try:
                from app.services.affiliate_service import AffiliateService
                service = AffiliateService(db)
                processed = await service.process_ready_commissions()
                print(f"[SCHEDULER] Processed {processed} commissions to READY status")
            except Exception as e:
                print(f"[SCHEDULER] Error processing ready commissions: {e}")
                import traceback
                traceback.print_exc()
    
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
