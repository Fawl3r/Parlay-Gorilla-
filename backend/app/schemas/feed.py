"""Feed event schemas."""

from __future__ import annotations

from typing import Dict, Optional
from pydantic import BaseModel


class FeedEventResponse(BaseModel):
    """Feed event response for marquee."""
    id: str
    event_type: str
    sport: Optional[str]
    summary: str
    created_at: str
    metadata: Dict


class WinWallResponse(BaseModel):
    """Win wall response."""
    id: str
    parlay_type: str  # AI or CUSTOM
    legs_count: int
    odds: str
    user_alias: Optional[str]
    settled_at: str
    summary: str
