"""Schemas for Saved Parlays and inscription metadata."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from app.schemas.parlay import CustomParlayLeg, LegResponse


class SaveCustomParlayRequest(BaseModel):
    """Create or update a saved custom parlay."""

    saved_parlay_id: Optional[str] = Field(
        default=None,
        description="If provided, updates the existing saved parlay and increments version.",
    )
    title: Optional[str] = Field(default=None, max_length=200)
    legs: List[CustomParlayLeg] = Field(min_length=1, max_length=20)


class SaveAiParlayRequest(BaseModel):
    """Create or update a saved AI-generated parlay."""

    saved_parlay_id: Optional[str] = Field(
        default=None,
        description="If provided, updates the existing saved parlay and increments version.",
    )
    title: Optional[str] = Field(default=None, max_length=200)
    legs: List[LegResponse] = Field(min_length=1, max_length=20)


class SavedParlayResponse(BaseModel):
    id: str
    user_id: str
    parlay_type: str
    title: str
    legs: List[Dict[str, Any]]
    created_at: str
    updated_at: str
    version: int
    content_hash: str

    inscription_status: str
    inscription_hash: Optional[str] = None
    inscription_tx: Optional[str] = None
    solscan_url: Optional[str] = None
    inscription_error: Optional[str] = None
    inscribed_at: Optional[str] = None

    # Optional: outcome tracking (hit/miss/push/pending + per-leg results)
    results: Optional[Dict[str, Any]] = None




