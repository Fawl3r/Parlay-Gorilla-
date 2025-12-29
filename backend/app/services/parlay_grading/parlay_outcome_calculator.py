from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.parlay_grading.types import ParlayLegStatus


@dataclass(frozen=True)
class ParlayOutcome:
    status: str  # hit | missed | pending | push
    hit: Optional[bool]  # True/False for hit/missed, None for pending/push
    legs_hit: int
    legs_missed: int
    legs_push: int
    legs_pending: int
    resolved_at: Optional[datetime]
    actual_probability: Optional[float]
    calibration_error: Optional[float]


class ParlayOutcomeCalculator:
    """Computes overall parlay outcome (including push handling) from per-leg results."""

    def compute(
        self,
        *,
        leg_results: List[Dict[str, Any]],
        predicted_probability: Optional[float] = None,
    ) -> ParlayOutcome:
        statuses = [str((lr or {}).get("status") or ParlayLegStatus.pending.value) for lr in (leg_results or [])]

        legs_hit = sum(1 for s in statuses if s == ParlayLegStatus.hit.value)
        legs_missed = sum(1 for s in statuses if s == ParlayLegStatus.missed.value)
        legs_push = sum(1 for s in statuses if s == ParlayLegStatus.push.value)
        legs_pending = sum(1 for s in statuses if s == ParlayLegStatus.pending.value)

        has_missed = legs_missed > 0
        has_pending = legs_pending > 0
        has_hit = legs_hit > 0
        all_push = bool(statuses) and legs_push == len(statuses)

        if has_missed:
            status = ParlayLegStatus.missed.value
            hit: Optional[bool] = False
            resolved_at: Optional[datetime] = datetime.now(timezone.utc)
        elif has_pending:
            status = ParlayLegStatus.pending.value
            hit = None
            resolved_at = None
        elif all_push:
            status = ParlayLegStatus.push.value
            hit = None
            resolved_at = datetime.now(timezone.utc)
        else:
            status = ParlayLegStatus.hit.value if has_hit else ParlayLegStatus.pending.value
            hit = True if has_hit else None
            resolved_at = datetime.now(timezone.utc) if has_hit else None

        actual_probability: Optional[float] = None
        calibration_error: Optional[float] = None
        if status in {ParlayLegStatus.hit.value, ParlayLegStatus.missed.value} and leg_results:
            actual = 1.0
            for lr in leg_results:
                lr_status = str((lr or {}).get("status") or ParlayLegStatus.pending.value)
                prob = lr.get("probability", 0.5)
                try:
                    p = float(prob) if prob is not None else 0.5
                except Exception:
                    p = 0.5

                if lr_status == ParlayLegStatus.hit.value:
                    actual *= p
                elif lr_status == ParlayLegStatus.missed.value:
                    actual *= (1.0 - p)
                elif lr_status == ParlayLegStatus.push.value:
                    actual *= 1.0
            actual_probability = float(actual)

            if predicted_probability is not None:
                try:
                    calibration_error = abs(float(predicted_probability) - float(actual_probability))
                except Exception:
                    calibration_error = None

        return ParlayOutcome(
            status=status,
            hit=hit,
            legs_hit=legs_hit,
            legs_missed=legs_missed,
            legs_push=legs_push,
            legs_pending=legs_pending,
            resolved_at=resolved_at,
            actual_probability=actual_probability,
            calibration_error=calibration_error,
        )


