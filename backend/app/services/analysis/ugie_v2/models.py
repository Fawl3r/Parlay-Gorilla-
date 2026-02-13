"""UGIE v2 schema models: pillars, signals, data quality, weather block."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

DataQualitySubStatus = Literal["ready", "stale", "missing", "unavailable"]


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
    """Data quality: status, missing, stale, provider; optional roster/injuries for UI badges."""

    status: str  # Good | Partial | Poor
    missing: List[str] = field(default_factory=list)
    stale: List[str] = field(default_factory=list)
    provider: str = ""  # api-sports | fallback | mixed
    roster: Optional[DataQualitySubStatus] = None  # ready | stale | missing | unavailable
    injuries: Optional[DataQualitySubStatus] = None
    roster_reason: Optional[str] = None  # team_mapping_missing, quota_blocked, etc.
    injuries_reason: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "status": self.status,
            "missing": self.missing,
            "stale": self.stale,
            "provider": self.provider,
        }
        if self.roster is not None:
            out["roster"] = self.roster
        if self.injuries is not None:
            out["injuries"] = self.injuries
        if self.roster_reason is not None:
            out["roster_reason"] = self.roster_reason
        if self.injuries_reason is not None:
            out["injuries_reason"] = self.injuries_reason
        return out


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
class KeyPlayer:
    """Single key player: name, team, role, impact, why, optional metrics, confidence."""

    name: str
    team: Literal["home", "away"]
    role: str
    impact: Literal["High", "Medium"]
    why: str
    metrics: Optional[List[Dict[str, str]]] = None  # label/value strings only
    confidence: float = 0.0

    def as_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "name": self.name,
            "team": self.team,
            "role": self.role,
            "impact": self.impact,
            "why": self.why[:200] if self.why else "",
            "confidence": round(max(0.0, min(1.0, self.confidence)), 4),
        }
        if self.metrics:
            out["metrics"] = [
                {"label": str(m.get("label", "")), "value": str(m.get("value", ""))}
                for m in self.metrics if isinstance(m, dict)
            ]
        return out


@dataclass
class KeyPlayersBlock:
    """Key players block: status, reason, players, allowlist_source, optional updated_at."""

    status: Literal["available", "limited", "unavailable"]
    reason: Optional[str] = None
    players: List[KeyPlayer] = field(default_factory=list)
    allowlist_source: str = "roster_current_matchup_teams"
    updated_at: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "players": [p.as_dict() for p in self.players],
            "allowlist_source": self.allowlist_source,
            "updated_at": self.updated_at,
        }


@dataclass
class UgieV2:
    """Root UGIE v2 output: pillars, confidence_score, risk_level, data_quality, recommended_action, market_snapshot, optional weather, optional key_players."""

    pillars: Dict[str, UgiePillar]
    confidence_score: float
    risk_level: str  # Low | Medium | High
    data_quality: UgieDataQuality
    recommended_action: str = ""
    market_snapshot: Dict[str, Any] = field(default_factory=dict)
    weather: Optional[UgieWeatherBlock] = None
    key_players: Optional[KeyPlayersBlock] = None

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
        if self.key_players is not None:
            out["key_players"] = self.key_players.as_dict()
        return out
