from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.model_config import MODEL_VERSION
from app.core.parlay_errors import InsufficientCandidatesException
from app.services.parlay_builder_impl.leg_selection_service import ParlayLegSelectionService
from app.services.parlay_builder_impl.parlay_metrics_calculator import ParlayMetricsCalculator
from app.services.parlay_builder_impl.triple_config import TRIPLE_MIN_CONFIDENCE
from app.services.parlay_probability import (
    CorrelatedParlayProbabilityCalculator,
    ParlayCorrelationModel,
    ParlayProbabilityCalibrationService,
)
from app.core.event_logger import log_event
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
        trace_id: Optional[str] = None,
        request_mode: Optional[str] = None,
    ) -> Dict:
        """
        Build a parlay suggestion.

        When request_mode=TRIPLE: STRICT policy (no fallback), strong-edge filter only;
        returns 3 legs or downgrades to 2 with downgrade meta; never uses fallback ladder.

        Returns a dict that the API route later enriches with AI explanations.
        """
        requested_legs = self._clamp_legs(num_legs)
        normalized_profile = self._normalize_risk_profile(risk_profile)
        active_sport = (sport or self.sport or "NFL").upper()
        is_triple_strict = (request_mode or "").upper() == "TRIPLE"

        # Season-awareness: block AI parlay generation for out-of-season sports; avoid empty-game errors
        from app.services.sport_availability_resolver import SportAvailabilityResolver
        availability = await SportAvailabilityResolver(self.db).resolve(active_sport)
        if not availability.available:
            logger.info(
                "Parlay build skipped: sport %s is %s; user message: %s",
                active_sport,
                availability.state,
                availability.message[:80] if availability.message else "",
            )
            raise InsufficientCandidatesException(
                needed=requested_legs,
                have=0,
                message=availability.message or f"{active_sport} is not available for parlay generation.",
            )

        log_event(
            logger,
            "parlay.generate.start",
            trace_id=trace_id,
            sport=active_sport,
            num_legs=requested_legs,
            week=week,
            risk_profile=normalized_profile,
            request_mode=request_mode,
        )

        # Cheap preflight: if no odds exist for this slate, return 503 to avoid heavy work/OOM.
        from app.models.game import Game
        from app.models.market import Market
        from app.models.odds import Odds

        now_utc = datetime.now(timezone.utc)
        window_start = now_utc - timedelta(hours=12)
        window_end = now_utc + timedelta(days=14)
        odds_check = await self.db.execute(
            select(Odds.id)
            .select_from(Odds)
            .join(Market, Odds.market_id == Market.id)
            .join(Game, Market.game_id == Game.id)
            .where(Game.sport == active_sport)
            .where(Game.start_time >= window_start)
            .where(Game.start_time <= window_end)
            .limit(1)
        )
        if odds_check.scalar_one_or_none() is None:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=503,
                detail="Odds are not loaded yet for today's slate. Try again in a minute.",
            )

        engine = self._get_engine(active_sport)
        candidates = await self._load_candidates(
            engine=engine,
            sport=active_sport,
            week=week,
            include_player_props=include_player_props,
            trace_id=trace_id,
        )

        # Cold-start protection: if we have no candidate legs, try warming odds once
        if not candidates:
            logger.info(f"No candidates found for {active_sport}, attempting odds warmup...")
            warmed = await OddsWarmupService(self.db).warm_sport(active_sport)
            if warmed:
                logger.info(f"Odds warmup succeeded for {active_sport}, reloading candidates...")
                candidates = await self._load_candidates(engine=engine, sport=active_sport, week=week, include_player_props=include_player_props)
            else:
                logger.warning(f"Odds warmup failed or returned no games for {active_sport}")

        # STRICT (Triple): no time-window expansion; skip week fallback
        if not is_triple_strict:
            # If still no candidates, try wider date range fallback
            if not candidates and week is not None and active_sport == "NFL":
                logger.info(f"No candidates found for NFL Week {week}, trying all upcoming games...")
                candidates = await self._load_candidates(
                    engine=engine,
                    sport=active_sport,
                    week=None,
                    include_player_props=include_player_props,
                    trace_id=trace_id,
                )
        
        # Final check: if still no candidates, check database state and provide helpful error
        if not candidates:
            week_msg = f" for Week {week}" if week else ""
            
            # Check if there are ANY games for this sport (regardless of date/status)
            from app.models.game import Game

            # Check total games
            total_result = await self.db.execute(
                select(func.count(Game.id)).where(Game.sport == active_sport)
            )
            total_games = total_result.scalar() or 0
            
            # Check scheduled games
            scheduled_statuses = ("scheduled", "status_scheduled")
            scheduled_result = await self.db.execute(
                select(func.count(Game.id))
                .where(Game.sport == active_sport)
                .where(or_(Game.status.is_(None), func.lower(Game.status).in_(scheduled_statuses)))
            )
            scheduled_games = scheduled_result.scalar() or 0
            
            # Check upcoming games (next 14 days)
            now = datetime.now(timezone.utc)
            future_cutoff = now + timedelta(days=14)
            upcoming_result = await self.db.execute(
                select(func.count(Game.id))
                .where(Game.sport == active_sport)
                .where(Game.start_time >= now)
                .where(Game.start_time <= future_cutoff)
                .where(or_(Game.status.is_(None), func.lower(Game.status).in_(scheduled_statuses)))
            )
            upcoming_games = upcoming_result.scalar() or 0
            
            # Build error message and next_action_hint based on database state
            if total_games == 0:
                error_msg = (
                    f"No games found in database for {active_sport}{week_msg}. "
                    "Games may not have been loaded yet. Please try again in a few moments."
                )
                next_action_hint = "load_games"
            elif scheduled_games == 0:
                error_msg = (
                    f"Found {total_games} games for {active_sport}{week_msg}, but none are scheduled. "
                    "All games may have finished. Try selecting a different sport or week."
                )
                next_action_hint = "different_sport_or_week"
            elif upcoming_games == 0:
                error_msg = (
                    f"Found {scheduled_games} scheduled games for {active_sport}{week_msg}, "
                    f"but none are in the next 14 days. "
                    "Try selecting a different sport or wait for upcoming games to be scheduled."
                )
                next_action_hint = "wait_or_different_sport"
            else:
                error_msg = (
                    f"Not enough candidate legs available for {active_sport}{week_msg}. "
                    f"Found {upcoming_games} upcoming games but no valid odds/markets loaded. "
                    "This usually means odds haven't been synced yet. Try again in a few moments."
                )
                next_action_hint = "sync_odds_or_retry"

            log_event(
                logger,
                "parlay.generate.fail.not_enough_games",
                trace_id=trace_id,
                sport=active_sport,
                week=week,
                total_games=total_games,
                scheduled_games=scheduled_games,
                upcoming_games=upcoming_games,
                next_action_hint=next_action_hint,
                level=logging.WARNING,
            )
            logger.warning(
                f"Candidate leg generation failed for {active_sport}{week_msg}: "
                f"total_games={total_games}, scheduled={scheduled_games}, upcoming={upcoming_games}"
            )
            try:
                from app.services.alerting import get_alerting_service
                await get_alerting_service().emit(
                    "parlay.generate.fail.not_enough_games",
                    "warning",
                    {
                        "trace_id": trace_id,
                        "sport": active_sport,
                        "week": week,
                        "total_games": total_games,
                        "scheduled_games": scheduled_games,
                        "upcoming_games": upcoming_games,
                    },
                    next_action_hint=next_action_hint,
                    sport=active_sport,
                )
            except Exception as alert_err:
                logger.debug("Alerting emit skipped: %s", alert_err)
            
            raise InsufficientCandidatesException(needed=requested_legs, have=0, message=error_msg)

        # Triple (confidence-gated): strong-edge filter, 1 per game, no fallback
        if is_triple_strict and requested_legs == 3:
            strong_one_per_game = self._strong_edges_one_per_game(candidates)
            have_strong = len(strong_one_per_game)
            have_eligible = len(candidates)
            debug_id = str(uuid.uuid4())[:8]

            if have_strong >= 3:
                selected = self._leg_selector.select_legs(
                    candidates=strong_one_per_game,
                    num_legs=3,
                    risk_profile=normalized_profile,
                )
                payload = await self._build_parlay_payload(
                    engine=engine,
                    selected_legs=selected[:3],
                    risk_profile=normalized_profile,
                    sport=active_sport,
                )
                payload["mode_returned"] = "TRIPLE"
                payload["downgraded"] = False
                payload["explain"] = {
                    "correlation_guard": "We avoid stacking multiple picks from the same game or team in Confidence Mode.",
                }
                return payload

            if have_strong == 2 and have_eligible >= 2:
                selected = self._leg_selector.select_legs(
                    candidates=strong_one_per_game,
                    num_legs=2,
                    risk_profile=normalized_profile,
                )
                payload = await self._build_parlay_payload(
                    engine=engine,
                    selected_legs=selected[:2],
                    risk_profile=normalized_profile,
                    sport=active_sport,
                )
                payload["mode_returned"] = "DOUBLE"
                payload["downgraded"] = True
                payload["downgrade_from"] = "TRIPLE"
                payload["downgrade_reason_code"] = "INSUFFICIENT_STRONG_EDGES"
                payload["downgrade_summary"] = {"needed": 3, "have_strong": have_strong, "have_eligible": have_eligible}
                payload["ui_suggestion"] = {
                    "primary_action": "Reduce to 2 picks (recommended)",
                    "secondary_action": "Expand time window to 72h or enable Moneyline-only",
                }
                payload["explain"] = {
                    "short_reason": f"Triple requires 3 high-confidence edges. Today we have {have_strong}.",
                    "correlation_guard": "We avoid stacking multiple picks from the same game or team in Confidence Mode.",
                }
                payload["_debug_id"] = debug_id
                return payload

            # < 2 strong edges or < 2 eligible: hard fail (route returns 409)
            raise InsufficientCandidatesException(
                needed=3,
                have=min(have_strong, have_eligible),
                message="Not enough eligible games with clean odds right now. Try a smaller parlay or check back soon.",
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
        trace_id: Optional[str] = None,
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
            trace_id=trace_id,
        )

        if candidates or week is None or active_sport != "NFL":
            return candidates

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
                trace_id=trace_id,
            )

        if not candidates:
            logger.info("No games found for NFL Week %s or current week, trying all upcoming games", week)
            candidates = await engine.get_candidate_legs(
                sport=active_sport,
                min_confidence=0.0,
                max_legs=500,
                week=None,
                include_player_props=include_player_props,
                trace_id=trace_id,
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

    @staticmethod
    def _strong_edges_one_per_game(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter to legs with confidence >= TRIPLE_MIN_CONFIDENCE and take at most one per game
        (best confidence per game). Returns list suitable for Triple selection (1 leg per game).
        confidence_score must be 0-100 (see triple_config); assert prevents silent break if scale changes.
        """
        best_per_game: Dict[str, Dict[str, Any]] = {}
        for c in (candidates or []):
            conf = float(c.get("confidence_score") or 0)
            assert 0 <= conf <= 100, "confidence_score must be 0-100 for Triple; got %s" % conf
            if conf < TRIPLE_MIN_CONFIDENCE:
                continue
            gid = c.get("game_id")
            if not gid:
                continue
            gid_str = str(gid)
            if gid_str not in best_per_game or float(best_per_game[gid_str].get("confidence_score") or 0) < conf:
                best_per_game[gid_str] = c
        return sorted(best_per_game.values(), key=lambda x: float(x.get("confidence_score") or 0), reverse=True)

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


