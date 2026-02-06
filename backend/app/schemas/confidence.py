"""Confidence result contract: availability, score, components, blockers."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ConfidenceBlocker(str, Enum):
    """Reasons confidence could not be computed or is degraded."""

    MARKET_DATA_UNAVAILABLE = "market_data_unavailable"
    STATS_UNAVAILABLE = "stats_unavailable"
    SITUATIONAL_DATA_UNAVAILABLE = "situational_data_unavailable"
    DATA_QUALITY_TOO_LOW = "data_quality_too_low"
    WEATHER_UNAVAILABLE = "weather_unavailable"
    WEATHER_NOT_APPLICABLE = "weather_not_applicable"
    MODEL_OUTPUT_MISSING = "model_output_missing"
    UNKNOWN = "unknown"


class ConfidenceComponents(BaseModel):
    """Per-component scores (same max as ConfidenceBreakdownBuilder)."""

    market_agreement: float = Field(ge=0, le=30, default=0)
    statistical_edge: float = Field(ge=0, le=30, default=0)
    situational_edge: float = Field(ge=0, le=20, default=0)
    data_quality: float = Field(ge=0, le=20, default=0)

    @property
    def total(self) -> float:
        return (
            self.market_agreement
            + self.statistical_edge
            + self.situational_edge
            + self.data_quality
        )


class ConfidenceResult(BaseModel):
    """User-facing confidence: available or unavailable with blockers."""

    confidence_available: bool
    confidence_score: Optional[float] = Field(default=None, ge=0, le=100)
    components: Optional[ConfidenceComponents] = None
    blockers: List[ConfidenceBlocker] = Field(default_factory=list)
    debug: Optional[Dict[str, object]] = None
