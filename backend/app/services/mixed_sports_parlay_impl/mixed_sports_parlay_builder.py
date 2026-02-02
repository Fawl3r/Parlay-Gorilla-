"""Mixed sports parlay builder service.

This builder mixes legs across sports to reduce correlation between picks.
It uses model-derived candidate legs (probability/edge/confidence) provided by
the per-sport `BaseProbabilityEngine` implementations.
"""

from __future__ import annotations

import logging
from itertools import cycle
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_logger import log_event
from app.core.model_config import MODEL_VERSION
from app.services.mixed_sports_parlay_impl.conflict_resolver import MixedParlayConflictResolver
from app.services.parlay_builder_impl.parlay_metrics_calculator import ParlayMetricsCalculator
from app.services.probability_engine import BaseProbabilityEngine, get_probability_engine

logger = logging.getLogger(__name__)


class MixedSportsParlayBuilder:
    """
    Service for building parlays that mix legs from multiple sports.

    Key behaviors:
    - Filters for positive edge legs (model_prob > implied_prob) when possible
    - Balances legs across sports for diversification (optional)
    - Avoids mutually exclusive selections within a single game (best-effort)
    - Never returns a "0-leg parlay" (raises ValueError instead)
    """

    SUPPORTED_SPORTS = ["NFL", "NBA", "NHL", "MLB"]

    def __init__(self, db: AsyncSession):
        self.db = db
        self._engines: Dict[str, BaseProbabilityEngine] = {}
        self._metrics = ParlayMetricsCalculator()
        self._conflicts = MixedParlayConflictResolver()

    def _get_engine(self, sport: str) -> BaseProbabilityEngine:
        sport_upper = (sport or "NFL").upper()
        engine = self._engines.get(sport_upper)
        if engine is None:
            engine = get_probability_engine(self.db, sport_upper)
            self._engines[sport_upper] = engine
        return engine

    async def get_multi_sport_candidates(
        self,
        sports: List[str],
        min_confidence: float = 50.0,
        max_legs_per_sport: int = 50,
        week: Optional[int] = None,
        include_player_props: bool = False,
    ) -> List[Dict]:
        all_candidates: List[Dict] = []
        for sport in sports:
            sport_upper = str(sport).upper()
            if sport_upper not in self.SUPPORTED_SPORTS:
                continue

            try:
                engine = self._get_engine(sport_upper)
                week_filter = week if sport_upper == "NFL" else None
                candidates = await engine.get_candidate_legs(
                    sport=sport_upper,
                    min_confidence=float(min_confidence),
                    max_legs=int(max_legs_per_sport),
                    week=week_filter,
                    include_player_props=include_player_props,
                )
            except Exception as exc:
                logger.warning("Failed fetching candidates for %s: %s", sport_upper, exc)
                continue

            for candidate in candidates:
                candidate["sport"] = sport_upper
            all_candidates.extend(candidates)

        all_candidates.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
        return all_candidates

    async def build_mixed_parlay(
        self,
        num_legs: int,
        sports: List[str],
        risk_profile: str = "balanced",
        balance_sports: bool = True,
        week: Optional[int] = None,
        include_player_props: bool = False,
    ) -> Dict:
        requested_legs = self._clamp_legs(num_legs)
        normalized_profile = self._normalize_risk_profile(risk_profile)
        valid_sports = self._resolve_valid_sports(sports)

        log_event(
            logger,
            "parlay.generate.start",
            sport="mixed",
            sports=valid_sports,
            num_legs=requested_legs,
            risk_profile=normalized_profile,
            week=week,
        )

        min_confidence = self._get_min_confidence(normalized_profile)
        candidates = await self._load_candidates_with_fallback(
            sports=valid_sports,
            min_confidence=min_confidence,
            requested_legs=requested_legs,
            week=week,
            include_player_props=include_player_props,
        )

        if not candidates:
            sports_label = ", ".join(valid_sports) if valid_sports else "NFL"
            week_msg = f" (Week {week})" if week and "NFL" in valid_sports else ""
            log_event(
                logger,
                "parlay.generate.fail.not_enough_games",
                sport="mixed",
                sports=valid_sports,
                week=week,
                next_action_hint="different_sport_or_later",
                level=logging.WARNING,
            )
            try:
                from app.services.alerting import get_alerting_service
                await get_alerting_service().emit(
                    "parlay.generate.fail.not_enough_games",
                    "warning",
                    {"sport": "mixed", "sports": valid_sports, "week": week},
                    next_action_hint="different_sport_or_later",
                    sport="mixed",
                )
            except Exception as alert_err:
                logger.debug("Alerting emit skipped: %s", alert_err)
            raise ValueError(
                f"Not enough candidate legs available for {sports_label}{week_msg}. Found 0 candidate legs. "
                "This usually means there are no upcoming games with odds loaded for those sports right now. "
                "Try selecting a different sport, disabling mixing, or trying again later."
            )

        # Debug: candidates per sport (for prod diagnosis)
        counts_by_sport: Dict[str, int] = {}
        for c in candidates:
            s = str(c.get("sport", "NFL"))
            counts_by_sport[s] = counts_by_sport.get(s, 0) + 1
        log_event(
            logger,
            "parlay.mixed.candidates_by_sport",
            sport="mixed",
            candidates_by_sport=counts_by_sport,
            total=len(candidates),
            requested_legs=requested_legs,
            week=week,
            level=logging.DEBUG,
        )

        # NFL week starvation fallback: if user set an NFL week and we don't have enough legs,
        # retry with current NFL week then with no week filter (all upcoming).
        if len(candidates) < requested_legs and week is not None and "NFL" in valid_sports:
            from app.utils.nfl_week import get_current_nfl_week
            current_nfl_week = get_current_nfl_week()
            retry_weeks: List[Optional[int]] = []
            if current_nfl_week is not None and current_nfl_week != week:
                retry_weeks.append(current_nfl_week)
            retry_weeks.append(None)
            for wk in retry_weeks:
                candidates_retry = await self._load_candidates_with_fallback(
                    sports=valid_sports,
                    min_confidence=min_confidence,
                    requested_legs=requested_legs,
                    week=wk,
                    include_player_props=include_player_props,
                )
                if len(candidates_retry) >= requested_legs:
                    candidates = self._prefer_positive_edge_candidates(
                        candidates_retry, requested_legs, normalized_profile
                    )
                    selected = (
                        self._select_balanced_legs(candidates, requested_legs, valid_sports)
                        if balance_sports and len(valid_sports) > 1
                        else self._select_best_legs(candidates, requested_legs)
                    )
                    selected = self._conflicts.remove_conflicting_legs(selected)
                    selected = self._fill_remaining_slots(selected, candidates, requested_legs)
                    legs_data = self._build_legs_data(selected)
                    if legs_data:
                        result = self._build_response_payload(legs_data, normalized_profile)
                        result.setdefault("meta", {})["nfl_week_fallback_used"] = True
                        result["meta"]["nfl_week_used"] = wk
                        return result

        if len(candidates) < requested_legs:
            raise ValueError(
                f"Could not fulfill requested number of legs with available games. "
                f"requested={requested_legs} available={len(candidates)}"
            )

        candidates = self._prefer_positive_edge_candidates(candidates, requested_legs, normalized_profile)

        selected = (
            self._select_balanced_legs(candidates, requested_legs, valid_sports)
            if balance_sports and len(valid_sports) > 1
            else self._select_best_legs(candidates, requested_legs)
        )

        selected = self._conflicts.remove_conflicting_legs(selected)
        selected = self._fill_remaining_slots(selected, candidates, requested_legs)

        legs_data = self._build_legs_data(selected)
        if not legs_data:
            raise ValueError(
                "Unable to build a mixed-sports parlay from the available data. "
                "Try a different sport selection or try again later."
            )

        return self._build_response_payload(legs_data, normalized_profile)

    # ------------------------------------------------------------------
    # Selection + formatting helpers (kept as methods for testability)
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_risk_profile(risk_profile: str) -> str:
        value = (risk_profile or "balanced").lower().strip()
        return value if value in {"conservative", "balanced", "degen"} else "balanced"

    @staticmethod
    def _clamp_legs(num_legs: int) -> int:
        try:
            value = int(num_legs)
        except Exception:
            value = 5
        return max(1, min(20, value))

    def _resolve_valid_sports(self, sports: List[str]) -> List[str]:
        valid = [str(s).upper() for s in (sports or []) if str(s).upper() in self.SUPPORTED_SPORTS]
        return valid or ["NFL"]

    def _get_min_confidence(self, risk_profile: str) -> float:
        thresholds = {"conservative": 70.0, "balanced": 55.0, "degen": 40.0}
        return float(thresholds.get(risk_profile, 55.0))

    async def _load_candidates_with_fallback(
        self,
        *,
        sports: List[str],
        min_confidence: float,
        requested_legs: int,
        week: Optional[int],
        include_player_props: bool = False,
    ) -> List[Dict]:
        # Start with a confidence floor tuned to the risk profile.
        candidates = await self.get_multi_sport_candidates(
            sports=sports,
            min_confidence=min_confidence,
            max_legs_per_sport=100,
            week=week,
            include_player_props=include_player_props,
        )
        if len(candidates) >= requested_legs:
            return candidates

        # Gradually relax thresholds when data is sparse.
        thresholds = [min_confidence * 0.8, min_confidence * 0.6, 30.0, 20.0, 0.0]
        for threshold in thresholds:
            candidates = await self.get_multi_sport_candidates(
                sports=sports,
                min_confidence=float(threshold),
                max_legs_per_sport=150,
                week=week,
                include_player_props=include_player_props,
            )
            if len(candidates) >= requested_legs:
                return candidates
        return candidates

    def _prefer_positive_edge_candidates(self, candidates: List[Dict], requested_legs: int, risk_profile: str) -> List[Dict]:
        positive = self._filter_positive_edge_legs(candidates, risk_profile)
        return positive if len(positive) >= requested_legs else candidates

    def _filter_positive_edge_legs(self, candidates: List[Dict], risk_profile: str) -> List[Dict]:
        min_edge_thresholds = {"conservative": 0.02, "balanced": 0.01, "degen": 0.0}
        min_edge = float(min_edge_thresholds.get(risk_profile, 0.01))

        positive: List[Dict] = []
        for leg in candidates:
            model_prob = float(leg.get("adjusted_prob", 0) or 0)
            implied_prob = float(leg.get("implied_prob", 0) or 0)
            edge = float(leg.get("edge", model_prob - implied_prob if implied_prob > 0 else 0) or 0)
            if edge >= min_edge:
                leg["model_edge"] = edge
                positive.append(leg)

        positive.sort(key=lambda x: x.get("model_edge", 0), reverse=True)
        return positive

    def _select_balanced_legs(self, candidates: List[Dict], num_legs: int, sports: List[str]) -> List[Dict]:
        by_sport = {sport: [] for sport in sports}
        for candidate in candidates:
            sport = candidate.get("sport", "NFL")
            if sport in by_sport:
                by_sport[sport].append(candidate)

        legs_per_sport = {sport: 0 for sport in sports}
        sports_cycle = cycle(sports)
        for _ in range(num_legs):
            sport = next(sports_cycle)
            while not by_sport[sport] and any(by_sport.values()):
                sport = next(sports_cycle)
            if by_sport[sport]:
                legs_per_sport[sport] += 1

        selected: List[Dict] = []
        selected_keys = set()
        for sport, count in legs_per_sport.items():
            sport_candidates = sorted(by_sport[sport], key=lambda x: x.get("confidence_score", 0), reverse=True)
            for candidate in sport_candidates:
                if len(selected) >= num_legs:
                    break
                if count <= 0:
                    break
                key = (candidate.get("game_id"), candidate.get("market_type"), candidate.get("outcome"))
                if key in selected_keys:
                    continue
                if self._conflicts.conflicts_with_selected(candidate, selected):
                    continue
                selected.append(candidate)
                selected_keys.add(key)
                count -= 1

        return selected[:num_legs]

    def _select_best_legs(self, candidates: List[Dict], num_legs: int) -> List[Dict]:
        unique: Dict[tuple, Dict] = {}
        for leg in candidates:
            key = (leg.get("game_id"), leg.get("market_type"), leg.get("outcome"))
            existing = unique.get(key)
            if existing is None or leg.get("confidence_score", 0) > existing.get("confidence_score", 0):
                unique[key] = leg

        sorted_legs = sorted(unique.values(), key=lambda x: x.get("confidence_score", 0), reverse=True)
        selected: List[Dict] = []
        for leg in sorted_legs:
            if len(selected) >= num_legs:
                break
            if self._conflicts.conflicts_with_selected(leg, selected):
                continue
            selected.append(leg)
        return selected[:num_legs]

    def _fill_remaining_slots(self, selected: List[Dict], candidates: List[Dict], num_legs: int) -> List[Dict]:
        if len(selected) >= num_legs:
            return selected[:num_legs]

        selected_keys = {(c.get("game_id"), c.get("market_type"), c.get("outcome")) for c in selected}
        for candidate in sorted(candidates, key=lambda x: x.get("confidence_score", 0), reverse=True):
            if len(selected) >= num_legs:
                break
            key = (candidate.get("game_id"), candidate.get("market_type"), candidate.get("outcome"))
            if key in selected_keys:
                continue
            if self._conflicts.conflicts_with_selected(candidate, selected):
                continue
            selected.append(candidate)
            selected_keys.add(key)

        return selected[:num_legs]

    def _build_legs_data(self, selected_legs: List[Dict]) -> List[Dict]:
        legs_data: List[Dict] = []
        for leg in selected_legs:
            game_str = str(leg.get("game", "") or "").strip()
            if not game_str:
                home_team = str(leg.get("home_team", "") or "")
                away_team = str(leg.get("away_team", "") or "")
                game_str = f"{away_team} @ {home_team}".strip(" @") if (home_team or away_team) else f"Game {str(leg.get('game_id', ''))[:8]}"

            leg_data = {
                "market_id": str(leg.get("market_id", "")),
                "outcome": str(leg.get("outcome", "")),
                "game": game_str,
                "home_team": str(leg.get("home_team", "")),
                "away_team": str(leg.get("away_team", "")),
                "market_type": str(leg.get("market_type", "")),
                "odds": str(leg.get("odds", "")),
                "probability": float(leg.get("adjusted_prob", 0.0) or 0.0),
                "confidence": float(leg.get("confidence_score", 0.0) or 0.0),
                "sport": str(leg.get("sport", "NFL")),
            }

            if not leg_data["market_id"] or not leg_data["outcome"]:
                continue
            legs_data.append(leg_data)

        return legs_data

    @staticmethod
    def _calculate_parlay_probability(leg_probabilities: List[float]) -> float:
        if not leg_probabilities:
            return 0.0
        prob = 1.0
        for p in leg_probabilities:
            prob *= float(p)
        return float(prob)

    def _build_response_payload(self, legs_data: List[Dict], risk_profile: str) -> Dict:
        leg_probs = [float(leg.get("probability", 0.5) or 0.5) for leg in legs_data]
        parlay_prob = self._calculate_parlay_probability(leg_probs)

        confidence_scores = [float(leg.get("confidence", 50.0) or 50.0) for leg in legs_data]
        actual_num_legs = len(legs_data)
        overall_confidence = (sum(confidence_scores) / actual_num_legs) if actual_num_legs > 0 else 0.0
        model_confidence = min(1.0, overall_confidence / 100.0) if overall_confidence > 0 else 0.5

        upset_count = int(self._metrics.count_upsets(legs_data))
        parlay_ev = float(self._metrics.calculate_parlay_ev(legs_data, parlay_prob))

        sports_used = sorted({str(leg.get("sport", "NFL")) for leg in legs_data})

        return {
            "legs": legs_data,
            "num_legs": int(actual_num_legs),
            "parlay_hit_prob": float(parlay_prob),
            "risk_profile": str(risk_profile),
            "confidence_scores": confidence_scores,
            "overall_confidence": float(overall_confidence),
            "sports_mixed": sports_used,
            "is_mixed_sports": len(sports_used) > 1,
            "parlay_ev": float(parlay_ev),
            "model_confidence": float(model_confidence),
            "upset_count": int(upset_count),
            "model_version": MODEL_VERSION,
        }


async def build_mixed_sports_parlay(
    db: AsyncSession,
    num_legs: int,
    sports: List[str],
    risk_profile: str = "balanced",
    balance_sports: bool = True,
    week: Optional[int] = None,
) -> Dict:
    builder = MixedSportsParlayBuilder(db)
    return await builder.build_mixed_parlay(
        num_legs=num_legs,
        sports=sports,
        risk_profile=risk_profile,
        balance_sports=balance_sports,
        week=week,
    )





