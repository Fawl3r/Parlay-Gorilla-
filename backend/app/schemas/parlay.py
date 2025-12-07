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
    sport: Optional[str] = None  # Sport for this leg (NFL, NBA, NHL, etc.)


class ParlayRequest(BaseModel):
    """Parlay suggestion request schema"""
    num_legs: int = Field(ge=1, le=20, description="Number of legs (1-20)")
    risk_profile: str = Field(
        default="balanced",
        description="Risk profile: conservative, balanced, or degen"
    )
    sports: Optional[List[str]] = Field(
        default=None,
        description="List of sports to mix in the parlay (e.g., ['NFL', 'NBA', 'NHL']). If not provided, defaults to NFL."
    )
    mix_sports: bool = Field(
        default=False,
        description="Whether to mix legs from multiple sports for lower correlation"
    )
    week: Optional[int] = Field(
        default=None,
        ge=1,
        le=18,
        description="NFL week number to build parlay from (1-18). If not provided, uses current week's games."
    )


class BadgeInfo(BaseModel):
    """Badge information for newly unlocked badges"""
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    requirement_type: str
    requirement_value: int
    display_order: int
    unlocked: bool = True
    unlocked_at: Optional[str] = None


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
    
    # Model metrics (new - for UI confidence display)
    parlay_ev: Optional[float] = Field(
        default=None, 
        description="Expected value of the parlay (model_prob * payout - 1)"
    )
    model_confidence: Optional[float] = Field(
        default=None, 
        description="Model confidence in the parlay (0-1)"
    )
    upset_count: Optional[int] = Field(
        default=0, 
        description="Number of upset picks (plus-money underdogs) in the parlay"
    )
    model_version: Optional[str] = Field(
        default=None, 
        description="Model version used for predictions"
    )
    
    # Badge unlocks (returned when user earns new badges)
    newly_unlocked_badges: Optional[List[BadgeInfo]] = Field(
        default=None,
        description="List of badges unlocked from this parlay generation"
    )


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


# ============================================================================
# Custom Parlay Builder (User-selected legs)
# ============================================================================

class CustomParlayLeg(BaseModel):
    """Single leg for custom parlay - user's pick"""
    game_id: str = Field(description="Game ID from the database")
    pick: str = Field(description="The pick: team name for moneyline, 'home'/'away' for spreads, 'over'/'under' for totals")
    market_type: str = Field(
        default="h2h",
        description="Market type: h2h (moneyline), spreads, totals"
    )
    odds: Optional[str] = Field(default=None, description="American odds if known (e.g., '-110')")
    point: Optional[float] = Field(default=None, description="Point spread or total line if applicable")


class CustomParlayRequest(BaseModel):
    """Request to analyze a user-built custom parlay"""
    legs: List[CustomParlayLeg] = Field(
        min_length=2,
        max_length=15,
        description="List of user-selected legs (2-15)"
    )


class CustomParlayLegAnalysis(BaseModel):
    """Analysis for a single leg in the custom parlay"""
    game_id: str
    game: str  # Display string like "Team A vs Team B"
    home_team: str
    away_team: str
    sport: str
    market_type: str
    pick: str
    pick_display: str  # Human-readable pick
    odds: str
    decimal_odds: float
    implied_probability: float
    ai_probability: float  # Model's adjusted probability
    confidence: float  # 0-100 confidence score
    edge: float  # How much edge (positive = value, negative = bad value)
    recommendation: str  # "strong", "moderate", "weak", "avoid"


class CustomParlayAnalysisResponse(BaseModel):
    """Full analysis response for custom parlay"""
    legs: List[CustomParlayLegAnalysis]
    num_legs: int
    
    # Combined probabilities
    combined_implied_probability: float  # What books say
    combined_ai_probability: float  # What our model says
    
    # Confidence and risk assessment
    overall_confidence: float  # 0-100
    confidence_color: str  # green, yellow, red
    
    # Payout calculations
    parlay_odds: str  # American odds for full parlay
    parlay_decimal_odds: float
    
    # AI Analysis
    ai_summary: str  # Overall analysis of the parlay
    ai_risk_notes: str  # Risk factors and concerns
    ai_recommendation: str  # "strong_play", "solid_play", "risky_play", "avoid"
    
    # Individual leg concerns
    weak_legs: List[str]  # List of concerning picks
    strong_legs: List[str]  # List of strong picks
