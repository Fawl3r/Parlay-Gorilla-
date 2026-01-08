"""Saved parlay verification queue API.

These endpoints are the user-triggered entry points for creating optional verification records.
"""

from __future__ import annotations

import uuid
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import AccessErrorCode, PaywallException
from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.middleware.rate_limiter import rate_limit
from app.models.saved_parlay import SavedParlay, SavedParlayType
from app.models.user import User
from app.models.verification_record import VerificationRecord, VerificationStatus
from app.schemas.verification_record import VerificationRecordResponse
from app.services.verification_records.saved_parlay_verification_service import SavedParlayVerificationService
from app.services.verification_records.viewer_url_builder import VerificationRecordViewerUrlBuilder

router = APIRouter()
_viewer_urls = VerificationRecordViewerUrlBuilder()


def _to_response(record: VerificationRecord) -> VerificationRecordResponse:
    created_at = record.created_at.astimezone(timezone.utc).isoformat() if record.created_at else ""
    confirmed_at = record.confirmed_at.astimezone(timezone.utc).isoformat() if record.confirmed_at else None
    return VerificationRecordResponse(
        id=str(record.id),
        saved_parlay_id=str(record.saved_parlay_id),
        status=str(record.status),
        data_hash=str(record.data_hash),
        created_at=created_at,
        confirmed_at=confirmed_at,
        receipt_id=str(record.tx_digest) if record.tx_digest else None,
        record_object_id=str(record.object_id) if record.object_id else None,
        viewer_url=_viewer_urls.build(str(record.id)),
        error=str(record.error) if record.error else None,
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


def _ensure_verification_enabled() -> None:
    enabled = bool(getattr(settings, "verification_enabled", True))
    if enabled:
        return
    raise PaywallException(
        error_code=AccessErrorCode.FEATURE_DISABLED,
        message="Verification records are temporarily unavailable.",
        feature="inscriptions",  # legacy feature key (frontend paywall mapping)
    )


@router.post("/parlays/{saved_parlay_id}/verification/queue", response_model=VerificationRecordResponse)
@rate_limit("30/hour")
async def queue_verification(
    request: Request,
    saved_parlay_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ = request
    _ensure_verification_enabled()

    saved = await _get_saved_parlay_for_user(db, saved_parlay_id=saved_parlay_id, user_id=user.id)
    try:
        record = await SavedParlayVerificationService(db).queue(saved=saved, user=user)
        return _to_response(record)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/parlays/{saved_parlay_id}/verification/retry", response_model=VerificationRecordResponse)
@rate_limit("30/hour")
async def retry_verification(
    request: Request,
    saved_parlay_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ = request
    _ensure_verification_enabled()

    saved = await _get_saved_parlay_for_user(db, saved_parlay_id=saved_parlay_id, user_id=user.id)
    if str(getattr(saved, "parlay_type", "") or "").strip() != SavedParlayType.custom.value:
        raise HTTPException(status_code=400, detail="Retry is only available for Custom parlays.")

    data_hash = str(getattr(saved, "content_hash", "") or "").strip()
    if not data_hash:
        raise HTTPException(status_code=400, detail="Missing parlay hash")

    res = await db.execute(
        select(VerificationRecord)
        .where(VerificationRecord.saved_parlay_id == saved.id)
        .where(VerificationRecord.data_hash == data_hash)
        .order_by(VerificationRecord.created_at.desc())
        .limit(1)
    )
    last = res.scalar_one_or_none()
    if last is None:
        raise HTTPException(status_code=400, detail="Retry is only available after a failed verification attempt.")
    if str(getattr(last, "status", "") or "") != VerificationStatus.failed.value:
        raise HTTPException(status_code=400, detail="Retry is only allowed for failed verification attempts.")

    try:
        record = await SavedParlayVerificationService(db).queue(saved=saved, user=user)
        return _to_response(record)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


