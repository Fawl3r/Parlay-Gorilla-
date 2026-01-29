from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from app.core.event_logger import log_event
from app.services.parlay_builder_impl.parlay_selection_optimizer import ParlaySelectionOptimizer
from app.services.parlay_probability.parlay_correlation_model import ParlayCorrelationModel

_logger = logging.getLogger(__name__)


class ParlayLegSelectionService:
    """Selects the best set of parlay legs from a candidate pool."""

    def __init__(self):
        self._correlation_model = ParlayCorrelationModel()
        self._optimizer = ParlaySelectionOptimizer(correlation_model=self._correlation_model)

    def select_legs(self, candidates: List[Dict], num_legs: int, risk_profile: str) -> List[Dict]:
        if not candidates:
            log_event(
                _logger,
                "parlay.generate.filters.summary",
                candidates_count=0,
                num_legs=num_legs,
                risk_profile=risk_profile or "balanced",
                level=logging.WARNING,
            )
            raise ValueError("Not enough candidate legs available. Found 0 candidate legs.")

        normalized_profile = (risk_profile or "balanced").lower()
        positive_edge_candidates = self._filter_positive_edge_legs(candidates, normalized_profile)
        working_candidates = (
            positive_edge_candidates if len(positive_edge_candidates) >= num_legs else candidates
        )

        deduplicated = self._deduplicate(working_candidates)
        if len(deduplicated) < num_legs:
            deduplicated = self._expand_deduplication(candidates, num_legs)

        scored = self._with_ev_scores(deduplicated)
        scored = self._prefilter_for_profile(scored, num_legs, normalized_profile)

        selected: List[Dict] = []
        for corr_ceiling in self._correlation_ceilings(normalized_profile):
            selected = self._optimizer.select(
                candidates=scored,
                num_legs=num_legs,
                risk_profile=normalized_profile,
                conflict_checker=self._conflicts_with_selected,
                max_legs_per_game=2,
                max_pair_corr=corr_ceiling,
            )
            selected = self._remove_conflicting_legs(selected)
            if len(selected) >= num_legs:
                break

        return selected[:num_legs]

    def _prefilter_for_profile(self, candidates: List[Dict], num_legs: int, risk_profile: str) -> List[Dict]:
        """
        Apply profile-specific confidence filtering before running the optimizer.

        This keeps search fast and makes risk tiers behave similarly to the legacy selector.
        """
        profile = (risk_profile or "balanced").lower().strip()
        min_confidence = {"conservative": 70.0, "balanced": 55.0, "degen": 40.0}.get(profile, 55.0)
        allow_lower = profile == "degen"

        filtered = [leg for leg in candidates if float(leg.get("confidence_score", 0) or 0) >= min_confidence]
        if not allow_lower and len(filtered) < num_legs:
            filtered = [
                leg
                for leg in candidates
                if float(leg.get("confidence_score", 0) or 0) >= (min_confidence * 0.8)
            ]

        # If we still don't have enough, keep the full pool (best-effort).
        if len(filtered) < num_legs:
            return candidates
        return filtered

    @staticmethod
    def _correlation_ceilings(risk_profile: str) -> List[float]:
        """
        Progressive relaxation sequence for the correlation ceiling.

        Important: these values are for the *latent* correlation model (copula), not the
        legacy heuristic correlation score.
        """
        profile = (risk_profile or "balanced").lower().strip()
        base = {"conservative": 0.35, "balanced": 0.55, "degen": 0.75}.get(profile, 0.55)
        return [base, 0.85, 0.99]

    def _filter_positive_edge_legs(self, candidates: List[Dict], risk_profile: str) -> List[Dict]:
        min_edge = {"conservative": 0.02, "balanced": 0.01, "degen": 0.0}.get(risk_profile, 0.01)
        filtered: List[Dict] = []
        for leg in candidates:
            model_prob = float(leg.get("adjusted_prob", 0) or 0)
            implied_prob = float(leg.get("implied_prob", 0) or 0)
            edge = float(leg.get("edge", model_prob - implied_prob if implied_prob > 0 else 0) or 0)
            if edge >= min_edge:
                leg["model_edge"] = edge
                leg["edge_percentage"] = edge * 100
                filtered.append(leg)

        filtered.sort(key=lambda x: x.get("model_edge", 0), reverse=True)
        return filtered

    @staticmethod
    def _deduplicate(candidates: List[Dict]) -> List[Dict]:
        unique: Dict[Tuple[str, str, str], Dict] = {}
        for leg in candidates:
            key = (str(leg.get("game_id")), str(leg.get("market_type")), str(leg.get("outcome")))
            if key not in unique or float(leg.get("confidence_score", 0) or 0) > float(
                unique[key].get("confidence_score", 0) or 0
            ):
                unique[key] = leg
        return list(unique.values())

    def _expand_deduplication(self, candidates: List[Dict], num_legs: int) -> List[Dict]:
        expanded = self._deduplicate_by_game_outcome(candidates)
        if len(expanded) >= num_legs:
            return expanded

        relaxed = self._deduplicate_by_game_outcome(candidates)  # already relaxed
        if len(relaxed) >= num_legs:
            return relaxed

        # Last resort: remove exact duplicates only
        seen = set()
        final_candidates: List[Dict] = []
        for leg in candidates:
            key = (
                str(leg.get("game_id")),
                str(leg.get("market_type")),
                str(leg.get("outcome")),
                str(leg.get("odds")),
            )
            if key in seen:
                continue
            seen.add(key)
            final_candidates.append(leg)

        # If we still can't satisfy the requested leg count, return the best effort pool
        # instead of hard-failing the entire parlay build. The caller will naturally
        # return a shorter parlay (with `num_legs` reflecting what was actually built).
        #
        # This improves UX for high-leg requests on slates with limited markets.
        if len(final_candidates) < num_legs:
            return final_candidates
        return final_candidates

    @staticmethod
    def _deduplicate_by_game_outcome(candidates: List[Dict]) -> List[Dict]:
        unique: Dict[Tuple[str, str], Dict] = {}
        for leg in candidates:
            key = (str(leg.get("game_id")), str(leg.get("outcome")))
            if key not in unique or float(leg.get("confidence_score", 0) or 0) > float(
                unique[key].get("confidence_score", 0) or 0
            ):
                unique[key] = leg
        return list(unique.values())

    def _with_ev_scores(self, candidates: List[Dict]) -> List[Dict]:
        for leg in candidates:
            leg["ev_score"] = self._calculate_leg_ev(leg)
        return candidates

    def _optimize_for_profile(self, candidates: List[Dict], num_legs: int, risk_profile: str) -> List[Dict]:
        if risk_profile == "conservative":
            return self._optimize_for_ev(candidates, num_legs, min_confidence=70.0, allow_lower_confidence=False)
        if risk_profile == "degen":
            return self._optimize_for_ev(candidates, num_legs, min_confidence=40.0, allow_lower_confidence=True)
        return self._optimize_for_ev(candidates, num_legs, min_confidence=55.0, allow_lower_confidence=False)

    @staticmethod
    def _calculate_leg_ev(leg: Dict) -> float:
        prob = float(leg.get("adjusted_prob", 0) or 0)
        decimal_odds = float(leg.get("decimal_odds", 1.0) or 1.0)
        ev = (prob * decimal_odds) - 1.0
        confidence = float(leg.get("confidence_score", 0) or 0) / 100.0
        edge = float(leg.get("edge", 0) or 0)
        move = float(leg.get("market_move_score", 0.0) or 0.0)
        # Minor tie-breaker using historical line movement alignment.
        return ev * (0.7 + 0.3 * confidence) + edge * 0.5 + move * 0.08

    def _optimize_for_ev(
        self,
        candidates: List[Dict],
        num_legs: int,
        min_confidence: float,
        allow_lower_confidence: bool,
    ) -> List[Dict]:
        filtered = [leg for leg in candidates if float(leg.get("confidence_score", 0) or 0) >= min_confidence]
        if not allow_lower_confidence and len(filtered) < num_legs:
            filtered = [
                leg for leg in candidates if float(leg.get("confidence_score", 0) or 0) >= min_confidence * 0.8
            ]

        filtered.sort(key=lambda x: x.get("ev_score", -999), reverse=True)
        selected: List[Dict] = []
        selected_keys = set()

        for leg in filtered:
            if len(selected) >= num_legs:
                break
            key = (leg.get("game_id"), leg.get("market_type"), leg.get("outcome"))
            if key in selected_keys:
                continue
            selected.append(leg)
            selected_keys.add(key)

        return selected

    def _ensure_diversification(self, selected: List[Dict], num_legs: int) -> List[Dict]:
        if len(selected) <= 1:
            return selected

        diversified: List[Dict] = []
        game_counts: Dict[str, int] = {}

        for leg in sorted(selected, key=lambda x: x.get("ev_score", -999), reverse=True):
            game_id = str(leg.get("game_id"))
            if game_counts.get(game_id, 0) >= 2:
                continue
            diversified.append(leg)
            game_counts[game_id] = game_counts.get(game_id, 0) + 1
            if len(diversified) >= num_legs:
                break

        return diversified

    def _remove_correlated_legs(self, selected: List[Dict], max_correlation: float) -> List[Dict]:
        if len(selected) <= 1:
            return selected

        sorted_legs = sorted(selected, key=lambda x: x.get("ev_score", -999), reverse=True)
        filtered: List[Dict] = []
        for leg in sorted_legs:
            if self._is_correlated_with_selected(leg, filtered, threshold=max_correlation):
                continue
            if self._conflicts_with_selected(leg, filtered):
                continue
            filtered.append(leg)
        return filtered

    def _is_correlated_with_selected(self, leg: Dict, selected: List[Dict], threshold: float) -> bool:
        for selected_leg in selected:
            if self._calculate_leg_correlation(leg, selected_leg) >= threshold:
                return True
        return False

    @staticmethod
    def _calculate_leg_correlation(leg1: Dict, leg2: Dict) -> float:
        correlation = 0.0
        if str(leg1.get("game_id")) == str(leg2.get("game_id")):
            correlation += 0.5
            if str(leg1.get("market_type")) == str(leg2.get("market_type")):
                correlation += 0.3
            if str(leg1.get("outcome")) == str(leg2.get("outcome")):
                correlation += 0.2
        return min(1.0, correlation)

    def _remove_conflicting_legs(self, selected: List[Dict]) -> List[Dict]:
        if len(selected) <= 1:
            return selected
        sorted_legs = sorted(selected, key=lambda x: x.get("ev_score", -999), reverse=True)
        filtered: List[Dict] = []
        for leg in sorted_legs:
            if not self._conflicts_with_selected(leg, filtered):
                filtered.append(leg)
        return filtered

    def _conflicts_with_selected(self, leg: Dict, selected: List[Dict]) -> bool:
        for other in selected:
            if str(leg.get("game_id")) != str(other.get("game_id")):
                continue
            if self._conflicts_moneyline(leg, other):
                return True
            if self._conflicts_totals(leg, other):
                return True
            if self._conflicts_spreads(leg, other):
                return True
            if self._conflicts_player_props(leg, other):
                return True
        return False

    @staticmethod
    def _conflicts_moneyline(leg: Dict, other: Dict) -> bool:
        if leg.get("market_type") != "h2h" or other.get("market_type") != "h2h":
            return False
        o1 = str(leg.get("outcome", "")).lower()
        o2 = str(other.get("outcome", "")).lower()
        if o1 in ("home", "away") and o2 in ("home", "away") and o1 != o2:
            return True
        return False

    @staticmethod
    def _conflicts_totals(leg: Dict, other: Dict) -> bool:
        if leg.get("market_type") != "totals" or other.get("market_type") != "totals":
            return False
        o1 = str(leg.get("outcome", "")).lower()
        o2 = str(other.get("outcome", "")).lower()
        return ("over" in o1 and "under" in o2) or ("under" in o1 and "over" in o2)

    @staticmethod
    def _conflicts_spreads(leg: Dict, other: Dict) -> bool:
        if leg.get("market_type") != "spreads" or other.get("market_type") != "spreads":
            return False
        o1 = str(leg.get("outcome", "")).lower()
        o2 = str(other.get("outcome", "")).lower()
        if o1 in ("home", "away") and o2 in ("home", "away") and o1 != o2:
            return True
        return False

    @staticmethod
    def _conflicts_player_props(leg: Dict, other: Dict) -> bool:
        # Minimal placeholder: current system doesn't robustly encode player props.
        # Keep behavior conservative (don't mark conflict) unless both look like over/under.
        o1 = str(leg.get("outcome", "")).lower()
        o2 = str(other.get("outcome", "")).lower()
        if ("over" in o1 and "under" in o2) or ("under" in o1 and "over" in o2):
            # If both are totals market, totals conflict is already handled.
            if leg.get("market_type") != "totals" and other.get("market_type") != "totals":
                return True
        return False

    def _fill_selected(
        self,
        selected: List[Dict],
        candidates: List[Dict],
        num_legs: int,
        correlation_threshold: float,
    ) -> List[Dict]:
        remaining = [leg for leg in candidates if leg not in selected]
        remaining.sort(key=lambda x: x.get("ev_score", -999), reverse=True)

        for leg in remaining:
            if len(selected) >= num_legs:
                break
            if self._is_correlated_with_selected(leg, selected, threshold=correlation_threshold):
                continue
            if self._conflicts_with_selected(leg, selected):
                continue
            selected.append(leg)

        return selected


