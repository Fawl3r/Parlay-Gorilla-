from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.services.probability_engine_impl.external_data_repository import ExternalDataRepository
from app.services.probability_engine_impl.team_strength_service import TeamStrengthService


class ProbabilityHeuristicsService:
    """Applies heuristic adjustments on top of market-implied probability."""

    def __init__(
        self,
        engine: "BaseProbabilityEngine",
        repo: ExternalDataRepository,
        team_strength_service: TeamStrengthService,
    ):
        from app.services.probability_engine_impl.base_engine import BaseProbabilityEngine

        if not isinstance(engine, BaseProbabilityEngine):
            raise TypeError("engine must be a BaseProbabilityEngine")

        self._engine = engine
        self._repo = repo
        self._team_strength = team_strength_service

    async def apply_heuristics(
        self,
        implied_prob: float,
        market_id: str,
        outcome: str,
        home_team: str,
        away_team: str,
        game_start_time: Optional[datetime] = None,
        market_type: Optional[str] = None,
    ) -> float:
        adjusted = float(implied_prob)

        outcome_lower = (outcome or "").lower()
        is_home_outcome = "home" in outcome_lower or outcome_lower == (home_team or "").lower()
        favored_team = home_team if is_home_outcome else away_team
        opponent_team = away_team if is_home_outcome else home_team

        # 1) Team strength (if stats fetcher is available)
        strength = await self._team_strength.get_team_strength(favored_team, opponent_team)
        if strength:
            adjusted += float(strength.get("strength_diff", 0.0)) * 0.05

        # 2) Situational adjustments (sport-specific override hook)
        adjusted += await self._engine._apply_situational_adjustments(
            home_team, away_team, is_home_outcome, game_start_time
        )

        # 3) Weather impact (cached / best-effort)
        if game_start_time:
            weather = await self._repo.get_weather(home_team, game_start_time)
            if weather and weather.get("affects_game"):
                adjusted += 0.02 if is_home_outcome else -0.02

        # 4) Injury impact (cached / best-effort)
        injury_adj = await self._calculate_injury_adjustment(favored_team, opponent_team)
        adjusted += injury_adj

        # 5) Sport-specific adjustments (override hook)
        adjusted += await self._engine._apply_sport_specific_adjustments(
            implied_prob, market_id, outcome, home_team, away_team, market_type
        )

        # 6) Market inefficiency heuristic
        adjusted += self._engine._detect_market_inefficiencies(implied_prob)

        # 7) Extreme odds damping
        if implied_prob > 0.85:
            adjusted *= 0.98
        elif implied_prob < 0.15:
            adjusted *= 1.02

        return max(0.01, min(0.99, adjusted))

    async def _calculate_injury_adjustment(self, favored_team: str, opponent_team: str) -> float:
        if not self._engine.injury_fetcher:
            return 0.0

        favored_injuries = await self._repo.get_key_player_status(favored_team)
        opponent_injuries = await self._repo.get_key_player_status(opponent_team)

        adjustment = 0.0
        for _player, status in (favored_injuries or {}).items():
            impact = (status or {}).get("impact", "none")
            if impact == "high":
                adjustment -= 0.03
            elif impact == "medium":
                adjustment -= 0.015

        for _player, status in (opponent_injuries or {}).items():
            impact = (status or {}).get("impact", "none")
            if impact == "high":
                adjustment += 0.03
            elif impact == "medium":
                adjustment += 0.015

        return adjustment


