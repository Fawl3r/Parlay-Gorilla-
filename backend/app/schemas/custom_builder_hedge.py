"""
Data model for Custom Builder hedge outputs (Counter Ticket + Coverage Pack).

Decoupled from analysis text; used by hedge_engine and /parlay/hedges endpoint.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

MarketType = Literal["h2h", "moneyline", "spread", "total"]  # normalized from legs


class HedgePick(BaseModel):
    """Single pick in a derived (hedge) ticket."""

    game_id: str
    market_type: MarketType
    selection: str = Field(
        description="'home' | 'away' | 'over' | 'under' (or existing pick encoding)",
    )
    line: Optional[float] = None
    odds: Optional[float] = Field(default=None, description="Decimal odds if known")


class DerivedTicket(BaseModel):
    """One hedge ticket: flipped picks, label, optional score."""

    ticket_id: str
    label: str = Field(description="e.g. 'Counter Ticket', '1 upset hedge'")
    flip_count: int = Field(ge=0, description="Number of picks flipped vs original")
    picks: List[HedgePick]
    notes: Optional[str] = Field(default=None, description="Short user-friendly explanation")
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Optional; never show as probability")


class UpsetBreakdownItem(BaseModel):
    """Count of combinations for a given number of upsets."""

    k: int = Field(ge=0, description="Number of upsets (flipped picks)")
    count: int = Field(ge=0, description="C(n,k)")


class UpsetPossibilities(BaseModel):
    """Read-only combinatorics: n picks, total combinations, breakdown by k."""

    n: int = Field(ge=0, description="Number of picks")
    total: int = Field(ge=0, description="2^n total flip combinations")
    breakdown: List[UpsetBreakdownItem] = Field(default_factory=list)


class HedgesResponse(BaseModel):
    """Response for POST /parlay/hedges: counter ticket, coverage pack, upset possibilities."""

    counter_ticket: Optional[DerivedTicket] = None
    coverage_pack: Optional[List[DerivedTicket]] = None
    upset_possibilities: Optional[UpsetPossibilities] = None
