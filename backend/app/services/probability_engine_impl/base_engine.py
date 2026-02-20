from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import Market
from app.models.odds import Odds
from app.services.probability_engine_impl.candidate_leg_service import CandidateLegService
from app.services.probability_engine_impl.external_data_repository import ExternalDataRepository
from app.services.probability_engine_impl.heuristics_service import ProbabilityHeuristicsService
from app.services.probability_engine_impl.team_strength_service import TeamStrengthService
from app.services.institutional.strategy_decomposition_service import StrategyDecompositionService


class BaseProbabilityEngine:
    """Engine for calculating win probabilities and edges."""

    sport_code = "GENERIC"

    def __init__(
        self,
        db: AsyncSession,
        stats_fetcher: Any = None,
        weather_fetcher: Any = None,
        injury_fetcher: Any = None,
    ):
        self.db = db
        self.stats_fetcher = stats_fetcher
        self.weather_fetcher = weather_fetcher
        self.injury_fetcher = injury_fetcher

        # Caches (request-scoped; avoid repeating network work inside one request)
        self._team_stats_cache: Dict[str, Optional[Dict]] = {}
        self._team_form_cache: Dict[str, List[Dict]] = {}
        self._weather_cache: Dict[tuple, Optional[Dict]] = {}
        self._injury_cache: Dict[str, Dict] = {}
        self._team_strength_cache: Dict[tuple[str, str], Dict[str, float]] = {}

        self._repo = ExternalDataRepository(self)
        self._team_strength = TeamStrengthService(self._repo, self._team_strength_cache)
        self._heuristics = ProbabilityHeuristicsService(self, self._repo, self._team_strength)
        self._candidates = CandidateLegService(self, self._repo)

    async def calculate_leg_probability_from_odds(
        self,
        odds_obj: Odds,
        market_id,
        outcome: str,
        home_team: str,
        away_team: str,
        game_start_time: Optional[datetime] = None,
        market_type: Optional[str] = None,
    ) -> Dict:
        implied_prob = float(getattr(odds_obj, "implied_prob", 0.0) or 0.0)
        model_adjusted = await self._heuristics.apply_heuristics(
            implied_prob=implied_prob,
            market_id=str(market_id),
            outcome=outcome,
            home_team=home_team,
            away_team=away_team,
            game_start_time=game_start_time,
            market_type=market_type,
        )

        strategy_svc = StrategyDecompositionService(self.db)
        try:
            adjusted_prob, strategy_components, strategy_contributions = await strategy_svc.compute_ensemble(
                implied_prob=implied_prob,
                model_adjusted_prob=model_adjusted,
                sport=self.sport_code,
                home_team=home_team,
                away_team=away_team,
            )
        except Exception:
            adjusted_prob = model_adjusted
            strategy_components = None
            strategy_contributions = []

        edge = adjusted_prob - implied_prob
        decimal_odds = float(getattr(odds_obj, "decimal_price", 1.0) or 1.0)
        value_score = self._calculate_value_score(adjusted_prob, implied_prob, decimal_odds)
        confidence = self._calculate_confidence(adjusted_prob, edge, value_score)

        out = {
            "market_id": str(market_id),
            "outcome": outcome,
            "implied_prob": implied_prob,
            "adjusted_prob": adjusted_prob,
            "edge": edge,
            "value_score": value_score,
            "confidence_score": confidence,
            "odds": getattr(odds_obj, "price", None),
            "decimal_odds": decimal_odds,
        }
        if strategy_components is not None:
            out["strategy_components"] = strategy_components
        if strategy_contributions:
            out["strategy_contributions"] = strategy_contributions
        return out

    async def calculate_leg_probability(
        self,
        market_id,
        outcome: str,
        home_team: str,
        away_team: str,
        game_start_time: Optional[datetime] = None,
        market_type: Optional[str] = None,
    ) -> Optional[Dict]:
        result = await self.db.execute(
            select(Odds)
            .join(Market)
            .where(Market.id == market_id)
            .where(Odds.outcome == outcome)
            .order_by(Odds.implied_prob.desc())
            .limit(1)
        )
        odds_obj = result.scalar_one_or_none()
        if not odds_obj:
            return None

        return await self.calculate_leg_probability_from_odds(
            odds_obj=odds_obj,
            market_id=market_id,
            outcome=outcome,
            home_team=home_team,
            away_team=away_team,
            game_start_time=game_start_time,
            market_type=market_type,
        )

    async def get_candidate_legs(
        self,
        sport: Optional[str] = None,
        min_confidence: float = 50.0,
        max_legs: int = 50,
        week: Optional[int] = None,
        include_player_props: bool = False,
        trace_id: Optional[str] = None,
        now_utc: Optional[datetime] = None,
    ) -> List[Dict]:
        return await self._candidates.get_candidate_legs(
            sport=sport,
            min_confidence=min_confidence,
            max_legs=max_legs,
            week=week,
            include_player_props=include_player_props,
            trace_id=trace_id,
            now_utc=now_utc,
        )

    async def _apply_situational_adjustments(
        self,
        home_team: str,
        away_team: str,
        is_home_outcome: bool,
        game_start_time: Optional[datetime],
    ) -> float:
        return 0.0

    async def _apply_sport_specific_adjustments(
        self,
        implied_prob: float,
        market_id: str,
        outcome: str,
        home_team: str,
        away_team: str,
        market_type: Optional[str] = None,
    ) -> float:
        return 0.0

    async def _get_team_stats(self, team_name: str) -> Optional[Dict]:
        return await self._repo.get_team_stats(team_name)

    async def _get_recent_form(self, team_name: str, games: int = 5) -> List[Dict]:
        return await self._repo.get_recent_form(team_name, games=games)

    def _detect_market_inefficiencies(self, implied_prob: float) -> float:
        if 0.40 <= implied_prob <= 0.60:
            return 0.01
        return 0.0

    def _calculate_value_score(self, adjusted_prob: float, implied_prob: float, decimal_odds: float) -> float:
        expected_value = (adjusted_prob * decimal_odds) - 1.0
        return max(-1.0, min(1.0, expected_value))

    def _calculate_confidence(self, probability: float, edge: float, value_score: float = 0.0) -> float:
        prob_score = 50 + (probability * 50)
        edge_bonus = min(20, max(0, edge * 200))
        value_bonus = min(10, max(0, value_score * 10))
        confidence = prob_score + edge_bonus + value_bonus
        return max(0, min(100, confidence))

    def calculate_parlay_probability(self, leg_probabilities: List[float]) -> float:
        if not leg_probabilities:
            return 0.0
        parlay_prob = 1.0
        for prob in leg_probabilities:
            parlay_prob *= prob
        return parlay_prob


