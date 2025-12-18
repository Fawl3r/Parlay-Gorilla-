from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.services.parlay_probability.parlay_probability_calibration_service import (
    ParlayProbabilityCalibrationService,
)


class _EmptyScalarResult:
    def scalars(self):
        return self

    def all(self):
        return []


@pytest.mark.asyncio
async def test_calibration_is_identity_when_not_trained():
    # Reset cache (tests run in-process; avoid cross-test leakage).
    ParlayProbabilityCalibrationService._cached_at = None
    ParlayProbabilityCalibrationService._cached_map = {}

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_EmptyScalarResult())

    svc = ParlayProbabilityCalibrationService(db)
    out = await svc.calibrate(0.42)
    assert out == pytest.approx(0.42, abs=1e-12)


@pytest.mark.asyncio
async def test_calibration_applies_cached_map_when_available():
    # Prime cache to avoid DB access.
    ParlayProbabilityCalibrationService._cached_at = datetime.now(timezone.utc)
    ParlayProbabilityCalibrationService._cached_map = {0.5: 0.2}

    db = AsyncMock()
    svc = ParlayProbabilityCalibrationService(db)

    # MLCalibrationService logic: 70% calibrated + 30% original
    expected = (0.7 * 0.2) + (0.3 * 0.52)
    out = await svc.calibrate(0.52)
    assert out == pytest.approx(expected, abs=1e-12)

    # Clean up global cache to avoid leaking state into other tests.
    ParlayProbabilityCalibrationService._cached_at = None
    ParlayProbabilityCalibrationService._cached_map = {}


