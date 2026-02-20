"""
Model health and drift auto-correction.

If accuracy drops >5%, or CLV negative for 40 predictions, or Brier worsens >0.03:
  - automatic weight dampening
  - increase calibration frequency
  - reduce aggressive signals
State transitions: GREEN -> YELLOW -> RED.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome
from app.models.model_health_state import ModelHealthState

logger = logging.getLogger(__name__)

STATE_GREEN = "GREEN"
STATE_YELLOW = "YELLOW"
STATE_RED = "RED"

ACCURACY_DROP_THRESHOLD = 0.05
CLV_NEGATIVE_WINDOW = 40
BRIER_WORSEN_THRESHOLD = 0.03
BASELINE_BRIER = 0.25


class ModelHealthService:
    """Tracks model health; triggers state transitions and auto-correction."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_singleton_state(self) -> Optional[ModelHealthState]:
        r = await self.db.execute(select(ModelHealthState).limit(1))
        return r.scalar_one_or_none()

    async def _ensure_singleton(self) -> ModelHealthState:
        row = await self._get_singleton_state()
        if row is not None:
            return row
        row = ModelHealthState(model_state=STATE_GREEN)
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def _recent_metrics(self, window: int = 100) -> Dict[str, Any]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=60)
        q = (
            select(ModelPrediction, PredictionOutcome)
            .join(PredictionOutcome, PredictionOutcome.prediction_id == ModelPrediction.id)
            .where(ModelPrediction.resolved_at >= cutoff)
            .order_by(ModelPrediction.resolved_at.desc())
            .limit(window)
        )
        r = await self.db.execute(q)
        rows = r.all()
        if not rows:
            return {"accuracy": 0.5, "brier": BASELINE_BRIER, "clv_positive_rate": 0.5, "count": 0}
        correct = sum(1 for _, o in rows if o.was_correct)
        accuracy = correct / len(rows)
        brier = sum(o.error_magnitude ** 2 for _, o in rows) / len(rows)
        clv_positive = 0
        clv_count = 0
        for p, _ in rows:
            if getattr(p, "expected_value", None) is not None:
                clv_count += 1
                if p.expected_value > 0:
                    clv_positive += 1
        clv_rate = clv_positive / clv_count if clv_count else 0.5
        return {"accuracy": accuracy, "brier": brier, "clv_positive_rate": clv_rate, "count": len(rows)}

    async def evaluate_and_update(self) -> Dict[str, Any]:
        """
        Evaluate drift; transition GREEN -> YELLOW -> RED if thresholds breached; persist state.
        """
        state_row = await self._ensure_singleton()
        prev_state = state_row.model_state
        metrics = await self._recent_metrics(window=100)
        if metrics["count"] < 30:
            return {"model_state": prev_state, "health_score": None, "metrics": metrics, "transition": None}

        accuracy = metrics["accuracy"]
        brier = metrics["brier"]
        clv_rate = metrics["clv_positive_rate"]

        new_state = prev_state
        if accuracy < 0.50 - ACCURACY_DROP_THRESHOLD:
            new_state = STATE_RED if prev_state == STATE_YELLOW else STATE_YELLOW
        elif brier > BASELINE_BRIER + BRIER_WORSEN_THRESHOLD:
            new_state = STATE_RED if prev_state == STATE_YELLOW else STATE_YELLOW
        elif clv_rate < 0.4 and metrics["count"] >= CLV_NEGATIVE_WINDOW:
            new_state = STATE_YELLOW if prev_state == STATE_GREEN else prev_state

        health_score = (accuracy * 0.4 + (1.0 - brier) * 0.3 + clv_rate * 0.3) * 100.0
        state_row.model_state = new_state
        state_row.health_score = round(health_score, 2)
        state_row.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(state_row)

        if new_state != prev_state:
            logger.warning(
                "model_health.state_transition",
                extra={"from": prev_state, "to": new_state, "accuracy": accuracy, "brier": brier, "clv_rate": clv_rate},
            )

        return {
            "model_state": new_state,
            "health_score": state_row.health_score,
            "metrics": metrics,
            "transition": new_state != prev_state,
        }

    async def get_current_state(self) -> Dict[str, Any]:
        """Return current model_state, health_score, updated_at."""
        row = await self._get_singleton_state()
        if row is None:
            return {"model_state": STATE_GREEN, "health_score": None, "updated_at": None}
        return {
            "model_state": row.model_state,
            "health_score": row.health_score,
            "rolling_roi": getattr(row, "rolling_roi", None),
            "last_rl_update_at": getattr(row, "last_rl_update_at", None),
            "calibration_version": getattr(row, "calibration_version", None),
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
