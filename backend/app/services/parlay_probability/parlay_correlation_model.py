from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class ParlayCorrelationModel:
    """
    Estimates *latent* (Gaussian-copula) correlations between legs within the same game.

    Notes:
    - This is intentionally heuristic-first and configurable.
    - It is designed to be deterministic and fast.
    - It can later be upgraded to learn correlations from historical outcomes.
    """

    _DEFAULT_MARKET_PAIR_CORR: Dict[Tuple[str, str], float] = {
        # Same market (different books / slightly different lines): high dependence
        ("h2h", "h2h"): 0.70,
        ("spreads", "spreads"): 0.65,
        ("totals", "totals"): 0.65,
        # Cross-market within the same game (latent / copula): moderate dependence
        # These are conservative priors; correlation is further adjusted by side alignment
        # for team-side markets (h2h/spreads).
        ("h2h", "spreads"): 0.35,
        ("h2h", "totals"): 0.06,
        ("spreads", "totals"): 0.12,
    }

    def __init__(
        self,
        *,
        base_same_game_corr: float = 0.06,
        market_pair_corr: Optional[Dict[Tuple[str, str], float]] = None,
        min_corr: float = -0.60,
        max_corr: float = 0.85,
        side_alignment_bonus: float = 0.06,
        side_misalignment_penalty: float = 0.08,
    ):
        self._base_same_game_corr = float(base_same_game_corr)
        self._pair_corr = dict(self._DEFAULT_MARKET_PAIR_CORR)
        if market_pair_corr:
            # Allow callers (tests / future training) to override defaults.
            for k, v in market_pair_corr.items():
                self._pair_corr[self._pair_key(k[0], k[1])] = float(v)

        self._min_corr = float(min_corr)
        self._max_corr = float(max_corr)
        self._side_alignment_bonus = float(side_alignment_bonus)
        self._side_misalignment_penalty = float(side_misalignment_penalty)

    def build_correlation_matrix(self, legs: List[Dict[str, Any]]) -> List[List[float]]:
        """
        Build an NxN symmetric correlation matrix for legs assumed to be in the same game group.
        """
        n = len(legs or [])
        if n <= 0:
            return []
        if n == 1:
            return [[1.0]]

        matrix: List[List[float]] = [[0.0 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            matrix[i][i] = 1.0
        for i in range(n):
            for j in range(i + 1, n):
                corr = self.estimate_latent_correlation(legs[i], legs[j])
                matrix[i][j] = corr
                matrix[j][i] = corr
        return matrix

    def estimate_latent_correlation(self, leg_a: Dict[str, Any], leg_b: Dict[str, Any]) -> float:
        """
        Estimate the latent correlation between two legs.

        Returns:
            Correlation in [min_corr, max_corr]. Returns 0.0 for cross-game pairs.
        """
        game_a = str(leg_a.get("game_id") or "").strip()
        game_b = str(leg_b.get("game_id") or "").strip()
        if game_a and game_b and game_a != game_b:
            return 0.0

        m1 = self._normalize_market_type(leg_a.get("market_type"))
        m2 = self._normalize_market_type(leg_b.get("market_type"))

        base = self._base_same_game_corr
        pair = float(self._pair_corr.get(self._pair_key(m1, m2), 0.0))

        corr = base + pair
        corr += self._side_adjustment(leg_a, leg_b, m1, m2)

        return float(max(self._min_corr, min(self._max_corr, corr)))

    def _side_adjustment(self, leg_a: Dict[str, Any], leg_b: Dict[str, Any], m1: str, m2: str) -> float:
        # Only attempt directionality for team-side markets.
        if m1 not in {"h2h", "spreads"} or m2 not in {"h2h", "spreads"}:
            return 0.0

        side_a = self._infer_team_side(leg_a)
        side_b = self._infer_team_side(leg_b)
        if side_a is None or side_b is None:
            return 0.0
        if side_a == side_b:
            return self._side_alignment_bonus
        return -self._side_misalignment_penalty

    @staticmethod
    def _pair_key(m1: str, m2: str) -> Tuple[str, str]:
        a = (m1 or "").lower().strip()
        b = (m2 or "").lower().strip()
        return (a, b) if a <= b else (b, a)

    @staticmethod
    def _normalize_market_type(value: Any) -> str:
        v = str(value or "").lower().strip()
        if v in {"moneyline", "ml", "h2h"}:
            return "h2h"
        if v in {"spread", "spreads"}:
            return "spreads"
        if v in {"total", "totals", "over_under"}:
            return "totals"
        return v or "unknown"

    @staticmethod
    def _infer_team_side(leg: Dict[str, Any]) -> Optional[str]:
        """
        Best-effort inference of whether a leg is on the home or away side.
        """
        outcome = str(leg.get("outcome") or "").lower().strip()
        if "home" in outcome:
            return "home"
        if "away" in outcome:
            return "away"

        # Try matching against explicit team names if present.
        home = str(leg.get("home_team") or "").lower().strip()
        away = str(leg.get("away_team") or "").lower().strip()
        if home and outcome and home in outcome:
            return "home"
        if away and outcome and away in outcome:
            return "away"

        return None


