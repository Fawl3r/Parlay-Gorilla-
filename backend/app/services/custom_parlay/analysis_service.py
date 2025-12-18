from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from app.schemas.parlay import (
    CustomParlayLeg,
    CustomParlayLegAnalysis,
    CustomParlayAnalysisResponse,
)
from app.services.probability_engine import get_probability_engine

from .odds_utils import OddsConverter


@dataclass(frozen=True)
class _ResolvedOdds:
    market: Optional[Market]
    odds: Optional[Odds]
    decimal_odds: float
    implied_prob: float
    odds_str: str
    point: Optional[float]


class CustomParlayAnalysisService:
    """
    Deterministic analysis for user-selected custom parlays.

    Key behavior:
    - Resolves the exact odds row for each leg (prefers market_id if provided).
    - Calculates implied + model-adjusted probabilities and edges.
    - Produces a stable text summary without requiring OpenAI.
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._engine_by_sport: Dict[str, Any] = {}

    async def load_games(self, legs: List[CustomParlayLeg]) -> Dict[str, Game]:
        """Batch-load games (with markets + odds) for the given legs."""
        normalized_ids: List[str] = []
        for leg in legs:
            try:
                normalized_ids.append(str(uuid.UUID(str(leg.game_id))))
            except Exception as exc:
                raise ValueError(f"Invalid game_id: {leg.game_id}") from exc

        unique_game_ids = list(dict.fromkeys(normalized_ids))
        game_uuid_ids = [uuid.UUID(gid) for gid in unique_game_ids]

        result = await self._db.execute(
            select(Game)
            .options(selectinload(Game.markets).selectinload(Market.odds))
            .where(Game.id.in_(game_uuid_ids))
        )
        games = result.scalars().all()
        games_by_id = {str(g.id): g for g in games}
        return games_by_id

    async def analyze(self, legs: List[CustomParlayLeg]) -> CustomParlayAnalysisResponse:
        games_by_id = await self.load_games(legs)
        return await self.analyze_with_loaded_games(legs, games_by_id)

    async def analyze_with_loaded_games(
        self,
        legs: List[CustomParlayLeg],
        games_by_id: Dict[str, Game],
    ) -> CustomParlayAnalysisResponse:
        if not legs:
            return CustomParlayAnalysisResponse(
                legs=[],
                num_legs=0,
                combined_implied_probability=0.0,
                combined_ai_probability=0.0,
                overall_confidence=0.0,
                confidence_color="red",
                parlay_odds="+100",
                parlay_decimal_odds=1.0,
                ai_summary="No legs provided.",
                ai_risk_notes="Add at least one leg to analyze.",
                ai_recommendation="avoid",
                weak_legs=[],
                strong_legs=[],
            )

        leg_analyses: List[CustomParlayLegAnalysis] = []
        combined_implied = 1.0
        combined_ai = 1.0
        parlay_decimal = 1.0
        weak_legs: List[str] = []
        strong_legs: List[str] = []

        for leg in legs:
            game_id_norm = self._normalize_uuid_str(leg.game_id)
            game = games_by_id.get(game_id_norm)
            if not game:
                raise ValueError(f"Game not found: {leg.game_id}")

            resolved = self._resolve_odds(game, leg)
            ai_prob, confidence, edge = await self._calculate_model_metrics(
                game=game,
                market=resolved.market,
                odds=resolved.odds,
                implied_prob=resolved.implied_prob,
                market_type=str(leg.market_type),
            )

            recommendation = self._get_recommendation(confidence=confidence, edge=edge)
            pick_display = self._format_pick_display(game, leg, resolved.point)

            leg_analysis_obj = CustomParlayLegAnalysis(
                game_id=str(game.id),
                game=f"{game.away_team} @ {game.home_team}",
                home_team=game.home_team,
                away_team=game.away_team,
                sport=game.sport or "NFL",
                market_type=str(leg.market_type),
                pick=str(leg.pick),
                pick_display=pick_display,
                odds=resolved.odds_str,
                decimal_odds=round(resolved.decimal_odds, 2),
                implied_probability=round(resolved.implied_prob * 100.0, 1),
                ai_probability=round(ai_prob * 100.0, 1),
                confidence=round(confidence, 1),
                edge=round(edge * 100.0, 2),
                recommendation=recommendation,
            )

            leg_analyses.append(leg_analysis_obj)

            combined_implied *= resolved.implied_prob
            combined_ai *= ai_prob
            parlay_decimal *= resolved.decimal_odds

            if recommendation in {"avoid", "weak"}:
                weak_legs.append(f"{leg_analysis_obj.game}: {pick_display}")
            elif recommendation == "strong":
                strong_legs.append(f"{leg_analysis_obj.game}: {pick_display}")

        num_legs = len(leg_analyses)
        avg_confidence = sum(l.confidence for l in leg_analyses) / num_legs if num_legs else 0.0
        leg_penalty = max(0.0, float(num_legs - 3) * 2.0)
        overall_confidence = max(10.0, avg_confidence - leg_penalty) if num_legs else 0.0

        confidence_color = self._get_confidence_color(overall_confidence)
        overall_recommendation = self._get_overall_recommendation(overall_confidence, len(weak_legs), num_legs)

        ai_summary, ai_risk_notes = self._build_deterministic_ai_text(
            legs=leg_analyses,
            combined_ai_probability=combined_ai * 100.0,
            overall_confidence=overall_confidence,
            weak_legs=weak_legs,
            strong_legs=strong_legs,
        )

        return CustomParlayAnalysisResponse(
            legs=leg_analyses,
            num_legs=num_legs,
            combined_implied_probability=round(combined_implied * 100.0, 2),
            combined_ai_probability=round(combined_ai * 100.0, 2),
            overall_confidence=round(overall_confidence, 1),
            confidence_color=confidence_color,
            parlay_odds=OddsConverter.decimal_to_american(parlay_decimal),
            parlay_decimal_odds=round(parlay_decimal, 2),
            ai_summary=ai_summary,
            ai_risk_notes=ai_risk_notes,
            ai_recommendation=overall_recommendation,
            weak_legs=weak_legs,
            strong_legs=strong_legs,
        )

    # ------------------------------------------------------------------
    # Odds resolution
    # ------------------------------------------------------------------

    def _resolve_odds(self, game: Game, leg: CustomParlayLeg) -> _ResolvedOdds:
        market = self._find_market(game, leg)
        odds = self._find_matching_odds(game, market, leg) if market else None

        # Prefer DB odds; fallback to request odds string.
        decimal_odds = float(getattr(odds, "decimal_price", 0) or 0) if odds else 0.0
        if decimal_odds <= 0:
            decimal_odds = OddsConverter.american_to_decimal(leg.odds or "-110")

        implied_prob = float(getattr(odds, "implied_prob", 0) or 0) if odds else 0.0
        if implied_prob <= 0:
            implied_prob = OddsConverter.implied_prob_from_decimal(decimal_odds)

        odds_str = str(getattr(odds, "price", "") or "").strip() if odds else str(leg.odds or "-110")
        point = self._resolve_point(market, odds, leg)

        return _ResolvedOdds(
            market=market,
            odds=odds,
            decimal_odds=float(decimal_odds),
            implied_prob=float(implied_prob),
            odds_str=odds_str,
            point=point,
        )

    @staticmethod
    def _find_market(game: Game, leg: CustomParlayLeg) -> Optional[Market]:
        if leg.market_id:
            wanted = str(leg.market_id)
            for m in getattr(game, "markets", []) or []:
                if str(getattr(m, "id", "")) == wanted:
                    return m
        for m in getattr(game, "markets", []) or []:
            if str(getattr(m, "market_type", "")).lower() == str(leg.market_type).lower():
                return m
        return None

    def _find_matching_odds(self, game: Game, market: Market, leg: CustomParlayLeg) -> Optional[Odds]:
        market_type = str(leg.market_type).lower()
        if market_type == "h2h":
            desired = self._resolve_h2h_outcome(game, str(leg.pick))
            for o in getattr(market, "odds", []) or []:
                if str(getattr(o, "outcome", "")).lower() == desired:
                    return o
            # Fallback: contains match
            for o in getattr(market, "odds", []) or []:
                if desired in str(getattr(o, "outcome", "")).lower():
                    return o
            return None

        if market_type == "spreads":
            desired_team = self._resolve_spread_team(game, str(leg.pick))
            desired_point = float(leg.point) if leg.point is not None else None
            return self._find_team_point_odds(market, desired_team, desired_point)

        if market_type == "totals":
            desired_pick = str(leg.pick).lower().strip()
            desired_point = float(leg.point) if leg.point is not None else None
            return self._find_total_odds(market, desired_pick, desired_point)

        return None

    @staticmethod
    def _resolve_point(market: Optional[Market], odds: Optional[Odds], leg: CustomParlayLeg) -> Optional[float]:
        if leg.point is not None:
            try:
                return float(leg.point)
            except Exception:
                return None
        if odds is not None:
            return OddsConverter.extract_point(getattr(odds, "outcome", ""))
        # If we have a market but no odds, can't infer.
        _ = market
        return None

    @staticmethod
    def _resolve_h2h_outcome(game: Game, pick: str) -> str:
        pick_lower = str(pick).lower().strip()
        if pick_lower in {"home", "away"}:
            return pick_lower
        if str(game.home_team).lower() == pick_lower:
            return "home"
        if str(game.away_team).lower() == pick_lower:
            return "away"
        # Best-effort contains match
        if pick_lower and pick_lower in str(game.home_team).lower():
            return "home"
        if pick_lower and pick_lower in str(game.away_team).lower():
            return "away"
        raise ValueError(f"Invalid moneyline pick '{pick}' for game {game.away_team} @ {game.home_team}")

    @staticmethod
    def _resolve_spread_team(game: Game, pick: str) -> str:
        pick_lower = str(pick).lower().strip()
        if pick_lower == "home":
            return str(game.home_team)
        if pick_lower == "away":
            return str(game.away_team)
        # If pick is a team name, accept.
        if str(game.home_team).lower() == pick_lower:
            return str(game.home_team)
        if str(game.away_team).lower() == pick_lower:
            return str(game.away_team)
        return str(pick)

    @staticmethod
    def _find_team_point_odds(market: Market, team_name: str, point: Optional[float]) -> Optional[Odds]:
        team_lower = str(team_name).lower()
        candidates: List[Tuple[Odds, Optional[float]]] = []
        for o in getattr(market, "odds", []) or []:
            outcome = str(getattr(o, "outcome", "")).lower()
            if team_lower and team_lower not in outcome:
                continue
            candidates.append((o, OddsConverter.extract_point(outcome)))

        if not candidates:
            return None

        if point is None:
            return candidates[0][0]

        # Match point with small tolerance
        for o, p in candidates:
            if p is None:
                continue
            if abs(float(p) - float(point)) <= 0.01:
                return o

        return candidates[0][0]

    @staticmethod
    def _find_total_odds(market: Market, pick: str, point: Optional[float]) -> Optional[Odds]:
        pick_lower = str(pick).lower().strip()
        candidates: List[Tuple[Odds, Optional[float]]] = []
        for o in getattr(market, "odds", []) or []:
            outcome = str(getattr(o, "outcome", "")).lower()
            if pick_lower and pick_lower not in outcome:
                continue
            candidates.append((o, OddsConverter.extract_point(outcome)))

        if not candidates:
            return None

        if point is None:
            return candidates[0][0]

        for o, p in candidates:
            if p is None:
                continue
            if abs(float(p) - float(point)) <= 0.01:
                return o

        return candidates[0][0]

    # ------------------------------------------------------------------
    # Model metrics
    # ------------------------------------------------------------------

    async def _calculate_model_metrics(
        self,
        game: Game,
        market: Optional[Market],
        odds: Optional[Odds],
        implied_prob: float,
        market_type: str,
    ) -> tuple[float, float, float]:
        """
        Returns (ai_prob, confidence, edge) with probabilities in [0,1] and edge as (ai - implied).
        """
        ai_prob = implied_prob
        confidence = 50.0
        edge = 0.0

        if market is None or odds is None:
            # Fallback: light bump to implied probability
            ai_prob = min(0.95, max(0.05, implied_prob * 1.02))
            confidence = 50.0
            edge = ai_prob - implied_prob
            return ai_prob, confidence, edge

        sport_key = (str(getattr(game, "sport", "") or "NFL")).upper()
        engine = self._engine_by_sport.get(sport_key)
        if engine is None:
            engine = get_probability_engine(self._db, sport_key)
            self._engine_by_sport[sport_key] = engine

        try:
            leg_analysis = await engine.calculate_leg_probability_from_odds(
                odds_obj=odds,
                market_id=market.id,
                outcome=getattr(odds, "outcome", ""),
                home_team=getattr(game, "home_team", ""),
                away_team=getattr(game, "away_team", ""),
                game_start_time=getattr(game, "start_time", None),
                market_type=market_type,
            )
            ai_prob = float(leg_analysis.get("adjusted_prob", implied_prob) or implied_prob)
            confidence = float(leg_analysis.get("confidence_score", 50.0) or 50.0)
            edge = float(leg_analysis.get("edge", ai_prob - implied_prob) or (ai_prob - implied_prob))
        except Exception:
            ai_prob = min(0.95, max(0.05, implied_prob * 1.02))
            confidence = 50.0
            edge = ai_prob - implied_prob

        ai_prob = min(0.95, max(0.05, ai_prob))
        return ai_prob, confidence, edge

    # ------------------------------------------------------------------
    # Presentation + recommendation logic
    # ------------------------------------------------------------------

    @staticmethod
    def _format_pick_display(game: Game, leg: CustomParlayLeg, point: Optional[float]) -> str:
        market_type = str(leg.market_type).lower()
        pick = str(leg.pick)
        if market_type == "h2h":
            # If a user passed "home"/"away", translate to team names.
            pick_lower = pick.lower().strip()
            if pick_lower == "home":
                return f"{game.home_team} ML"
            if pick_lower == "away":
                return f"{game.away_team} ML"
            return f"{pick} ML"
        if market_type == "spreads":
            p = point
            pick_lower = pick.lower().strip()
            team = game.home_team if pick_lower == "home" else game.away_team if pick_lower == "away" else pick
            if p is None:
                return str(team)
            sign_point = f"{p:+.1f}"
            return f"{team} {sign_point}"
        if market_type == "totals":
            p = point
            label = pick.upper().strip()
            return f"{label} {p}" if p is not None else label
        return pick

    @staticmethod
    def _get_recommendation(confidence: float, edge: float) -> str:
        if confidence >= 70 and edge >= 0.02:
            return "strong"
        if confidence >= 55 and edge >= 0:
            return "moderate"
        if confidence >= 40:
            return "weak"
        return "avoid"

    @staticmethod
    def _get_overall_recommendation(overall_confidence: float, weak_leg_count: int, num_legs: int) -> str:
        weak_ratio = weak_leg_count / num_legs if num_legs > 0 else 0.0
        if overall_confidence >= 65 and weak_ratio < 0.2:
            return "strong_play"
        if overall_confidence >= 50 and weak_ratio < 0.4:
            return "solid_play"
        if overall_confidence >= 35:
            return "risky_play"
        return "avoid"

    @staticmethod
    def _get_confidence_color(score: float) -> str:
        if score >= 70:
            return "green"
        if score >= 50:
            return "yellow"
        return "red"

    @staticmethod
    def _build_deterministic_ai_text(
        legs: List[CustomParlayLegAnalysis],
        combined_ai_probability: float,
        overall_confidence: float,
        weak_legs: List[str],
        strong_legs: List[str],
    ) -> tuple[str, str]:
        confidence_text = "high" if overall_confidence >= 60 else "moderate" if overall_confidence >= 40 else "risky"
        strongest = strong_legs[:2]
        concerns = weak_legs[:2]

        strongest_text = f" Strong picks: {', '.join(strongest)}." if strongest else ""
        concerns_text = f" Watch outs: {', '.join(concerns)}." if concerns else ""

        summary = (
            f"This {len(legs)}-leg parlay has a {combined_ai_probability:.2f}% combined probability by our model. "
            f"Overall confidence is {confidence_text} at {overall_confidence:.1f}/100."
            f"{strongest_text}{concerns_text}"
        )

        risk_notes = (
            f"With {len(legs)} legs, the ticket compounds risk (every leg must hit). "
            f"{'There are concerns flagged on ' + str(len(weak_legs)) + ' leg(s). ' if weak_legs else ''}"
            "Consider trimming lower-confidence legs if you want a higher hit rate. "
            "Never bet more than you can afford to lose."
        )

        return summary, risk_notes

    @staticmethod
    def _normalize_uuid_str(value: str) -> str:
        try:
            return str(uuid.UUID(str(value)))
        except Exception as exc:
            raise ValueError(f"Invalid game_id: {value}") from exc




