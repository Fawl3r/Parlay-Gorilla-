from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class OddsMovement:
    spread_delta_points: Optional[float]
    total_delta_points: Optional[float]
    home_implied_prob_delta: Optional[float]
    away_implied_prob_delta: Optional[float]
    summary: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "spread_delta_points": self.spread_delta_points,
            "total_delta_points": self.total_delta_points,
            "home_implied_prob_delta": self.home_implied_prob_delta,
            "away_implied_prob_delta": self.away_implied_prob_delta,
            "summary": self.summary,
        }


class OddsMovementService:
    """Compute a human-friendly movement summary between two snapshots."""

    def build(self, *, current: Dict[str, Any], historical: Dict[str, Any]) -> OddsMovement:
        spread_delta = _delta_float(current.get("home_spread_point"), historical.get("home_spread_point"))
        total_delta = _delta_float(current.get("total_line"), historical.get("total_line"))

        home_prob_delta = _delta_float(current.get("home_implied_prob"), historical.get("home_implied_prob"))
        away_prob_delta = _delta_float(current.get("away_implied_prob"), historical.get("away_implied_prob"))

        parts: list[str] = []
        if historical.get("home_spread_point") is not None and current.get("home_spread_point") is not None:
            parts.append(
                f"Spread {historical['home_spread_point']:+.1f} → {current['home_spread_point']:+.1f}"
            )
        if historical.get("total_line") is not None and current.get("total_line") is not None:
            parts.append(f"Total {historical['total_line']:.1f} → {current['total_line']:.1f}")
        summary = "Line movement (lookback): " + "; ".join(parts) + "." if parts else ""

        return OddsMovement(
            spread_delta_points=spread_delta,
            total_delta_points=total_delta,
            home_implied_prob_delta=home_prob_delta,
            away_implied_prob_delta=away_prob_delta,
            summary=summary,
        )


def _delta_float(current: Any, historical: Any) -> Optional[float]:
    try:
        if current is None or historical is None:
            return None
        return float(current) - float(historical)
    except Exception:
        return None




