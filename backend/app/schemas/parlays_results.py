"""Schemas for parlay history/detail with outcome tracking."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ParlayLegOutcomeResponse(BaseModel):
    market_id: Optional[str] = None
    game_id: Optional[str] = None
    market_type: Optional[str] = None
    outcome: Optional[str] = None
    game: Optional[str] = None
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    sport: Optional[str] = None
    odds: Optional[str] = None
    probability: Optional[float] = None
    confidence: Optional[float] = None

    status: str = Field(description="hit|missed|push|pending")
    hit: Optional[bool] = Field(default=None, description="True/False for hit/missed, None for push/pending")
    notes: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    line: Optional[float] = None
    selection: Optional[str] = None

    raw: Optional[Dict[str, Any]] = Field(default=None, description="Best-effort raw leg payload (for debugging)")


class ParlayHistoryItemResponse(BaseModel):
    id: str
    created_at: Optional[str] = None
    num_legs: int
    risk_profile: str
    parlay_hit_prob: float

    status: str = Field(description="hit|missed|push|pending")
    legs: List[ParlayLegOutcomeResponse] = Field(default_factory=list)


class ParlayDetailResponse(BaseModel):
    id: str
    created_at: Optional[str] = None
    num_legs: int
    risk_profile: str
    parlay_hit_prob: float

    ai_summary: Optional[str] = None
    ai_risk_notes: Optional[str] = None

    status: str = Field(description="hit|missed|push|pending")
    legs: List[ParlayLegOutcomeResponse] = Field(default_factory=list)


