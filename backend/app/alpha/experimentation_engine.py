"""
Auto Experimentation Framework: A/B experiments (Group A = production, Group B = + alpha feature).

Compare accuracy, brier_score, CLV, ROI; promote only if statistically superior.
All experiments logged with experiment_id and correlation_id.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alpha_experiment import AlphaExperiment
from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome

logger = logging.getLogger(__name__)

MIN_SAMPLE_SIZE = 50
P_VALUE_PROMOTE_THRESHOLD = 0.05  # Promote only if p < 0.05 for superiority


class ExperimentationEngine:
    """
    Runs A/B experiments: Group A (current production) vs Group B (with new alpha feature).
    Logs to alpha_experiments; promotes only when B is statistically superior.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_experiment(
        self,
        feature_id: Optional[uuid.UUID],
        experiment_name: str,
        correlation_id: Optional[str] = None,
    ) -> AlphaExperiment:
        """Create and return an experiment record (started_at set)."""
        exp = AlphaExperiment(
            id=uuid.uuid4(),
            feature_id=feature_id,
            experiment_name=experiment_name,
            correlation_id=correlation_id,
        )
        self.db.add(exp)
        await self.db.commit()
        await self.db.refresh(exp)
        logger.info(
            "[AlphaExperiment] Started experiment_id=%s name=%s correlation_id=%s",
            exp.id,
            experiment_name,
            correlation_id or "",
        )
        return exp

    async def end_experiment(
        self,
        experiment_id: uuid.UUID,
        group_a_accuracy: float,
        group_b_accuracy: float,
        group_a_brier: float,
        group_b_brier: float,
        group_a_clv: Optional[float],
        group_b_clv: Optional[float],
        group_a_roi: Optional[float],
        group_b_roi: Optional[float],
        sample_size_a: int,
        sample_size_b: int,
        p_value: Optional[float],
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Write metrics and set promoted=True only if B is statistically superior (p < 0.05).
        """
        result = await self.db.execute(
            select(AlphaExperiment).where(AlphaExperiment.id == experiment_id)
        )
        row = result.first()
        exp = row[0] if row else None
        if not exp:
            return False
        exp.group_a_accuracy = group_a_accuracy
        exp.group_b_accuracy = group_b_accuracy
        exp.group_a_brier_score = group_a_brier
        exp.group_b_brier_score = group_b_brier
        exp.group_a_clv = group_a_clv
        exp.group_b_clv = group_b_clv
        exp.group_a_roi = group_a_roi
        exp.group_b_roi = group_b_roi
        exp.sample_size_a = sample_size_a
        exp.sample_size_b = sample_size_b
        exp.p_value = p_value
        exp.ended_at = datetime.now(timezone.utc)
        promoted = (
            sample_size_a >= MIN_SAMPLE_SIZE
            and sample_size_b >= MIN_SAMPLE_SIZE
            and p_value is not None
            and p_value < P_VALUE_PROMOTE_THRESHOLD
            and group_b_accuracy is not None
            and group_a_accuracy is not None
            and group_b_accuracy > group_a_accuracy
        )
        exp.promoted = promoted
        await self.db.commit()
        logger.info(
            "[AlphaExperiment] Ended experiment_id=%s promoted=%s p_value=%s correlation_id=%s",
            experiment_id,
            promoted,
            p_value,
            correlation_id or "",
        )
        return promoted

    async def get_metrics_from_resolved(
        self,
        prediction_ids_a: List[uuid.UUID],
        prediction_ids_b: List[uuid.UUID],
    ) -> Dict[str, Any]:
        """
        Compute accuracy, Brier, and optional CLV/ROI from resolved predictions.
        Returns dict with group_a_* and group_b_* and p_value (simplified: proportion test).
        """
        # Load outcomes for both groups
        all_ids = list(prediction_ids_a) + list(prediction_ids_b)
        q = select(ModelPrediction, PredictionOutcome).join(
            PredictionOutcome, PredictionOutcome.prediction_id == ModelPrediction.id
        ).where(ModelPrediction.id.in_(all_ids))
        res = await self.db.execute(q)
        rows = res.all()
        by_id = {}
        for row in rows:
            p, o = row[0], row[1]
            by_id[str(p.id)] = (p, o)
        def metrics(ids: List[uuid.UUID]) -> Dict[str, Any]:
            correct = []
            probs = []
            for i in ids:
                row = by_id.get(str(i))
                if not row:
                    continue
                pred, out = row
                correct.append(1.0 if out.was_correct else 0.0)
                probs.append(pred.predicted_prob)
            if not correct:
                return {"accuracy": 0.0, "brier": 0.0, "n": 0}
            acc = sum(correct) / len(correct)
            brier = np.mean([(p - c) ** 2 for p, c in zip(probs, correct)]) if probs else 0.0
            return {"accuracy": acc, "brier": brier, "n": len(correct)}
        ma = metrics(prediction_ids_a)
        mb = metrics(prediction_ids_b)
        # Simple p_value: two-proportion z (approximate)
        na, nb = ma["n"], mb["n"]
        if na < 10 or nb < 10:
            p_value = 1.0
        else:
            p1, p2 = ma["accuracy"], mb["accuracy"]
            pooled = (p1 * na + p2 * nb) / (na + nb)
            se = (pooled * (1 - pooled) * (1/na + 1/nb)) ** 0.5
            if se < 1e-9:
                p_value = 1.0
            else:
                try:
                    from scipy.stats import norm
                    z = (p2 - p1) / se
                    p_value = float(2 * (1 - norm.cdf(abs(z))))
                except Exception:
                    p_value = 1.0
        return {
            "group_a_accuracy": ma["accuracy"],
            "group_b_accuracy": mb["accuracy"],
            "group_a_brier_score": ma["brier"],
            "group_b_brier_score": mb["brier"],
            "sample_size_a": na,
            "sample_size_b": nb,
            "p_value": p_value,
        }
