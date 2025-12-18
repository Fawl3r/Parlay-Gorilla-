import pytest

from app.services.parlay_probability.correlated_parlay_probability_calculator import (
    CorrelatedParlayProbabilityCalculator,
)
from app.services.parlay_probability.parlay_correlation_model import ParlayCorrelationModel


class _ConstantCorrelationModel:
    """Test-only correlation model returning a constant within-game correlation."""

    def __init__(self, rho: float):
        self._rho = float(rho)

    def build_correlation_matrix(self, legs):
        n = len(legs or [])
        if n <= 0:
            return []
        if n == 1:
            return [[1.0]]
        return [[1.0 if i == j else self._rho for j in range(n)] for i in range(n)]


def test_calculate_independent_groups_falls_back_to_product():
    calc = CorrelatedParlayProbabilityCalculator(ParlayCorrelationModel())
    legs = [
        {"game_id": "g1", "market_type": "h2h", "outcome": "home", "adjusted_prob": 0.70},
        {"game_id": "g2", "market_type": "h2h", "outcome": "away", "adjusted_prob": 0.60},
    ]
    assert calc.calculate(legs, risk_profile="balanced") == pytest.approx(0.42, abs=1e-12)


def test_calculate_monotonic_with_higher_correlation_for_same_game_group():
    legs = [
        {"game_id": "g1", "market_type": "h2h", "outcome": "home", "adjusted_prob": 0.65},
        {"game_id": "g1", "market_type": "spreads", "outcome": "home", "adjusted_prob": 0.65},
    ]

    low = CorrelatedParlayProbabilityCalculator(
        _ConstantCorrelationModel(0.0),
        samples_by_profile={"balanced": 20000},
    )
    high = CorrelatedParlayProbabilityCalculator(
        _ConstantCorrelationModel(0.70),
        samples_by_profile={"balanced": 20000},
    )

    p_low = low.calculate(legs, risk_profile="balanced", rng_seed=123)
    p_high = high.calculate(legs, risk_profile="balanced", rng_seed=123)
    assert p_high > p_low + 0.01


def test_calculate_is_stable_with_fixed_seed():
    legs = [
        {"game_id": "g1", "market_type": "h2h", "outcome": "home", "adjusted_prob": 0.62},
        {"game_id": "g1", "market_type": "totals", "outcome": "over", "adjusted_prob": 0.58},
    ]
    calc = CorrelatedParlayProbabilityCalculator(
        _ConstantCorrelationModel(0.35),
        samples_by_profile={"balanced": 8000},
    )

    p1 = calc.calculate(legs, risk_profile="balanced", rng_seed=999)
    p2 = calc.calculate(legs, risk_profile="balanced", rng_seed=999)
    assert p1 == p2


def test_calculate_is_deterministic_by_default():
    legs = [
        {"game_id": "g1", "market_type": "h2h", "outcome": "home", "adjusted_prob": 0.62},
        {"game_id": "g1", "market_type": "totals", "outcome": "over", "adjusted_prob": 0.58},
    ]
    calc = CorrelatedParlayProbabilityCalculator(
        _ConstantCorrelationModel(0.35),
        samples_by_profile={"balanced": 8000},
    )

    p1 = calc.calculate(legs, risk_profile="balanced")
    p2 = calc.calculate(list(reversed(legs)), risk_profile="balanced")
    assert p1 == p2


