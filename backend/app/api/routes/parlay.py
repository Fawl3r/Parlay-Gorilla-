"""Parlay API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, List
import logging
import asyncio

from app.core.dependencies import get_db, get_current_user, get_optional_user
from app.services.entitlements import EntitlementService
from app.core.access_control import (
    check_parlay_access_with_purchase,
    consume_parlay_access,
    PaywallException,
    AccessErrorCode,
)
from app.core.config import settings
from app.core.event_logger import log_event
from app.models.user import User
from app.schemas.parlay import (
    ParlayRequest,
    ParlayResponse,
    ParlaySuggestError,
    InsufficientCandidatesError,
    RequestMode,
    TripleParlayRequest,
    TripleParlayResponse,
)
from app.services.parlay_builder import ParlayBuilderService
from app.services.parlay_eligibility_service import get_parlay_eligibility, derive_hint_from_reasons
from app.core.parlay_errors import InsufficientCandidatesException
from app.core.safety_mode import (
    require_generation_allowed,
    get_safety_state,
    get_safety_snapshot,
    SafetyModeBlocked,
    apply_degraded_policy,
)
from app.core import telemetry
from app.services.mixed_sports_parlay import MixedSportsParlayBuilder
from app.services.openai_service import OpenAIService
from app.services.parlay_explanation_manager import ParlayExplanationManager
from app.services.cache_manager import CacheManager
from app.services.badge_service import BadgeService
from app.services.subscription_service import SubscriptionService
from app.services.guards.generator_guard import get_generator_guard
from app.utils.memory import log_mem
from app.models.parlay import Parlay
from app.middleware.rate_limiter import rate_limit
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/parlay/candidate-legs-count")
async def get_candidate_legs_count(
    sport: str,
    week: Optional[int] = None,
    num_legs: Optional[int] = None,
    include_player_props: Optional[bool] = None,
    request_mode: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get the count of available candidate legs (single eligibility source).
    When request_mode=TRIPLE, also returns strong_edges (games with >= TRIPLE_MIN_CONFIDENCE leg).
    When count is zero, returns top_exclusion_reasons for preflight UI.
    """
    try:
        legs = num_legs if num_legs is not None else 5
        include_props = include_player_props if include_player_props is not None else False
        eligibility = await get_parlay_eligibility(
            db=db,
            sport=sport,
            num_legs=legs,
            week=week,
            include_player_props=include_props,
            request_mode=request_mode,
        )
        out = {
            "sport": sport.upper(),
            "week": week,
            "candidate_legs_count": eligibility.eligible_count,
            "unique_games": eligibility.unique_games,
            "available": eligibility.eligible_count > 0,
            "top_exclusion_reasons": eligibility.exclusion_reasons[:5] if eligibility.eligible_count == 0 else [],
            "debug_id": eligibility.debug_id,
        }
        if (request_mode or "").upper() == "TRIPLE":
            out["strong_edges"] = getattr(eligibility, "strong_edges", 0)
        return out
    except Exception as e:
        logger.error(f"Error getting candidate legs count for {sport}: {e}")
        return {
            "sport": sport.upper(),
            "week": week,
            "candidate_legs_count": 0,
            "unique_games": 0,
            "available": False,
            "top_exclusion_reasons": ["error_loading_eligibility"],
            "error": str(e),
        }


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
    fallback_used: Optional[bool] = None,
    fallback_stage: Optional[str] = None,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    sports: Optional[List[str]] = None,
    safety_mode: Optional[str] = None,
    safety_warning: Optional[str] = None,
    safety_reasons: Optional[List[str]] = None,
    requested_legs: Optional[int] = None,
    final_legs: Optional[int] = None,
    degraded_policies_applied: Optional[List[str]] = None,
) -> ParlayResponse:
    """Generate AI explanation (fail-safe), persist parlay, and return ParlayResponse."""
    # Defensive validation
    if not parlay_data or not isinstance(parlay_data, dict):
        raise ValueError("parlay_data must be a non-empty dictionary")
    
    required_keys = ["legs", "parlay_hit_prob", "overall_confidence", "num_legs", "confidence_scores"]
    missing_keys = [key for key in required_keys if key not in parlay_data]
    if missing_keys:
        raise ValueError(f"Missing required keys in parlay_data: {missing_keys}")
    
    explanation_fallback_used = False
    explanation_fallback_error_type: Optional[str] = None

    if explanation_override:
        explanation = explanation_override
    else:
        manager = ParlayExplanationManager(openai_service=openai_service)
        explanation, explanation_fallback_used, explanation_fallback_error_type = (
            await manager.get_explanation(
                parlay_data=parlay_data,
                risk_profile=risk_profile,
                request_id=request_id,
                user_id=user_id,
                sports=sports,
            )
            )

    explain_meta = dict(parlay_data.get("explain") or {})
    if explanation_fallback_used:
        explain_meta["explanation_fallback_used"] = True
        if explanation_fallback_error_type:
            explain_meta["explanation_fallback_error_type"] = explanation_fallback_error_type

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
        
        # Create parlay_legs records for settlement tracking
        try:
            from app.services.parlay_leg_creator import ParlayLegCreator
            leg_creator = ParlayLegCreator(db)
            await leg_creator.create_legs_from_json(
                legs_json=parlay_data["legs"],
                parlay_id=parlay.id,
            )
        except Exception as leg_error:
            # Log but don't fail parlay creation if leg creation fails
            logger.warning(f"Error creating parlay_legs for parlay {parlay_id}: {leg_error}")
    except Exception as db_error:
        # Rollback the failed transaction
        await db.rollback()
        # Re-raise with user-friendly message - will be caught by global exception handler
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail="Unable to save your parlay. Please try again in a moment."
        ) from db_error

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
        parlay_ev=parlay_data.get("parlay_ev"),
        model_confidence=parlay_data.get("model_confidence"),
        upset_count=parlay_data.get("upset_count", 0),
        model_version=parlay_data.get("model_version"),
        fallback_used=fallback_used,
        fallback_stage=fallback_stage,
        mode_returned=parlay_data.get("mode_returned"),
        downgraded=parlay_data.get("downgraded"),
        downgrade_from=parlay_data.get("downgrade_from"),
        downgrade_reason_code=parlay_data.get("downgrade_reason_code"),
        downgrade_summary=parlay_data.get("downgrade_summary"),
        ui_suggestion=parlay_data.get("ui_suggestion"),
        explain=explain_meta if explain_meta else None,
        safety_mode=safety_mode,
        warning=safety_warning,
        reasons=safety_reasons,
        requested_legs=requested_legs,
        final_legs=final_legs,
        degraded_policies_applied=degraded_policies_applied,
    )

    return response


