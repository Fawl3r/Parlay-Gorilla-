"""Tools endpoints for frontend utilities like odds heatmap and upset finder"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import get_optional_user_access
from app.core.event_logger import log_event
from app.core.dependencies import get_db
from app.middleware.rate_limiter import rate_limit
from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.schemas.tools import HeatmapProbabilityResponse, UpsetFinderToolsResponse
from app.services.analysis.analysis_repository import AnalysisRepository
from app.services.model_win_probability import compute_game_win_probability
from app.services.odds_snapshot_builder import OddsSnapshotBuilder
from app.services.sports_config import get_sport_config
from app.services.subscription_access_level import UserAccessLevel
from app.services.tools.upset_finder_service import UpsetFinderToolsService
from app.services.tools.upset_finder_response_cache import upset_finder_response_cache
from app.utils.timezone_utils import TimezoneNormalizer

router = APIRouter(prefix="/tools", tags=["tools"])
logger = logging.getLogger(__name__)


@router.get("/odds-heatmap-probabilities", response_model=List[HeatmapProbabilityResponse])
async def get_heatmap_probabilities(
    sport: str = Query(..., description="Sport code (e.g., NFL, NBA, NHL)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get model probabilities for all games in a sport for the odds heatmap.
    
    For each game:
    - If cached analysis exists: extract probabilities from analysis_content
    - If not cached: calculate lightweight probabilities using compute_game_win_probability
    
    Returns probabilities for H2H markets and confidence scores for spreads/totals.
    """
    try:
        sport_config = get_sport_config(sport)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Get upcoming games for the sport
    now = datetime.utcnow()
    cutoff_time = now - timedelta(hours=24)
    future_cutoff = now + timedelta(days=sport_config.lookahead_days)
    
    result = await db.execute(
        select(Game)
        .where(Game.sport == sport_config.code)
        .where(Game.start_time >= cutoff_time)
        .where(Game.start_time <= future_cutoff)
        .where((Game.status.is_(None)) | (Game.status.notin_(["finished", "closed", "complete", "Final"])))
        .order_by(Game.start_time)
    )
    games = result.scalars().all()
    
    if not games:
        return []
    
    # Initialize services
    analysis_repo = AnalysisRepository(db)
    odds_snapshot_builder = OddsSnapshotBuilder()
    
    responses: List[HeatmapProbabilityResponse] = []
    
    for game in games:
        try:
            # Check for cached analysis
            cached_analysis = await analysis_repo.get_by_game_id(
                league=game.sport,
                game_id=game.id
            )
            
            if cached_analysis and cached_analysis.analysis_content:
                # Extract from cached analysis
                content = cached_analysis.analysis_content
                model_probs = content.get("model_win_probability", {})
                spread_pick = content.get("ai_spread_pick", {})
                total_pick = content.get("ai_total_pick", {})
                
                home_win_prob = float(model_probs.get("home_win_prob", 0.5))
                away_win_prob = float(model_probs.get("away_win_prob", 0.5))
                spread_confidence = spread_pick.get("confidence") if isinstance(spread_pick, dict) else None
                total_confidence = total_pick.get("confidence") if isinstance(total_pick, dict) else None
                
                # Convert confidence to float if present
                if spread_confidence is not None:
                    try:
                        spread_confidence = float(spread_confidence)
                    except (ValueError, TypeError):
                        spread_confidence = None
                
                if total_confidence is not None:
                    try:
                        total_confidence = float(total_confidence)
                    except (ValueError, TypeError):
                        total_confidence = None
                
                responses.append(HeatmapProbabilityResponse(
                    game_id=str(game.id),
                    home_win_prob=home_win_prob,
                    away_win_prob=away_win_prob,
                    spread_confidence=spread_confidence,
                    total_confidence=total_confidence,
                    has_cached_analysis=True,
                ))
            else:
                # Calculate lightweight probabilities
                # Load markets for odds snapshot
                from app.models.market import Market
                markets_result = await db.execute(
                    select(Market).where(Market.game_id == game.id)
                )
                markets = markets_result.scalars().all()
                
                odds_snapshot = odds_snapshot_builder.build(game=game, markets=markets)
                
                # Build minimal matchup_data (empty dict is fine for lightweight calc)
                matchup_data = {}
                
                # Calculate probabilities
                model_result = await compute_game_win_probability(
                    db=db,
                    home_team=game.home_team,
                    away_team=game.away_team,
                    sport=game.sport,
                    matchup_data=matchup_data,
                    odds_data=odds_snapshot,
                )
                
                home_win_prob = float(model_result.get("home_model_prob", 0.5))
                away_win_prob = float(model_result.get("away_model_prob", 0.5))
                
                responses.append(HeatmapProbabilityResponse(
                    game_id=str(game.id),
                    home_win_prob=home_win_prob,
                    away_win_prob=away_win_prob,
                    spread_confidence=None,
                    total_confidence=None,
                    has_cached_analysis=False,
                ))
        except Exception as e:
            # Log error but continue processing other games
            print(f"[HEATMAP_PROBABILITIES] Error processing game {game.id}: {e}")
            import traceback
            traceback.print_exc()
            # Add fallback response
            responses.append(HeatmapProbabilityResponse(
                game_id=str(game.id),
                home_win_prob=0.5,
                away_win_prob=0.5,
                spread_confidence=None,
                total_confidence=None,
                has_cached_analysis=False,
            ))
            continue
    
    return responses


