"""Tools endpoints for frontend utilities like odds heatmap"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.schemas.tools import HeatmapProbabilityResponse
from app.services.analysis.analysis_repository import AnalysisRepository
from app.services.model_win_probability import compute_game_win_probability
from app.services.odds_snapshot_builder import OddsSnapshotBuilder
from app.services.sports_config import get_sport_config
from app.utils.timezone_utils import TimezoneNormalizer

router = APIRouter(prefix="/tools", tags=["tools"])


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
    from datetime import datetime, timedelta
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
