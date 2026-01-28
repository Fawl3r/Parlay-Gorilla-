"""
Confidence engine: blend model probability with odds-implied probability.

final_prob = w * model_prob + (1-w) * implied_prob
w depends on data freshness, sample size, and calibration quality.
Returns confidence_meter bucket and explanation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Confidence meter buckets (percent ranges)
BUCKETS = [(50, 60), (60, 70), (70, 80), (80, 90), (90, 101)]


@dataclass
class ConfidenceResult:
    """Result of confidence blending."""
    final_prob: float
    confidence_meter: str  # e.g. "60-70"
    explanation: str
    w_used: float


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class ConfidenceEngine:
    """
    Produces final probability and confidence meter from model + odds.
    w = clamp(base_w * freshness * sample_score, min_w, max_w)
    final_prob = w * model_prob + (1-w) * implied_prob
    """

    def __init__(
        self,
        *,
        base_w: float = 0.6,
        min_w: float = 0.2,
        max_w: float = 0.9,
    ):
        self._base_w = base_w
        self._min_w = min_w
        self._max_w = max_w

    def blend(
        self,
        model_prob: float,
        implied_prob: float,
        data_freshness_score: float = 1.0,
        sample_size_score: float = 1.0,
    ) -> ConfidenceResult:
        """
        Blend model and implied probability. freshness and sample_size in [0, 1].
        """
        w = clamp(
            self._base_w * data_freshness_score * sample_size_score,
            self._min_w,
            self._max_w,
        )
        final_prob = clamp(w * model_prob + (1.0 - w) * implied_prob, 0.0, 1.0)
        pct = final_prob * 100.0
        bucket = "50-60"
        for lo, hi in BUCKETS:
            if lo <= pct < hi:
                bucket = f"{lo}-{hi}"
                break
        if pct >= 90:
            bucket = "90+"

        explanation_parts = []
        if data_freshness_score < 0.5:
            explanation_parts.append("data stale")
        elif data_freshness_score >= 0.9:
            explanation_parts.append("data fresh")
        if abs(model_prob - implied_prob) > 0.15:
            explanation_parts.append("market disagrees with model")
        elif abs(model_prob - implied_prob) < 0.05:
            explanation_parts.append("market agrees with model")
        explanation = "; ".join(explanation_parts) if explanation_parts else "blended"

        return ConfidenceResult(
            final_prob=final_prob,
            confidence_meter=bucket,
            explanation=explanation,
            w_used=w,
        )


def get_confidence_engine() -> ConfidenceEngine:
    return ConfidenceEngine()
