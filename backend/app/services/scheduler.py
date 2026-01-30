"""Background job scheduler using APScheduler"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from typing import Optional, Callable, Any
import asyncio
import logging
import traceback
from functools import wraps

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
from app.services.scheduler_jobs.apisports_refresh_job import ApisportsRefreshJob

logger = logging.getLogger(__name__)


def crash_proof_job(job_name: str, max_retries: int = 3, backoff_base: float = 2.0):
    """
    Decorator to make background jobs crash-proof.
    
    Wraps job functions with:
    - Try/except that catches all exceptions
    - Exponential backoff for retries
    - Never allows job to crash the app
    - Logs errors with job_name for debugging
    
    Args:
        job_name: Name of the job for logging
        max_retries: Maximum number of retries (default: 3)
        backoff_base: Base for exponential backoff in seconds (default: 2.0)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            job_id = f"{job_name}_{id(func)}"
            retry_count = 0
            
            while retry_count <= max_retries:
                try:
                    # Execute the job
                    result = await func(*args, **kwargs)
                    if retry_count > 0:
                        logger.info(f"[JOB] {job_name} succeeded after {retry_count} retries [job_id={job_id}]")
                    return result
                except Exception as e:
                    retry_count += 1
                    error_msg = str(e)[:200]  # Truncate long errors
                    
                    if retry_count <= max_retries:
                        # Exponential backoff
                        wait_time = backoff_base ** (retry_count - 1)
                        logger.warning(
                            f"[JOB] {job_name} failed (attempt {retry_count}/{max_retries + 1}), "
                            f"retrying in {wait_time:.1f}s [job_id={job_id}]: {error_msg}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        # Max retries exceeded - log error but don't crash
                        logger.error(
                            f"[JOB] {job_name} failed after {max_retries} retries [job_id={job_id}]: {error_msg}",
                            exc_info=True
                        )
                        print(f"[JOB] {job_name} failed permanently [job_id={job_id}]: {error_msg}")
                        print(traceback.format_exc())
                        # Return None to indicate failure but don't raise
                        return None
            
            return None
        return wrapper
    return decorator


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

            # API-Sports refresh (quota-safe: 100/day; every 60 min during active hours)
            self.scheduler.add_job(
                self._run_apisports_refresh,
                IntervalTrigger(minutes=60),
                id="apisports_refresh",
                name="Refresh API-Sports fixtures and standings (quota-safe)"
            )
        
        self.scheduler.start()
        print("Background scheduler started")
        
        # Start background workers (they run their own loops)
        try:
            await self._start_score_scraper_worker()
            await self._start_settlement_worker()
            await self._start_heartbeat_worker()
        except Exception as e:
            print(f"[SCHEDULER] Error starting workers: {e}")
    
    async def stop(self):
        """Stop the scheduler"""
        # Stop background workers
        try:
            from app.workers.score_scraper_worker import stop_score_scraper_worker
            from app.workers.settlement_worker import stop_settlement_worker
            from app.workers.heartbeat_worker import stop_heartbeat_worker
            
            await stop_score_scraper_worker()
            await stop_settlement_worker()
            await stop_heartbeat_worker()
        except Exception as e:
            print(f"[SCHEDULER] Error stopping workers: {e}")
        
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
    
    @crash_proof_job("cleanup_expired_cache")
    async def _cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        async with AsyncSessionLocal() as db:
            cache_manager = CacheManager(db)
            deleted_count = await cache_manager.clear_expired_cache()
            print(f"Cleaned up {deleted_count} expired cache entries")
    
    @crash_proof_job("auto_resolve_parlays")
    async def _auto_resolve_parlays(self):
        """Automatically resolve parlays that have completed"""
        from app.core.config import settings
        if not settings.feature_settlement:
            logger.info("[JOB] auto_resolve_parlays skipped (FEATURE_SETTLEMENT disabled)")
            return
        
        async with AsyncSessionLocal() as db:
            tracker = ParlayTrackerService(db)
            resolved_count = await tracker.auto_resolve_parlays()
            print(f"Auto-resolved {resolved_count} parlays")
    
    @crash_proof_job("warmup_cache")
    async def _warmup_cache(self):
        """Pre-generate cache for common parlay requests"""
        async with AsyncSessionLocal() as db:
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
                            logger.warning(f"Error warming up cache for {num_legs}-leg {risk_profile}: {e}")
                            continue
    
    @crash_proof_job("refresh_games")
    async def _refresh_games(self):
        """Refresh games in the background for all supported sports."""
        async with AsyncSessionLocal() as db:
            from app.services.odds_fetcher import OddsFetcherService
            fetcher = OddsFetcherService(db)
            for config in list_supported_sports():
                try:
                    # Conserve credits: do not force API refresh in the background.
                    # OddsSyncWorker already keeps odds updated with rate limiting.
                    games = await fetcher.get_or_fetch_games(config.slug, force_refresh=False)
                    print(f"[SCHEDULER] Refreshed {len(games)} {config.display_name} games")
                except Exception as sport_error:
                    logger.warning(f"[SCHEDULER] Error refreshing {config.display_name} games: {sport_error}")
                    continue
    
    @crash_proof_job("cleanup_old_games")
    async def _cleanup_old_games(self):
        """Remove old and completed games from the database."""
        from datetime import datetime, timedelta
        from sqlalchemy import delete, and_
        from app.models.game import Game
        
        async with AsyncSessionLocal() as db:
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
    
    @crash_proof_job("generate_upcoming_analyses")
    async def _generate_upcoming_analyses(self):
        """Generate analyses for upcoming games (missing, expired, or missing core fields like confidence_breakdown)."""
        from datetime import datetime, timedelta
        from sqlalchemy import or_, select, func
        from app.models.game import Game
        from app.models.game_analysis import GameAnalysis
        from app.services.sports_config import list_supported_sports
        from app.services.analysis import AnalysisOrchestratorService
        from app.services.analysis.analysis_contract import is_core_ready
        from app.core.config import settings

        async with AsyncSessionLocal() as db:
                now = datetime.utcnow()
                future_cutoff = now + timedelta(days=7)  # Generate for next 7 days

                generated_count = 0
                skipped_count = 0
                orchestrator = AnalysisOrchestratorService(db)

                for config in list_supported_sports():
                    # Game IDs in window (same as below for backfill)
                    game_subquery = (
                        select(Game.id)
                        .where(Game.sport == config.code)
                        .where(Game.start_time >= now)
                        .where(Game.start_time <= future_cutoff)
                        .where(Game.home_team != "TBD")
                        .where(Game.away_team != "TBD")
                        .where(~Game.home_team.ilike("tbd"))
                        .where(~Game.away_team.ilike("tbd"))
                        .limit(20)
                    ).subquery()

                    # Pass 1: No analysis or expired -> ensure_core (force if expired)
                    result = await db.execute(
                        select(Game, GameAnalysis)
                        .select_from(Game)
                        .outerjoin(
                            GameAnalysis,
                            (Game.id == GameAnalysis.game_id) & (GameAnalysis.league == config.code),
                        )
                        .where(Game.id.in_(select(game_subquery.c.id)))
                        .where(
                            or_(
                                GameAnalysis.id.is_(None),
                                (GameAnalysis.expires_at.is_not(None) & (GameAnalysis.expires_at <= now)),
                            ),
                        )
                    )
                    for game, analysis in result.all():
                        try:
                            is_expired = bool(
                                analysis is not None
                                and analysis.expires_at is not None
                                and analysis.expires_at <= now
                            )
                            await orchestrator.ensure_core_for_game(
                                game=game,
                                core_timeout_seconds=settings.analysis_core_timeout_seconds,
                                force_regenerate=is_expired,
                            )
                            generated_count += 1
                        except Exception as e:
                            logger.warning(f"[SCHEDULER] Error generating analysis for game {game.id}: {e}")
                            skipped_count += 1
                            continue

                    # Pass 2: Non-expired analyses missing confidence_breakdown (or other core fields) -> regenerate
                    latest_per_game = (
                        select(
                            GameAnalysis.game_id,
                            GameAnalysis.league,
                            func.max(GameAnalysis.version).label("max_ver"),
                        )
                        .where(GameAnalysis.game_id.in_(select(game_subquery.c.id)))
                        .group_by(GameAnalysis.game_id, GameAnalysis.league)
                        .subquery()
                    )
                    backfill_result = await db.execute(
                        select(Game, GameAnalysis)
                        .select_from(Game)
                        .join(
                            GameAnalysis,
                            (Game.id == GameAnalysis.game_id) & (Game.sport == GameAnalysis.league),
                        )
                        .join(
                            latest_per_game,
                            (GameAnalysis.game_id == latest_per_game.c.game_id)
                            & (GameAnalysis.league == latest_per_game.c.league)
                            & (GameAnalysis.version == latest_per_game.c.max_ver),
                        )
                        .where(Game.id.in_(select(game_subquery.c.id)))
                        .where(
                            or_(
                                GameAnalysis.expires_at.is_(None),
                                (GameAnalysis.expires_at > now),
                            ),
                        )
                    )
                    for game, analysis in backfill_result.all():
                        if analysis.analysis_content and is_core_ready(analysis.analysis_content):
                            continue
                        try:
                            await orchestrator.ensure_core_for_game(
                                game=game,
                                core_timeout_seconds=settings.analysis_core_timeout_seconds,
                                force_regenerate=True,
                            )
                            generated_count += 1
                        except Exception as e:
                            logger.warning(
                                f"[SCHEDULER] Error backfilling analysis for game {game.id}: {e}"
                            )
                            skipped_count += 1
                            continue

                print(f"[SCHEDULER] Generated {generated_count} analyses, skipped {skipped_count}")

                # Best-effort: send a single Web Push notification for the batch.
                try:
                    if generated_count > 0:
                        from app.services.notifications.analysis_generation_notifier import AnalysisGenerationNotifier
                        await AnalysisGenerationNotifier(db).notify_batch(generated_count=generated_count)
                except Exception as notify_exc:
                    logger.warning(f"[SCHEDULER] Web push notify failed: {notify_exc}")
    
    @crash_proof_job("cleanup_expired_analyses")
    async def _cleanup_expired_analyses(self):
        """Clean up expired analyses"""
        from datetime import datetime, timedelta
        from sqlalchemy import delete
        from app.models.game_analysis import GameAnalysis
        
        async with AsyncSessionLocal() as db:
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
    
    @crash_proof_job("cleanup_expired_tokens")
    async def _cleanup_expired_tokens(self):
        """Clean up expired verification tokens"""
        async with AsyncSessionLocal() as db:
            verification_service = VerificationService(db)
            deleted_count = await verification_service.cleanup_expired_tokens()
            if deleted_count > 0:
                logger.info(f"[SCHEDULER] Cleaned up {deleted_count} expired verification tokens")
    
    @crash_proof_job("sync_odds")
    async def _sync_odds(self):
        """Sync odds from The Odds API"""
        from app.workers.odds_sync_worker import OddsSyncWorker
        worker = OddsSyncWorker()
        await worker.sync_all_sports()
    
    async def trigger_odds_sync(self):
        """Trigger odds sync on demand (e.g., when analytics update)"""
        if self.scheduler and self.scheduler.running:
            # Run the sync job immediately
            await self._sync_odds()
        else:
            logger.warning("[SCHEDULER] Cannot trigger odds sync: scheduler not running")
    
    @crash_proof_job("run_scraper")
    async def _run_scraper(self):
        """Run scraper worker for team stats"""
        from app.workers.scraper_worker import ScraperWorker
        worker = ScraperWorker()
        await worker.run_full_scrape()
    
    @crash_proof_job("train_ai_model")
    async def _train_ai_model(self):
        """Train AI model on recent results"""
        from app.workers.ai_model_trainer import AIModelTrainer
        trainer = AIModelTrainer()
        await trainer.analyze_performance()
        await trainer.train_on_game_results()
    
    @crash_proof_job("calculate_ats_ou_trends")
    async def _calculate_ats_ou_trends(self):
        """Calculate ATS and Over/Under trends for all sports"""
        await AtsOuTrendsJob().run()
    
    @crash_proof_job("sync_game_results")
    async def _sync_game_results(self):
        """Sync completed game results from ESPN scoreboard"""
        await GameResultsSyncJob().run()
    
    @crash_proof_job("resolve_saved_parlays")
    async def _resolve_saved_parlays(self):
        """Auto-resolve saved parlay outcomes"""
        from app.core.config import settings
        if not settings.feature_settlement:
            logger.info("[JOB] resolve_saved_parlays skipped (FEATURE_SETTLEMENT disabled)")
            return
        
        await SavedParlayResolutionJob().run()
    
    @crash_proof_job("award_arcade_points")
    async def _award_arcade_points(self):
        """Award arcade points for eligible verified wins"""
        await ArcadePointsAwardJob().run()

    @crash_proof_job("apisports_refresh")
    async def _run_apisports_refresh(self):
        """Refresh API-Sports cache (fixtures, standings). Quota-safe: 100/day."""
        await ApisportsRefreshJob().run()
    
    @crash_proof_job("check_expired_subscriptions")
    async def _check_expired_subscriptions(self):
        """Check and expire subscriptions past their period end"""
        from app.services.payment_service import PaymentService
        
        async with AsyncSessionLocal() as db:
            payment_service = PaymentService(db)
            expired_count = await payment_service.check_expired_subscriptions()
            if expired_count > 0:
                print(f"[SCHEDULER] Expired {expired_count} subscriptions")
    
    @crash_proof_job("process_ready_commissions")
    async def _process_ready_commissions(self):
        """Process affiliate commissions that are ready for payout"""
        from app.core.config import settings
        if not settings.feature_settlement:
            logger.info("[JOB] process_ready_commissions skipped (FEATURE_SETTLEMENT disabled)")
            return
        
        async with AsyncSessionLocal() as db:
            from app.services.affiliate_service import AffiliateService
            service = AffiliateService(db)
            processed = await service.process_ready_commissions()
            print(f"[SCHEDULER] Processed {processed} commissions to READY status")
    
    async def _start_score_scraper_worker(self):
        """Start the score scraper worker."""
        try:
            from app.workers.score_scraper_worker import start_score_scraper_worker
            await start_score_scraper_worker()
        except Exception as e:
            print(f"[SCHEDULER] Error starting score scraper worker: {e}")
    
    async def _start_settlement_worker(self):
        """Start the settlement worker."""
        try:
            from app.workers.settlement_worker import start_settlement_worker
            await start_settlement_worker()
        except Exception as e:
            print(f"[SCHEDULER] Error starting settlement worker: {e}")
    
    async def _start_heartbeat_worker(self):
        """Start the heartbeat worker."""
        try:
            from app.workers.heartbeat_worker import start_heartbeat_worker
            await start_heartbeat_worker()
        except Exception as e:
            print(f"[SCHEDULER] Error starting heartbeat worker: {e}")
    
    @crash_proof_job("initial_refresh", max_retries=1)
    async def _initial_refresh(self):
        """Run initial refresh on startup if games are stale."""
        import asyncio
        # Wait 10 seconds after startup to let database and everything initialize
        await asyncio.sleep(10)
        
        async with AsyncSessionLocal() as db:
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


# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler
