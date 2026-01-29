"""UGIE v2 schema models: pillars, signals, data quality, weather block."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class UgieSignal:
    """Normalized signal with key, value, weight, direction, explain."""

    key: str
    value: Any
    weight: float = 0.0
    direction: str = ""  # e.g. "favor_home", "favor_under"
    explain: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "weight": round(self.weight, 4),
            "direction": self.direction,
            "explain": self.explain,
        }


@dataclass
class UgiePillar:
    """Single pillar: score, confidence, signals, why_summary, top_edges."""

    score: float
    confidence: float
    signals: List[UgieSignal] = field(default_factory=list)
    why_summary: str = ""
    top_edges: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "score": round(max(0.0, min(1.0, self.score)), 4),
            "confidence": round(max(0.0, min(1.0, self.confidence)), 4),
            "signals": [s.as_dict() for s in self.signals],
            "why_summary": self.why_summary,
            "top_edges": self.top_edges[:10],
        }


@dataclass
class UgieDataQuality:
    """Data quality: status, missing, stale, provider."""

    status: str  # Good | Partial | Poor
    missing: List[str] = field(default_factory=list)
    stale: List[str] = field(default_factory=list)
    provider: str = ""  # api-sports | fallback | mixed

    def as_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "missing": self.missing,
            "stale": self.stale,
            "provider": self.provider,
        }


@dataclass
class UgieWeatherBlock:
    """Weather impact transparency block."""

    weather_efficiency_modifier: float
    weather_volatility_modifier: float
    weather_confidence_modifier: float
    why: str = ""
    rules_fired: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "weather_efficiency_modifier": round(self.weather_efficiency_modifier, 4),
            "weather_volatility_modifier": round(self.weather_volatility_modifier, 4),
            "weather_confidence_modifier": round(self.weather_confidence_modifier, 4),
            "why": self.why,
            "rules_fired": self.rules_fired,
        }


@dataclass
class UgieV2:
    """Root UGIE v2 output: pillars, confidence_score, risk_level, data_quality, recommended_action, market_snapshot, optional weather."""

    pillars: Dict[str, UgiePillar]
    confidence_score: float
    risk_level: str  # Low | Medium | High
    data_quality: UgieDataQuality
    recommended_action: str = ""
    market_snapshot: Dict[str, Any] = field(default_factory=dict)
    weather: Optional[UgieWeatherBlock] = None

    def as_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "pillars": {k: v.as_dict() for k, v in self.pillars.items()},
            "confidence_score": round(max(0.0, min(1.0, self.confidence_score)), 4),
            "risk_level": self.risk_level,
            "data_quality": self.data_quality.as_dict(),
            "recommended_action": self.recommended_action,
            "market_snapshot": self.market_snapshot,
        }
        if self.weather is not None:
            out["weather"] = self.weather.as_dict()
        return out
