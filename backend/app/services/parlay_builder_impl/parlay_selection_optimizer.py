from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from app.services.parlay_probability import ParlayCorrelationModel

ConflictChecker = Callable[[Dict[str, Any], List[Dict[str, Any]]], bool]


@dataclass
class _State:
    selected: List[Dict[str, Any]]
    score: float
    game_counts: Dict[str, int]
    keys: Set[Tuple[str, str, str]]


class ParlaySelectionOptimizer:
    """
    Constraint-aware leg selection optimizer.

    Uses a lightweight beam search to maximize an additive objective (sum of `ev_score`)
    subject to hard constraints (duplicates/conflicts/correlation/max legs per game).
    """

    _DEFAULT_BEAM_WIDTH: Dict[str, int] = {
        "conservative": 40,
        "balanced": 60,
        "degen": 80,
    }

    _DEFAULT_MAX_PAIR_CORR: Dict[str, float] = {
        # Latent (copula) correlation ceiling, not the old heuristic score.
        "conservative": 0.35,
        "balanced": 0.55,
        "degen": 0.75,
    }

    def __init__(self, *, correlation_model: ParlayCorrelationModel):
        self._corr = correlation_model

    def select(
        self,
        *,
        candidates: List[Dict[str, Any]],
        num_legs: int,
        risk_profile: str,
        conflict_checker: ConflictChecker,
        max_legs_per_game: int = 2,
        max_pair_corr: Optional[float] = None,
        beam_width: Optional[int] = None,
        candidate_pool_limit: int = 250,
        max_expansions_per_state: int = 60,
    ) -> List[Dict[str, Any]]:
        requested = max(1, int(num_legs))
        profile = (risk_profile or "balanced").lower().strip()

        max_per_game = max(1, int(max_legs_per_game))
        corr_ceiling = (
            float(max_pair_corr)
            if max_pair_corr is not None
            else float(self._DEFAULT_MAX_PAIR_CORR.get(profile, self._DEFAULT_MAX_PAIR_CORR["balanced"]))
        )
        width = (
            int(beam_width)
            if beam_width is not None
            else int(self._DEFAULT_BEAM_WIDTH.get(profile, self._DEFAULT_BEAM_WIDTH["balanced"]))
        )
        width = max(5, min(200, width))

        pool = sorted(candidates or [], key=self._candidate_sort_key, reverse=True)
        if candidate_pool_limit > 0:
            pool = pool[: max(1, int(candidate_pool_limit))]

        if not pool:
            return []

        start = _State(selected=[], score=0.0, game_counts={}, keys=set())
        beam: List[_State] = [start]
        best: _State = start

        for _step in range(requested):
            next_states: List[_State] = []
            for state in beam:
                expansions = 0
                for leg in pool:
                    if expansions >= max_expansions_per_state:
                        break
                    key = self._leg_key(leg)
                    if key in state.keys:
                        continue

                    game_id = str(leg.get("game_id") or "").strip()
                    if game_id and state.game_counts.get(game_id, 0) >= max_per_game:
                        continue

                    if conflict_checker(leg, state.selected):
                        continue

                    if self._is_too_correlated(leg, state.selected, ceiling=corr_ceiling):
                        continue

                    new_selected = state.selected + [leg]
                    new_score = state.score + float(leg.get("ev_score", 0.0) or 0.0)

                    new_game_counts = dict(state.game_counts)
                    if game_id:
                        new_game_counts[game_id] = new_game_counts.get(game_id, 0) + 1

                    new_keys = set(state.keys)
                    new_keys.add(key)

                    next_states.append(
                        _State(
                            selected=new_selected,
                            score=new_score,
                            game_counts=new_game_counts,
                            keys=new_keys,
                        )
                    )
                    expansions += 1

            if not next_states:
                break

            next_states.sort(key=lambda s: s.score, reverse=True)
            beam = next_states[:width]

            # Track best-so-far by length then score.
            top = beam[0]
            if len(top.selected) > len(best.selected) or (
                len(top.selected) == len(best.selected) and top.score > best.score
            ):
                best = top

        return list(best.selected)[:requested]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _candidate_sort_key(leg: Dict[str, Any]) -> tuple:
        return (
            float(leg.get("ev_score", -9999.0) or -9999.0),
            float(leg.get("confidence_score", 0.0) or 0.0),
            str(leg.get("game_id") or ""),
            str(leg.get("market_type") or ""),
            str(leg.get("outcome") or ""),
            str(leg.get("market_id") or ""),
        )

    @staticmethod
    def _leg_key(leg: Dict[str, Any]) -> Tuple[str, str, str]:
        return (
            str(leg.get("game_id") or ""),
            str(leg.get("market_type") or ""),
            str(leg.get("outcome") or ""),
        )

    def _is_too_correlated(self, leg: Dict[str, Any], selected: List[Dict[str, Any]], *, ceiling: float) -> bool:
        if not selected:
            return False

        # Only same-game legs will have non-zero correlation, but keep the loop simple.
        for other in selected:
            corr = float(self._corr.estimate_latent_correlation(leg, other))
            if abs(corr) >= float(ceiling):
                return True
        return False


