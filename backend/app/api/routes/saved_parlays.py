"""Saved Parlays API.

These endpoints back the Analytics Dashboard "Saved Parlays" section and are the
ONLY place where saved parlays are queued for Solana inscription.

Rules:
- Saving a parlay does NOT auto-inscribe (user selects what to inscribe).
- Both custom and AI-generated saved parlays can be inscribed, subject to plan limits.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.access_control import AccessErrorCode, PaywallException
from app.core.dependencies import get_current_user, get_db
from app.models.game import Game
from app.models.market import Market
from app.models.saved_parlay import InscriptionStatus, SavedParlay, SavedParlayType
from app.models.saved_parlay_results import SavedParlayResult
from app.models.user import User
from app.schemas.saved_parlay import SaveAiParlayRequest, SaveCustomParlayRequest, SavedParlayResponse
from app.services.parlay_grading import ParlayLegStatus, ParlayOutcomeCalculator
from app.services.premium_usage_service import PremiumUsageService
from app.services.saved_parlay_tracker import SavedParlayTrackerService
from app.services.saved_parlays.inscription_queue import InscriptionQueue
from app.services.saved_parlays.payloads import SavedParlayHashInputs, payload_builder
from app.services.saved_parlays.solscan import SolscanConfig, SolscanUrlBuilder
from app.services.subscription_service import SubscriptionService

router = APIRouter()


def _default_title(*, parlay_type: str, legs_count: int) -> str:
    if parlay_type == SavedParlayType.custom.value:
        return f"Custom Parlay ({legs_count} legs)"
    return f"AI Parlay ({legs_count} legs)"


def _solscan_builder() -> SolscanUrlBuilder:
    return SolscanUrlBuilder(SolscanConfig(cluster=settings.solana_cluster, base_url=settings.solscan_base_url))


def _to_response(parlay: SavedParlay, *, results: Optional[dict] = None) -> SavedParlayResponse:
    builder = _solscan_builder()
    tx = (parlay.inscription_tx or "").strip()
    solscan_url = builder.tx_url(tx) if tx else None
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


async def _enqueue_inscription_if_needed(db: AsyncSession, parlay: SavedParlay) -> tuple[SavedParlay, bool]:
    """
    Enqueue inscription job for queued saved parlays.

    If Redis is unavailable, marks the parlay as failed (so the UI can surface Retry).
    """
    if parlay.inscription_status != InscriptionStatus.queued.value:
        return parlay, False

    queue = InscriptionQueue()
    try:
        await queue.enqueue_saved_parlay(saved_parlay_id=str(parlay.id))
        return parlay, True
    except Exception as exc:
        # Avoid leaking connection strings / secrets.
        parlay.inscription_status = InscriptionStatus.failed.value
        parlay.inscription_error = f"Enqueue failed: {exc.__class__.__name__}"
        db.add(parlay)
        await db.commit()
        await db.refresh(parlay)
        return parlay, False


async def _build_custom_legs_snapshot(db: AsyncSession, legs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich custom legs with book + game start timestamps for better provenance.
    """
    game_ids: set[uuid.UUID] = set()
    market_ids: set[uuid.UUID] = set()
    for leg in legs:
        try:
            game_ids.add(uuid.UUID(str(leg["game_id"])))
        except Exception:
            continue
        market_id = leg.get("market_id")
        if market_id:
            try:
                market_ids.add(uuid.UUID(str(market_id)))
            except Exception:
                pass

    games_by_id: Dict[str, Game] = {}
    if game_ids:
        res = await db.execute(select(Game).where(Game.id.in_(list(game_ids))))
        games_by_id = {str(g.id): g for g in res.scalars().all()}

    markets_by_id: Dict[str, Market] = {}
    if market_ids:
        res = await db.execute(select(Market).where(Market.id.in_(list(market_ids))))
        markets_by_id = {str(m.id): m for m in res.scalars().all()}

    enriched: List[Dict[str, Any]] = []
    for leg in legs:
        out = dict(leg)
        game = games_by_id.get(str(leg.get("game_id")))
        if game and game.start_time:
            out["game_start_time_utc"] = game.start_time.astimezone(timezone.utc).isoformat()
        market = markets_by_id.get(str(leg.get("market_id")))
        if market:
            out["book"] = market.book
        enriched.append(out)
    return enriched


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

        legs_snapshot = await _build_custom_legs_snapshot(db, legs_raw)
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
        await db.commit()
        await db.refresh(saved)
        return _to_response(saved)

    # Create new record.
    new_id = uuid.uuid4()
    legs_snapshot = await _build_custom_legs_snapshot(db, legs_raw)
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
    Queue a saved parlay for Solana inscription (hash-only proof).

    This is the "inscription selector" endpoint: users explicitly choose which
    saved parlays (custom OR AI-generated) to inscribe, subject to plan limits.
    """
    saved = await _get_saved_parlay_for_user(db, saved_parlay_id=saved_parlay_id, user_id=user.id)

    status = str(getattr(saved, "inscription_status", InscriptionStatus.none.value) or InscriptionStatus.none.value)
    if status in {InscriptionStatus.confirmed.value, InscriptionStatus.queued.value}:
        return _to_response(saved)

    # Inscriptions are a premium feature (for now).
    subscription_service = SubscriptionService(db)
    if not await subscription_service.is_user_premium(str(user.id)):
        raise PaywallException(
            error_code=AccessErrorCode.PREMIUM_REQUIRED,
            message="On-chain inscriptions are a Gorilla Premium feature.",
            feature="inscriptions",
        )

    usage = PremiumUsageService(db)

    # Consume quota once per saved parlay (retries shouldn't double-consume).
    consumed_flag = bool(getattr(saved, "inscription_quota_consumed", False) or False)
    should_consume_quota = not consumed_flag

    if should_consume_quota:
        snap = await usage.get_inscriptions_snapshot(user)
        if snap.remaining <= 0:
            raise PaywallException(
                error_code=AccessErrorCode.FREE_LIMIT_REACHED,
                message=(
                    f"You've used all {snap.limit} inscriptions in your current "
                    f"{settings.premium_inscriptions_period_days}-day period. "
                    "Your quota will reset automatically."
                ),
                remaining_today=0,
                feature="inscriptions",
            )

    saved.inscription_status = InscriptionStatus.queued.value
    saved.inscription_hash = str(getattr(saved, "content_hash", "") or "")
    saved.inscription_error = None
    saved.inscription_tx = None
    saved.inscribed_at = None

    db.add(saved)
    await db.commit()
    await db.refresh(saved)

    saved, enqueued = await _enqueue_inscription_if_needed(db, saved)

    if should_consume_quota and enqueued:
        await usage.increment_inscriptions_used(user, count=1)
        saved.inscription_quota_consumed = True
        db.add(saved)
        await db.commit()
        await db.refresh(saved)

    return _to_response(saved)


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
    if saved.inscription_status != InscriptionStatus.failed.value:
        raise HTTPException(status_code=400, detail="Retry is only allowed for failed inscriptions")
    # Reuse queue logic (handles quota consumption correctly via `inscription_quota_consumed`).
    return await queue_inscription(saved_parlay_id=saved_parlay_id, db=db, user=user)


