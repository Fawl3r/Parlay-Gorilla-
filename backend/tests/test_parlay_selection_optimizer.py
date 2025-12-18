from typing import Any, Dict, List

import pytest

from app.services.parlay_builder_impl.parlay_selection_optimizer import ParlaySelectionOptimizer
from app.services.parlay_probability.parlay_correlation_model import ParlayCorrelationModel


class _NoCorrelationModel(ParlayCorrelationModel):
    def estimate_latent_correlation(self, leg_a: Dict[str, Any], leg_b: Dict[str, Any]) -> float:  # type: ignore[override]
        return 0.0


class _ScriptedCorrelationModel(ParlayCorrelationModel):
    """
    Test-only correlation model that allows per-leg-pair correlation scripting.
    """

    def __init__(self, mapping):
        super().__init__()
        self._mapping = mapping

    def estimate_latent_correlation(self, leg_a: Dict[str, Any], leg_b: Dict[str, Any]) -> float:  # type: ignore[override]
        if str(leg_a.get("game_id")) != str(leg_b.get("game_id")):
            return 0.0
        a = str(leg_a.get("market_id") or "")
        b = str(leg_b.get("market_id") or "")
        key = tuple(sorted((a, b)))
        return float(self._mapping.get(key, 0.0))


def _no_conflicts(_leg: Dict[str, Any], _selected: List[Dict[str, Any]]) -> bool:
    return False


def _h2h_conflict_checker(leg: Dict[str, Any], selected: List[Dict[str, Any]]) -> bool:
    """Minimal conflict rule: same game + h2h + opposite outcomes."""
    if not selected:
        return False
    if str(leg.get("market_type")) != "h2h":
        return False
    outcome = str(leg.get("outcome") or "").lower()
    for other in selected:
        if str(other.get("game_id")) != str(leg.get("game_id")):
            continue
        if str(other.get("market_type")) != "h2h":
            continue
        other_outcome = str(other.get("outcome") or "").lower()
        if outcome in {"home", "away"} and other_outcome in {"home", "away"} and outcome != other_outcome:
            return True
    return False


def test_optimizer_returns_exact_k_when_possible():
    optimizer = ParlaySelectionOptimizer(correlation_model=_NoCorrelationModel())
    candidates = [
        {"game_id": "g1", "market_type": "h2h", "outcome": "home", "market_id": "m1", "ev_score": 3.0},
        {"game_id": "g2", "market_type": "h2h", "outcome": "home", "market_id": "m2", "ev_score": 2.5},
        {"game_id": "g3", "market_type": "h2h", "outcome": "away", "market_id": "m3", "ev_score": 2.0},
        {"game_id": "g4", "market_type": "h2h", "outcome": "home", "market_id": "m4", "ev_score": 1.0},
    ]

    selected = optimizer.select(
        candidates=candidates,
        num_legs=3,
        risk_profile="balanced",
        conflict_checker=_no_conflicts,
        max_legs_per_game=2,
        max_pair_corr=0.99,
        beam_width=20,
    )

    assert len(selected) == 3


def test_optimizer_never_selects_conflicting_h2h_legs():
    optimizer = ParlaySelectionOptimizer(correlation_model=_NoCorrelationModel())
    candidates = [
        {"game_id": "g1", "market_type": "h2h", "outcome": "home", "market_id": "m1", "ev_score": 10.0},
        {"game_id": "g1", "market_type": "h2h", "outcome": "away", "market_id": "m2", "ev_score": 9.9},
        {"game_id": "g2", "market_type": "h2h", "outcome": "home", "market_id": "m3", "ev_score": 1.0},
    ]

    selected = optimizer.select(
        candidates=candidates,
        num_legs=2,
        risk_profile="balanced",
        conflict_checker=_h2h_conflict_checker,
        max_legs_per_game=2,
        max_pair_corr=0.99,
        beam_width=20,
    )

    assert len(selected) == 2
    assert not _h2h_conflict_checker(selected[0], [selected[1]])
    assert not _h2h_conflict_checker(selected[1], [selected[0]])


def test_optimizer_beats_naive_greedy_in_constructed_case():
    # In game g1: picking A blocks adding any other g1 leg due to correlation ceiling.
    mapping = {
        ("A", "B"): 0.90,
        ("A", "C"): 0.90,
        ("B", "C"): 0.10,
    }
    optimizer = ParlaySelectionOptimizer(correlation_model=_ScriptedCorrelationModel(mapping))

    candidates = [
        # Game 1
        {"game_id": "g1", "market_type": "h2h", "outcome": "home", "market_id": "A", "ev_score": 100.0},
        {"game_id": "g1", "market_type": "totals", "outcome": "over", "market_id": "B", "ev_score": 80.0},
        {"game_id": "g1", "market_type": "spreads", "outcome": "home", "market_id": "C", "ev_score": 79.0},
        # Game 2
        {"game_id": "g2", "market_type": "h2h", "outcome": "home", "market_id": "D", "ev_score": 90.0},
        # Game 3 (fallback junk leg)
        {"game_id": "g3", "market_type": "h2h", "outcome": "home", "market_id": "E", "ev_score": 1.0},
    ]

    corr_ceiling = 0.50

    def greedy_select():
        chosen: List[Dict[str, Any]] = []
        for leg in sorted(candidates, key=lambda x: float(x.get("ev_score", 0.0)), reverse=True):
            if len(chosen) >= 3:
                break
            # max 2 legs per game
            if sum(1 for c in chosen if str(c.get("game_id")) == str(leg.get("game_id"))) >= 2:
                continue
            if _no_conflicts(leg, chosen):
                continue
            # correlation ceiling within same game
            too_corr = False
            for c in chosen:
                corr = optimizer._corr.estimate_latent_correlation(leg, c)
                if abs(corr) >= corr_ceiling:
                    too_corr = True
                    break
            if too_corr:
                continue
            chosen.append(leg)
        return chosen

    greedy = greedy_select()
    opt = optimizer.select(
        candidates=candidates,
        num_legs=3,
        risk_profile="balanced",
        conflict_checker=_no_conflicts,
        max_legs_per_game=2,
        max_pair_corr=corr_ceiling,
        beam_width=40,
    )

    greedy_score = sum(float(l.get("ev_score", 0.0) or 0.0) for l in greedy)
    opt_score = sum(float(l.get("ev_score", 0.0) or 0.0) for l in opt)

    assert len(opt) == 3
    assert opt_score > greedy_score


