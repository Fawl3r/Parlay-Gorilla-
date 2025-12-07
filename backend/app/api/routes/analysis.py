"""Analysis API endpoints for game breakdowns"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import re

from app.core.dependencies import get_db
from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.models.market import Market
from app.models.odds import Odds
from app.schemas.analysis import (
    GameAnalysisResponse,
    GameAnalysisListItem,
    AnalysisGenerationRequest,
)
from app.services.analysis_generator import AnalysisGeneratorService
from app.services.odds_fetcher import OddsFetcherService
from app.services.sports_config import get_sport_config
from app.services.data_fetchers.team_photos import TeamPhotoFetcher
from app.services.stats_scraper import StatsScraperService
from app.services.model_win_probability import compute_game_win_probability
from app.utils.nfl_week import calculate_nfl_week

router = APIRouter()


def _generate_slug(home_team: str, away_team: str, league: str, game_time: datetime) -> str:
    """Generate URL-friendly slug for analysis page"""
    # Clean team names
    home_clean = re.sub(r'[^a-z0-9]+', '-', home_team.lower()).strip('-')
    away_clean = re.sub(r'[^a-z0-9]+', '-', away_team.lower()).strip('-')
    
    # Add week/date info
    if league == "NFL":
        week = calculate_nfl_week(game_time)
        slug = f"{league.lower()}/{away_clean}-vs-{home_clean}-week-{week}-{game_time.year}"
    else:
        date_str = game_time.strftime("%Y-%m-%d")
        slug = f"{league.lower()}/{away_clean}-vs-{home_clean}-{date_str}"
    
    return slug


# NOTE: This route MUST come before /{slug:path} to avoid being captured by the path parameter
@router.get("/analysis/{sport}/upcoming", response_model=List[GameAnalysisListItem])
async def list_upcoming_analyses(
    sport: str,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List available analyses for upcoming games"""
    try:
        sport_config = get_sport_config(sport)
        league = sport_config.code
        
        # Get analyses for upcoming games
        now = datetime.utcnow()
        future_cutoff = now + timedelta(days=sport_config.lookahead_days)
        
        try:
            result = await db.execute(
                select(GameAnalysis, Game)
                .join(Game, GameAnalysis.game_id == Game.id)
                .where(
                    GameAnalysis.league == league,
                    Game.start_time >= now,
                    Game.start_time <= future_cutoff
                )
                .order_by(Game.start_time)
                .limit(limit)
            )
            
            items = []
            for analysis, game in result.all():
                items.append(GameAnalysisListItem(
                    id=str(analysis.id),
                    slug=analysis.slug,
                    league=analysis.league,
                    matchup=analysis.matchup,
                    game_time=game.start_time,
                    generated_at=analysis.generated_at,
                ))
            
            return items
        except Exception as db_error:
            # If database query fails (e.g., connection issue, no games), return empty list
            print(f"[Analysis API] Database query error: {db_error}")
            # Try to get analyses without joining to Game table as fallback
            try:
                result = await db.execute(
                    select(GameAnalysis)
                    .where(
                        GameAnalysis.league == league,
                        GameAnalysis.expires_at >= now
                    )
                    .order_by(GameAnalysis.generated_at.desc())
                    .limit(limit)
                )
                
                items = []
                for analysis in result.scalars().all():
                    # Use generated_at as game_time fallback
                    items.append(GameAnalysisListItem(
                        id=str(analysis.id),
                        slug=analysis.slug,
                        league=analysis.league,
                        matchup=analysis.matchup,
                        game_time=analysis.generated_at,  # Fallback
                        generated_at=analysis.generated_at,
                    ))
                return items
            except Exception as fallback_error:
                print(f"[Analysis API] Fallback query also failed: {fallback_error}")
                return []  # Return empty list instead of error
        
    except Exception as e:
        print(f"[Analysis API] Error listing analyses: {e}")
        import traceback
        traceback.print_exc()
        # Return empty list instead of 500 error for better UX
        return []


