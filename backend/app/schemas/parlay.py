"""Parlay-related Pydantic schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from decimal import Decimal


class LegResponse(BaseModel):
    """Parlay leg response schema"""
    market_id: str
    outcome: str
    game: str
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    market_type: str
    odds: str
    probability: float
    confidence: float


class ParlayRequest(BaseModel):
    """Parlay suggestion request schema"""
    num_legs: int = Field(ge=1, le=20, description="Number of legs (1-20)")
    risk_profile: str = Field(
        default="balanced",
        description="Risk profile: conservative, balanced, or degen"
    )


class ParlayResponse(BaseModel):
    """Parlay suggestion response schema"""
    id: Optional[str] = None
    legs: List[LegResponse]
    num_legs: int
    parlay_hit_prob: float
    risk_profile: str
    confidence_scores: List[float]
    overall_confidence: float
    ai_summary: str
    ai_risk_notes: str
    confidence_meter: dict  # {score: float, color: str}


class TripleParlayRequest(BaseModel):
    """Request schema for triple (safe/balanced/degen) parlays"""
    sports: Optional[List[str]] = Field(
        default=None,
        description="List of sports to include (e.g., ['NFL', 'NBA']). Defaults to builder sport.",
    )
    safe_legs: Optional[int] = Field(
        default=None,
        ge=3,
        le=6,
        description="Override number of legs for the Safe Core parlay (3-6).",
    )
    balanced_legs: Optional[int] = Field(
        default=None,
        ge=7,
        le=12,
        description="Override number of legs for the Balanced parlay (7-12).",
    )
    degen_legs: Optional[int] = Field(
        default=None,
        ge=13,
        le=20,
        description="Override number of legs for the Degen parlay (13-20).",
    )


class TripleParlayResponse(BaseModel):
    """Response schema for triple parlay output"""
    safe: ParlayResponse
    balanced: ParlayResponse
    degen: ParlayResponse
    metadata: Dict[str, Dict]

