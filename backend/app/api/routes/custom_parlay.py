"""Custom parlay endpoints (user-selected legs)."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.access_control import AccessErrorCode, CustomBuilderAccess, PaywallException, require_custom_builder_access
from app.core.config import settings
from app.core.dependencies import get_db
from app.core.event_logger import log_event
from app.services.guards.generator_guard import get_generator_guard
from app.middleware.rate_limiter import rate_limit
from app.models.user import User
from app.schemas.parlay import (
    CounterParlayRequest,
    CounterParlayResponse,
    CustomParlayAnalysisResponse,
    CustomParlayLeg,
    CustomParlayRequest,
    HedgesRequest,
    ParlayCoverageRequest,
    ParlayCoverageResponse,
    VerificationRecordSummary,
)
from app.schemas.custom_builder_hedge import HedgesResponse
from app.services.custom_parlay import CounterParlayService, CustomParlayAnalysisService, ParlayCoverageService
from app.services.custom_builder.hedge_engine import HedgeEngine, build_upset_possibilities, is_supported_market
from app.services.custom_parlay_verification.auto_verification_service import CustomParlayAutoVerificationService
from app.services.subscription_service import SubscriptionService
from app.services.verification_records.viewer_url_builder import VerificationRecordViewerUrlBuilder

logger = logging.getLogger(__name__)
router = APIRouter()
_viewer_urls = VerificationRecordViewerUrlBuilder()

@router.post("/parlay/analyze", response_model=CustomParlayAnalysisResponse)
@rate_limit("30/hour")
async def analyze_custom_parlay(
    request: Request,
    parlay_request: CustomParlayRequest,
    db: AsyncSession = Depends(get_db),
    builder_access: CustomBuilderAccess = Depends(require_custom_builder_access),
):
    """
    Analyze a user-built custom parlay.

    Access:
    - Premium: includes 25 custom builder AI actions per rolling period (then credits for overage)
    - Credits: costs credits per AI action (settings.credits_cost_custom_builder_action)
    """
    _ = request
    current_user = builder_access.user
    try:
        # Check if user is trying to include player props (premium-only)
        has_player_props = any(leg.market_type == "player_props" for leg in parlay_request.legs)
        if has_player_props:
            subscription_service = SubscriptionService(db)
            is_premium = await subscription_service.is_user_premium(str(current_user.id))
            if not is_premium:
                raise HTTPException(
                    status_code=403,
                    detail="Player props are only available for premium users. Please upgrade to Elite to access this feature."
                )

        guard = get_generator_guard()
        guard_token = await guard.try_acquire("parlay_generate", ttl_s=180)
        if guard_token is None:
            log_event(
                logger,
                "parlay.generator_busy",
                trace_id=getattr(request.state, "request_id", None),
                endpoint="/parlay/analyze",
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
            service = CustomParlayAnalysisService(db)
            result = await service.analyze(parlay_request.legs)
        finally:
            await guard.release("parlay_generate", guard_token)

        subscription_service = SubscriptionService(db)
        is_premium = await subscription_service.is_user_premium(str(current_user.id))
        is_free_usage = not builder_access.use_credits and not is_premium
        
        if builder_access.use_credits:
            # Credit users pay per AI action (deduct after success)
            from app.core.config import settings
            from app.services.credit_balance_service import CreditBalanceService

            credits_required = int(builder_access.credits_required or getattr(settings, "credits_cost_custom_builder_action", 3))
            credit_service = CreditBalanceService(db)
            new_balance = await credit_service.try_spend(str(current_user.id), credits_required)
            if new_balance is None:
                raise PaywallException(
                    error_code=AccessErrorCode.PREMIUM_REQUIRED,
                    message=f"Custom builder AI actions cost {credits_required} credits. Buy credits or upgrade to Premium.",
                    feature="custom_builder",
                )
            logger.info(
                "Spent %s credits for custom analysis (user=%s, new_balance=%s)",
                credits_required,
                current_user.id,
                new_balance,
            )
        elif is_premium:
            # Premium included quota path
            await subscription_service.increment_custom_parlay_usage(str(current_user.id))
            logger.info("Used included premium custom builder action (user=%s)", current_user.id)
        else:
            # Free user weekly limit path
            await subscription_service.increment_free_custom_parlay_usage(str(current_user.id))
            logger.info("Used free custom builder action (user=%s)", current_user.id)

        # Automatic verification record (skip for free users to save costs).
        # Only create verification for premium users or credit-paid custom parlays.
        if not is_free_usage:
            try:
                record = await CustomParlayAutoVerificationService(db).ensure_verification_record(
                    user=current_user,
                    request_legs=parlay_request.legs,
                    analysis_legs=result.legs,
                )
                if record is not None:
                    result = result.model_copy(
                        update={
                            "verification": VerificationRecordSummary(
                                id=str(record.id),
                                status=str(record.status),
                                viewer_url=_viewer_urls.build(str(record.id)),
                            )
                        }
                    )
            except Exception:
                logger.exception("Custom parlay verification failed (non-fatal) user=%s", current_user.id)
        else:
            logger.info("Skipping verification for free user custom parlay (user=%s)", current_user.id)

        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to analyze parlay: {str(exc)}") from exc


@router.post("/parlay/counter", response_model=CounterParlayResponse)
@rate_limit("30/hour")
async def build_counter_parlay(
    request: Request,
    counter_request: CounterParlayRequest,
    db: AsyncSession = Depends(get_db),
    builder_access: CustomBuilderAccess = Depends(require_custom_builder_access),
):
    """
    Build a counter/hedge parlay for the same games as the user's ticket.

    Access:
    - Premium: includes 25 custom builder AI actions per rolling period (then credits for overage)
    - Credits: costs credits per AI action (settings.credits_cost_custom_builder_action)
    """
    current_user = builder_access.user
    _ = request, current_user
    try:
        analysis_service = CustomParlayAnalysisService(db)
        counter_service = CounterParlayService(analysis_service)
        result = await counter_service.generate(counter_request)

        if builder_access.use_credits:
            from app.core.config import settings
            from app.services.credit_balance_service import CreditBalanceService

            credits_required = int(builder_access.credits_required or getattr(settings, "credits_cost_custom_builder_action", 3))
            credit_service = CreditBalanceService(db)
            new_balance = await credit_service.try_spend(str(current_user.id), credits_required)
            if new_balance is None:
                raise PaywallException(
                    error_code=AccessErrorCode.PREMIUM_REQUIRED,
                    message=f"Custom builder AI actions cost {credits_required} credits. Buy credits or upgrade to Premium.",
                    feature="custom_builder",
                )
            logger.info(
                "Spent %s credits for counter parlay (user=%s, new_balance=%s)",
                credits_required,
                current_user.id,
                new_balance,
            )
        else:
            subscription_service = SubscriptionService(db)
            is_premium = await subscription_service.is_user_premium(str(current_user.id))
            is_free_usage = not builder_access.use_credits and not is_premium
            
            if is_premium:
                await subscription_service.increment_custom_parlay_usage(str(current_user.id))
                logger.info("Used included premium custom builder action (counter) (user=%s)", current_user.id)
            else:
                await subscription_service.increment_free_custom_parlay_usage(str(current_user.id))
                logger.info("Used free custom builder action (counter) (user=%s)", current_user.id)

        # Automatic verification record for the counter ticket (skip for free users).
        subscription_service = SubscriptionService(db)
        is_premium = await subscription_service.is_user_premium(str(current_user.id))
        is_free_usage = not builder_access.use_credits and not is_premium
        
        if not is_free_usage:
            try:
                record = await CustomParlayAutoVerificationService(db).ensure_verification_record(
                    user=current_user,
                    request_legs=result.counter_legs,
                    analysis_legs=result.counter_analysis.legs,
                )
                if record is not None:
                    updated_analysis = result.counter_analysis.model_copy(
                        update={
                            "verification": VerificationRecordSummary(
                                id=str(record.id),
                                status=str(record.status),
                                viewer_url=_viewer_urls.build(str(record.id)),
                            )
                        }
                    )
                    result = result.model_copy(update={"counter_analysis": updated_analysis})
            except Exception:
                logger.exception("Counter parlay verification failed (non-fatal) user=%s", current_user.id)
        else:
            logger.info("Skipping verification for free user counter parlay (user=%s)", current_user.id)

        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to build counter parlay: {str(exc)}") from exc


@router.post("/parlay/hedges", response_model=HedgesResponse)
@rate_limit("30/hour")
async def build_hedges(
    request: Request,
    hedges_request: HedgesRequest,
    db: AsyncSession = Depends(get_db),
    builder_access: CustomBuilderAccess = Depends(require_custom_builder_access),
):
    """
    Generate Counter Ticket + Coverage Pack (deterministic flip math, no analysis).

    Counter Ticket: Premium OR credits. Coverage Pack: Premium only.
    When features are disabled via config, returns None for those parts.
    """
    _ = request
    current_user = builder_access.user
    try:
        feature_counter = getattr(settings, "feature_counter_ticket", False)
        feature_coverage = getattr(settings, "feature_coverage_pack", False)
        if not feature_counter and not feature_coverage:
            return HedgesResponse(
                counter_ticket=None,
                coverage_pack=None,
                upset_possibilities=build_upset_possibilities(len(hedges_request.legs) or len(hedges_request.picks)),
            )

        # Normalize: use legs when present; else build from back-compat picks
        if hedges_request.legs:
            raw_legs = list(hedges_request.legs)
        elif hedges_request.picks:
            raw_legs = [
                CustomParlayLeg(
                    game_id=p.game_id,
                    pick=p.selection,
                    market_type=p.market,
                    point=p.line,
                    odds=str(p.odds) if p.odds is not None else None,
                )
                for p in hedges_request.picks
            ]
        else:
            raw_legs = []
        legs = [leg for leg in raw_legs if is_supported_market(leg)]
        if not legs:
            return HedgesResponse(
                counter_ticket=None,
                coverage_pack=None,
                upset_possibilities=build_upset_possibilities(len(raw_legs)),
            )

        analysis_service = CustomParlayAnalysisService(db)
        games_by_id = await analysis_service.load_games(legs)

        subscription_service = SubscriptionService(db)
        is_premium = await subscription_service.is_user_premium(str(current_user.id))
        use_credits = bool(builder_access.use_credits)

        allow_counter = feature_counter and (is_premium or use_credits)
        allow_coverage = feature_coverage and is_premium

        counter_ticket, coverage_pack_list, upset_possibilities = HedgeEngine.run(
            legs,
            games_by_id,
            mode=hedges_request.mode or "best_edges",
            pick_signals=hedges_request.pick_signals,
            max_coverage_tickets=hedges_request.max_tickets if allow_coverage else 0,
            scenario_tickets=10,
            round_robin_tickets=10,
            round_robin_size=2,
        )

        return HedgesResponse(
            counter_ticket=counter_ticket if allow_counter else None,
            coverage_pack=coverage_pack_list if allow_coverage else None,
            upset_possibilities=upset_possibilities,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Hedges build failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to build hedges") from exc


@router.post("/parlay/coverage", response_model=ParlayCoverageResponse)
@rate_limit("20/hour")
async def build_coverage_pack(
    request: Request,
    coverage_request: ParlayCoverageRequest,
    db: AsyncSession = Depends(get_db),
    builder_access: CustomBuilderAccess = Depends(require_custom_builder_access),
):
    """
    Generate an upset coverage pack for the user's selected games.

    Access:
    - Premium: includes 25 custom builder AI actions per rolling period (then credits for overage)
    - Credits: costs credits per AI action (settings.credits_cost_custom_builder_action)
    """
    current_user = builder_access.user
    _ = request, current_user
    try:
        analysis_service = CustomParlayAnalysisService(db)
        coverage_service = ParlayCoverageService(analysis_service)
        result = await coverage_service.build_coverage_pack(coverage_request)

        if builder_access.use_credits:
            from app.core.config import settings
            from app.services.credit_balance_service import CreditBalanceService

            credits_required = int(builder_access.credits_required or getattr(settings, "credits_cost_custom_builder_action", 3))
            credit_service = CreditBalanceService(db)
            new_balance = await credit_service.try_spend(str(current_user.id), credits_required)
            if new_balance is None:
                raise PaywallException(
                    error_code=AccessErrorCode.PREMIUM_REQUIRED,
                    message=f"Custom builder AI actions cost {credits_required} credits. Buy credits or upgrade to Premium.",
                    feature="custom_builder",
                )
            logger.info(
                "Spent %s credits for coverage pack (user=%s, new_balance=%s)",
                credits_required,
                current_user.id,
                new_balance,
            )
        else:
            subscription_service = SubscriptionService(db)
            is_premium = await subscription_service.is_user_premium(str(current_user.id))
            is_free_usage = not builder_access.use_credits and not is_premium
            
            if is_premium:
                await subscription_service.increment_custom_parlay_usage(str(current_user.id))
                logger.info("Used included premium custom builder action (coverage) (user=%s)", current_user.id)
            else:
                await subscription_service.increment_free_custom_parlay_usage(str(current_user.id))
                logger.info("Used free custom builder action (coverage) (user=%s)", current_user.id)

        # Automatic verification records for generated tickets (skip for free users).
        subscription_service = SubscriptionService(db)
        is_premium = await subscription_service.is_user_premium(str(current_user.id))
        is_free_usage = not builder_access.use_credits and not is_premium
        
        if not is_free_usage:
            try:
                verifier = CustomParlayAutoVerificationService(db)

                async def _verify_ticket(ticket):
                    record = await verifier.ensure_verification_record(
                        user=current_user,
                        request_legs=ticket.legs,
                        analysis_legs=ticket.analysis.legs,
                    )
                    if record is None:
                        return ticket
                    updated_analysis = ticket.analysis.model_copy(
                        update={
                            "verification": VerificationRecordSummary(
                                id=str(record.id),
                                status=str(record.status),
                                viewer_url=_viewer_urls.build(str(record.id)),
                            )
                        }
                    )
                    return ticket.model_copy(update={"analysis": updated_analysis})

                if result.scenario_tickets:
                    result = result.model_copy(
                        update={
                            "scenario_tickets": [await _verify_ticket(t) for t in result.scenario_tickets],
                        }
                    )
                if result.round_robin_tickets:
                    result = result.model_copy(
                        update={
                            "round_robin_tickets": [await _verify_ticket(t) for t in result.round_robin_tickets],
                        }
                    )
            except Exception:
                logger.exception("Coverage pack verification failed (non-fatal) user=%s", current_user.id)
        else:
            logger.info("Skipping verification for free user coverage pack (user=%s)", current_user.id)

        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to build coverage pack: {str(exc)}") from exc

