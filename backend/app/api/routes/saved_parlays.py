"""Saved Parlays API.

These endpoints back the Analytics Dashboard "Saved Parlays" section and are the
ONLY place where saved parlays are queued for Solana inscription.

Rules:
- Saving a parlay does NOT auto-inscribe (user selects what to inscribe).
- Only custom saved parlays are eligible for on-chain verification (inscription).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.access_control import PaywallException
from app.core.dependencies import get_current_user, get_db
from app.models.game import Game
from app.models.market import Market
from app.models.saved_parlay import InscriptionStatus, SavedParlay, SavedParlayType
from app.models.saved_parlay_results import SavedParlayResult
from app.models.user import User
from app.schemas.saved_parlay import SaveAiParlayRequest, SaveCustomParlayRequest, SavedParlayResponse
from app.services.parlay_grading import ParlayLegStatus, ParlayOutcomeCalculator
from app.services.saved_parlay_tracker import SavedParlayTrackerService
from app.services.saved_parlays.saved_parlay_inscription_service import SavedParlayInscriptionService
from app.services.saved_parlays.payloads import SavedParlayHashInputs, payload_builder
from app.services.saved_parlays.custom_legs_snapshot_builder import CustomLegsSnapshotBuilder
# Legacy: SolscanUrlBuilder removed (no longer using Solana inscriptions)
from app.services.subscription_service import SubscriptionService

router = APIRouter()
logger = logging.getLogger(__name__)


def _default_title(*, parlay_type: str, legs_count: int) -> str:
    if parlay_type == SavedParlayType.custom.value:
        return f"Custom Parlay ({legs_count} legs)"
    return f"AI Parlay ({legs_count} legs)"


def _to_response(parlay: SavedParlay, *, results: Optional[dict] = None) -> SavedParlayResponse:
    # Legacy: solscan_url removed (no longer using Solana inscriptions)
    solscan_url = None
    return SavedParlayResponse(
        id=str(parlay.id),
        user_id=str(parlay.user_id),
        parlay_type=str(parlay.parlay_type),
        title=str(parlay.title),
        legs=list(parlay.legs or []),
        created_at=parlay.created_at.astimezone(timezone.utc).isoformat() if parlay.created_at else "",
        updated_at=parlay.updated_at.astimezone(timezone.utc).isoformat() if parlay.updated_at else "",
        version=int(parlay.version or 1),
        content_hash=str(parlay.content_hash),
        inscription_status=str(parlay.inscription_status),
        inscription_hash=parlay.inscription_hash,
        inscription_tx=parlay.inscription_tx,
        solscan_url=solscan_url,
        inscription_error=parlay.inscription_error,
        inscribed_at=parlay.inscribed_at.astimezone(timezone.utc).isoformat() if parlay.inscribed_at else None,
        results=results,
    )


async def _get_saved_parlay_for_user(db: AsyncSession, *, saved_parlay_id: str, user_id: uuid.UUID) -> SavedParlay:
    try:
        parlay_uuid = uuid.UUID(saved_parlay_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid saved parlay id") from exc

    res = await db.execute(select(SavedParlay).where(SavedParlay.id == parlay_uuid, SavedParlay.user_id == user_id))
    parlay = res.scalar_one_or_none()
    if not parlay:
        raise HTTPException(status_code=404, detail="Saved parlay not found")
    return parlay


@router.post("/parlays/custom/save", response_model=SavedParlayResponse)
async def save_custom_parlay(
    body: SaveCustomParlayRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Save a custom (user-built) parlay.

    NOTE: Saving does NOT auto-inscribe. Users explicitly choose which saved parlays
    to inscribe (subject to plan limits).
    """
    now = datetime.now(timezone.utc)
    title = (body.title or "").strip()
    legs_raw = [leg.model_dump() for leg in body.legs]
    if not title:
        title = _default_title(parlay_type=SavedParlayType.custom.value, legs_count=len(legs_raw))

    # If updating, load existing record and increment version.
    if body.saved_parlay_id:
        saved = await _get_saved_parlay_for_user(db, saved_parlay_id=body.saved_parlay_id, user_id=user.id)
        if saved.parlay_type != SavedParlayType.custom.value:
            raise HTTPException(status_code=400, detail="Saved parlay type mismatch")
        created_at = saved.created_at or now

        legs_snapshot = await CustomLegsSnapshotBuilder(db).build(legs_raw)
        content_hash = payload_builder.compute_content_hash(
            SavedParlayHashInputs(
                saved_parlay_id=str(saved.id),
                account_number=str(user.account_number),
                created_at_utc=created_at,
                parlay_type=SavedParlayType.custom.value,
                legs=legs_snapshot,
                app_version=settings.app_version,
            )
        )

        # If the parlay changed, reset its inscription state back to "none"
        # (the old on-chain proof no longer matches the new content_hash).
        hash_changed = content_hash != (saved.content_hash or "")

        saved.title = title
        saved.legs = legs_snapshot
        saved.version = int(saved.version or 1) + 1
        saved.updated_at = now
        saved.content_hash = content_hash
        saved.inscription_hash = content_hash

        if hash_changed:
            saved.inscription_status = InscriptionStatus.none.value
            saved.inscription_error = None
            saved.inscription_tx = None
            saved.inscribed_at = None
            saved.inscription_quota_consumed = False
        # else: keep previous confirmed status/tx if it exists.

        db.add(saved)
        await db.flush()
        
        # Create parlay_legs records for settlement tracking
        try:
            from app.services.parlay_leg_creator import ParlayLegCreator
            leg_creator = ParlayLegCreator(db)
            await leg_creator.create_legs_from_json(
                legs_json=legs_snapshot,
                saved_parlay_id=saved.id,
            )
        except Exception as leg_error:
            logger.warning(f"Error creating parlay_legs for saved_parlay {saved.id}: {leg_error}")
        
        await db.commit()
        await db.refresh(saved)
        return _to_response(saved)

    # Create new record.
    new_id = uuid.uuid4()
    legs_snapshot = await CustomLegsSnapshotBuilder(db).build(legs_raw)
    content_hash = payload_builder.compute_content_hash(
        SavedParlayHashInputs(
            saved_parlay_id=str(new_id),
            account_number=str(user.account_number),
            created_at_utc=now,
            parlay_type=SavedParlayType.custom.value,
            legs=legs_snapshot,
            app_version=settings.app_version,
        )
    )

    saved = SavedParlay(
        id=new_id,
        user_id=user.id,
        parlay_type=SavedParlayType.custom.value,
        title=title,
        legs=legs_snapshot,
        created_at=now,
        updated_at=now,
        version=1,
        content_hash=content_hash,
        inscription_status=InscriptionStatus.none.value,
        inscription_hash=content_hash,
        inscription_quota_consumed=False,
    )
    db.add(saved)
    await db.flush()
    
    # Create parlay_legs records for settlement tracking
    try:
        from app.services.parlay_leg_creator import ParlayLegCreator
        leg_creator = ParlayLegCreator(db)
        await leg_creator.create_legs_from_json(
            legs_json=legs_snapshot,
            saved_parlay_id=saved.id,
        )
    except Exception as leg_error:
        logger.warning(f"Error creating parlay_legs for saved_parlay {saved.id}: {leg_error}")
    
    await db.commit()
    await db.refresh(saved)
    return _to_response(saved)


