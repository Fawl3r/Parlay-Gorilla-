"""Parlay API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, List
import logging
import asyncio

from app.core.dependencies import get_db, get_current_user
from app.core.access_control import (
    enforce_free_parlay_limit,
    check_and_increment_parlay_usage,
    check_parlay_access_with_purchase,
    consume_parlay_access,
    PaywallException,
    AccessErrorCode,
)
from app.core.config import settings
from app.models.user import User
from app.schemas.parlay import (
    ParlayRequest,
    ParlayResponse,
    TripleParlayRequest,
    TripleParlayResponse,
)
from app.services.parlay_builder import ParlayBuilderService
from app.services.mixed_sports_parlay import MixedSportsParlayBuilder
from app.services.openai_service import OpenAIService
from app.services.cache_manager import CacheManager
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
        # Include model metrics if available
        parlay_ev=parlay_data.get("parlay_ev"),
        model_confidence=parlay_data.get("model_confidence"),
        upset_count=parlay_data.get("upset_count", 0),
        model_version=parlay_data.get("model_version"),
    )

    return response


@router.post("/parlay/suggest", response_model=ParlayResponse)
@rate_limit("20/hour")  # Limit expensive parlay generation
async def suggest_parlay(
    request: Request,
    parlay_request: ParlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a parlay suggestion based on parameters.
    
    Supports mixed sports parlays when sports list is provided.
    Mixed sports parlays help reduce correlation between legs.
    
    Access Control:
    - Premium users: Unlimited
    - Free users: 3 AI parlays per day
    - After free limit: Can purchase individual parlays ($3 single, $5 multi)
    
    Returns 402 Payment Required with error_code:
    - FREE_LIMIT_REACHED: No free parlays left and no purchase available
    - PAY_PER_USE_REQUIRED: Needs to purchase a parlay to continue
    """
    try:
        import traceback
        
        # Determine if this is a mixed sports request
        sports = parlay_request.sports or ["NFL"]
        is_mixed = parlay_request.mix_sports or (parlay_request.sports and len(parlay_request.sports) > 1)
        
        # Check access with purchase support
        access_info = await check_parlay_access_with_purchase(
            user=current_user,
            db=db,
            is_multi_sport=is_mixed,
        )
        
        if not access_info["can_generate"]:
            # User cannot generate - raise appropriate error
            logger.info(f"User {current_user.id} blocked from parlay generation: {access_info['error_code']}")
            
            raise PaywallException(
                error_code=access_info["error_code"],
                message="You've used all 3 free AI parlays for today. Purchase a single parlay or upgrade to Gorilla Premium!",
                remaining_today=access_info.get("remaining_free", 0),
                feature="ai_parlay",
                parlay_type="multi" if is_mixed else "single",
                single_price=settings.single_parlay_price_dollars,
                multi_price=settings.multi_parlay_price_dollars,
            )
        
        # Store access info for later consumption
        access_info["is_multi_sport"] = is_mixed
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
            # Build parlay with timeout protection (150 seconds max for building)
            try:
                if is_mixed and len(sports) > 1:
                    print(f"Building mixed sports parlay from: {sports} for week {week}")
                    mixed_builder = MixedSportsParlayBuilder(db)
                    parlay_data = await asyncio.wait_for(
                        mixed_builder.build_mixed_parlay(
                            num_legs=parlay_request.num_legs,
                            sports=sports,
                            risk_profile=parlay_request.risk_profile,
                            balance_sports=True,
                            week=week
                        ),
                        timeout=150.0  # 150 second timeout for parlay building
                    )
                else:
                    # Single sport parlay
                    sport = sports[0] if sports else "NFL"
                    print(f"Building single sport parlay from: {sport} for week {week}")
                    builder = ParlayBuilderService(db, sport=sport)
                    parlay_data = await asyncio.wait_for(
                        builder.build_parlay(
                            num_legs=parlay_request.num_legs,
                            risk_profile=parlay_request.risk_profile,
                            sport=sport,
                            week=week
                        ),
                        timeout=150.0  # 150 second timeout for parlay building
                    )
            except asyncio.TimeoutError:
                logger.error(f"Parlay building timed out after 150 seconds")
                raise HTTPException(
                    status_code=504,
                    detail="Parlay generation timed out. The system is taking longer than expected. Please try again with fewer legs or a different risk profile."
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
            
            # Consume parlay access (free or purchased) AFTER successful generation
            await consume_parlay_access(current_user, db, access_info)
            
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

"""
NOTE:
Custom parlay analysis and upset-finder endpoints were split out to keep this
module focused and smaller:
- `app.api.routes.custom_parlay`
- `app.api.routes.upset_finder`
"""
