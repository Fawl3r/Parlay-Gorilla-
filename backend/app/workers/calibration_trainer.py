"""
Calibration trainer: lightweight monotonic calibration from resolved predictions.

Runs every 6 hours. Only trains if >= 50 resolved. Buckets predicted_prob into bins,
computes empirical hit rate per bin, stores in calibration_bins. No sklearn/torch.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select, delete
from app.database.session import AsyncSessionLocal
from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome
from app.models.calibration_bin import CalibrationBin

logger = logging.getLogger(__name__)

_NUM_BINS = 10
_MIN_SAMPLES_TO_TRAIN = 50


async def run_calibration_trainer_cycle() -> None:
    """
    One cycle: if >= 50 resolved predictions, compute bin hit rates and store in calibration_bins.
    Idempotent: overwrites latest run by inserting new rows (get_latest_bins uses trained_at).
    """
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ModelPrediction.predicted_prob, PredictionOutcome.was_correct)
                .select_from(ModelPrediction)
                .join(PredictionOutcome, PredictionOutcome.prediction_id == ModelPrediction.id)
            )
            rows = result.all()
        if len(rows) < _MIN_SAMPLES_TO_TRAIN:
            logger.debug(
                "[CalibrationTrainer] Skipping: resolved_count=%s (need >= %s)",
                len(rows),
                _MIN_SAMPLES_TO_TRAIN,
            )
            return

        bins: list[tuple[float, float, int, int]] = []  # bin_low, bin_high, hits, count
        step = 1.0 / _NUM_BINS
        for i in range(_NUM_BINS):
            low = i * step
            high = (i + 1) * step if i < _NUM_BINS - 1 else 1.0
            hits = 0
            count = 0
            for prob, was_correct in rows:
                if low <= prob < high or (i == _NUM_BINS - 1 and prob == 1.0):
                    count += 1
                    if was_correct:
                        hits += 1
            rate = hits / count if count > 0 else 0.5
            bins.append((low, high, hits, count))

        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as db:
            for i, (bin_low, bin_high, hits, count) in enumerate(bins):
                db.add(
                    CalibrationBin(
                        bin_index=i,
                        bin_low=bin_low,
                        bin_high=bin_high,
                        empirical_hit_rate=hits / count if count else 0.5,
                        sample_count=count,
                        trained_at=now,
                    )
                )
            await db.commit()

        logger.info(
            "calibration_trained",
            extra={
                "sample_size": len(rows),
                "timestamp": now.isoformat(),
                "num_bins": _NUM_BINS,
            },
        )
    except Exception as e:
        logger.exception("[CalibrationTrainer] Cycle failed: %s", e)
