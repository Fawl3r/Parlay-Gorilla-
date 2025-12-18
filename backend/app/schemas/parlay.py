"""Parlay-related Pydantic schemas"""

from pydantic import BaseModel, Field, model_validator
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
    # Optional: when provided, we can resolve odds precisely (book + market instance)
    # and avoid ambiguity when multiple books exist for the same market type.
    market_id: Optional[str] = Field(default=None, description="Market ID (recommended) for precise odds resolution")
    odds: Optional[str] = Field(default=None, description="American odds if known (e.g., '-110')")
    point: Optional[float] = Field(default=None, description="Point spread or total line if applicable")


class CustomParlayRequest(BaseModel):
    """Request to analyze a user-built custom parlay"""
    legs: List[CustomParlayLeg] = Field(
        min_length=1,
        max_length=20,
        description="List of user-selected legs (1-20)"
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


# ============================================================================
# Counter / Hedge Parlay (Opposite ticket for the same games)
# ============================================================================

class CounterParlayMode(str):
    """How to build the counter ticket from the user's legs."""

    BEST_EDGES = "best_edges"  # default: pick the flipped legs with the best model edge/EV
    FLIP_ALL = "flip_all"  # strictly flip every leg (same count as input)


class CounterParlayRequest(BaseModel):
    """Request to generate a counter/hedge parlay from the user's selected legs."""

    legs: List[CustomParlayLeg] = Field(
        min_length=1,
        max_length=20,
        description="List of user-selected legs (1-20) to counter",
    )
    target_legs: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Desired number of legs for the counter ticket (defaults to input size).",
    )
    mode: str = Field(
        default=CounterParlayMode.BEST_EDGES,
        description="Counter mode: best_edges (recommended) or flip_all.",
    )
    min_edge: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Minimum model edge required to include a flipped leg (best_edges mode only).",
    )


class CounterLegCandidate(BaseModel):
    """A single flipped-leg candidate and whether it was included in the counter ticket."""

    game_id: str
    market_type: str
    original_pick: str
    counter_pick: str
    counter_odds: Optional[str] = None
    counter_ai_probability: float  # percentage (0-100)
    counter_confidence: float  # 0-100
    counter_edge: float  # percentage (can be negative)
    score: float
    included: bool


class CounterParlayResponse(BaseModel):
    """Response containing the generated counter parlay legs + analysis."""

    counter_legs: List[CustomParlayLeg]
    counter_analysis: CustomParlayAnalysisResponse
    candidates: List[CounterLegCandidate]


# ============================================================================
# Coverage Pack (Up upset possibilities + up to 20 tickets)
# ============================================================================


class CoverageTicket(BaseModel):
    """A generated ticket (either scenario-based or round-robin subset)."""

    legs: List[CustomParlayLeg]
    num_upsets: int = Field(ge=0, description="How many legs are flipped vs the user's original picks.")
    analysis: CustomParlayAnalysisResponse


class ParlayCoverageRequest(BaseModel):
    """Request to generate an upset coverage pack from the user's selected legs."""

    legs: List[CustomParlayLeg] = Field(
        min_length=1,
        max_length=20,
        description="List of user-selected legs (1-20) to build coverage from",
    )
    max_total_parlays: int = Field(default=20, ge=1, le=20, description="Max total tickets to return (1-20)")
    scenario_max: int = Field(default=10, ge=0, le=20, description="Max full-slate scenario tickets to return (0-20)")
    round_robin_max: int = Field(default=10, ge=0, le=20, description="Max round-robin tickets to return (0-20)")
    round_robin_size: int = Field(default=3, ge=2, le=20, description="Leg count for each round-robin ticket")

    @model_validator(mode="after")
    def _validate_limits(self):
        if (self.scenario_max + self.round_robin_max) > self.max_total_parlays:
            raise ValueError("scenario_max + round_robin_max must be <= max_total_parlays")
        if self.round_robin_max > 0:
            if len(self.legs) < 2:
                raise ValueError("round_robin_max > 0 requires at least 2 legs")
            if self.round_robin_size > len(self.legs):
                raise ValueError("round_robin_size must be <= number of legs")
        return self


class ParlayCoverageResponse(BaseModel):
    """Response containing upset possibility counts and generated coverage tickets."""

    num_games: int
    total_scenarios: int  # 2^N
    by_upset_count: Dict[int, int]  # k -> C(N,k)
    scenario_tickets: List[CoverageTicket]
    round_robin_tickets: List[CoverageTicket]
