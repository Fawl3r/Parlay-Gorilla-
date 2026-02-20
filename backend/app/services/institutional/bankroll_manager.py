"""
Bankroll and risk management: Kelly fraction, fractional Kelly (default 0.25), risk-adjusted confidence.

Tracks simulated bankroll from historical predictions; reduces exposure during drawdowns.
risk_confidence = confidence * bankroll_safety_multiplier.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome

logger = logging.getLogger(__name__)

DEFAULT_FRACTIONAL_KELLY = 0.25
DRAWDOWN_THRESHOLD = 0.15
ROLLING_WINDOW = 100


class BankrollManager:
    """
    Simulates bankroll performance from resolved predictions; computes Kelly fraction and safety multiplier.
    """

    def __init__(self, db: AsyncSession, fractional_kelly: float = DEFAULT_FRACTIONAL_KELLY):
        self.db = db
        self.fractional_kelly = max(0.1, min(0.5, fractional_kelly))

    async def _recent_resolved_with_ev(self, limit: int = 500) -> List[tuple[Any, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=180)
        q = (
            select(ModelPrediction, PredictionOutcome)
            .join(PredictionOutcome, PredictionOutcome.prediction_id == ModelPrediction.id)
            .where(ModelPrediction.resolved_at >= cutoff)
            .order_by(ModelPrediction.resolved_at.desc())
            .limit(limit)
        )
        r = await self.db.execute(q)
        return list(r.all())

    async def kelly_fraction(self, win_prob: float, decimal_odds: float) -> float:
        """Optimal Kelly: (p * b - q) / b where b = decimal_odds - 1, q = 1 - p."""
        if decimal_odds <= 1.0:
            return 0.0
        b = decimal_odds - 1.0
        q = 1.0 - win_prob
        k = (win_prob * b - q) / b if b else 0.0
        return max(0.0, min(0.25, k))

    async def get_bankroll_safety_multiplier(self) -> float:
        """
        Returns multiplier in (0.5, 1.0]. During drawdown (rolling loss > threshold), reduce exposure.
        """
        rows = await self._recent_resolved_with_ev(limit=ROLLING_WINDOW)
        if len(rows) < 20:
            return 1.0

        cumulative = 0.0
        peak = 0.0
        drawdown = 0.0
        for pred, outcome in reversed(rows):
            ev = getattr(pred, "expected_value", None) or 0.0
            implied_odds = getattr(pred, "implied_odds", None) or 2.0
            unit = 1.0
            if outcome.was_correct:
                cumulative += unit * (implied_odds - 1.0)
            else:
                cumulative -= unit
            peak = max(peak, cumulative)
            dd = peak - cumulative
            if dd > drawdown:
                drawdown = dd

        if peak <= 0:
            return 1.0
        dd_pct = drawdown / peak if peak else 0
        if dd_pct >= DRAWDOWN_THRESHOLD:
            return max(0.5, 1.0 - (dd_pct - DRAWDOWN_THRESHOLD))
        return 1.0

    async def risk_adjusted_confidence(self, confidence: float) -> float:
        """confidence * bankroll_safety_multiplier, clamped to [0, 100]."""
        mult = await self.get_bankroll_safety_multiplier()
        return max(0.0, min(100.0, confidence * mult))

    async def get_metrics(self) -> Dict[str, Any]:
        """Return kelly_fraction (as used), fractional_kelly, drawdown proxy, safety_multiplier."""
        mult = await self.get_bankroll_safety_multiplier()
        return {
            "fractional_kelly": self.fractional_kelly,
            "bankroll_safety_multiplier": round(mult, 4),
            "drawdown_threshold": DRAWDOWN_THRESHOLD,
        }
