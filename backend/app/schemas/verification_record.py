"""Pydantic schemas for verification records (user-facing, product-safe terms)."""

from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class VerificationRecordResponse(BaseModel):
    id: str
    saved_parlay_id: str
    status: str
    data_hash: str
    created_at: str
    confirmed_at: Optional[str] = None

    # Neutral “receipt” identifiers (internally they map to tx digest + object id).
    receipt_id: Optional[str] = None
    record_object_id: Optional[str] = None

    viewer_url: str
    error: Optional[str] = None


