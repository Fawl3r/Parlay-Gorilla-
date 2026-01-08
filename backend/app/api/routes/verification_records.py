"""Verification record retrieval API.

User-facing routes for viewing verification record status/metadata.
"""

from __future__ import annotations

import uuid
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.verification_record import VerificationRecord
from app.schemas.verification_record import VerificationRecordResponse
from app.services.verification_records.viewer_url_builder import VerificationRecordViewerUrlBuilder

router = APIRouter()
_viewer_urls = VerificationRecordViewerUrlBuilder()


def _to_response(record: VerificationRecord) -> VerificationRecordResponse:
    created_at = record.created_at.astimezone(timezone.utc).isoformat() if record.created_at else ""
    confirmed_at = record.confirmed_at.astimezone(timezone.utc).isoformat() if record.confirmed_at else None
    return VerificationRecordResponse(
        id=str(record.id),
        saved_parlay_id=str(record.saved_parlay_id) if record.saved_parlay_id else None,
        status=str(record.status),
        data_hash=str(record.data_hash),
        created_at=created_at,
        confirmed_at=confirmed_at,
        receipt_id=str(record.tx_digest) if record.tx_digest else None,
        record_object_id=str(record.object_id) if record.object_id else None,
        viewer_url=_viewer_urls.build(str(record.id)),
        error=str(record.error) if record.error else None,
    )


@router.get("/verification-records/{verification_id}", response_model=VerificationRecordResponse)
async def get_verification_record(
    verification_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        rec_uuid = uuid.UUID(str(verification_id))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid verification id") from exc

    res = await db.execute(
        select(VerificationRecord).where(VerificationRecord.id == rec_uuid, VerificationRecord.user_id == user.id)
    )
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Verification record not found")
    return _to_response(record)


@router.get("/public/verification-records/{verification_id}", response_model=VerificationRecordResponse)
async def get_public_verification_record(
    verification_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public verification record viewer endpoint.

    This is intentionally unauthenticated so users can open/share their receipt link
    without needing an active session. The payload is hash-only (no PII).
    """
    try:
        rec_uuid = uuid.UUID(str(verification_id))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid verification id") from exc

    res = await db.execute(select(VerificationRecord).where(VerificationRecord.id == rec_uuid))
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Verification record not found")
    return _to_response(record)


