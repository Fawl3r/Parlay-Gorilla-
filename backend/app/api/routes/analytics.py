"""Analytics routes for parlay performance tracking"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.dependencies import get_db, get_current_user, get_optional_user
from app.models.user import User
from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.models.market import Market
from app.models.analysis_page_views import AnalysisPageViews
from app.services.parlay_tracker import ParlayTrackerService
from app.services.analysis.analysis_repository import AnalysisRepository
from app.services.traffic_ranker import TrafficRanker
from app.services.model_win_probability import compute_game_win_probability
from app.services.odds_snapshot_builder import OddsSnapshotBuilder
from app.services.sports_config import get_sport_config
from app.services.team_name_normalizer import TeamNameNormalizer
from app.schemas.analytics import (
    AnalyticsResponse,
    AnalyticsSnapshotResponse,
    AnalyticsGameResponse,
)

router = APIRouter()


class PerformanceStatsResponse(BaseModel):
    """Performance statistics response"""
    total_parlays: int
    hits: int
    misses: int
    hit_rate: float
    avg_predicted_prob: float
    avg_actual_prob: float
    avg_calibration_error: float


@router.get("/performance", response_model=PerformanceStatsResponse)
async def get_performance_stats(
    risk_profile: Optional[str] = Query(None, description="Filter by risk profile"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get parlay performance statistics
    
    Returns aggregated stats for resolved parlays.
    Requires authentication.
    """
    tracker = ParlayTrackerService(db)
    stats = await tracker.get_parlay_performance_stats(
        risk_profile=risk_profile,
        start_date=start_date,
        end_date=end_date,
        user_id=str(current_user.id)
    )
    
    return PerformanceStatsResponse(**stats)


