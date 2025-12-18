from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ml_calibration import MLCalibrationService

logger = logging.getLogger(__name__)


class ParlayProbabilityCalibrationService:
    """
    Calibrates a raw parlay hit probability to better match observed hit rates.

    Uses `MLCalibrationService` under the hood and caches the learned calibration map
    in-process (best-effort).
    """

    _cache_lock: asyncio.Lock = asyncio.Lock()
    _cached_at: Optional[datetime] = None
    _cached_map: Dict[float, float] = {}
    _cache_ttl_seconds: int = 60 * 60  # 1 hour

    def __init__(self, db: AsyncSession):
        self._db = db

    async def calibrate(self, predicted_prob: float) -> float:
        raw = self._clamp01(predicted_prob)
        await self._ensure_loaded()

        cache_map = dict(self.__class__._cached_map or {})
        if not cache_map:
            return raw

        # Reuse the existing MLCalibrationService logic for applying the map.
        svc = MLCalibrationService(self._db)
        svc._calibration_map = cache_map  # type: ignore[attr-defined]
        try:
            return self._clamp01(float(svc.calibrate_probability(raw)))
        except Exception:
            # Safety net: never fail parlay generation due to calibration.
            return raw

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _ensure_loaded(self) -> None:
        if self._is_cache_fresh():
            return

        async with self.__class__._cache_lock:
            if self._is_cache_fresh():
                return

            try:
                trainer = MLCalibrationService(self._db)
                result = await trainer.train_calibration_model()
                trained = bool(result.get("trained"))
                calibration_map = dict(getattr(trainer, "_calibration_map", {}) or {})

                # Only cache maps when training succeeded and bins exist.
                self.__class__._cached_map = calibration_map if trained and calibration_map else {}
                self.__class__._cached_at = datetime.now(timezone.utc)

                if trained:
                    logger.info(
                        "[ParlayCalibration] Loaded calibration map: bins=%s sample_size=%s",
                        len(self.__class__._cached_map),
                        result.get("sample_size"),
                    )
                else:
                    logger.debug(
                        "[ParlayCalibration] Calibration not trained yet (sample_size=%s)",
                        result.get("sample_size"),
                    )
            except Exception as exc:
                # Best-effort only; cache empty to avoid repeated failures.
                self.__class__._cached_map = {}
                self.__class__._cached_at = datetime.now(timezone.utc)
                logger.debug("[ParlayCalibration] Failed to load calibration (ignored): %s", exc)

    def _is_cache_fresh(self) -> bool:
        ts = self.__class__._cached_at
        if ts is None:
            return False
        age_seconds = (datetime.now(timezone.utc) - ts).total_seconds()
        return age_seconds < float(self.__class__._cache_ttl_seconds)

    @staticmethod
    def _clamp01(value: float) -> float:
        try:
            x = float(value)
        except Exception:
            return 0.0
        return max(0.0, min(1.0, x))