@router.post("/parlays/ai/save", response_model=SavedParlayResponse)
async def save_ai_parlay(
    body: SaveAiParlayRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Save an AI-generated parlay for the user.

    NOTE: Saving does NOT auto-inscribe. Users can later choose to inscribe
    any saved parlay (AI or custom), subject to plan limits.
    """
    now = datetime.now(timezone.utc)
    title = (body.title or "").strip()
    legs_snapshot = [leg.model_dump() for leg in body.legs]
    if not title:
        title = _default_title(parlay_type=SavedParlayType.ai_generated.value, legs_count=len(legs_snapshot))

    if body.saved_parlay_id:
        saved = await _get_saved_parlay_for_user(db, saved_parlay_id=body.saved_parlay_id, user_id=user.id)
        if saved.parlay_type != SavedParlayType.ai_generated.value:
            raise HTTPException(status_code=400, detail="Saved parlay type mismatch")
        created_at = saved.created_at or now

        content_hash = payload_builder.compute_content_hash(
            SavedParlayHashInputs(
                saved_parlay_id=str(saved.id),
                account_number=str(user.account_number),
                created_at_utc=created_at,
                parlay_type=SavedParlayType.ai_generated.value,
                legs=legs_snapshot,
                app_version=settings.app_version,
            )
        )

        hash_changed = content_hash != (saved.content_hash or "")

        saved.title = title
        saved.legs = legs_snapshot
        saved.version = int(saved.version or 1) + 1
        saved.updated_at = now
        saved.content_hash = content_hash
        saved.inscription_hash = content_hash
        if hash_changed:
            saved.inscription_status = InscriptionStatus.none.value
            saved.inscription_tx = None
            saved.inscription_error = None
            saved.inscribed_at = None
            saved.inscription_quota_consumed = False
        db.add(saved)
        await db.flush()
        
        # Create parlay_legs records for settlement tracking
        try:
            from app.services.parlay_leg_creator import ParlayLegCreator
            leg_creator = ParlayLegCreator(db)
            await leg_creator.create_legs_from_json(
                legs_json=legs_snapshot,
                saved_parlay_id=saved.id,
            )
        except Exception as leg_error:
            logger.warning(f"Error creating parlay_legs for saved_parlay {saved.id}: {leg_error}")
        
        await db.commit()
        await db.refresh(saved)
        return _to_response(saved)

    new_id = uuid.uuid4()
    content_hash = payload_builder.compute_content_hash(
        SavedParlayHashInputs(
            saved_parlay_id=str(new_id),
            account_number=str(user.account_number),
            created_at_utc=now,
            parlay_type=SavedParlayType.ai_generated.value,
            legs=legs_snapshot,
            app_version=settings.app_version,
        )
    )

    saved = SavedParlay(
        id=new_id,
        user_id=user.id,
        parlay_type=SavedParlayType.ai_generated.value,
        title=title,
        legs=legs_snapshot,
        created_at=now,
        updated_at=now,
        version=1,
        content_hash=content_hash,
        inscription_status=InscriptionStatus.none.value,
        inscription_hash=content_hash,
        inscription_quota_consumed=False,
    )
    db.add(saved)
    await db.flush()
    
    # Create parlay_legs records for settlement tracking
    try:
        from app.services.parlay_leg_creator import ParlayLegCreator
        leg_creator = ParlayLegCreator(db)
        await leg_creator.create_legs_from_json(
            legs_json=legs_snapshot,
            saved_parlay_id=saved.id,
        )
    except Exception as leg_error:
        logger.warning(f"Error creating parlay_legs for saved_parlay {saved.id}: {leg_error}")
    
    await db.commit()
    await db.refresh(saved)
    return _to_response(saved)


@router.get("/parlays/saved", response_model=List[SavedParlayResponse])
async def list_saved_parlays(
    type: str = Query("all", description="Filter: all|custom|ai"),
    limit: int = Query(50, ge=1, le=200),
    include_results: bool = Query(False, description="When true, include outcome tracking for each saved parlay"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    List user's saved parlays (custom and/or AI-generated).
    """
    q = select(SavedParlay).where(SavedParlay.user_id == user.id).order_by(SavedParlay.created_at.desc()).limit(limit)
    t = (type or "all").strip().lower()
    if t in ("custom", "onchain"):
        q = q.where(SavedParlay.parlay_type == SavedParlayType.custom.value)
    elif t in ("ai", "ai_generated"):
        q = q.where(SavedParlay.parlay_type == SavedParlayType.ai_generated.value)
    elif t != "all":
        raise HTTPException(status_code=400, detail="Invalid type filter (expected all|custom|ai)")

    res = await db.execute(q)
    rows = list(res.scalars().all())

    if not include_results:
        return [_to_response(p) for p in rows]

    # Best-effort: resolve missing/pending results on-demand (DB-only grading).
    tracker = SavedParlayTrackerService(db)
    outcome_calc = ParlayOutcomeCalculator()

    ids = [r.id for r in rows]
    existing_by_saved: dict[str, SavedParlayResult] = {}
    if ids:
        res2 = await db.execute(select(SavedParlayResult).where(SavedParlayResult.saved_parlay_id.in_(ids)))
        existing_by_saved = {str(rr.saved_parlay_id): rr for rr in res2.scalars().all()}

    out: List[SavedParlayResponse] = []
    for p in rows:
        rr = existing_by_saved.get(str(p.id))
        if rr is None or not _saved_parlay_result_is_final(rr):
            rr = await tracker.resolve_saved_parlay_if_needed(saved_parlay=p)

        leg_results = list(getattr(rr, "leg_results", None) or []) if rr else []
        status = outcome_calc.compute(leg_results=leg_results).status if leg_results else ParlayLegStatus.pending.value

        results_payload = None
        if rr:
            results_payload = {
                "status": status,
                "hit": rr.hit,
                "legs_hit": rr.legs_hit,
                "legs_missed": rr.legs_missed,
                "resolved_at": rr.resolved_at.astimezone(timezone.utc).isoformat() if rr.resolved_at else None,
                "leg_results": leg_results,
            }

        out.append(_to_response(p, results=results_payload))

    return out


def _saved_parlay_result_is_final(result: SavedParlayResult) -> bool:
    leg_results = getattr(result, "leg_results", None)
    if not isinstance(leg_results, list) or not leg_results:
        return False
    for lr in leg_results:
        status = str((lr or {}).get("status") or "").lower().strip()
        if status not in {ParlayLegStatus.hit.value, ParlayLegStatus.missed.value, ParlayLegStatus.push.value}:
            return False
    return True


@router.post("/parlays/{saved_parlay_id}/inscription/queue", response_model=SavedParlayResponse)
async def queue_inscription(
    saved_parlay_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Queue a saved parlay for Solana on-chain verification (hash-only proof).

    This is the "inscription selector" endpoint: users explicitly choose which
    custom saved parlays to verify on-chain (subject to plan limits).
    """
    saved = await _get_saved_parlay_for_user(db, saved_parlay_id=saved_parlay_id, user_id=user.id)
    try:
        updated = await SavedParlayInscriptionService(db).queue(saved=saved, user=user)
        return _to_response(updated)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/parlays/{saved_parlay_id}/inscription/retry", response_model=SavedParlayResponse)
async def retry_inscription(
    saved_parlay_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retry Solana inscription for a failed saved parlay.
    """
    saved = await _get_saved_parlay_for_user(db, saved_parlay_id=saved_parlay_id, user_id=user.id)
    if str(getattr(saved, "parlay_type", "") or "").strip() != SavedParlayType.custom.value:
        raise HTTPException(status_code=400, detail="Retry is only available for Custom AI parlays.")
    if saved.inscription_status != InscriptionStatus.failed.value:
        raise HTTPException(status_code=400, detail="Retry is only allowed for failed inscriptions")
    # Reuse queue logic (handles quota consumption correctly via `inscription_quota_consumed`).
    return await queue_inscription(saved_parlay_id=saved_parlay_id, db=db, user=user)