@router.get("/upsets", response_model=UpsetFinderToolsResponse)
@rate_limit("20/hour")
async def get_tools_upsets(
    request: Request,
    sport: str = Query("nba", description="Sport slug/code or 'all'"),
    days: int = Query(7, ge=1, le=30, description="Next N days window"),
    min_edge: float = Query(3.0, ge=0.0, le=50.0, description="Min edge (percent points)"),
    max_results: int = Query(20, ge=1, le=50, description="Max candidates to return"),
    min_underdog_odds: int = Query(110, ge=100, le=1000, description="Min underdog American odds (e.g. 110 = +110)"),
    meta_only: int = Query(0, ge=0, le=1, description="If 1, return meta only (no candidates)"),
    force: int = Query(0, ge=0, le=1, description="If 1, bypass cache READ (still writes cache)"),
    db: AsyncSession = Depends(get_db),
    user_access: Optional[UserAccessLevel] = Depends(get_optional_user_access),
):
    """
    Gorilla Upset Finder (tools): next X days, usable H2H only, ROI-ranked candidates + honest meta.

    Non-negotiables:
    - Returns 200 always with typed `access` + typed `meta`.
    - For anon/non-premium: `candidates=[]` but meta is real.
    - `meta_only=1` must be CHEAP: no implied probs, no model probs, no candidate building.
    """
    start_ts = time.perf_counter()
    trace_id = getattr(getattr(request, "state", None), "request_id", None)

    sport_norm = (sport or "").strip().lower() or "nba"
    meta_only_bool = bool(meta_only)
    force_bool = bool(force)

    entitlement = "anon"
    can_view_candidates = False
    access_reason: Optional[str] = "login_required"
    if user_access is not None:
        entitlement = "premium" if user_access.can_use_upset_finder else "free"
        can_view_candidates = bool(user_access.can_use_upset_finder)
        access_reason = None if can_view_candidates else "premium_required"

    # Back-compat: if min_edge <= 1.0 treat as fraction and convert to percent points
    edge_pct = min_edge * 100.0 if min_edge <= 1.0 and min_edge > 0 else min_edge

    cache_hit = False
    error: Optional[str] = None
    response_payload: Dict[str, Any]

    async def _compute_meta_response() -> Dict[str, Any]:
        service = UpsetFinderToolsService(db)
        meta_dict = await service.scan_meta(sport=sport_norm, days=days)
        return {
            "sport": sport_norm,
            "window_days": days,
            "min_edge": float(edge_pct),
            "max_results": int(max_results),
            "min_underdog_odds": int(min_underdog_odds),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "access": {"can_view_candidates": False if not can_view_candidates else True, "reason": access_reason},
            "candidates": [],
            "meta": meta_dict,
            "error": None,
        }

    async def _compute_full_response() -> Dict[str, Any]:
        service = UpsetFinderToolsService(db)
        result = await service.find_candidates(
            sport=sport_norm,
            days=days,
            min_edge=edge_pct,
            max_results=max_results,
            min_underdog_odds=min_underdog_odds,
        )
        payload = result.to_dict()
        payload.update(
            {
                "max_results": int(max_results),
                "min_underdog_odds": int(min_underdog_odds),
                "access": {"can_view_candidates": True, "reason": None},
                "error": None,
            }
        )
        return payload

    try:
        ttl = upset_finder_response_cache.ttl_seconds(sport=sport_norm, days=days)
        if meta_only_bool or not can_view_candidates:
            cache_key = upset_finder_response_cache.meta_key(
                sport=sport_norm,
                days=days,
                min_edge=float(edge_pct),
                max_results=max_results,
                min_underdog_odds=min_underdog_odds,
                entitlement=entitlement,
            )
            response_payload, cache_hit = await upset_finder_response_cache.get_or_compute_json(
                key=cache_key,
                ttl_seconds=ttl,
                force_refresh=force_bool,
                compute=_compute_meta_response,
            )
            # If locked, enforce empty candidates even if cached incorrectly.
            if not can_view_candidates:
                response_payload["candidates"] = []
                response_payload["access"] = {"can_view_candidates": False, "reason": access_reason}
        else:
            cache_key = upset_finder_response_cache.full_key(
                sport=sport_norm,
                days=days,
                min_edge=float(edge_pct),
                max_results=max_results,
                min_underdog_odds=min_underdog_odds,
                entitlement=entitlement,
            )
            response_payload, cache_hit = await upset_finder_response_cache.get_or_compute_json(
                key=cache_key,
                ttl_seconds=ttl,
                force_refresh=force_bool,
                compute=_compute_full_response,
            )
    except Exception as exc:
        error = str(exc)
        response_payload = {
            "sport": sport_norm,
            "window_days": days,
            "min_edge": float(edge_pct),
            "max_results": int(max_results),
            "min_underdog_odds": int(min_underdog_odds),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "access": {"can_view_candidates": False if not can_view_candidates else True, "reason": access_reason},
            "candidates": [],
            "meta": {"games_scanned": 0, "games_with_odds": 0, "missing_odds": 0, "games_scanned_capped": None},
            "error": error,
        }

    # Instrumentation: one structured event per request
    try:
        meta_obj = response_payload.get("meta") or {}
        candidates_count = len(response_payload.get("candidates") or [])
        games_scanned = int(meta_obj.get("games_scanned") or 0)
        games_with_odds = int(meta_obj.get("games_with_odds") or 0)
        missing_odds = int(meta_obj.get("missing_odds") or 0)
        rejected_reason_counts = meta_obj.get("rejected_reason_counts") if isinstance(meta_obj, dict) else None

        candidates = response_payload.get("candidates") or []
        books_counts = [
            int(c.get("books_count") or 0)
            for c in candidates
            if isinstance(c, dict)
        ]
        avg_books_count = (sum(books_counts) / len(books_counts)) if books_counts else 0.0
        thin_odds_count = sum(
            1
            for c in candidates
            if isinstance(c, dict) and (c.get("odds_quality") or "bad") != "good"
        )
        stale_flag_count = sum(
            1
            for c in candidates
            if isinstance(c, dict) and "stale_odds_suspected" in (c.get("flags") or [])
        )

        empty_reason = "unknown"
        if games_scanned == 0:
            empty_reason = "no_upcoming_games"
        elif games_with_odds == 0:
            empty_reason = "no_odds"
        elif not can_view_candidates:
            empty_reason = "locked"
        elif can_view_candidates and games_with_odds > 0 and candidates_count == 0:
            empty_reason = "threshold_too_high"

        duration_ms = int((time.perf_counter() - start_ts) * 1000.0)
        log_event(
            logger,
            "upset_finder_generated",
            trace_id=trace_id,
            sport=sport_norm,
            days=days,
            min_edge=float(edge_pct),
            max_results=int(max_results),
            min_underdog_odds=int(min_underdog_odds),
            meta_only=meta_only_bool,
            force=force_bool,
            candidates_count=candidates_count,
            games_scanned=games_scanned,
            games_with_odds=games_with_odds,
            missing_odds=missing_odds,
            cache_hit=cache_hit,
            user_entitlement=entitlement,
            duration_ms=duration_ms,
            empty_reason=empty_reason,
            avg_books_count=round(avg_books_count, 2),
            thin_odds_count=thin_odds_count,
            stale_flag_count=stale_flag_count,
            rejected_reason_counts=rejected_reason_counts,
            error=error,
        )
    except Exception:
        pass

    return response_payload
