"""
Meta performance model: predicts "probability that this prediction will outperform market".

Inputs: calibrated_prob, clv_signal, disagreement, regime, confidence, historical_strategy_performance.
Output: meta_score (0-1). Blended into final_confidence: 0.8 * confidence + 0.2 * meta_score.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

META_WEIGHT = 0.2
CONFIDENCE_WEIGHT = 0.8


class MetaModelService:
    """
    Lightweight meta-score from inputs (no heavy ML by default). Degrades safely with insufficient data.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, float] = {}

    def meta_score(
        self,
        calibrated_prob: float,
        clv_signal: Optional[float] = None,
        disagreement: Optional[float] = None,
        regime: Optional[str] = None,
        confidence: Optional[float] = None,
        historical_strategy_performance: Optional[float] = None,
    ) -> float:
        """
        Return meta_score in [0, 1]. Simple heuristic: higher when calibrated_prob is confident,
        clv positive, low chaos regime. Degrades to 0.5 when data missing.
        """
        score = 0.5
        if calibrated_prob is not None and 0 <= calibrated_prob <= 1:
            score = 0.4 + 0.2 * abs(calibrated_prob - 0.5)
        if clv_signal is not None and clv_signal > 0.5:
            score = min(1.0, score + 0.1)
        if regime in ("LINE_CHAOS",):
            score = max(0.2, score - 0.15)
        if historical_strategy_performance is not None and historical_strategy_performance > 0.55:
            score = min(1.0, score + 0.1)
        return max(0.0, min(1.0, score))

    def blend_confidence(self, confidence: float, meta_score: float) -> float:
        """final_confidence = 0.8 * confidence + 0.2 * meta_score (confidence in 0-100, meta 0-1)."""
        c = max(0, min(100, confidence)) / 100.0
        m = max(0, min(1, meta_score))
        return (CONFIDENCE_WEIGHT * c + META_WEIGHT * m) * 100.0
