"""Parlay history + detail endpoints with outcome tracking (leg-by-leg)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List, Optional
import uuid

from app.core.dependencies import get_current_user, get_db
from app.models.parlay import Parlay
from app.models.parlay_results import ParlayResult
from app.models.user import User
from app.schemas.parlays_results import ParlayDetailResponse, ParlayHistoryItemResponse, ParlayLegOutcomeResponse
from app.services.parlay_grading import ParlayOutcomeCalculator, ParlayLegStatus
from app.services.parlay_tracker import ParlayTrackerService


router = APIRouter()


def _compute_status(leg_results: List[Dict[str, Any]]) -> str:
    return ParlayOutcomeCalculator().compute(leg_results=leg_results).status


def _as_leg_response(item: Dict[str, Any]) -> ParlayLegOutcomeResponse:
    return ParlayLegOutcomeResponse(
        market_id=item.get("market_id"),
        game_id=item.get("game_id"),
        market_type=item.get("market_type"),
        outcome=item.get("outcome"),
        game=item.get("game"),
        home_team=item.get("home_team"),
        away_team=item.get("away_team"),
        sport=item.get("sport"),
        odds=item.get("odds"),
        probability=item.get("probability"),
        confidence=item.get("confidence"),
        status=str(item.get("status") or ParlayLegStatus.pending.value),
        hit=item.get("hit"),
        notes=item.get("notes"),
        home_score=item.get("home_score"),
        away_score=item.get("away_score"),
        line=item.get("line"),
        selection=item.get("selection"),
        raw=None,
    )


def _fallback_leg_results_from_parlay(parlay: Parlay) -> List[Dict[str, Any]]:
    legs = list(getattr(parlay, "legs", []) or [])
    out: List[Dict[str, Any]] = []
    for leg in legs:
        out.append(
            {
                "market_id": leg.get("market_id"),
                "market_type": leg.get("market_type"),
                "outcome": leg.get("outcome"),
                "game": leg.get("game"),
                "home_team": leg.get("home_team"),
                "away_team": leg.get("away_team"),
                "sport": leg.get("sport"),
                "odds": leg.get("odds"),
                "probability": leg.get("probability"),
                "confidence": leg.get("confidence"),
                "status": ParlayLegStatus.pending.value,
                "hit": None,
                "notes": "unresolved",
            }
        )
    return out


@router.get("/parlays/history", response_model=List[ParlayHistoryItemResponse])
async def get_my_parlay_history_with_results(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the current user's AI-generated parlay history with per-leg outcomes.
    """
    # Load parlay rows
    res = await db.execute(
        select(Parlay)
        .where(Parlay.user_id == current_user.id)
        .order_by(desc(Parlay.created_at))
        .limit(limit)
        .offset(offset)
    )
    parlays = list(res.scalars().all())
    if not parlays:
        return []

    tracker = ParlayTrackerService(db)

    items: List[ParlayHistoryItemResponse] = []
    for parlay in parlays:
        # Best-effort resolve on-demand (fast DB-only grading).
        pr: Optional[ParlayResult] = await tracker.resolve_parlay_if_needed(parlay=parlay)
        leg_results = list(getattr(pr, "leg_results", None) or []) if pr else _fallback_leg_results_from_parlay(parlay)
        status = _compute_status(leg_results)

        items.append(
            ParlayHistoryItemResponse(
                id=str(parlay.id),
                created_at=parlay.created_at.isoformat() if parlay.created_at else None,
                num_legs=int(parlay.num_legs or 0),
                risk_profile=str(parlay.risk_profile or ""),
                parlay_hit_prob=float(parlay.parlay_hit_prob or 0.0),
                status=status,
                legs=[_as_leg_response(lr) for lr in leg_results],
            )
        )

    return items


@router.get("/parlays/{parlay_id}", response_model=ParlayDetailResponse)
async def get_my_parlay_detail_with_results(
    parlay_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return one AI-generated parlay with per-leg outcomes.
    """
    try:
        parlay_uuid = uuid.UUID(parlay_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid parlay id") from exc

    res = await db.execute(
        select(Parlay).where(Parlay.id == parlay_uuid).where(Parlay.user_id == current_user.id).limit(1)
    )
    parlay = res.scalar_one_or_none()
    if not parlay:
        raise HTTPException(status_code=404, detail="Parlay not found")

    tracker = ParlayTrackerService(db)
    pr: Optional[ParlayResult] = await tracker.resolve_parlay_if_needed(parlay=parlay)

    leg_results = list(getattr(pr, "leg_results", None) or []) if pr else _fallback_leg_results_from_parlay(parlay)
    status = _compute_status(leg_results)

    return ParlayDetailResponse(
        id=str(parlay.id),
        created_at=parlay.created_at.isoformat() if parlay.created_at else None,
        num_legs=int(parlay.num_legs or 0),
        risk_profile=str(parlay.risk_profile or ""),
        parlay_hit_prob=float(parlay.parlay_hit_prob or 0.0),
        ai_summary=str(getattr(parlay, "ai_summary", None) or "") or None,
        ai_risk_notes=str(getattr(parlay, "ai_risk_notes", None) or "") or None,
        status=status,
        legs=[_as_leg_response(lr) for lr in leg_results],
    )


