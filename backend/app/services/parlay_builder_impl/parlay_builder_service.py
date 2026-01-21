from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.model_config import MODEL_VERSION
from app.services.parlay_builder_impl.leg_selection_service import ParlayLegSelectionService
from app.services.parlay_builder_impl.parlay_metrics_calculator import ParlayMetricsCalculator
from app.services.parlay_probability import (
    CorrelatedParlayProbabilityCalculator,
    ParlayCorrelationModel,
    ParlayProbabilityCalibrationService,
)
from app.services.odds_warmup_service import OddsWarmupService
from app.services.probability_engine import BaseProbabilityEngine, get_probability_engine

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TripleProfileConfig:
    risk_profile: str
    default_legs: int
    min_legs: int
    max_legs: int
    confidence_floor: int


class ParlayBuilderService:
    """
    Builds AI parlay suggestions from model-based candidate legs.

    Notes:
    - This service is called by API routes; keep it fast and deterministic.
    - Expensive text generation is handled elsewhere (OpenAIService).
    """

    def __init__(self, db: AsyncSession, sport: str = "NFL"):
        self.db = db
        self.sport = (sport or "NFL").upper()
        self._engine_by_sport: Dict[str, BaseProbabilityEngine] = {}
        self._leg_selector = ParlayLegSelectionService()
        self._metrics = ParlayMetricsCalculator()
        self._parlay_prob = CorrelatedParlayProbabilityCalculator(ParlayCorrelationModel())
        self._parlay_prob_calibration = ParlayProbabilityCalibrationService(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def build_parlay(
        self,
        num_legs: int,
        risk_profile: str = "balanced",
        sport: Optional[str] = None,
        week: Optional[int] = None,
        include_player_props: bool = False,
    ) -> Dict:
        """
        Build a parlay suggestion.

        Returns a dict that the API route later enriches with AI explanations.
        """
        requested_legs = self._clamp_legs(num_legs)
        normalized_profile = self._normalize_risk_profile(risk_profile)
        active_sport = (sport or self.sport or "NFL").upper()

        engine = self._get_engine(active_sport)
        candidates = await self._load_candidates(engine=engine, sport=active_sport, week=week, include_player_props=include_player_props)

        # Cold-start protection: if we have no candidate legs, try warming odds once
        # and reloading the candidates. This recovers from cases where the odds sync
        # job hasn't populated the DB yet.
        if not candidates:
            warmed = await OddsWarmupService(self.db).warm_sport(active_sport)
            if warmed:
                candidates = await self._load_candidates(engine=engine, sport=active_sport, week=week, include_player_props=include_player_props)
        
        if not candidates:
            week_msg = f" for Week {week}" if week else ""
            raise ValueError(
                f"Not enough candidate legs available for {active_sport}{week_msg}. Found 0 candidate legs. "
                "This usually means there are no upcoming games with odds loaded for that sport right now. "
                "Try refreshing games/odds, removing any week filter, or selecting a different sport."
            )

        selected = self._leg_selector.select_legs(
            candidates=candidates,
            num_legs=requested_legs,
            risk_profile=normalized_profile,
        )

        return await self._build_parlay_payload(
            engine=engine,
            selected_legs=selected,
            risk_profile=normalized_profile,
            sport=active_sport,
        )

    async def build_triple_parlay(
        self,
        sports: Optional[List[str]] = None,
        leg_overrides: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Dict]:
        """
        Build Safe/Balanced/Degen parlays.

        Optimization:
        - Candidate legs are fetched at most once per sport and reused across all profiles.
        """
        leg_overrides = leg_overrides or {}
        available_sports = [s for s in (sports or [self.sport]) if s]
        if not available_sports:
            raise ValueError("At least one sport must be provided to build triple parlays")

        profile_configs: Dict[str, TripleProfileConfig] = {
            "safe": TripleProfileConfig("conservative", default_legs=4, min_legs=3, max_legs=6, confidence_floor=70),
            "balanced": TripleProfileConfig("balanced", default_legs=8, min_legs=7, max_legs=12, confidence_floor=55),
            "degen": TripleProfileConfig("degen", default_legs=14, min_legs=13, max_legs=20, confidence_floor=40),
        }

        # Cache candidate pools per sport to avoid repeating the expensive work.
        candidates_by_sport: Dict[str, List[Dict[str, Any]]] = {}

        results: Dict[str, Dict] = {}
        for profile_name, cfg in profile_configs.items():
            requested_override = leg_overrides.get(profile_name)
            num_legs = cfg.default_legs
            if requested_override is not None:
                num_legs = max(cfg.min_legs, min(cfg.max_legs, int(requested_override)))

            parlay_data: Optional[Dict] = None
            used_sport: Optional[str] = None
            errors: List[str] = []

            for sport_code in available_sports:
                sport_upper = str(sport_code).upper()
                try:
                    engine = self._get_engine(sport_upper)
                    candidates = candidates_by_sport.get(sport_upper)
                    if candidates is None:
                        candidates = await engine.get_candidate_legs(
                            sport=sport_upper,
                            min_confidence=0.0,
                            max_legs=500,
                            week=None,
                        )
                        if not candidates:
                            warmed = await OddsWarmupService(self.db).warm_sport(sport_upper)
                            if warmed:
                                candidates = await engine.get_candidate_legs(
                                    sport=sport_upper,
                                    min_confidence=0.0,
                                    max_legs=500,
                                    week=None,
                                )
                        candidates_by_sport[sport_upper] = candidates

                    selected = self._leg_selector.select_legs(
                        candidates=candidates,
                        num_legs=num_legs,
                        risk_profile=cfg.risk_profile,
                    )
                    parlay_data = await self._build_parlay_payload(
                        engine=engine,
                        selected_legs=selected,
                        risk_profile=cfg.risk_profile,
                        sport=sport_upper,
                    )
                    used_sport = sport_upper
                    break
                except Exception as exc:
                    errors.append(f"{sport_upper}: {exc}")
                    continue

            if parlay_data is None:
                raise ValueError(
                    f"Failed to build {profile_name} parlay. "
                    f"No sports have enough games. Tried: {', '.join(errors)}"
                )

            results[profile_name] = {
                "parlay": parlay_data,
                "config": {
                    "num_legs": parlay_data.get("num_legs", num_legs),
                    "risk_profile": cfg.risk_profile,
                    "sport": used_sport,
                    "confidence_floor": cfg.confidence_floor,
                    "leg_range": (cfg.min_legs, cfg.max_legs),
                },
            }

        return results

    # Backwards-compat helpers used by legacy variant builders.
    def _get_min_confidence(self, risk_profile: str) -> float:
        normalized = self._normalize_risk_profile(risk_profile)
        return {"conservative": 70.0, "balanced": 55.0, "degen": 40.0}.get(normalized, 55.0)

    async def _select_legs_optimized(self, candidates: List[Dict], num_legs: int, risk_profile: str) -> List[Dict]:
        return self._leg_selector.select_legs(candidates, self._clamp_legs(num_legs), risk_profile)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_engine(self, sport: str) -> BaseProbabilityEngine:
        key = (sport or "NFL").upper()
        engine = self._engine_by_sport.get(key)
        if engine is None:
            engine = get_probability_engine(self.db, key)
            self._engine_by_sport[key] = engine
        return engine

    async def _load_candidates(
        self,
        *,
        engine: BaseProbabilityEngine,
        sport: str,
        week: Optional[int],
        include_player_props: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Fetch candidate legs once at a permissive threshold; selection logic applies
        risk-profile constraints later.

        For NFL with a specific week selected, apply a pragmatic fallback:
        - Try requested week
        - Then current week
        - Then all upcoming games (no week filter)
        """
        active_sport = (sport or "NFL").upper()
        candidates = await engine.get_candidate_legs(
            sport=active_sport,
            min_confidence=0.0,
            max_legs=500,
            week=week,
            include_player_props=include_player_props,
        )

        if candidates or week is None or active_sport != "NFL":
            return candidates

        # If no candidates found for a specific week, try fallback to current week or no week filter.
        from app.utils.nfl_week import get_current_nfl_week

        current_week = get_current_nfl_week()
        if current_week and current_week != week:
            logger.info("No games found for NFL Week %s, trying current week %s", week, current_week)
            candidates = await engine.get_candidate_legs(
                sport=active_sport,
                min_confidence=0.0,
                max_legs=500,
                week=current_week,
                include_player_props=include_player_props,
            )

        if not candidates:
            logger.info("No games found for NFL Week %s or current week, trying all upcoming games", week)
            candidates = await engine.get_candidate_legs(
                sport=active_sport,
                min_confidence=0.0,
                max_legs=500,
                week=None,
                include_player_props=include_player_props,
            )

        return candidates

    @staticmethod
    def _normalize_risk_profile(risk_profile: str) -> str:
        value = (risk_profile or "balanced").lower().strip()
        if value not in {"conservative", "balanced", "degen"}:
            return "balanced"
        return value

    @staticmethod
    def _clamp_legs(num_legs: int) -> int:
        try:
            value = int(num_legs)
        except Exception:
            value = 5
        return max(1, min(20, value))

    async def _build_parlay_payload(
        self,
        engine: BaseProbabilityEngine,
        selected_legs: List[Dict[str, Any]],
        risk_profile: str,
        sport: str,
    ) -> Dict:
        legs_data: List[Dict[str, Any]] = []
        prob_legs: List[Dict[str, Any]] = []
        for leg in selected_legs:
            built = self._build_leg_dict(leg, sport=sport)
            if not built.get("market_id") or not built.get("outcome"):
                continue
            legs_data.append(built)
            # Keep the richer leg for probability/correlation calculations.
            prob_legs.append(leg)

        actual_num_legs = len(legs_data)
        raw_parlay_prob = float(self._parlay_prob.calculate(prob_legs, risk_profile=risk_profile))
        parlay_prob = float(await self._parlay_prob_calibration.calibrate(raw_parlay_prob))

        confidence_scores = [float(leg.get("confidence", 0.0) or 0.0) for leg in legs_data]
        overall_confidence = float(sum(confidence_scores) / actual_num_legs) if actual_num_legs > 0 else 0.0
        model_confidence = min(1.0, overall_confidence / 100.0) if overall_confidence > 0 else 0.5

        upset_count = int(self._metrics.count_upsets(legs_data))
        parlay_ev = float(self._metrics.calculate_parlay_ev(legs_data, parlay_prob))

        return {
            "legs": legs_data,
            "num_legs": int(actual_num_legs),
            "parlay_hit_prob": float(parlay_prob),
            # Optional debug field (ignored by public response schema).
            "raw_parlay_hit_prob": float(raw_parlay_prob),
            "risk_profile": str(risk_profile),
            "confidence_scores": confidence_scores,
            "overall_confidence": float(overall_confidence),
            "parlay_ev": parlay_ev,
            "model_confidence": float(model_confidence),
            "upset_count": upset_count,
            "model_version": MODEL_VERSION,
        }

    @staticmethod
    def _build_leg_dict(leg: Dict[str, Any], sport: str) -> Dict[str, Any]:
        game_str = str(leg.get("game") or "").strip()
        if not game_str:
            away = str(leg.get("away_team") or "").strip()
            home = str(leg.get("home_team") or "").strip()
            game_str = f"{away} @ {home}".strip(" @") if (home or away) else "Unknown Game"

        return {
            "market_id": str(leg.get("market_id") or ""),
            "outcome": str(leg.get("outcome") or ""),
            "game": game_str,
            "home_team": str(leg.get("home_team") or ""),
            "away_team": str(leg.get("away_team") or ""),
            "market_type": str(leg.get("market_type") or ""),
            "odds": str(leg.get("odds") or ""),
            "probability": float(leg.get("adjusted_prob", 0.0) or 0.0),
            "confidence": float(leg.get("confidence_score", 0.0) or 0.0),
            "sport": sport,
        }


