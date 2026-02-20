"""
Confidence engine: blend model probability with odds-implied probability.

Supports:
- Legacy: final_prob = w * model_prob + (1-w) * implied_prob
- Composite: weighted sum of calibrated_prob, CLV score, historical accuracy,
  market disagreement, calibration adjustment; normalized 0-1. Deterministic.
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
    Produces final probability and confidence meter.
    Legacy: blend model + implied. Composite: 0.35*calibrated + 0.25*clv + 0.20*hist_acc
    + 0.10*market_disagreement_factor + 0.10*calibration_adjustment, normalized 0-1.
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

    def composite_confidence(
        self,
        calibrated_probability: float,
        closing_line_value_score: float = 0.5,
        historical_model_accuracy: float = 0.5,
        market_disagreement_factor: float = 0.0,
        calibration_adjustment: float = 0.0,
    ) -> float:
        """
        Weighted composite confidence. All inputs in [0, 1] where applicable.
        closing_line_value_score: 0-1 (higher = better CLV).
        market_disagreement_factor: 0-1 (higher = more disagreement, penalized).
        Returns value in [0, 1]. Deterministic.
        """
        calibrated_probability = clamp(calibrated_probability, 0.0, 1.0)
        closing_line_value_score = clamp(closing_line_value_score, 0.0, 1.0)
        historical_model_accuracy = clamp(historical_model_accuracy, 0.0, 1.0)
        market_disagreement_factor = clamp(market_disagreement_factor, 0.0, 1.0)
        calibration_adjustment = clamp(calibration_adjustment, -0.2, 0.2)
        raw = (
            0.35 * calibrated_probability
            + 0.25 * closing_line_value_score
            + 0.20 * historical_model_accuracy
            + 0.10 * (1.0 - market_disagreement_factor)
            + 0.10 * (0.5 + calibration_adjustment)
        )
        return clamp(raw, 0.0, 1.0)

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
