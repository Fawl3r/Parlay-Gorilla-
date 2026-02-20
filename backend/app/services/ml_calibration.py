"""ML-based probability calibration using scikit-learn (Platt scaling)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome
from app.models.parlay_results import ParlayResult

logger = logging.getLogger(__name__)

_CALIBRATION_MODEL_PATH_ENV = "CALIBRATION_MODEL_PATH"
_DEFAULT_CALIBRATION_PATH = "data/calibration_model.joblib"


def _get_calibration_path() -> Path:
    path = os.environ.get(_CALIBRATION_MODEL_PATH_ENV)
    if path:
        return Path(path)
    return Path(_DEFAULT_CALIBRATION_PATH)


class MLCalibrationService:
    """Service for calibrating probabilities using logistic regression (Platt scaling)."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._logistic_model: Any = None
        self._calibration_map: Dict[float, float] = {}
        self._load_serialized()

    def _load_serialized(self) -> None:
        """Load serialized calibration model from disk if present."""
        path = _get_calibration_path()
        if not path.exists():
            return
        try:
            import joblib
            data = joblib.load(path)
            self._logistic_model = data.get("model")
            self._calibration_map = data.get("calibration_map") or {}
            logger.info("[MLCalibration] Loaded serialized model from %s", path)
        except Exception as e:
            logger.warning("[MLCalibration] Failed to load model from %s: %s", path, e)

    def _save_serialized(self, model: Any, calibration_map: Dict[float, float], meta: Dict[str, Any]) -> None:
        """Persist calibration model to disk."""
        path = _get_calibration_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import joblib
            joblib.dump({
                "model": model,
                "calibration_map": calibration_map,
                "meta": meta,
            }, path)
            logger.info("[MLCalibration] Saved calibration model to %s", path)
        except Exception as e:
            logger.warning("[MLCalibration] Failed to save model to %s: %s", path, e)

    async def train_on_resolved_predictions(self, min_samples: int = 30) -> Dict[str, Any]:
        """
        Train logistic calibration (Platt scaling) on resolved model_predictions.
        X = predicted_prob, y = actual outcome (0/1).
        """
        result = await self.db.execute(
            select(ModelPrediction, PredictionOutcome)
            .join(PredictionOutcome, PredictionOutcome.prediction_id == ModelPrediction.id)
        )
        rows = result.all()
        if len(rows) < min_samples:
            return {
                "trained": False,
                "message": f"Not enough resolved predictions (need at least {min_samples})",
                "sample_size": len(rows),
            }
        X = np.array([[pred.predicted_prob] for pred, _ in rows], dtype=np.float64)
        y = np.array([1.0 if outcome.was_correct else 0.0 for _, outcome in rows], dtype=np.float64)
        return await self._train_logistic(X, y, sample_size=len(rows), source="model_predictions")

    async def train_calibration_model(self) -> Dict[str, Any]:
        """
        Train calibration from resolved model_predictions (primary) or parlay results (fallback).
        Uses logistic regression (Platt scaling).
        """
        # Prefer model_predictions for single-leg calibration
        out = await self.train_on_resolved_predictions(min_samples=20)
        if out.get("trained"):
            return out
        # Fallback: parlay results
        res = await self.db.execute(
            select(ParlayResult)
            .where(ParlayResult.hit.isnot(None))
            .where(ParlayResult.predicted_probability.isnot(None))
        )
        results = res.scalars().all()
        if not isinstance(results, list):
            results = list(results or [])
        if len(results) < 10:
            return {
                "trained": False,
                "message": "Not enough historical data (need at least 10 resolved)",
                "sample_size": len(results),
            }
        X = np.array([[r.predicted_probability] for r in results], dtype=np.float64)
        y = np.array([1.0 if r.hit else 0.0 for r in results], dtype=np.float64)
        return await self._train_logistic(X, y, sample_size=len(results), source="parlay_results")

    async def _train_logistic(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_size: int,
        source: str,
    ) -> Dict[str, Any]:
        """Fit LogisticRegression on (predicted_prob, actual) and persist."""
        try:
            from sklearn.linear_model import LogisticRegression
        except ImportError:
            logger.warning("[MLCalibration] sklearn not available; using bin fallback")
            return self._train_bin_fallback(X, y, sample_size, source)
        X_flat = X.reshape(-1, 1)
        model = LogisticRegression(C=1e10, max_iter=500, solver="lbfgs")
        model.fit(X_flat, y)
        self._logistic_model = model
        self._calibration_map = {}
        brier_before = float(np.mean((X.ravel() - y) ** 2))
        calibrated = np.array([self.calibrate_probability(float(p)) for p in X.ravel()])
        brier_after = float(np.mean((calibrated - y) ** 2))
        meta = {
            "sample_size": sample_size,
            "source": source,
            "brier_before": round(brier_before, 4),
            "brier_after": round(brier_after, 4),
        }
        self._save_serialized(model, self._calibration_map, meta)
        logger.info(
            "[MLCalibration] Trained logistic calibration; sample_size=%s brier_before=%s brier_after=%s",
            sample_size, brier_before, brier_after,
        )
        return {
            "trained": True,
            "sample_size": sample_size,
            "message": f"Logistic calibration trained on {sample_size} samples",
            "brier_before": round(brier_before, 4),
            "brier_after": round(brier_after, 4),
        }

    def _train_bin_fallback(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_size: int,
        source: str,
    ) -> Dict[str, Any]:
        """Bin-averaging fallback when sklearn is not available."""
        predicted_probs = X.ravel()
        actual_hits = y
        bins = np.linspace(0, 1, 11)
        bin_indices = np.digitize(predicted_probs, bins) - 1
        bin_indices = np.clip(bin_indices, 0, len(bins) - 2)
        calibration_map = {}
        for i in range(len(bins) - 1):
            mask = bin_indices == i
            if np.sum(mask) > 0:
                actual_rate = float(np.mean(actual_hits[mask]))
                predicted_center = (bins[i] + bins[i + 1]) / 2
                calibration_map[float(predicted_center)] = actual_rate
        self._calibration_map = calibration_map
        self._logistic_model = None
        avg_error = float(np.mean(np.abs(predicted_probs - actual_hits)))
        self._save_serialized(None, calibration_map, {"sample_size": sample_size, "source": source})
        return {
            "trained": True,
            "sample_size": sample_size,
            "avg_calibration_error": round(avg_error, 4),
            "calibration_bins": len(calibration_map),
            "message": f"Bin calibration trained on {sample_size} samples (sklearn not used)",
        }

    def calibrate_probability(self, predicted_prob: float) -> float:
        """
        Calibrate a predicted probability. Uses logistic model if trained, else bin map, else pass-through.
        """
        if predicted_prob is None or (isinstance(predicted_prob, float) and not (0 <= predicted_prob <= 1)):
            return 0.5
        p = float(predicted_prob)
        if self._logistic_model is not None:
            try:
                proba = self._logistic_model.predict_proba(np.array([[p]]))[0, 1]
                return float(np.clip(proba, 0.01, 0.99))
            except Exception as e:
                logger.debug("[MLCalibration] logistic predict failed: %s", e)
        if self._calibration_map:
            keys = sorted(self._calibration_map.keys())
            if keys:
                closest = min(keys, key=lambda x: abs(x - p))
                calibrated = self._calibration_map[closest]
                return float(np.clip(0.7 * calibrated + 0.3 * p, 0.01, 0.99))
        return float(np.clip(p, 0.01, 0.99))

    async def get_calibration_stats(self) -> Dict[str, Any]:
        """Get calibration statistics from parlay results (legacy) or resolved predictions."""
        result = await self.db.execute(
            select(ParlayResult).where(ParlayResult.hit.isnot(None))
        )
        results = result.scalars().all()
        if not results:
            return {"total_samples": 0, "calibration_available": bool(self._logistic_model or self._calibration_map)}
        brier_scores = [(r.predicted_probability - (1.0 if r.hit else 0.0)) ** 2 for r in results if r.predicted_probability is not None]
        avg_brier = float(np.mean(brier_scores)) if brier_scores else 0.0
        return {
            "total_samples": len(results),
            "avg_brier_score": round(avg_brier, 4),
            "calibration_available": bool(self._logistic_model or self._calibration_map),
        }
