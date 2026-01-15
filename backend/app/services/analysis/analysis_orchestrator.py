"""Analysis orchestrator.

This is the route-facing service that coordinates:
- slug -> game resolution
- cache/load policy (use cached-good if any)
- fast core generation
- background long-form generation
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
import re
from typing import Any, Dict, Optional

from sqlalchemy import select

from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.services.analysis.analysis_contract import is_core_ready, is_full_article_ready
from app.services.analysis.analysis_repository import AnalysisRepository
from app.services.analysis.core_analysis_generator import CoreAnalysisGenerator
from app.services.analysis.full_article_job_runner import FullArticleJobRunner
from app.services.analysis_slug_resolver import AnalysisSlugResolver
from app.utils.nfl_week import calculate_nfl_week


@dataclass(frozen=True)
class OrchestratorResult:
    analysis: GameAnalysis
    core_generated: bool


class AnalysisOrchestratorService:
    def __init__(
        self,
        db,
        *,
        repository: Optional[AnalysisRepository] = None,
        core_generator: Optional[CoreAnalysisGenerator] = None,
        slug_resolver: Optional[AnalysisSlugResolver] = None,
        full_article_jobs: Optional[FullArticleJobRunner] = None,
    ):
        self._db = db
        self._repo = repository or AnalysisRepository(db)
        self._core = core_generator or CoreAnalysisGenerator(db)
        self._resolver = slug_resolver or AnalysisSlugResolver(db)
        self._full_jobs = full_article_jobs or FullArticleJobRunner()

    async def get_or_generate_for_slug(
        self,
        *,
        sport_identifier: str,
        slug: str,
        refresh: bool,
        core_timeout_seconds: float = 8.0,
    ) -> OrchestratorResult:
        league = sport_identifier.upper()

        # Attempt to load by requested slug (supports both prefixed and legacy).
        analysis = await self._repo.get_by_slug(league=league, slug=f"{sport_identifier.lower()}/{slug}")
        if analysis and self._repo.analysis_has_core(analysis) and not refresh:
            self._maybe_enqueue_full_article(analysis)
            return OrchestratorResult(analysis=analysis, core_generated=False)

        # Resolve game if needed.
        game: Optional[Game] = None
        if analysis is None:
            game = await self._resolver.find_game(sport_identifier=sport_identifier, slug=slug)
            if not game:
                raise LookupError(f"Analysis not found for slug: {slug}")
            analysis = await self._repo.get_by_game_id(league=game.sport, game_id=game.id)
        else:
            # Load game only if we need to regenerate.
            if refresh or not self._repo.analysis_has_core(analysis):
                game = await self._resolver.find_game(sport_identifier=sport_identifier, slug=slug)

        if not game:
            # As a fallback, attempt to resolve game by analysis.game_id.
            if analysis is None:
                raise LookupError(f"Analysis not found for slug: {slug}")
            game = await self._fetch_game_by_id(game_id=analysis.game_id)
            if not game:
                raise LookupError(f"Game not found for analysis: {analysis.id}")

        canonical_slug = _generate_slug(
            home_team=game.home_team,
            away_team=game.away_team,
            league=game.sport,
            game_time=game.start_time,
        )

        lock = self._repo.core_lock(league=game.sport, game_id=str(game.id))
        async with lock:
            # Re-check after acquiring lock.
            latest = await self._repo.get_by_game_id(league=game.sport, game_id=game.id)
            if latest and self._repo.analysis_has_core(latest) and not refresh:
                self._maybe_enqueue_full_article(latest)
                return OrchestratorResult(analysis=latest, core_generated=False)

            # If refresh is True, log that we're regenerating with fresh data
            if refresh:
                print(f"[AnalysisOrchestrator] Regenerating analysis for {game.away_team} @ {game.home_team} (refresh=true)")

            core_content = await self._core.generate(game=game, timeout_seconds=core_timeout_seconds)
            core_ok = is_core_ready(core_content)
            core_status = "ready" if core_ok else "partial"
            full_status = self._full_article_status_for(core_content)

            seo_metadata = self._build_seo_metadata(game=game, core_content=core_content)

            upserted = await self._repo.upsert_core(
                analysis=latest,
                game=game,
                canonical_slug=canonical_slug,
                core_content=core_content,
                core_status=core_status,
                full_article_status=full_status,
                last_error=None if core_ok else "Core analysis incomplete (partial generation).",
                seo_metadata=seo_metadata,
                force_refresh=refresh,  # Force refresh core content when refresh=true
            )

            self._maybe_enqueue_full_article(upserted)
            return OrchestratorResult(analysis=upserted, core_generated=True)

    async def ensure_core_for_game(
        self,
        *,
        game: Game,
        core_timeout_seconds: float = 8.0,
        force_regenerate: bool = False,
    ) -> Optional[GameAnalysis]:
        """Used by schedulers: ensure core exists for an upcoming game (idempotent)."""
        canonical_slug = _generate_slug(
            home_team=game.home_team,
            away_team=game.away_team,
            league=game.sport,
            game_time=game.start_time,
        )

        lock = self._repo.core_lock(league=game.sport, game_id=str(game.id))
        async with lock:
            existing = await self._repo.get_by_game_id(league=game.sport, game_id=game.id)
            if existing and self._repo.analysis_has_core(existing) and not force_regenerate:
                self._maybe_enqueue_full_article(existing)
                return existing

            core_content = await self._core.generate(game=game, timeout_seconds=core_timeout_seconds)
            core_ok = is_core_ready(core_content)
            seo_metadata = self._build_seo_metadata(game=game, core_content=core_content)
            full_status = self._full_article_status_for(core_content)

            upserted = await self._repo.upsert_core(
                analysis=existing,
                game=game,
                canonical_slug=canonical_slug,
                core_content=core_content,
                core_status="ready" if core_ok else "partial",
                full_article_status=full_status,
                last_error=None if core_ok else "Core analysis incomplete (partial generation).",
                seo_metadata=seo_metadata,
                force_refresh=force_regenerate,  # Force refresh core content when force_regenerate=true
            )
            self._maybe_enqueue_full_article(upserted)
            
            # Trigger odds sync when analytics are updated (for Gorilla Bot)
            # This ensures odds stay fresh when new analyses are generated
            if core_ok:
                try:
                    from app.services.scheduler import get_scheduler
                    scheduler = get_scheduler()
                    # Trigger async without awaiting to avoid blocking
                    import asyncio
                    asyncio.create_task(scheduler.trigger_odds_sync())
                except Exception as sync_error:
                    # Non-critical: log but don't fail analysis generation
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Could not trigger odds sync after analysis update: {sync_error}")
            
            return upserted

    def _maybe_enqueue_full_article(self, analysis: GameAnalysis) -> None:
        content = analysis.analysis_content or {}
        if not isinstance(content, dict):
            return
        if is_full_article_ready(content):
            return
        status = (content.get("generation") or {}).get("full_article_status")
        if status not in ("queued", "ready") and self._full_jobs.enabled:
            # Marking queued happens on next core upsert; enqueue anyway.
            self._full_jobs.enqueue(analysis_id=str(analysis.id))
        elif status == "queued" and self._full_jobs.enabled:
            self._full_jobs.enqueue(analysis_id=str(analysis.id))

    def _full_article_status_for(self, core_content: Dict[str, Any]) -> str:
        if is_full_article_ready(core_content):
            return "ready"
        return "queued" if self._full_jobs.enabled else "disabled"

    @staticmethod
    def _build_seo_metadata(*, game: Game, core_content: Dict[str, Any]) -> Dict[str, Any]:
        title = f"{game.away_team} vs {game.home_team} Prediction, Picks & Best Bets | {game.sport}"
        description = str(core_content.get("opening_summary") or "")[:160]
        keywords = f"{game.away_team}, {game.home_team}, {game.sport}, prediction, picks, best bets"
        return {"title": title, "description": description, "keywords": keywords}

    async def _fetch_game_by_id(self, *, game_id) -> Optional[Game]:
        result = await self._db.execute(select(Game).where(Game.id == game_id))
        return result.scalar_one_or_none()


def _generate_slug(home_team: str, away_team: str, league: str, game_time: datetime) -> str:
    """Generate analysis slug without importing route modules (avoid circular imports)."""
    home_clean = re.sub(r"[^a-z0-9]+", "-", (home_team or "").lower()).strip("-")
    away_clean = re.sub(r"[^a-z0-9]+", "-", (away_team or "").lower()).strip("-")

    if (league or "").upper() == "NFL":
        week = calculate_nfl_week(game_time)
        # Fallback to date format if week is None (e.g., before season start or after week 18)
        if week is not None:
            return f"{league.lower()}/{away_clean}-vs-{home_clean}-week-{week}-{game_time.year}"

    date_str = game_time.strftime("%Y-%m-%d")
    return f"{league.lower()}/{away_clean}-vs-{home_clean}-{date_str}"