@router.post("/parlay/suggest", response_model=ParlayResponse)
@rate_limit("20/hour")  # Limit expensive parlay generation
async def suggest_parlay(
    request: Request,
    parlay_request: ParlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Generate a parlay suggestion based on parameters.
    
    Supports mixed sports parlays when sports list is provided.
    Mixed sports parlays help reduce correlation between legs.
    
    Access Control:
    - Anonymous: 401 login_required (ParlaySuggestError)
    - Mix sports + not premium: 403 premium_required (ParlaySuggestError)
    - No free quota and no credits: 402 credits_required (ParlaySuggestError)
    - Else: limited by rolling premium/free limit; after limit, pay-per-use.
    
    Returns 422 with ParlaySuggestError for expected failures (insufficient candidates, invalid filters).
    """
    trace_id = getattr(request.state, "request_id", None)
    sports = parlay_request.sports or ["NFL"]
    is_mixed = parlay_request.mix_sports or (parlay_request.sports and len(parlay_request.sports) > 1)

    # Entitlement gate: login, premium for mix_sports, credits when out of quota
    entitlement_service = EntitlementService(db)
    access = await entitlement_service.get_parlay_suggest_access(current_user, is_mixed)
    log_event(
        logger,
        "parlay_suggest_access",
        trace_id=trace_id,
        mix_sports=is_mixed,
        allowed=access.allowed,
        reason=access.reason,
        credits_remaining=access.credits_remaining,
        is_authenticated=current_user is not None,
    )
    if not access.allowed:
        code = access.reason or "invalid_request"
        status_code = 401 if code == "login_required" else (403 if code == "premium_required" else 402)
        payload = ParlaySuggestError(
            code=code,
            message=(
                "Sign in to generate parlays." if code == "login_required" else
                "Mix Sports is a Premium feature. Upgrade to unlock." if code == "premium_required" else
                "No credits remaining. Buy credits or use your free parlays."
            ),
            hint=(
                None if code == "login_required" else
                "Upgrade to Elite to use Mix Sports." if code == "premium_required" else
                "Buy credits or wait for your free parlay limit to reset."
            ),
            meta={"credits_remaining": access.credits_remaining} if access.reason else None,
        ).model_dump()
        return JSONResponse(status_code=status_code, content=payload)

    assert current_user is not None  # Guaranteed by entitlement check above

    # Request deduplication: same user + same options within 45s → friendly 409 (avoids duplicate load)
    try:
        from app.services.redis.redis_client_provider import get_redis_provider
        import hashlib
        dedupe_payload = f"{sports}_{parlay_request.num_legs}_{parlay_request.risk_profile or 'balanced'}"
        dedupe_hash = hashlib.sha256(dedupe_payload.encode()).hexdigest()[:16]
        dedupe_key = f"parlay_dedup:{current_user.id}:{dedupe_hash}"
        redis = get_redis_provider()
        if redis.is_configured():
            client = redis.get_client()
            if await client.get(dedupe_key):
                return JSONResponse(
                    status_code=409,
                    content={
                        "detail": "Please wait a moment before requesting the same parlay again.",
                        "code": "request_dedupe",
                    },
                )
            await client.set(dedupe_key, "1", ex=45)
    except Exception:
        pass  # Fail open: if Redis errors, allow request to proceed

    try:
        import traceback
        
        # Check access with purchase support (limits + pay-per-use)
        try:
            access_info = await check_parlay_access_with_purchase(
                user=current_user,
                db=db,
                is_multi_sport=is_mixed,
            )
        except Exception as access_error:
            error_type = type(access_error).__name__
            logger.error(
                f"Access check failed: {error_type}: {str(access_error)}",
                extra={
                    "error_type": error_type,
                    "error_message": str(access_error),
                    "user_id": str(current_user.id) if current_user else None,
                },
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to check parlay access: {str(access_error)}"
            )
        
        if not access_info or not isinstance(access_info, dict) or not access_info.get("can_generate"):
            # User cannot generate - raise appropriate error
            error_code = access_info.get("error_code") if isinstance(access_info, dict) else AccessErrorCode.FREE_LIMIT_REACHED
            logger.info(f"User {current_user.id} blocked from parlay generation: {error_code}")

            is_premium = bool(access_info.get("is_premium")) if isinstance(access_info, dict) else False
            remaining_free = int(access_info.get("remaining_free") or 0) if isinstance(access_info, dict) else 0

            if is_premium:
                message = (
                    f"You've used all {settings.premium_ai_parlays_per_month} parlays in your current "
                    f"{settings.premium_ai_parlays_period_days}-day period. Limit resets automatically."
                )
            elif (access_info.get("error_code") if isinstance(access_info, dict) else None) == AccessErrorCode.PAY_PER_USE_REQUIRED:
                message = (
                    f"You've used all {settings.free_parlays_per_week} free parlays for this week. "
                    "Buy credits or upgrade to Elite."
                )
            else:
                message = "No access available. Buy credits or upgrade to Elite."

            raise PaywallException(
                error_code=error_code,
                message=message,
                remaining_today=remaining_free,
                feature="ai_parlay",
                parlay_type="multi" if is_mixed else "single",
                single_price=settings.single_parlay_price_dollars,
                multi_price=settings.multi_parlay_price_dollars,
            )
        
        # Store access info for later consumption
        if isinstance(access_info, dict):
            access_info["is_multi_sport"] = is_mixed
        week = parlay_request.week  # Week filter for NFL games
        
        # Check premium status for player props
        subscription_service = SubscriptionService(db)
        is_premium_user = await subscription_service.is_user_premium(str(current_user.id))
        include_player_props = parlay_request.include_player_props
        
        # Validate: only premium users can request player props
        if include_player_props and not is_premium_user:
            raise HTTPException(
                status_code=403,
                detail="Player props are only available for premium users. Please upgrade to Elite to access this feature."
            )

        # Safety Mode: load critical telemetry from Redis (if available) then check
        try:
            await telemetry.load_critical_from_redis()
        except Exception:
            pass
        try:
            require_generation_allowed()
        except SafetyModeBlocked as block:
            if getattr(settings, "admin_alerts_enabled", False):
                try:
                    from app.services.alerting import get_alerting_service
                    await get_alerting_service().emit(
                        "safety_mode.red",
                        "critical",
                        {"message": block.message, "reasons": block.reasons},
                    )
                except Exception:
                    pass
            resp = JSONResponse(
                status_code=503,
                content={
                    "safety_mode": "RED",
                    "message": block.message,
                    "reasons": block.reasons,
                },
            )
            resp.headers["X-Safety-Mode"] = "RED"
            resp.headers["X-Safety-Reasons"] = ",".join(block.reasons)[:200]
            return resp
        safety_state = get_safety_state()
        requested_legs_orig = parlay_request.num_legs
        adjusted_params, degraded_policies = apply_degraded_policy({
            "num_legs": parlay_request.num_legs,
            "risk_profile": parlay_request.risk_profile,
        })
        parlay_request.num_legs = adjusted_params.get("num_legs", parlay_request.num_legs)
        safety_yellow_reasons: Optional[List[str]] = None
        if safety_state == "YELLOW":
            snap = get_safety_snapshot()
            safety_yellow_reasons = snap.get("reasons") or []

        logger.info(
            "Parlay request received: num_legs=%s, risk_profile=%s, sports=%s, mix_sports=%s, week=%s, include_player_props=%s",
            parlay_request.num_legs,
            parlay_request.risk_profile,
            sports,
            is_mixed,
            week,
            include_player_props,
        )
        
        # request_mode: TRIPLE = confidence-gated 3-pick only (no fallback, no cache)
        request_mode_val = (
            (parlay_request.request_mode or RequestMode.SINGLE).value
            if hasattr(parlay_request.request_mode or RequestMode.SINGLE, "value")
            else str(parlay_request.request_mode or "SINGLE")
        )
        is_triple_request = (request_mode_val == "TRIPLE" and parlay_request.num_legs == 3)

        # Generate cache key based on request (include week)
        cache_key_sport = "_".join(sorted(s.upper() for s in sports))
        cache_key = f"{cache_key_sport}_week_{week}" if week else cache_key_sport
        cache_manager = CacheManager(db)

        # Check cache first (skip for mixed, week-specific, or Triple).
        # Triple is confidence-gated and must reflect current slate; do not reuse cached non-TRIPLE results.
        cached_parlay = None
        if not is_mixed and not week and not is_triple_request:
            cached_parlay = await cache_manager.get_cached_parlay(
                num_legs=parlay_request.num_legs,
                risk_profile=parlay_request.risk_profile,
                sport=cache_key,
                max_age_hours=6
            )

        if cached_parlay:
            logger.info("Using cached parlay data")
            parlay_data = cached_parlay
        else:
            guard = get_generator_guard()
            guard_token = await guard.try_acquire("parlay_generate", ttl_s=180)
            if guard_token is None:
                log_event(
                    logger,
                    "parlay.generator_busy",
                    trace_id=getattr(request.state, "request_id", None),
                    endpoint="/parlay/suggest",
                    user_id=str(current_user.id) if current_user and hasattr(current_user, "id") else None,
                    environment=getattr(settings, "environment", "unknown"),
                )
                return JSONResponse(
                    status_code=settings.generator_busy_http_status,
                    content={
                        "detail": "We're generating lots of parlays right now. Please try again in a moment.",
                        "code": "generator_busy",
                    },
                )
            try:
                # Build parlay with timeout protection (150 seconds max for building)
                if is_triple_request and not is_mixed:
                    # Triple (confidence-gated): STRICT only, no fallback ladder
                    sport = sports[0] if sports else "NFL"
                    trace_id = getattr(request.state, "request_id", None)
                    builder = ParlayBuilderService(db, sport=sport)
                    try:
                        parlay_data = await asyncio.wait_for(
                            builder.build_parlay(
                                num_legs=3,
                                risk_profile=parlay_request.risk_profile,
                                sport=sport,
                                week=week,
                                include_player_props=include_player_props,
                                trace_id=trace_id,
                                request_mode="TRIPLE",
                            ),
                            timeout=settings.parlay_generation_timeout_s,
                        )
                    except InsufficientCandidatesException as triple_err:
                        eligibility = await get_parlay_eligibility(
                            db=db,
                            sport=sport,
                            num_legs=3,
                            week=week,
                            include_player_props=include_player_props,
                            trace_id=trace_id,
                            request_mode="TRIPLE",
                        )
                        hint = derive_hint_from_reasons(
                            eligibility.exclusion_reasons,
                            allow_player_props=access.features.get("player_props", False),
                            allow_mix_sports=access.features.get("mix_sports", False),
                        ) or "Try 2 picks or expand time window."
                        payload = InsufficientCandidatesError(
                            code="NOT_ENOUGH_GAMES",
                            message="Not enough eligible games with clean odds right now. Try a smaller parlay or check back soon.",
                            hint=hint,
                            needed=3,
                            have=eligibility.eligible_count,
                            top_exclusion_reasons=eligibility.exclusion_reasons[:5],
                            debug_id=eligibility.debug_id,
                            meta={
                                "sports": sports,
                                "mix_sports": is_mixed,
                                "week": week,
                                "num_legs": 3,
                                "strong_edges": getattr(eligibility, "strong_edges", 0),
                                "unique_games": eligibility.unique_games,
                            },
                        ).model_dump()
                        logger.info(
                            "parlay_insufficient_candidates",
                            extra={
                                "debug_id": eligibility.debug_id,
                                "needed": 3,
                                "have": eligibility.eligible_count,
                                "exclusion_reasons": eligibility.exclusion_reasons,
                                "reason": "triple_not_enough_games",
                            },
                        )
                        log_event(
                            logger,
                            "parlay_suggest_failed",
                            trace_id=trace_id,
                            reason="triple_not_enough_games",
                            error=str(triple_err),
                            debug_id=eligibility.debug_id,
                            have_eligible=eligibility.eligible_count,
                            have_strong=getattr(eligibility, "strong_edges", 0),
                        )
                        return JSONResponse(status_code=409, content=payload)
                    except ValueError as triple_err:
                        # Non-insufficient ValueError from Triple path: re-raise so it bubbles as 500
                        raise
                elif is_mixed and len(sports) > 1:
                    logger.info("Building mixed sports parlay from: %s for week %s", sports, week)
                    mixed_builder = MixedSportsParlayBuilder(db)
                    parlay_data = await asyncio.wait_for(
                        mixed_builder.build_mixed_parlay(
                            num_legs=parlay_request.num_legs,
                            sports=sports,
                            risk_profile=parlay_request.risk_profile,
                            balance_sports=True,
                            week=week,
                            include_player_props=include_player_props
                        ),
                        timeout=settings.parlay_generation_timeout_s,
                    )
                else:
                    # Single sport parlay with fallback ladder
                    sport = sports[0] if sports else "NFL"
                    trace_id = getattr(request.state, "request_id", None)
                    builder = ParlayBuilderService(db, sport=sport)
                    fallback_used_flag = False
                    fallback_stage_val: Optional[str] = None
                    fallback_stages = []
                    if week is not None:
                        fallback_stages.append(("week_expanded", None, include_player_props))
                    fallback_stages.append(("ml_only", week, False))
                    if week is not None:
                        fallback_stages.append(("week_expanded_ml_only", None, False))
                    parlay_data = None
                    last_error: Optional[BaseException] = None
                    try:
                        parlay_data = await asyncio.wait_for(
                            builder.build_parlay(
                                num_legs=parlay_request.num_legs,
                                risk_profile=parlay_request.risk_profile,
                                sport=sport,
                                week=week,
                                include_player_props=include_player_props,
                                trace_id=trace_id,
                            ),
                            timeout=settings.parlay_generation_timeout_s,
                        )
                    except (ValueError, InsufficientCandidatesException) as e:
                        last_error = e
                    for stage_name, try_week, try_props in fallback_stages:
                        if parlay_data and parlay_data.get("legs"):
                            break
                        try:
                            parlay_data = await asyncio.wait_for(
                                builder.build_parlay(
                                    num_legs=parlay_request.num_legs,
                                    risk_profile=parlay_request.risk_profile,
                                    sport=sport,
                                    week=try_week,
                                    include_player_props=try_props,
                                    trace_id=trace_id,
                                ),
                                timeout=settings.parlay_generation_timeout_s,
                            )
                            if parlay_data and parlay_data.get("legs"):
                                fallback_used_flag = True
                                fallback_stage_val = stage_name
                                logger.info(
                                    "parlay_suggest_fallback_used",
                                    extra={
                                        "trace_id": trace_id,
                                        "fallback_stage": stage_name,
                                        "needed": parlay_request.num_legs,
                                        "sport": sport,
                                        "week": try_week,
                                        "include_player_props": try_props,
                                    },
                                )
                                log_event(logger, "parlay_suggest_fallback_used", trace_id=trace_id, stage=stage_name)
                                break
                        except (ValueError, InsufficientCandidatesException):
                            continue
                    if not parlay_data or not parlay_data.get("legs"):
                        if last_error:
                            raise last_error
                        from app.core.parlay_errors import record_insufficient_and_raise
                        record_insufficient_and_raise(
                            needed=parlay_request.num_legs,
                            have=0,
                            message="Not enough games available to build parlay with current filters.",
                        )
                    if fallback_used_flag and fallback_stage_val:
                        parlay_data["_fallback_used"] = True
                        parlay_data["_fallback_stage"] = fallback_stage_val
            except asyncio.TimeoutError:
                trace_id = getattr(request.state, "request_id", None)
                log_event(
                    logger,
                    "parlay.generation_timeout",
                    trace_id=trace_id,
                    endpoint="/parlay/suggest",
                    user_id=str(current_user.id) if current_user and hasattr(current_user, "id") else None,
                    environment=getattr(settings, "environment", "unknown"),
                )
                logger.error("Parlay building timed out after %s seconds", settings.parlay_generation_timeout_s)
                raise HTTPException(
                    status_code=504,
                    detail="This is taking longer than expected. Try again with fewer legs."
                )
            except MemoryError as oom:
                debug_id = (getattr(request.state, "request_id", None) or str(uuid.uuid4()))[:8]
                logger.warning(
                    "parlay_suggest_oom debug_id=%s path=/parlay/suggest error=%s",
                    debug_id,
                    oom,
                    exc_info=True,
                )
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": "We're under heavy load. Try fewer picks or single sport.",
                        "debug_id": debug_id,
                    },
                )
            finally:
                await guard.release("parlay_generate", guard_token)

            # Cache the result (skip for week-specific or Triple).
            # Triple is confidence-gated and must reflect current slate; do not reuse cached non-TRIPLE results.
            if not is_mixed and not week and not is_triple_request:
                await cache_manager.set_cached_parlay(
                    num_legs=parlay_request.num_legs,
                    risk_profile=parlay_request.risk_profile,
                    parlay_data=parlay_data,
                    sport=cache_key,
                    ttl_hours=6
                )
        
        # Validate parlay_data structure
        if not parlay_data or not isinstance(parlay_data, dict):
            logger.error(f"Invalid parlay_data: {type(parlay_data)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate parlay: Invalid parlay data structure"
            )
        
        required_keys = ["legs", "parlay_hit_prob", "overall_confidence", "num_legs", "confidence_scores"]
        missing_keys = [key for key in required_keys if key not in parlay_data]
        if missing_keys:
            logger.error(f"Missing required keys in parlay_data: {missing_keys}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate parlay: Missing required data fields: {', '.join(missing_keys)}"
            )
        
        if not parlay_data.get("legs") or len(parlay_data.get("legs", [])) == 0:
            sport = sports[0] if sports else "NFL"
            eligibility = await get_parlay_eligibility(
                db=db,
                sport=sport,
                num_legs=parlay_request.num_legs,
                week=week,
                include_player_props=include_player_props,
                trace_id=trace_id,
            )
            msg = "Not enough games available to build parlay with current filters."
            hint = derive_hint_from_reasons(
                eligibility.exclusion_reasons,
                allow_player_props=access.features.get("player_props", False),
                allow_mix_sports=access.features.get("mix_sports", False),
            ) or "Try lowering legs, switching week to 'All upcoming', or ML-only (no player props)."
            payload = InsufficientCandidatesError(
                message=msg,
                hint=hint,
                needed=parlay_request.num_legs,
                have=eligibility.eligible_count,
                top_exclusion_reasons=eligibility.exclusion_reasons[:5],
                debug_id=eligibility.debug_id,
                meta={
                    "sports": sports,
                    "mix_sports": is_mixed,
                    "week": week,
                    "num_legs": parlay_request.num_legs,
                    "risk_profile": parlay_request.risk_profile,
                    "unique_games": eligibility.unique_games,
                },
            ).model_dump()
            logger.info(
                "parlay_insufficient_candidates",
                extra={
                    "debug_id": eligibility.debug_id,
                    "needed": parlay_request.num_legs,
                    "have": eligibility.eligible_count,
                    "exclusion_reasons": eligibility.exclusion_reasons,
                    "reason": "no_legs",
                },
            )
            log_event(
                logger,
                "parlay_suggest_failed",
                trace_id=trace_id,
                reason="no_legs",
                error=msg,
                sports=sports,
                mix_sports=is_mixed,
                week=week,
                num_legs=parlay_request.num_legs,
                debug_id=eligibility.debug_id,
                have=eligibility.eligible_count,
                exclusion_reasons=eligibility.exclusion_reasons,
            )
            return JSONResponse(status_code=409, content=payload)
        
        logger.info("Parlay data built: %s legs", len(parlay_data.get("legs", [])))
        if is_mixed:
            sports_in_parlay = set(leg.get("sport", "NFL") for leg in parlay_data.get("legs", []))
            logger.info("Sports included in parlay: %s", sports_in_parlay)
        
        openai_service = OpenAIService()
        try:
            response = await _prepare_parlay_response(
                parlay_data=parlay_data,
                risk_profile=parlay_request.risk_profile,
                openai_service=openai_service,
                db=db,
                current_user=current_user,
                fallback_used=parlay_data.get("_fallback_used"),
                fallback_stage=parlay_data.get("_fallback_stage"),
                request_id=trace_id,
                safety_mode="YELLOW" if safety_yellow_reasons else None,
                safety_warning="Limited data mode." if safety_yellow_reasons else None,
                safety_reasons=safety_yellow_reasons,
                user_id=str(current_user.id) if current_user and hasattr(current_user, "id") else None,
                sports=sports,
                requested_legs=requested_legs_orig,
                final_legs=int(parlay_data.get("num_legs", 0)),
                degraded_policies_applied=degraded_policies if safety_yellow_reasons else None,
            )
        except Exception as e:
            telemetry.inc("generation_failures_5m")
            telemetry.inc("error_count_5m")
            import traceback
            error_type = type(e).__name__
            tb_str = traceback.format_exc()
            logger.error(
                "Error building parlay response: %s: %s",
                error_type,
                str(e),
                extra={
                    "error_type": error_type,
                    "error_message": str(e),
                    "user_id": str(current_user.id) if current_user else None,
                    "traceback": tb_str,
                },
            )
            try:
                from app.services.alerting import get_alerting_service
                await get_alerting_service().emit(
                    "parlay.suggest.failure",
                    "error",
                    {
                        "request_id": trace_id,
                        "user_id": str(current_user.id) if current_user and hasattr(current_user, "id") else None,
                        "error_type": error_type,
                        "error_message": (str(e) or "")[:500],
                    },
                )
            except Exception:
                pass
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
            error_type = type(commit_error).__name__
            logger.error(
                f"Failed to commit parlay: {error_type}: {str(commit_error)}",
                extra={
                    "error_type": error_type,
                    "error_message": str(commit_error),
                    "user_id": str(current_user.id) if current_user else None,
                }
            )
            logger.warning("Failed to commit parlay: %s: %s", error_type, commit_error)
            await db.rollback()
        
        log_event(
            logger,
            "parlay_suggest_ok",
            trace_id=trace_id,
            sports=sports,
            mix_sports=is_mixed,
            week=week,
            legs=parlay_request.num_legs,
            risk=parlay_request.risk_profile,
            mode_returned=parlay_data.get("mode_returned"),
            downgraded=parlay_data.get("downgraded"),
            downgrade_reason_code=parlay_data.get("downgrade_reason_code"),
        )
        selected_legs = len(parlay_data.get("legs") or [])
        eligible_games = parlay_data.get("_eligible_games")
        log_mem(logger, "parlay_suggest_after_response_built", {"trace_id": trace_id, "selected_legs": selected_legs, "eligible_games": eligible_games})
        out = JSONResponse(content=response.model_dump(exclude_none=False))
        out.headers["X-Safety-Mode"] = safety_state or "GREEN"
        out.headers["X-Safety-Reasons"] = (",".join(safety_yellow_reasons)[:200]) if safety_yellow_reasons else ""
        return out
        
    except InsufficientCandidatesException as e:
        telemetry.inc("generation_failures_5m")
        telemetry.inc("error_count_5m")
        sport = (parlay_request.sports or ["NFL"])[0]
        eligibility = await get_parlay_eligibility(
            db=db,
            sport=sport,
            num_legs=e.needed,
            week=getattr(parlay_request, "week", None),
            include_player_props=getattr(parlay_request, "include_player_props", False),
            trace_id=trace_id,
        )
        msg = str(e) or "Not enough games available to build parlay with current filters."
        hint = derive_hint_from_reasons(
            eligibility.exclusion_reasons,
            allow_player_props=access.features.get("player_props", False),
            allow_mix_sports=access.features.get("mix_sports", False),
        ) or "Try lowering legs, switching week to 'All upcoming', or ML-only (no player props)."
        payload = InsufficientCandidatesError(
            message=msg,
            hint=hint,
            needed=e.needed,
            have=e.have,
            top_exclusion_reasons=eligibility.exclusion_reasons[:5],
            debug_id=eligibility.debug_id,
            meta={
                "sports": parlay_request.sports,
                "mix_sports": getattr(parlay_request, "mix_sports", None),
                "week": parlay_request.week,
                "num_legs": parlay_request.num_legs,
                "risk_profile": parlay_request.risk_profile,
                "unique_games": eligibility.unique_games,
            },
        ).model_dump()
        logger.info(
            "parlay_insufficient_candidates",
            extra={
                "debug_id": eligibility.debug_id,
                "needed": e.needed,
                "have": e.have,
                "exclusion_reasons": eligibility.exclusion_reasons,
                "reason": "insufficient_candidates_exception",
            },
        )
        log_event(
            logger,
            "parlay_suggest_failed",
            trace_id=trace_id,
            reason="insufficient_candidates",
            error=msg,
            debug_id=eligibility.debug_id,
            have=eligibility.eligible_count,
            exclusion_reasons=eligibility.exclusion_reasons,
        )
        return JSONResponse(status_code=409, content=payload)
    except ValueError as e:
        msg = str(e) or "Unable to generate parlay with current filters."
        error_str = msg.lower()
        is_insufficient = (
            "not enough" in error_str or "no games" in error_str or "candidate" in error_str or "could not fulfill" in error_str
        )
        if is_insufficient:
            sport = (parlay_request.sports or ["NFL"])[0]
            eligibility = await get_parlay_eligibility(
                db=db,
                sport=sport,
                num_legs=parlay_request.num_legs,
                week=getattr(parlay_request, "week", None),
                include_player_props=getattr(parlay_request, "include_player_props", False),
                trace_id=trace_id,
            )
            hint = derive_hint_from_reasons(
                eligibility.exclusion_reasons,
                allow_player_props=access.features.get("player_props", False),
                allow_mix_sports=access.features.get("mix_sports", False),
            ) or "Try lowering legs, switching week to 'All upcoming', or ML-only (no player props)."
            payload = InsufficientCandidatesError(
                message=msg,
                hint=hint,
                needed=parlay_request.num_legs,
                have=eligibility.eligible_count,
                top_exclusion_reasons=eligibility.exclusion_reasons[:5],
                debug_id=eligibility.debug_id,
                meta={
                    "sports": parlay_request.sports,
                    "mix_sports": getattr(parlay_request, "mix_sports", None),
                    "week": parlay_request.week,
                    "num_legs": parlay_request.num_legs,
                    "risk_profile": parlay_request.risk_profile,
                    "unique_games": eligibility.unique_games,
                },
            ).model_dump()
            logger.info(
                "parlay_insufficient_candidates",
                extra={
                    "debug_id": eligibility.debug_id,
                    "needed": parlay_request.num_legs,
                    "have": eligibility.eligible_count,
                    "exclusion_reasons": eligibility.exclusion_reasons,
                    "reason": "value_error_pattern",
                },
            )
            log_event(
                logger,
                "parlay_suggest_failed",
                trace_id=trace_id,
                reason="value_error",
                error=msg,
                debug_id=eligibility.debug_id,
                have=eligibility.eligible_count,
                exclusion_reasons=eligibility.exclusion_reasons,
            )
            return JSONResponse(status_code=409, content=payload)
        # Non-insufficient ValueError: return 500 so real bugs are visible in Sentry
        logger.error("parlay_suggest_value_error", extra={"error_message": msg, "reason": "non_insufficient"})
        raise HTTPException(status_code=500, detail=msg)
    except HTTPException:
        raise
    except Exception as e:
        telemetry.inc("generation_failures_5m")
        telemetry.inc("error_count_5m")
        import traceback
        error_type = type(e).__name__
        tb_str = traceback.format_exc()
        log_event(
            logger,
            "parlay_suggest_failed",
            trace_id=trace_id,
            reason="exception",
            error=repr(e),
            error_type=error_type,
        )
        logger.error(
            "Parlay generation failed: %s: %s",
            error_type,
            str(e),
            extra={
                "error_type": error_type,
                "error_message": str(e),
                "user_id": str(current_user.id) if current_user else None,
                "num_legs": getattr(parlay_request, "num_legs", None),
                "risk_profile": getattr(parlay_request, "risk_profile", None),
                "traceback": tb_str,
            },
        )
        try:
            from app.services.alerting import get_alerting_service
            await get_alerting_service().emit(
                "parlay.suggest.failure",
                "error",
                {
                    "request_id": trace_id,
                    "user_id": str(current_user.id) if current_user and hasattr(current_user, "id") else None,
                    "error_type": error_type,
                    "error_message": (str(e) or "")[:500],
                },
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Failed to generate parlay. Please try again or contact support if the problem persists.")


@router.post("/parlay/suggest/triple", response_model=TripleParlayResponse)
@rate_limit("10/hour")
async def suggest_triple_parlay(
    request: Request,
    triple_request: TripleParlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate Safe/Balanced/Degen parlays in a single request."""
    try:
        sports = triple_request.sports or ["NFL"]
        is_mixed = bool(triple_request.sports and len(triple_request.sports) > 1)

        # Triple generation counts as 3 usages (premium usage +3 or credits -30).
        access_info = await check_parlay_access_with_purchase(
            user=current_user,
            db=db,
            is_multi_sport=is_mixed,
            usage_units=3,
            allow_purchases=False,
        )

        if not access_info["can_generate"]:
            credits_required = int(access_info.get("credits_required") or 0)
            credits_available = int(access_info.get("credits_available") or 0)
            remaining_free = int(access_info.get("remaining_free") or 0)
            if credits_required and credits_available < credits_required:
                msg = (
                    f"Generating triple parlays costs {credits_required} credits. "
                    f"You currently have {credits_available} credits. Buy credits or upgrade to Premium."
                )
            else:
                msg = "You don't have access available for triple parlays. Buy credits or upgrade to Premium."

            raise PaywallException(
                error_code=access_info["error_code"],
                message=msg,
                remaining_today=remaining_free,
                feature="ai_parlay",
            )

        leg_overrides = {
            "safe": triple_request.safe_legs,
            "balanced": triple_request.balanced_legs,
            "degen": triple_request.degen_legs,
        }
        leg_overrides = {k: v for k, v in leg_overrides.items() if v is not None}

        guard = get_generator_guard()
        guard_token = await guard.try_acquire("parlay_generate", ttl_s=180)
        if guard_token is None:
            log_event(
                logger,
                "parlay.generator_busy",
                trace_id=getattr(request.state, "request_id", None),
                endpoint="/parlay/suggest/triple",
                user_id=str(current_user.id) if current_user and hasattr(current_user, "id") else None,
                environment=getattr(settings, "environment", "unknown"),
            )
            return JSONResponse(
                status_code=settings.generator_busy_http_status,
                content={
                    "detail": "We're generating lots of parlays right now. Please try again in a moment.",
                    "code": "generator_busy",
                },
            )
        async def _build_triple_response():
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
                highlight = ai_explanations.get(profile_name, {}).get("highlight_leg")
                metadata_block = block.get("config", {}).copy()
                if highlight:
                    metadata_block["highlight_leg"] = highlight
                metadata[profile_name] = metadata_block
                responses[profile_name] = parlay_response

            try:
                await db.commit()
                await consume_parlay_access(current_user, db, access_info)
                newly_unlocked_badges = []
                if current_user and hasattr(current_user, "id"):
                    try:
                        badge_service = BadgeService(db)
                        newly_unlocked_badges = await badge_service.check_and_award_badges(str(current_user.id))
                        if newly_unlocked_badges:
                            logger.info(f"User {current_user.id} earned {len(newly_unlocked_badges)} new badge(s) from triple parlay")
                            responses["safe"].newly_unlocked_badges = newly_unlocked_badges
                    except Exception as badge_error:
                        logger.warning(f"Badge check failed (non-critical): {badge_error}")
            except Exception as commit_error:
                logger.warning("Failed to commit triple parlay: %s", commit_error)
                await db.rollback()

            log_mem(logger, "parlay_triple_after_response_built", {"trace_id": getattr(request.state, "request_id", None)})
            return TripleParlayResponse(
                safe=responses["safe"],
                balanced=responses["balanced"],
                degen=responses["degen"],
                metadata=metadata,
            )

        try:
            return await asyncio.wait_for(
                _build_triple_response(),
                timeout=settings.parlay_generation_timeout_s,
            )
        except asyncio.TimeoutError:
            log_event(
                logger,
                "parlay.generation_timeout",
                trace_id=getattr(request.state, "request_id", None),
                endpoint="/parlay/suggest/triple",
                user_id=str(current_user.id) if current_user and hasattr(current_user, "id") else None,
                environment=getattr(settings, "environment", "unknown"),
            )
            logger.error(
                "Triple parlay building timed out after %s seconds",
                settings.parlay_generation_timeout_s,
            )
            raise HTTPException(
                status_code=504,
                detail="This is taking longer than expected. Try again with fewer legs.",
            )
        finally:
            await guard.release("parlay_generate", guard_token)

    except ValueError as e:
        import traceback
        logger.warning("ValueError in triple parlay generation: %s", e, exc_info=True)
        await db.rollback()
        error_str = str(e).lower()
        # Check for data availability issues (should be 503, not 400)
        if "not enough" in error_str or "no games" in error_str or "candidate" in error_str:
            raise HTTPException(
                status_code=503,
                detail=str(e)
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error("Exception in triple parlay generation: %s", e, exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate triple parlays: {str(e)}")

"""
NOTE:
Custom parlay analysis and upset-finder endpoints were split out to keep this
module focused and smaller:
- `app.api.routes.custom_parlay`
- `app.api.routes.upset_finder`
"""