@router.get("/my-parlays")
async def get_my_parlay_history(
    limit: int = Query(50, ge=1, le=100, description="Number of parlays to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's parlay history"""
    tracker = ParlayTrackerService(db)
    parlays = await tracker.get_user_parlay_history(
        user_id=str(current_user.id),
        limit=limit
    )
    
    # Convert to response format
    return [
        {
            "id": str(p.id),
            "num_legs": p.num_legs,
            "risk_profile": p.risk_profile,
            "parlay_hit_prob": float(p.parlay_hit_prob),
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in parlays
    ]


@router.get("/games", response_model=AnalyticsResponse)
async def get_analytics_games(
    request: Request,
    sport: Optional[str] = Query(None, description="Filter by sport (NFL, NBA, etc.)"),
    market_type: Optional[str] = Query("moneyline", description="Market type: moneyline, spread, totals"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get analytics data for games heatmap.
    
    Returns:
    - Snapshot stats (games tracked, accuracy, high-confidence count, trending matchup)
    - Games list with probabilities/confidence, badges, and traffic scores
    
    Always returns 200 with empty state on errors (graceful degradation).
    """
    from fastapi import HTTPException
    from app.core.config import settings
    from app.utils.timezone_utils import TimezoneNormalizer
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Get request_id for error logging
    request_id = None
    try:
        if request is not None and hasattr(request, 'state'):
            request_id = getattr(request.state, 'request_id', None)
    except Exception:
        pass
    
    # Check feature flag
    if not settings.feature_analytics:
        logger.info(f"[ANALYTICS] Analytics endpoint disabled via feature flag [request_id={request_id}]")
        return AnalyticsResponse(
            snapshot=AnalyticsSnapshotResponse(
                games_tracked_today=0,
                model_accuracy_last_100=None,
                high_confidence_games=0,
                trending_matchup=None,
            ),
            games=[],
            total_games=0,
        )
    
    # Wrap entire endpoint in try/except for graceful degradation
    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        future_cutoff = now + timedelta(days=7)
        
        # Build base query
        query = (
            select(Game)
            .where(Game.start_time >= today_start)
            .where(Game.start_time <= future_cutoff)
            .where((Game.status.is_(None)) | (Game.status.notin_(["finished", "closed", "complete", "Final"])))
        )
        
        if sport:
            try:
                sport_config = get_sport_config(sport)
                query = query.where(Game.sport == sport_config.code)
            except ValueError:
                pass
        
        result = await db.execute(query.order_by(Game.start_time))
        games = result.scalars().all()
        
        if not games:
            return AnalyticsResponse(
                snapshot=AnalyticsSnapshotResponse(
                    games_tracked_today=0,
                    model_accuracy_last_100=None,
                    high_confidence_games=0,
                    trending_matchup=None,
                ),
                games=[],
                total_games=0,
            )
        
        # Initialize services
        analysis_repo = AnalysisRepository(db)
        traffic_ranker = TrafficRanker(db)
        odds_snapshot_builder = OddsSnapshotBuilder()
        
        # Get page views for traffic ranking
        page_views_map: dict[str, int] = {}
        if games:
            game_ids = [str(g.id) for g in games]
            cutoff_date = (now - timedelta(days=2)).date()
            
            views_result = await db.execute(
                select(
                    AnalysisPageViews.game_id,
                    func.sum(AnalysisPageViews.views).label("total_views"),
                )
                .where(AnalysisPageViews.game_id.in_([g.id for g in games]))
                .where(AnalysisPageViews.view_bucket_date >= cutoff_date)
                .group_by(AnalysisPageViews.game_id)
            )
            
            for row in views_result.all():
                page_views_map[str(row.game_id)] = int(row.total_views or 0)
        
        # Process games
        analytics_games: List[AnalyticsGameResponse] = []
        high_confidence_count = 0
        trending_matchup: Optional[str] = None
        max_traffic_score = 0.0
        
        for game in games:
            try:
                # Check for cached analysis
                cached_analysis = await analysis_repo.get_by_game_id(
                    league=game.sport,
                    game_id=game.id
                )
                
                has_cached = cached_analysis is not None and cached_analysis.analysis_content is not None
                
                # Extract probabilities/confidence
                home_win_prob = None
                away_win_prob = None
                spread_confidence = None
                total_confidence = None
                confidence_total = 0.0
                
                if has_cached and cached_analysis.analysis_content:
                    content = cached_analysis.analysis_content
                    model_probs = content.get("model_win_probability", {})
                    spread_pick = content.get("ai_spread_pick", {})
                    total_pick = content.get("ai_total_pick", {})
                    confidence_breakdown = content.get("confidence_breakdown", {})
                    
                    home_win_prob = float(model_probs.get("home_win_prob", 0.5))
                    away_win_prob = float(model_probs.get("away_win_prob", 0.5))
                    
                    if isinstance(spread_pick, dict):
                        spread_confidence = float(spread_pick.get("confidence", 0))
                    if isinstance(total_pick, dict):
                        total_confidence = float(total_pick.get("confidence", 0))
                    
                    confidence_total = float(confidence_breakdown.get("confidence_total", 0))
                else:
                    # Lightweight fallback
                    markets_result = await db.execute(
                        select(Market).where(Market.game_id == game.id)
                    )
                    markets = markets_result.scalars().all()
                    odds_snapshot = odds_snapshot_builder.build(game=game, markets=markets)
                    
                    # Ensure odds snapshot has valid data - if empty, try to extract directly from markets
                    # This is a fallback in case the snapshot builder didn't find the H2H market
                    if not odds_snapshot.get("home_implied_prob") and not odds_snapshot.get("home_ml"):
                        # Try to extract odds directly from H2H market
                        h2h_market = next((m for m in markets if m.market_type and m.market_type.lower() == "h2h"), None)
                        if h2h_market and h2h_market.odds:
                            team_normalizer = TeamNameNormalizer()
                            home_norm = team_normalizer.normalize(game.home_team)
                            away_norm = team_normalizer.normalize(game.away_team)
                            
                            # Prefer implied_prob if available (it's already calculated and stored)
                            for o in h2h_market.odds:
                                out_raw = str(o.outcome or "")
                                out_lower = out_raw.lower()
                                out_norm = team_normalizer.normalize(out_raw)
                                
                                is_home = out_lower == "home" or (out_norm and out_norm == home_norm)
                                is_away = out_lower == "away" or (out_norm and out_norm == away_norm)
                                
                                if is_home:
                                    if o.implied_prob is not None and not odds_snapshot.get("home_implied_prob"):
                                        odds_snapshot["home_implied_prob"] = float(o.implied_prob)
                                    if not odds_snapshot.get("home_ml"):
                                        odds_snapshot["home_ml"] = o.price
                                elif is_away:
                                    if o.implied_prob is not None and not odds_snapshot.get("away_implied_prob"):
                                        odds_snapshot["away_implied_prob"] = float(o.implied_prob)
                                    if not odds_snapshot.get("away_ml"):
                                        odds_snapshot["away_ml"] = o.price
                    
                    # Debug: Log odds snapshot for NHL games
                    if game.sport.upper() == "NHL":
                        print(f"[ANALYTICS_NHL] Game {game.id}: {game.away_team} @ {game.home_team}")
                        print(f"  Odds snapshot keys: {list(odds_snapshot.keys())}")
                        print(f"  home_ml: {odds_snapshot.get('home_ml')}, away_ml: {odds_snapshot.get('away_ml')}")
                        print(f"  home_implied_prob: {odds_snapshot.get('home_implied_prob')}, away_implied_prob: {odds_snapshot.get('away_implied_prob')}")
                        print(f"  Markets found: {len(markets)}, H2H markets: {len([m for m in markets if m.market_type and m.market_type.lower() == 'h2h'])}")
                    
                    model_result = await compute_game_win_probability(
                        db=db,
                        home_team=game.home_team,
                        away_team=game.away_team,
                        sport=game.sport,
                        matchup_data={},
                        odds_data=odds_snapshot,
                    )
                    
                    home_win_prob = float(model_result.get("home_model_prob", 0.5))
                    away_win_prob = float(model_result.get("away_model_prob", 0.5))
                    
                    # Debug: Log calculated probabilities for NHL
                    if game.sport.upper() == "NHL":
                        print(f"  Calculated: home={home_win_prob:.3f}, away={away_win_prob:.3f}, method={model_result.get('calculation_method', 'unknown')}")
                    
                    # If probabilities are too close to default (0.5), odds likely failed to parse
                    # Try direct odds calculation as fallback
                    if abs(home_win_prob - 0.5) < 0.03 and abs(away_win_prob - 0.5) < 0.03:
                        home_ml_raw = odds_snapshot.get("home_ml")
                        away_ml_raw = odds_snapshot.get("away_ml")
                        
                        if home_ml_raw and away_ml_raw:
                            try:
                                from app.services.model_win_probability import american_odds_to_probability, remove_vig_and_normalize
                                
                                # Parse odds strings more robustly
                                def parse_american_odds(odds_val):
                                    if isinstance(odds_val, (int, float)):
                                        return int(odds_val)
                                    odds_str = str(odds_val).strip().replace("+", "").replace("−", "-").replace("–", "-")
                                    # Extract numeric value (handle negative)
                                    if odds_str.startswith("-"):
                                        return -int("".join(c for c in odds_str[1:] if c.isdigit()) or "0")
                                    else:
                                        return int("".join(c for c in odds_str if c.isdigit()) or "0")
                                
                                home_ml_int = parse_american_odds(home_ml_raw)
                                away_ml_int = parse_american_odds(away_ml_raw)
                                
                                if home_ml_int != 0 and away_ml_int != 0:
                                    home_prob = american_odds_to_probability(home_ml_int)
                                    away_prob = american_odds_to_probability(away_ml_int)
                                    
                                    home_fair, away_fair = remove_vig_and_normalize(home_prob, away_prob)
                                    
                                    # Apply home advantage based on sport
                                    if game.sport.upper() == "NHL":
                                        home_advantage = 0.025
                                    elif game.sport.upper() == "NFL":
                                        home_advantage = 0.025
                                    elif game.sport.upper() == "NBA":
                                        home_advantage = 0.035
                                    else:
                                        home_advantage = 0.02
                                    
                                    home_win_prob = min(0.95, max(0.05, home_fair + home_advantage))
                                    away_win_prob = min(0.95, max(0.05, away_fair - home_advantage))
                                    
                                    if game.sport.upper() == "NHL":
                                        print(f"  Recalculated from odds: home={home_win_prob:.3f}, away={away_win_prob:.3f}")
                            except Exception as e:
                                print(f"[ANALYTICS] Failed to parse odds for game {game.id}: {e}, home_ml={home_ml_raw}, away_ml={away_ml_raw}")
                
                # Calculate traffic score
                page_views = page_views_map.get(str(game.id), 0)
                traffic_payload = {
                    "page_views": page_views,
                    "sport": game.sport,
                    "game_time": game.start_time.isoformat() if game.start_time else None,
                    "slug": cached_analysis.slug if cached_analysis else None,
                }
                traffic_score_obj = traffic_ranker.score(traffic_payload)
                traffic_score = traffic_score_obj.score
                
                # Track trending matchup
                if traffic_score > max_traffic_score:
                    max_traffic_score = traffic_score
                    trending_matchup = f"{game.away_team} @ {game.home_team}"
                
                # Check high confidence (>= 70)
                is_high_confidence = False
                if market_type == "moneyline":
                    is_high_confidence = (home_win_prob >= 0.7 or away_win_prob >= 0.7) if home_win_prob and away_win_prob else False
                elif market_type == "spread" and spread_confidence:
                    is_high_confidence = spread_confidence >= 70.0
                elif market_type == "totals" and total_confidence:
                    is_high_confidence = total_confidence >= 70.0
                elif confidence_total >= 70.0:
                    is_high_confidence = True
                
                if is_high_confidence:
                    high_confidence_count += 1
                
                # Determine if trending (top 10% by traffic)
                is_trending = traffic_score >= 0.7
                
                analytics_games.append(AnalyticsGameResponse(
                    game_id=str(game.id),
                    matchup=f"{game.away_team} @ {game.home_team}",
                    home_team=game.home_team,
                    away_team=game.away_team,
                    sport=game.sport,
                    start_time=game.start_time.isoformat() if game.start_time else "",
                    slug=cached_analysis.slug if cached_analysis else None,
                    home_win_prob=home_win_prob,
                    away_win_prob=away_win_prob,
                    spread_confidence=spread_confidence,
                    total_confidence=total_confidence,
                    has_cached_analysis=has_cached,
                    is_trending=is_trending,
                    traffic_score=traffic_score,
                ))
            except Exception as e:
                print(f"[ANALYTICS] Error processing game {game.id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Sort by traffic score (highest first)
        analytics_games.sort(key=lambda g: g.traffic_score, reverse=True)
        
        # Calculate model accuracy (placeholder - would need actual results tracking)
        # For now, return None if not available
        model_accuracy = None
        
        return AnalyticsResponse(
            snapshot=AnalyticsSnapshotResponse(
                games_tracked_today=len(analytics_games),
                model_accuracy_last_100=model_accuracy,
                high_confidence_games=high_confidence_count,
                trending_matchup=trending_matchup,
            ),
            games=analytics_games,
            total_games=len(analytics_games),
        )
    except Exception as e:
        # Log error with request_id for debugging
        error_msg = str(e)[:200]  # Truncate long errors
        log_msg = f"[ANALYTICS] Error in get_analytics_games"
        if request_id:
            log_msg += f" [request_id={request_id}]"
        log_msg += f": {error_msg}"
        logger.error(log_msg, exc_info=True)
        print(log_msg)
        import traceback
        traceback.print_exc()
        
        # Return graceful empty state - never return 500
        return AnalyticsResponse(
            snapshot=AnalyticsSnapshotResponse(
                games_tracked_today=0,
                model_accuracy_last_100=None,
                high_confidence_games=0,
                trending_matchup=None,
            ),
            games=[],
            total_games=0,
        )

