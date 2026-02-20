"""
Market regime detection: LOW_VOLATILITY, HIGH_VOLATILITY, LINE_CHAOS, SHARP_DOMINANT.

Inputs: odds movement variance, CLV variance, prediction variance, hit-rate shifts.
Persist regime per prediction; allow strategy weights to vary by regime (future).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_prediction import ModelPrediction

logger = logging.getLogger(__name__)

REGIME_LOW_VOLATILITY = "LOW_VOLATILITY"
REGIME_HIGH_VOLATILITY = "HIGH_VOLATILITY"
REGIME_LINE_CHAOS = "LINE_CHAOS"
REGIME_SHARP_DOMINANT = "SHARP_DOMINANT"
REGIME_UNKNOWN = "UNKNOWN"

WINDOW = 50
LOW_VOL_THRESHOLD = 0.02
HIGH_VOL_THRESHOLD = 0.08
CHAOS_THRESHOLD = 0.12


class MarketRegimeService:
    """Detect market regime from recent prediction variance and optional odds variance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _recent_prediction_variance(self, sport: Optional[str] = None, limit: int = WINDOW) -> Optional[float]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        q = select(ModelPrediction.predicted_prob).where(ModelPrediction.created_at >= cutoff).limit(limit)
        if sport:
            q = q.where(ModelPrediction.sport == sport.upper())
        r = await self.db.execute(q)
        probs = [float(row[0]) for row in r.all() if row[0] is not None]
        if len(probs) < 5:
            return None
        mean = sum(probs) / len(probs)
        variance = sum((x - mean) ** 2 for x in probs) / (len(probs) - 1)
        return variance

    async def detect_regime(
        self,
        sport: Optional[str] = None,
        odds_variance: Optional[float] = None,
        prediction_variance: Optional[float] = None,
    ) -> str:
        """
        Classify regime from variance of predictions (and optional odds variance).
        Uses rolling statistical thresholds.
        """
        var = prediction_variance
        if var is None:
            var = await self._recent_prediction_variance(sport=sport)
        if var is None:
            return REGIME_UNKNOWN
        if odds_variance is not None and odds_variance > CHAOS_THRESHOLD:
            return REGIME_LINE_CHAOS
        if var <= LOW_VOL_THRESHOLD:
            return REGIME_LOW_VOLATILITY
        if var >= HIGH_VOL_THRESHOLD:
            return REGIME_HIGH_VOLATILITY
        if var >= CHAOS_THRESHOLD:
            return REGIME_LINE_CHAOS
        return REGIME_SHARP_DOMINANT

    async def get_regime_for_prediction(
        self,
        sport: str,
        implied_prob: float,
        predicted_prob: float,
        odds_variance: Optional[float] = None,
    ) -> str:
        """Detect regime to attach to a new prediction (uses recent variance + optional odds variance)."""
        return await self.detect_regime(sport=sport, odds_variance=odds_variance)