@router.post("/analysis/generate")
async def generate_analysis(
    request: AnalysisGenerationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate or regenerate analysis for a game
    
    This endpoint triggers AI analysis generation. Use sparingly as it's expensive.
    """
    try:
        # Get game
        result = await db.execute(
            select(Game).where(Game.id == uuid.UUID(request.game_id))
        )
        game = result.scalar_one_or_none()
        
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Check if analysis already exists
        existing_result = await db.execute(
            select(GameAnalysis).where(GameAnalysis.game_id == game.id)
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing and not request.force_regenerate:
            return {
                "message": "Analysis already exists",
                "analysis_id": str(existing.id),
                "slug": existing.slug,
            }
        
        # Get odds data
        odds_fetcher = OddsFetcherService(db)
        sport_config = get_sport_config(game.sport.lower())
        games = await odds_fetcher.get_or_fetch_games(sport_config.slug, force_refresh=False)
        
        # Find this game in the list
        odds_data = {}
        for g in games:
            if str(g.id) == request.game_id:
                # Extract odds from markets
                for market in g.markets:
                    if market.market_type == "spreads":
                        # Get spread odds
                        pass
                    elif market.market_type == "totals":
                        # Get total odds
                        pass
                    elif market.market_type == "h2h":
                        # Get moneyline odds
                        pass
                break
        
        # Generate analysis
        generator = AnalysisGeneratorService(db)
        analysis_content = await generator.generate_game_analysis(
            game_id=request.game_id,
            sport=game.sport.lower(),
        )
        
        # Generate slug
        slug = _generate_slug(
            home_team=game.home_team,
            away_team=game.away_team,
            league=game.sport,
            game_time=game.start_time
        )
        
        # Generate SEO metadata
        seo_metadata = {
            "title": f"{game.away_team} vs {game.home_team} Prediction, Picks & Best Bets | {game.sport}",
            "description": analysis_content.get("opening_summary", "")[:160],
            "keywords": f"{game.away_team}, {game.home_team}, {game.sport}, prediction, picks, best bets",
        }
        
        # Create or update analysis
        if existing:
            existing.analysis_content = analysis_content
            existing.seo_metadata = seo_metadata
            existing.version += 1
            existing.generated_at = datetime.utcnow()
            existing.expires_at = game.start_time + timedelta(hours=2)  # Expire 2 hours after game
            analysis = existing
        else:
            analysis = GameAnalysis(
                game_id=game.id,
                slug=slug,
                league=game.sport,
                matchup=f"{game.away_team} @ {game.home_team}",
                analysis_content=analysis_content,
                seo_metadata=seo_metadata,
                expires_at=game.start_time + timedelta(hours=2),
            )
            db.add(analysis)
        
        await db.commit()
        await db.refresh(analysis)
        
        return {
            "message": "Analysis generated successfully",
            "analysis_id": str(analysis.id),
            "slug": analysis.slug,
            "version": analysis.version,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"[Analysis API] Error generating analysis: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")


# NOTE: Team photo route MUST come before /{slug:path} to avoid being captured
@router.get("/analysis/{sport}/team-photo")
async def get_team_photo(
    sport: str,
    team_name: str = Query(..., description="Team name (e.g., 'Miami Dolphins')"),
    opponent: Optional[str] = Query(None, description="Opponent team name (not used for stadium photos)"),
):
    """
    Get multiple stadium photos for the home team for carousel display.
    
    Returns list of photo URLs (cached for 7 days to save API requests).
    """
    try:
        photo_fetcher = TeamPhotoFetcher()
        photo_urls = await photo_fetcher.get_team_action_photo(
            team_name=team_name,
            league=sport.upper(),
            opponent=opponent
        )
        
        if photo_urls and len(photo_urls) > 0:
            return {
                "photo_urls": photo_urls,
                "photo_url": photo_urls[0],  # Keep first URL for backward compatibility
                "team": team_name,
                "league": sport.upper(),
                "count": len(photo_urls)
            }
        else:
            return {
                "photo_urls": [],
                "photo_url": None,
                "team": team_name,
                "league": sport.upper(),
                "count": 0
            }
            
    except Exception as e:
        print(f"[Team Photo API] Error fetching photos: {e}")
        return {
            "photo_urls": [],
            "photo_url": None,
            "team": team_name,
            "league": sport.upper(),
            "error": str(e)
        }


def _needs_probability_refresh(analysis_content: dict) -> bool:
    """
    Check if analysis has low-confidence probabilities that could benefit from refresh.
    
    With the new ModelWinProbabilityCalculator, we no longer have placeholder 50-50 values.
    Instead, we check confidence score - low confidence suggests stale or incomplete data.
    """
    model_probs = analysis_content.get("model_win_probability", {})
    
    # Check confidence score if available
    ai_confidence = model_probs.get("ai_confidence")
    if ai_confidence is not None and ai_confidence < 30:
        # Very low confidence - might benefit from refresh with current data
        return True
    
    # Legacy check: If both are exactly 0.5 (old analyses before upgrade)
    home_prob = model_probs.get("home_win_prob", 0.5)
    away_prob = model_probs.get("away_win_prob", 0.5)
    if abs(home_prob - 0.5) < 0.001 and abs(away_prob - 0.5) < 0.001:
        return True
    
    return False


# NOTE: This route MUST come after /upcoming and /team-photo to avoid slug:path capturing them
@router.get("/analysis/{sport}/{slug:path}", response_model=GameAnalysisResponse)
async def get_analysis(
    sport: str,
    slug: str,
    refresh: bool = Query(False, description="Force refresh probabilities if stale"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get pre-generated analysis for a game by slug
    
    Example: /api/analysis/nfl/bears-vs-packers-week-14-2025
    
    Query params:
    - refresh: If true and probabilities are 50-50, regenerate with fresh odds
    """
    try:
        # Construct full slug (stored format includes sport prefix)
        full_slug = f"{sport.lower()}/{slug}"
        
        # Query by full slug (stored format includes sport prefix)
        result = await db.execute(
            select(GameAnalysis).where(
                GameAnalysis.slug == full_slug,
                GameAnalysis.league == sport.upper()
            )
        )
        analysis = result.scalar_one_or_none()
        
        # Fallback: try without prefix for backward compatibility
        if not analysis:
            result = await db.execute(
                select(GameAnalysis).where(
                    GameAnalysis.slug == slug,
                    GameAnalysis.league == sport.upper()
                )
            )
            analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis not found for slug: {slug}"
            )
        
        # Check if probabilities need refresh
        analysis_content = analysis.analysis_content or {}
        if (refresh or _needs_probability_refresh(analysis_content)):
            print(f"[Analysis] Probabilities need refresh for {analysis.matchup}")
            
            # Try to recalculate probabilities from current odds
            try:
                generator = AnalysisGeneratorService(db)
                game_id_str = str(analysis.game_id)
                
                # Get fresh odds and recalculate probabilities
                from app.services.probability_engine import get_probability_engine
                
                game_result = await db.execute(
                    select(Game).where(Game.id == analysis.game_id)
                )
                game = game_result.scalar_one_or_none()
                
                if game:
                    # Fetch current odds
                    markets_result = await db.execute(
                        select(Market).where(Market.game_id == game.id)
                    )
                    markets = markets_result.scalars().all()
                    
                    odds_data = {}
                    for market in markets:
                        odds_result = await db.execute(
                            select(Odds).where(Odds.market_id == market.id)
                            .order_by(Odds.created_at.desc())
                            .limit(2)
                        )
                        market_odds = odds_result.scalars().all()
                        
                        if market.market_type == "h2h":
                            for odd in market_odds:
                                if odd.outcome == "home":
                                    odds_data["home_ml"] = odd.price
                                    odds_data["home_implied_prob"] = float(odd.implied_prob) if odd.implied_prob else None
                                elif odd.outcome == "away":
                                    odds_data["away_ml"] = odd.price
                                    odds_data["away_implied_prob"] = float(odd.implied_prob) if odd.implied_prob else None
                    
                    print(f"[Analysis] Fresh odds data: {odds_data}")
                    
                    # Calculate fresh probabilities
                    prob_engine = get_probability_engine(db, game.sport)
                    fresh_probs = await generator._calculate_model_probabilities(
                        game=game,
                        prob_engine=prob_engine,
                        matchup_data={},
                        odds_data=odds_data
                    )
                    
                    # Update the analysis content with fresh probabilities
                    # Now we always get valid probabilities (never exactly 0.5/0.5)
                    analysis_content["model_win_probability"] = {
                        "home_win_prob": fresh_probs.get("home_win_prob", 0.52),
                        "away_win_prob": fresh_probs.get("away_win_prob", 0.48),
                        "explanation": f"Win probability calculated using weighted model ({fresh_probs.get('calculation_method', 'unknown')})",
                        "ai_confidence": fresh_probs.get("ai_confidence", 50.0),
                        "calculation_method": fresh_probs.get("calculation_method", "unknown"),
                        "score_projection": fresh_probs.get("score_projection", "TBD"),
                    }
                    
                    # Update in database
                    analysis.analysis_content = analysis_content
                    await db.commit()
                    await db.refresh(analysis)
                    print(f"[Analysis] Updated probabilities: Home {fresh_probs.get('home_win_prob'):.1%}, "
                          f"Away {fresh_probs.get('away_win_prob'):.1%}, "
                          f"Confidence: {fresh_probs.get('ai_confidence', 0):.1f}")
                    
            except Exception as refresh_error:
                print(f"[Analysis] Failed to refresh probabilities: {refresh_error}")
                import traceback
                traceback.print_exc()
                # Continue with existing analysis
        
        # Check if expired (handle timezone-aware and naive datetimes)
        if analysis.expires_at:
            now = datetime.utcnow()
            expires = analysis.expires_at
            # Make both naive for comparison
            if expires.tzinfo is not None:
                expires = expires.replace(tzinfo=None)
            if expires < now:
                # Still return it, but could trigger regeneration
                pass
        
        # Final safety check: if analysis_content has 0.5/0.5 probabilities, recalculate
        analysis_content = analysis.analysis_content or {}
        model_probs = analysis_content.get("model_win_probability", {})
        home_prob = model_probs.get("home_win_prob", 0.5)
        away_prob = model_probs.get("away_win_prob", 0.5)
        
        if abs(home_prob - 0.5) < 0.001 and abs(away_prob - 0.5) < 0.001:
            print(f"[Analysis API] Detected 0.5/0.5 in stored analysis, recalculating...")
            try:
                game_result = await db.execute(
                    select(Game).where(Game.id == analysis.game_id)
                )
                game = game_result.scalar_one_or_none()
                
                if game:
                    # Get current odds
                    markets_result = await db.execute(
                        select(Market).where(Market.game_id == game.id)
                    )
                    markets = markets_result.scalars().all()
                    
                    odds_data = {}
                    for market in markets:
                        odds_result = await db.execute(
                            select(Odds).where(Odds.market_id == market.id)
                            .order_by(Odds.created_at.desc())
                            .limit(2)
                        )
                        market_odds = odds_result.scalars().all()
                        
                        if market.market_type == "h2h":
                            for odd in market_odds:
                                if odd.outcome == "home":
                                    odds_data["home_ml"] = odd.price
                                    odds_data["home_implied_prob"] = float(odd.implied_prob) if odd.implied_prob else None
                                elif odd.outcome == "away":
                                    odds_data["away_ml"] = odd.price
                                    odds_data["away_implied_prob"] = float(odd.implied_prob) if odd.implied_prob else None
                    
                    # Get matchup data
                    stats_scraper = StatsScraperService(db)
                    matchup_data = await stats_scraper.get_matchup_data(
                        home_team=game.home_team,
                        away_team=game.away_team,
                        league=game.sport,
                        season=str(game.start_time.year),
                        game_time=game.start_time
                    )
                    
                    # Recalculate probabilities
                    fresh_probs = await compute_game_win_probability(
                        db=db,
                        home_team=game.home_team,
                        away_team=game.away_team,
                        sport=game.sport,
                        matchup_data=matchup_data,
                        odds_data=odds_data if odds_data else None,
                    )
                    
                    # Update analysis content
                    analysis_content["model_win_probability"] = {
                        "home_win_prob": fresh_probs.get("home_model_prob", 0.52),
                        "away_win_prob": fresh_probs.get("away_model_prob", 0.48),
                        "explanation": f"Win probability recalculated ({fresh_probs.get('calculation_method', 'unknown')})",
                        "ai_confidence": fresh_probs.get("ai_confidence", 30.0),
                        "calculation_method": fresh_probs.get("calculation_method", "unknown"),
                        "score_projection": fresh_probs.get("score_projection", "TBD"),
                    }
                    
                    # Update in database
                    analysis.analysis_content = analysis_content
                    await db.commit()
                    await db.refresh(analysis)
                    print(f"[Analysis API] Recalculated probabilities: {fresh_probs.get('home_model_prob'):.1%}/{fresh_probs.get('away_model_prob'):.1%}")
            except Exception as recalc_error:
                print(f"[Analysis API] Failed to recalculate probabilities: {recalc_error}")
                # Apply minimal fix to avoid 0.5/0.5 display
                analysis_content["model_win_probability"] = {
                    "home_win_prob": 0.52,
                    "away_win_prob": 0.48,
                    "explanation": "Probability calculation unavailable (minimal home advantage applied)",
                    "ai_confidence": 15.0,
                    "calculation_method": "minimal_fallback",
                }
                analysis.analysis_content = analysis_content
        
        # Convert to response
        return GameAnalysisResponse(
            id=str(analysis.id),
            slug=analysis.slug,
            league=analysis.league,
            matchup=analysis.matchup,
            game_id=str(analysis.game_id),
            analysis_content=analysis_content,  # Use potentially updated content
            seo_metadata=analysis.seo_metadata,
            generated_at=analysis.generated_at,
            expires_at=analysis.expires_at,
            version=analysis.version,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Analysis API] Error fetching analysis: {e}")
        import traceback
        traceback.print_exc()
        # Check if it's a database connection error
        error_str = str(e).lower()
        if "getaddrinfo" in error_str or "connection" in error_str or "database" in error_str:
            raise HTTPException(
                status_code=503,
                detail="Database connection unavailable. Please try again later."
            )
        raise HTTPException(status_code=500, detail=f"Failed to fetch analysis: {str(e)}")

