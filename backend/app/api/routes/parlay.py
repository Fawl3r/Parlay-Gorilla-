"""Parlay API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, Dict, List
import logging

from app.core.dependencies import get_db, get_optional_user, get_current_user
from app.core.access_control import (
    enforce_free_parlay_limit,
    require_custom_builder_access,
    require_upset_finder_access,
    check_and_increment_parlay_usage,
)
from app.models.user import User
from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from app.schemas.parlay import (
    ParlayRequest,
    ParlayResponse,
    TripleParlayRequest,
    TripleParlayResponse,
    CustomParlayRequest,
    CustomParlayAnalysisResponse,
    CustomParlayLegAnalysis,
)
from app.services.parlay_builder import ParlayBuilderService
from app.services.mixed_sports_parlay import MixedSportsParlayBuilder
from app.services.openai_service import OpenAIService
from app.services.cache_manager import CacheManager
from app.services.probability_engine import get_probability_engine
from app.services.subscription_service import SubscriptionService
from app.services.badge_service import BadgeService
from app.models.parlay import Parlay
from app.middleware.rate_limiter import rate_limit
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_confidence_color(score: float) -> str:
    """Get color based on confidence score"""
    if score >= 70:
        return "green"
    elif score >= 50:
        return "yellow"
    else:
        return "red"


async def _prepare_parlay_response(
    parlay_data: Dict,
    risk_profile: str,
    openai_service: OpenAIService,
    db: AsyncSession,
    current_user: Optional[User],
    explanation_override: Optional[Dict[str, str]] = None,
) -> ParlayResponse:
    """Generate AI explanation, persist parlay, and return ParlayResponse."""
    if explanation_override:
        explanation = explanation_override
    else:
        explanation = await openai_service.generate_parlay_explanation(
            legs=parlay_data["legs"],
            risk_profile=risk_profile,
            parlay_probability=parlay_data["parlay_hit_prob"],
            overall_confidence=parlay_data["overall_confidence"],
        )

    confidence_meter = {
        "score": parlay_data["overall_confidence"],
        "color": _get_confidence_color(parlay_data["overall_confidence"]),
    }

    parlay_id = str(uuid.uuid4())
    try:
        parlay = Parlay(
            legs=parlay_data["legs"],
            num_legs=parlay_data["num_legs"],
            parlay_hit_prob=parlay_data["parlay_hit_prob"],
            risk_profile=risk_profile,
            ai_summary=explanation["summary"],
            ai_risk_notes=explanation["risk_notes"],
            user_id=current_user.id if current_user and hasattr(current_user, "id") else None,
        )
        db.add(parlay)
        await db.flush()
        parlay_id = str(parlay.id)
    except Exception as db_error:
        print(f"Warning: Failed to save parlay to database: {db_error}")
        import traceback

        traceback.print_exc()

    response = ParlayResponse(
        id=parlay_id,
        legs=parlay_data["legs"],
        num_legs=int(parlay_data["num_legs"]),
        parlay_hit_prob=float(parlay_data["parlay_hit_prob"]),
        risk_profile=str(risk_profile),
        confidence_scores=[float(c) for c in parlay_data["confidence_scores"]],
        overall_confidence=float(parlay_data["overall_confidence"]),
        ai_summary=str(explanation["summary"]),
        ai_risk_notes=str(explanation["risk_notes"]),
        confidence_meter=confidence_meter,
    )

    return response


@router.post("/parlay/suggest", response_model=ParlayResponse)
@rate_limit("20/hour")  # Limit expensive parlay generation
async def suggest_parlay(
    request: Request,
    parlay_request: ParlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(enforce_free_parlay_limit)
):
    """Generate a parlay suggestion based on parameters.
    
    Supports mixed sports parlays when sports list is provided.
    Mixed sports parlays help reduce correlation between legs.
    
    Access Control:
    - Free users: 1 AI parlay per day
    - Premium users: Unlimited
    
    Returns 402 Payment Required if free limit reached.
    """
    try:
        import traceback
        
        # Determine if this is a mixed sports request
        sports = parlay_request.sports or ["NFL"]
        is_mixed = parlay_request.mix_sports or (parlay_request.sports and len(parlay_request.sports) > 1)
        week = parlay_request.week  # Week filter for NFL games
        
        print(f"Parlay request received: num_legs={parlay_request.num_legs}, "
              f"risk_profile={parlay_request.risk_profile}, "
              f"sports={sports}, mix_sports={is_mixed}, week={week}")
        
        # Generate cache key based on request (include week)
        cache_key_sport = "_".join(sorted(s.upper() for s in sports))
        cache_key = f"{cache_key_sport}_week_{week}" if week else cache_key_sport
        cache_manager = CacheManager(db)
        
        # Check cache first (skip for mixed sports or week-specific as combinations vary)
        cached_parlay = None
        if not is_mixed and not week:
            cached_parlay = await cache_manager.get_cached_parlay(
                num_legs=parlay_request.num_legs,
                risk_profile=parlay_request.risk_profile,
                sport=cache_key,
                max_age_hours=6
            )
        
        if cached_parlay:
            print("Using cached parlay data")
            parlay_data = cached_parlay
        else:
            # Build parlay - use mixed sports builder if multiple sports
            if is_mixed and len(sports) > 1:
                print(f"Building mixed sports parlay from: {sports} for week {week}")
                mixed_builder = MixedSportsParlayBuilder(db)
                parlay_data = await mixed_builder.build_mixed_parlay(
                    num_legs=parlay_request.num_legs,
                    sports=sports,
                    risk_profile=parlay_request.risk_profile,
                    balance_sports=True,
                    week=week
                )
            else:
                # Single sport parlay
                sport = sports[0] if sports else "NFL"
                print(f"Building single sport parlay from: {sport} for week {week}")
                builder = ParlayBuilderService(db, sport=sport)
                parlay_data = await builder.build_parlay(
                    num_legs=parlay_request.num_legs,
                    risk_profile=parlay_request.risk_profile,
                    sport=sport,
                    week=week
                )
            
            # Cache the result (skip for week-specific)
            if not is_mixed and not week:
                await cache_manager.set_cached_parlay(
                    num_legs=parlay_request.num_legs,
                    risk_profile=parlay_request.risk_profile,
                    parlay_data=parlay_data,
                    sport=cache_key,
                    ttl_hours=6
                )
        
        print(f"Parlay data built: {len(parlay_data.get('legs', []))} legs")
        
        # Log sports distribution for mixed parlays
        if is_mixed:
            sports_in_parlay = set(leg.get("sport", "NFL") for leg in parlay_data.get("legs", []))
            print(f"Sports included in parlay: {sports_in_parlay}")
        
        openai_service = OpenAIService()
        try:
            response = await _prepare_parlay_response(
                parlay_data=parlay_data,
                risk_profile=parlay_request.risk_profile,
                openai_service=openai_service,
                db=db,
                current_user=current_user,
            )
        except Exception as e:
            import traceback

            print(f"Error building response: {e}")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Error building response: {str(e)}")
        
        try:
            await db.commit()
            
            # Increment usage for free users AFTER successful generation
            await check_and_increment_parlay_usage(current_user, db)
            
            # Check and award badges after successful parlay generation
            newly_unlocked_badges = []
            if current_user and hasattr(current_user, "id"):
                try:
                    badge_service = BadgeService(db)
                    newly_unlocked_badges = await badge_service.check_and_award_badges(str(current_user.id))
                    if newly_unlocked_badges:
                        logger.info(f"User {current_user.id} earned {len(newly_unlocked_badges)} new badge(s)")
                except Exception as badge_error:
                    logger.warning(f"Badge check failed (non-critical): {badge_error}")
            
            # Add newly unlocked badges to response
            if newly_unlocked_badges:
                response.newly_unlocked_badges = newly_unlocked_badges
            
        except Exception as commit_error:
            print(f"Warning: Failed to commit parlay: {commit_error}")
            await db.rollback()
        
        return response
        
    except ValueError as e:
        import traceback
        print(f"ValueError in parlay generation: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Exception in parlay generation: {e}")
        print(traceback.format_exc())
        error_str = str(e).lower()
        # Check for common issues
        if "not enough" in error_str or "no games" in error_str or "candidate" in error_str:
            raise HTTPException(
                status_code=503,
                detail="Not enough games available to build parlay. Please try again later when more games are loaded."
            )
        elif "getaddrinfo" in error_str or "connection" in error_str or "database" in error_str:
            raise HTTPException(
                status_code=503,
                detail="Database connection unavailable. Please try again later."
            )
        raise HTTPException(status_code=500, detail=f"Failed to generate parlay: {str(e)}")


@router.post("/parlay/suggest/triple", response_model=TripleParlayResponse)
@rate_limit("10/hour")
async def suggest_triple_parlay(
    request: Request,
    triple_request: TripleParlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(enforce_free_parlay_limit),
):
    """Generate Safe/Balanced/Degen parlays in a single request."""
    try:
        sports = triple_request.sports or ["NFL"]
        leg_overrides = {
            "safe": triple_request.safe_legs,
            "balanced": triple_request.balanced_legs,
            "degen": triple_request.degen_legs,
        }
        leg_overrides = {k: v for k, v in leg_overrides.items() if v is not None}

        builder = ParlayBuilderService(db, sports[0])
        triple_data = await builder.build_triple_parlay(
            sports=sports,
            leg_overrides=leg_overrides,
        )

        openai_service = OpenAIService()
        ai_explanations = await openai_service.generate_triple_parlay_explanations(triple_data)
        responses: Dict[str, ParlayResponse] = {}
        metadata: Dict[str, Dict] = {}

        for profile_name in ["safe", "balanced", "degen"]:
            block = triple_data.get(profile_name)
            if not block:
                raise HTTPException(status_code=500, detail=f"Missing data for {profile_name} parlay")
            parlay_response = await _prepare_parlay_response(
                parlay_data=block["parlay"],
                risk_profile=block["parlay"].get("risk_profile", profile_name),
                openai_service=openai_service,
                db=db,
                current_user=current_user,
                explanation_override={
                    "summary": ai_explanations.get(profile_name, {}).get("summary", ""),
                    "risk_notes": ai_explanations.get(profile_name, {}).get("risk_notes", ""),
                },
            )
            # Attach highlight leg metadata
            highlight = ai_explanations.get(profile_name, {}).get("highlight_leg")
            metadata_block = block.get("config", {}).copy()
            if highlight:
                metadata_block["highlight_leg"] = highlight
            metadata[profile_name] = metadata_block
            responses[profile_name] = parlay_response

        try:
            await db.commit()
            
            # Increment usage for free users AFTER successful generation
            await check_and_increment_parlay_usage(current_user, db)
            
            # Check and award badges after successful parlay generation
            # (triple parlay counts as 3 parlays for badge progress)
            newly_unlocked_badges = []
            if current_user and hasattr(current_user, "id"):
                try:
                    badge_service = BadgeService(db)
                    newly_unlocked_badges = await badge_service.check_and_award_badges(str(current_user.id))
                    if newly_unlocked_badges:
                        logger.info(f"User {current_user.id} earned {len(newly_unlocked_badges)} new badge(s) from triple parlay")
                        # Add badges to the first response (safe) for frontend display
                        responses["safe"].newly_unlocked_badges = newly_unlocked_badges
                except Exception as badge_error:
                    logger.warning(f"Badge check failed (non-critical): {badge_error}")
            
        except Exception as commit_error:
            print(f"Warning: Failed to commit triple parlay: {commit_error}")
            await db.rollback()

        return TripleParlayResponse(
            safe=responses["safe"],
            balanced=responses["balanced"],
            degen=responses["degen"],
            metadata=metadata,
        )

    except ValueError as e:
        import traceback

        print(f"ValueError in triple parlay generation: {e}")
        print(traceback.format_exc())
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback

        print(f"Exception in triple parlay generation: {e}")
        print(traceback.format_exc())
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate triple parlays: {str(e)}")


# ============================================================================
# Custom Parlay Analysis Endpoint
# ============================================================================

def _get_recommendation(confidence: float, edge: float) -> str:
    """Get recommendation level based on confidence and edge"""
    if confidence >= 70 and edge >= 0.02:
        return "strong"
    elif confidence >= 55 and edge >= 0:
        return "moderate"
    elif confidence >= 40:
        return "weak"
    else:
        return "avoid"


def _get_overall_recommendation(overall_confidence: float, weak_leg_count: int, num_legs: int) -> str:
    """Get overall parlay recommendation"""
    weak_ratio = weak_leg_count / num_legs if num_legs > 0 else 0
    
    if overall_confidence >= 65 and weak_ratio < 0.2:
        return "strong_play"
    elif overall_confidence >= 50 and weak_ratio < 0.4:
        return "solid_play"
    elif overall_confidence >= 35:
        return "risky_play"
    else:
        return "avoid"


def _american_to_decimal(american_odds: str) -> float:
    """Convert American odds to decimal odds"""
    try:
        odds = int(american_odds.replace("+", ""))
        if odds > 0:
            return 1 + (odds / 100)
        else:
            return 1 + (100 / abs(odds))
    except:
        return 2.0  # Default even odds


def _decimal_to_american(decimal_odds: float) -> str:
    """Convert decimal odds to American odds"""
    if decimal_odds >= 2.0:
        american = int((decimal_odds - 1) * 100)
        return f"+{american}"
    else:
        american = int(-100 / (decimal_odds - 1))
        return str(american)


@router.post("/parlay/analyze", response_model=CustomParlayAnalysisResponse)
@rate_limit("30/hour")
async def analyze_custom_parlay(
    request: Request,
    parlay_request: CustomParlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_custom_builder_access)
):
    """
    Analyze a user-built custom parlay.
    
    Users select their own picks and the AI provides:
    - Probability estimates for each leg
    - Confidence scores
    - Combined parlay probability
    - AI analysis and recommendations
    
    Access Control:
    - Premium only feature
    - Returns 402 Payment Required if not premium
    """
    try:
        leg_analyses: List[CustomParlayLegAnalysis] = []
        combined_implied = 1.0
        combined_ai = 1.0
        parlay_decimal = 1.0
        weak_legs = []
        strong_legs = []
        
        for leg in parlay_request.legs:
            # Validate leg data
            if not leg.pick or not isinstance(leg.pick, str):
                raise HTTPException(status_code=422, detail=f"Invalid pick value for leg: {leg.pick}")
            if not leg.game_id:
                raise HTTPException(status_code=422, detail="Missing game_id for leg")
            if not leg.market_type:
                raise HTTPException(status_code=422, detail="Missing market_type for leg")
            
            # Fetch the game with markets and odds
            game_query = select(Game).options(
                selectinload(Game.markets).selectinload(Market.odds)
            ).where(Game.id == leg.game_id)
            
            result = await db.execute(game_query)
            game = result.scalar_one_or_none()
            
            if not game:
                raise HTTPException(status_code=404, detail=f"Game not found: {leg.game_id}")
            
            # Find the matching market
            matching_market = None
            matching_odds = None
            
            for market in game.markets:
                if market.market_type == leg.market_type:
                    matching_market = market
                    # Find the matching outcome
                    for odds in market.odds:
                        outcome_lower = str(odds.outcome).lower() if odds.outcome else ""
                        pick_lower = str(leg.pick).lower()
                        
                        # Match logic based on market type
                        if leg.market_type == "h2h":
                            # Match team name or home/away
                            if (pick_lower in outcome_lower or 
                                outcome_lower in pick_lower or
                                (pick_lower == "home" and game.home_team.lower() in outcome_lower) or
                                (pick_lower == "away" and game.away_team.lower() in outcome_lower)):
                                matching_odds = odds
                                break
                        elif leg.market_type == "spreads":
                            if (("home" in pick_lower and "home" in outcome_lower) or
                                ("away" in pick_lower and "away" in outcome_lower) or
                                (game.home_team.lower() in pick_lower and "home" in outcome_lower) or
                                (game.away_team.lower() in pick_lower and "away" in outcome_lower)):
                                matching_odds = odds
                                break
                        elif leg.market_type == "totals":
                            if pick_lower in outcome_lower:  # over/under
                                matching_odds = odds
                                break
                    break
            
            if not matching_market or not matching_odds:
                # Use provided odds or default
                odds_str = leg.odds or "-110"
                decimal_odds = _american_to_decimal(odds_str)
                implied_prob = 1 / decimal_odds
            else:
                odds_str = matching_odds.price
                decimal_odds = float(matching_odds.decimal_price)
                implied_prob = float(matching_odds.implied_prob)
            
            # Get probability engine for the sport
            prob_engine = get_probability_engine(db, game.sport)
            
            # Calculate AI-adjusted probability
            if matching_market and matching_odds:
                leg_analysis = await prob_engine.calculate_leg_probability_from_odds(
                    odds_obj=matching_odds,
                    market_id=matching_market.id,
                    outcome=matching_odds.outcome,
                    home_team=game.home_team,
                    away_team=game.away_team,
                    game_start_time=game.start_time,
                    market_type=leg.market_type
                )
                ai_prob = leg_analysis.get("adjusted_prob", implied_prob)
                confidence = leg_analysis.get("confidence_score", 50.0)
                edge = leg_analysis.get("edge", 0.0)
            else:
                # Fallback calculation
                ai_prob = implied_prob * 1.02  # Slight adjustment
                confidence = 50.0
                edge = 0.0
            
            # Ensure reasonable bounds
            ai_prob = min(0.95, max(0.05, ai_prob))
            
            # Build pick display
            if leg.market_type == "h2h":
                pick_display = f"{leg.pick} ML"
            elif leg.market_type == "spreads":
                point_str = f"{leg.point:+.1f}" if leg.point else ""
                pick_display = f"{leg.pick} {point_str}"
            elif leg.market_type == "totals":
                point_str = f"{leg.point}" if leg.point else ""
                pick_display = f"{leg.pick.upper()} {point_str}"
            else:
                pick_display = leg.pick
            
            recommendation = _get_recommendation(confidence, edge)
            
            leg_analysis_obj = CustomParlayLegAnalysis(
                game_id=str(game.id),
                game=f"{game.away_team} @ {game.home_team}",
                home_team=game.home_team,
                away_team=game.away_team,
                sport=game.sport or "NFL",
                market_type=leg.market_type,
                pick=leg.pick,
                pick_display=pick_display,
                odds=odds_str,
                decimal_odds=round(decimal_odds, 2),
                implied_probability=round(implied_prob * 100, 1),
                ai_probability=round(ai_prob * 100, 1),
                confidence=round(confidence, 1),
                edge=round(edge * 100, 2),  # Convert to percentage
                recommendation=recommendation
            )
            
            leg_analyses.append(leg_analysis_obj)
            
            # Accumulate probabilities
            combined_implied *= implied_prob
            combined_ai *= ai_prob
            parlay_decimal *= decimal_odds
            
            # Track weak/strong legs
            if recommendation == "avoid" or recommendation == "weak":
                weak_legs.append(f"{leg_analysis_obj.game}: {pick_display}")
            elif recommendation == "strong":
                strong_legs.append(f"{leg_analysis_obj.game}: {pick_display}")
        
        # Calculate overall metrics
        num_legs = len(leg_analyses)
        avg_confidence = sum(l.confidence for l in leg_analyses) / num_legs if num_legs > 0 else 0
        
        # Adjust confidence based on number of legs (more legs = more risk)
        leg_penalty = max(0, (num_legs - 3) * 2)  # 2% penalty per leg beyond 3
        overall_confidence = max(10, avg_confidence - leg_penalty)
        
        confidence_color = _get_confidence_color(overall_confidence)
        overall_recommendation = _get_overall_recommendation(overall_confidence, len(weak_legs), num_legs)
        
        # Generate AI analysis
        openai_service = OpenAIService()
        
        legs_summary = []
        for leg in leg_analyses:
            legs_summary.append({
                "game": leg.game,
                "pick": leg.pick_display,
                "odds": leg.odds,
                "confidence": leg.confidence,
                "recommendation": leg.recommendation,
                "ai_probability": leg.ai_probability
            })
        
        ai_explanation = await openai_service.generate_custom_parlay_analysis(
            legs=legs_summary,
            combined_ai_probability=combined_ai * 100,
            overall_confidence=overall_confidence,
            weak_legs=weak_legs,
            strong_legs=strong_legs
        )
        
        return CustomParlayAnalysisResponse(
            legs=leg_analyses,
            num_legs=num_legs,
            combined_implied_probability=round(combined_implied * 100, 2),
            combined_ai_probability=round(combined_ai * 100, 2),
            overall_confidence=round(overall_confidence, 1),
            confidence_color=confidence_color,
            parlay_odds=_decimal_to_american(parlay_decimal),
            parlay_decimal_odds=round(parlay_decimal, 2),
            ai_summary=ai_explanation.get("summary", ""),
            ai_risk_notes=ai_explanation.get("risk_notes", ""),
            ai_recommendation=overall_recommendation,
            weak_legs=weak_legs,
            strong_legs=strong_legs
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error analyzing custom parlay: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to analyze parlay: {str(e)}")


# ============================================================================
# Upset Finder Endpoint (Premium Only)
# ============================================================================

@router.get("/parlay/upsets/{sport}")
@rate_limit("20/hour")
async def find_upsets(
    request: Request,
    sport: str,
    min_edge: float = 0.03,
    max_results: int = 20,
    risk_tier: Optional[str] = None,
    week: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_upset_finder_access),
):
    """
    Find upset candidates with positive expected value.
    
    The Gorilla Upset Finder identifies plus-money underdogs where
    the model sees an edge over the market.
    
    Parameters:
    - sport: Sport code (NFL, NBA, NHL, etc.)
    - min_edge: Minimum edge threshold (default 0.03 = 3%)
    - max_results: Maximum candidates to return (default 20)
    - risk_tier: Filter by risk level (low, medium, high)
    - week: NFL week filter (optional)
    
    Access Control:
    - Premium only feature
    - Returns 402 Payment Required if not premium
    """
    from app.services.upset_finder import get_upset_finder
    
    try:
        finder = get_upset_finder(db, sport.upper())
        
        upsets = await finder.find_upsets(
            min_edge=min_edge,
            max_results=max_results,
            risk_tier=risk_tier,
            week=week,
        )
        
        return {
            "sport": sport.upper(),
            "count": len(upsets),
            "upsets": [u.to_dict() for u in upsets],
        }
    
    except Exception as e:
        import traceback
        print(f"Error finding upsets: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to find upsets: {str(e)}")
