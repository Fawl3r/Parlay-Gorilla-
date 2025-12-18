"""Score projection helpers used by core analysis generation.

Split from `core_analysis_generator.py` to keep files small and focused.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class ScoreProjection:
    home_score: int
    away_score: int

    @property
    def margin_home_minus_away(self) -> int:
        return self.home_score - self.away_score

    @property
    def total_points(self) -> int:
        return self.home_score + self.away_score

    def as_str(self) -> str:
        return f"{self.home_score}-{self.away_score}"


class ScoreProjector:
    """Lightweight score projection based on win probabilities."""

    # Baseline is *per-team*.
    _BASELINE: Dict[str, Tuple[float, float]] = {
        "NFL": (24.0, 10.0),
        "NCAAF": (28.0, 14.0),
        "NBA": (112.0, 16.0),
        "NCAAB": (72.0, 12.0),
        "NHL": (3.0, 2.0),
        "MLB": (4.0, 3.0),
        # Soccer: goals per team baseline (rough).
        "EPL": (1.3, 1.4),
        "MLS": (1.4, 1.5),
        "LALIGA": (1.2, 1.3),
        "UCL": (1.2, 1.3),
        "SOCCER": (1.3, 1.4),
    }

    @classmethod
    def baseline_total(cls, *, league: str) -> float:
        base, _variance = cls._BASELINE.get((league or "").upper(), (24.0, 10.0))
        return float(base) * 2.0

    @classmethod
    def project(cls, *, league: str, home_prob: float, away_prob: float) -> ScoreProjection:
        base, variance = cls._BASELINE.get((league or "").upper(), (24.0, 10.0))
        home = int(round(base + (home_prob - 0.5) * variance * 2))
        away = int(round(base + (away_prob - 0.5) * variance * 2))

        # Clamp at 0 for low-scoring sports (prevents negative projections).
        home = max(0, home)
        away = max(0, away)

        if home == away:
            home += 1 if home_prob >= away_prob else 0
            away += 1 if home_prob < away_prob else 0

        return ScoreProjection(home_score=home, away_score=away)



