"""Custom parlay endpoints (user-selected legs)."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.access_control import require_custom_builder_access
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

    Premium-only feature. Counts against daily limit (15/day).
    """
    _ = request
    try:
        service = CustomParlayAnalysisService(db)
        result = await service.analyze(parlay_request.legs)
        
        # Track usage after successful analysis
        subscription_service = SubscriptionService(db)
        await subscription_service.increment_custom_parlay_usage(str(current_user.id))
        logger.info(f"Used custom parlay for user {current_user.id}")
        
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

    Premium-only feature.
    """
    _ = request, current_user
    try:
        analysis_service = CustomParlayAnalysisService(db)
        counter_service = CounterParlayService(analysis_service)
        return await counter_service.generate(counter_request)
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

    Premium-only feature.
    """
    _ = request, current_user
    try:
        analysis_service = CustomParlayAnalysisService(db)
        coverage_service = ParlayCoverageService(analysis_service)
        return await coverage_service.build_coverage_pack(coverage_request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to build coverage pack: {str(exc)}") from exc

