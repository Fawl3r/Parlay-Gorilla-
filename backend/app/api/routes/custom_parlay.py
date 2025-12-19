"""Custom parlay endpoints (user-selected legs)."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.access_control import AccessErrorCode, PaywallException, require_custom_builder_access
from app.core.dependencies import get_db
from app.middleware.rate_limiter import rate_limit
from app.models.user import User
from app.schemas.parlay import (
    CounterParlayRequest,
    CounterParlayResponse,
    CustomParlayAnalysisResponse,
    CustomParlayRequest,
    ParlayCoverageRequest,
    ParlayCoverageResponse,
)
from app.services.custom_parlay import CounterParlayService, CustomParlayAnalysisService, ParlayCoverageService
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/parlay/analyze", response_model=CustomParlayAnalysisResponse)
@rate_limit("30/hour")
async def analyze_custom_parlay(
    request: Request,
    parlay_request: CustomParlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_custom_builder_access),
):
    """
    Analyze a user-built custom parlay.

    Access:
    - Premium: counts against daily custom limit (settings.premium_custom_parlays_per_day)
    - Credits: costs credits per AI action (settings.credits_cost_custom_builder_action)
    """
    _ = request
    try:
        service = CustomParlayAnalysisService(db)
        result = await service.analyze(parlay_request.legs)
        
        subscription_service = SubscriptionService(db)
        if await subscription_service.is_user_premium(str(current_user.id)):
            # Track usage after successful analysis (premium daily limit)
            await subscription_service.increment_custom_parlay_usage(str(current_user.id))
            logger.info(f"Used premium custom parlay for user {current_user.id}")
        else:
            # Credit users pay per AI action (deduct after success)
            from app.core.config import settings
            from app.services.credit_balance_service import CreditBalanceService

            credits_required = int(getattr(settings, "credits_cost_custom_builder_action", 3))
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
    current_user: User = Depends(require_custom_builder_access),
):
    """
    Build a counter/hedge parlay for the same games as the user's ticket.

    Access:
    - Premium: allowed (may be limited by daily custom limit via shared gate)
    - Credits: costs credits per AI action (settings.credits_cost_custom_builder_action)
    """
    _ = request, current_user
    try:
        analysis_service = CustomParlayAnalysisService(db)
        counter_service = CounterParlayService(analysis_service)
        result = await counter_service.generate(counter_request)

        # Premium users count against daily custom usage; credit users pay per AI action.
        subscription_service = SubscriptionService(db)
        if await subscription_service.is_user_premium(str(current_user.id)):
            await subscription_service.increment_custom_parlay_usage(str(current_user.id))
            logger.info(f"Used premium custom counter parlay for user {current_user.id}")
        else:
            from app.core.config import settings
            from app.services.credit_balance_service import CreditBalanceService

            credits_required = int(getattr(settings, "credits_cost_custom_builder_action", 3))
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

        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to build counter parlay: {str(exc)}") from exc


@router.post("/parlay/coverage", response_model=ParlayCoverageResponse)
@rate_limit("20/hour")
async def build_coverage_pack(
    request: Request,
    coverage_request: ParlayCoverageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_custom_builder_access),
):
    """
    Generate an upset coverage pack for the user's selected games.

    Access:
    - Premium: allowed (may be limited by daily custom limit via shared gate)
    - Credits: costs credits per AI action (settings.credits_cost_custom_builder_action)
    """
    _ = request, current_user
    try:
        analysis_service = CustomParlayAnalysisService(db)
        coverage_service = ParlayCoverageService(analysis_service)
        result = await coverage_service.build_coverage_pack(coverage_request)

        # Premium users count against daily custom usage; credit users pay per AI action.
        subscription_service = SubscriptionService(db)
        if await subscription_service.is_user_premium(str(current_user.id)):
            await subscription_service.increment_custom_parlay_usage(str(current_user.id))
            logger.info(f"Used premium custom coverage pack for user {current_user.id}")
        else:
            from app.core.config import settings
            from app.services.credit_balance_service import CreditBalanceService

            credits_required = int(getattr(settings, "credits_cost_custom_builder_action", 3))
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

        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to build coverage pack: {str(exc)}") from exc

