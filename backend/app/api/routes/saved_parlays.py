"""Saved Parlays API.

These endpoints back the Analytics Dashboard "Saved Parlays" section and are the
ONLY place where custom user-built parlays are queued for Solana inscription.

Rules:
- AI-generated saved parlays are stored but never inscribed.
- Custom parlays are queued for inscription off-thread (Redis queue).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.models.game import Game
from app.models.market import Market
from app.models.saved_parlay import InscriptionStatus, SavedParlay, SavedParlayType
from app.models.user import User
from app.schemas.saved_parlay import SaveAiParlayRequest, SaveCustomParlayRequest, SavedParlayResponse
from app.services.saved_parlays.inscription_queue import InscriptionQueue
from app.services.saved_parlays.payloads import SavedParlayHashInputs, payload_builder
from app.services.saved_parlays.solscan import SolscanConfig, SolscanUrlBuilder

router = APIRouter()


def _default_title(*, parlay_type: str, legs_count: int) -> str:
    if parlay_type == SavedParlayType.custom.value:
        return f"Custom Parlay ({legs_count} legs)"
    return f"AI Parlay ({legs_count} legs)"


def _solscan_builder() -> SolscanUrlBuilder:
    return SolscanUrlBuilder(SolscanConfig(cluster=settings.solana_cluster, base_url=settings.solscan_base_url))


def _to_response(parlay: SavedParlay) -> SavedParlayResponse:
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
    )


async def _enqueue_inscription_if_needed(db: AsyncSession, parlay: SavedParlay) -> SavedParlay:
    """
    Enqueue inscription job for queued custom parlays.

    If Redis is unavailable, marks the parlay as failed (so the UI can surface Retry).
    """
    if parlay.parlay_type != SavedParlayType.custom.value:
        return parlay
    if parlay.inscription_status != InscriptionStatus.queued.value:
        return parlay

    queue = InscriptionQueue()
    try:
        await queue.enqueue_custom_parlay(saved_parlay_id=str(parlay.id))
        return parlay
    except Exception as exc:
        # Avoid leaking connection strings / secrets.
        parlay.inscription_status = InscriptionStatus.failed.value
        parlay.inscription_error = f"Enqueue failed: {exc.__class__.__name__}"
        db.add(parlay)
        await db.commit()
        await db.refresh(parlay)
        return parlay


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
    Save a custom (user-built) parlay and queue it for Solana inscription anchoring.
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

        # Default behavior: inscribe again only if legs/odds changed (content_hash changed).
        should_queue = content_hash != (saved.content_hash or "")

        saved.title = title
        saved.legs = legs_snapshot
        saved.version = int(saved.version or 1) + 1
        saved.updated_at = now
        saved.content_hash = content_hash
        saved.inscription_hash = content_hash

        if should_queue:
            saved.inscription_status = InscriptionStatus.queued.value
            saved.inscription_error = None
            saved.inscription_tx = None
            saved.inscribed_at = None
        # else: keep previous confirmed status/tx if it exists.

        db.add(saved)
        await db.commit()
        await db.refresh(saved)
        if should_queue:
            saved = await _enqueue_inscription_if_needed(db, saved)
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
        inscription_status=InscriptionStatus.queued.value,
        inscription_hash=content_hash,
    )
    db.add(saved)
    await db.commit()
    await db.refresh(saved)
    saved = await _enqueue_inscription_if_needed(db, saved)
    return _to_response(saved)


@router.post("/parlays/ai/save", response_model=SavedParlayResponse)
async def save_ai_parlay(
    body: SaveAiParlayRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Save an AI-generated parlay for the user.

    AI saved parlays are NEVER queued for inscription.
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

        saved.title = title
        saved.legs = legs_snapshot
        saved.version = int(saved.version or 1) + 1
        saved.updated_at = now
        saved.content_hash = content_hash
        saved.inscription_status = InscriptionStatus.none.value
        saved.inscription_hash = None
        saved.inscription_tx = None
        saved.inscription_error = None
        saved.inscribed_at = None
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
        inscription_hash=None,
    )
    db.add(saved)
    await db.commit()
    await db.refresh(saved)
    return _to_response(saved)


@router.get("/parlays/saved", response_model=List[SavedParlayResponse])
async def list_saved_parlays(
    type: str = Query("all", description="Filter: all|custom|ai"),
    limit: int = Query(50, ge=1, le=200),
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
    return [_to_response(p) for p in rows]


@router.post("/parlays/{saved_parlay_id}/inscription/retry", response_model=SavedParlayResponse)
async def retry_inscription(
    saved_parlay_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retry Solana inscription for a failed custom parlay.
    """
    saved = await _get_saved_parlay_for_user(db, saved_parlay_id=saved_parlay_id, user_id=user.id)
    if saved.parlay_type != SavedParlayType.custom.value:
        raise HTTPException(status_code=400, detail="Only custom parlays can be retried")
    if saved.inscription_status != InscriptionStatus.failed.value:
        raise HTTPException(status_code=400, detail="Retry is only allowed for failed inscriptions")

    saved.inscription_status = InscriptionStatus.queued.value
    saved.inscription_error = None
    db.add(saved)
    await db.commit()
    await db.refresh(saved)
    saved = await _enqueue_inscription_if_needed(db, saved)
    return _to_response(saved)


