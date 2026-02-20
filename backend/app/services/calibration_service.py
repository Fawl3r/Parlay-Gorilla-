"""
Lightweight monotonic calibration (no sklearn/torch).

Uses calibration_bins: bucket predicted_prob -> empirical hit rate.
calibrate(p) returns mapped probability if mapping is trained; otherwise returns p.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calibration_bin import CalibrationBin

logger = logging.getLogger(__name__)

_NUM_BINS = 10
_MIN_SAMPLES_TO_TRAIN = 50


async def get_latest_bins(db: AsyncSession) -> list[CalibrationBin]:
    """Load the most recent calibration bin set (by trained_at)."""
    result = await db.execute(
        select(CalibrationBin)
        .order_by(CalibrationBin.trained_at.desc())
        .limit(_NUM_BINS + 5)
    )
    rows = result.scalars().all()
    if not rows:
        return []
    latest_ts = rows[0].trained_at
    return [r for r in rows if r.trained_at == latest_ts]


def calibrate(p: float, bins: list[CalibrationBin]) -> float:
    """
    Map raw probability through calibration bins.
    If no bins or p outside range, return p unchanged.
    Uses linear interpolation between bin centers.
    """
    if not bins or not (0 <= p <= 1):
        return p
    sorted_bins = sorted(bins, key=lambda b: b.bin_low)
    for b in sorted_bins:
        if b.bin_low <= p <= b.bin_high:
            return b.empirical_hit_rate
    if p < sorted_bins[0].bin_low:
        return sorted_bins[0].empirical_hit_rate
    return sorted_bins[-1].empirical_hit_rate


async def calibrate_async(db: AsyncSession, p: float) -> float:
    """
    Load latest bins and apply calibrate(p).
    If no trained mapping, returns p unchanged.
    """
    bins = await get_latest_bins(db)
    return calibrate(p, bins)
