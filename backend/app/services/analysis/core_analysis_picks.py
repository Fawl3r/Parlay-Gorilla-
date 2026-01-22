"""Core pick generation helpers.

Split from `core_analysis_generator.py` to keep files under the size limit and
to make the pick logic reusable across sports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from app.models.game import Game
from app.services.analysis.score_projection import ScoreProjection, ScoreProjector, clamp


def _round_to_half(value: float) -> float:
    return round(float(value) * 2.0) / 2.0


@dataclass(frozen=True)
class CorePickBuilders:
    """Build spread/total picks and the derived best-bets blocks."""

    def build_spread_pick(
        self,
        *,
        game: Game,
        odds_snapshot: Dict[str, Any],
        model_probs: Dict[str, Any],
        projection: ScoreProjection,
    ) -> Dict[str, Any]:
        home_point = odds_snapshot.get("home_spread_point")

        # If no market spread is available (common when odds are missing), fall back to model margin.
        if home_point is None:
            margin = float(projection.margin_home_minus_away)
            pick_home = margin > 0
            pick_team = game.home_team if pick_home else game.away_team
            pick_point = -abs(margin)
            pick_point = _round_to_half(pick_point)
            pick = f"{pick_team} {pick_point:+.1f} (model)"

            ai_conf = float(model_probs.get("ai_confidence") or 30.0)
            confidence = clamp(45.0 + abs(margin) * 6.0 + (ai_conf - 50.0) * 0.20, 10.0, 90.0)
            rationale = "No market spread is available right now, so this is a model-based projected margin."
            return {"pick": pick, "confidence": float(round(confidence, 1)), "rationale": rationale}

        try:
            home_point_f = float(home_point)
        except Exception:
            return {"pick": "Spread not available", "confidence": 0.0, "rationale": "No usable spread line is available for this matchup right now."}

        cover_margin = projection.margin_home_minus_away + home_point_f
        pick_home = cover_margin > 0
        pick_team = game.home_team if pick_home else game.away_team
        pick_point = home_point_f if pick_home else (-home_point_f)
        pick = f"{pick_team} {pick_point:+.1f}"

        ai_conf = float(model_probs.get("ai_confidence") or 30.0)
        confidence = clamp(50.0 + abs(cover_margin) * 8.0 + (ai_conf - 50.0) * 0.25, 10.0, 95.0)
        rationale = f"Our projection ({projection.as_str()}) implies a margin that {'covers' if pick_home else 'does not cover'} the posted number."
        return {"pick": pick, "confidence": float(round(confidence, 1)), "rationale": rationale}

    def build_total_pick(
        self,
        *,
        game: Game,
        odds_snapshot: Dict[str, Any],
        model_probs: Dict[str, Any],
        projection: ScoreProjection,
    ) -> Dict[str, Any]:
        total_line = odds_snapshot.get("total_line")

        if total_line is None:
            # Fall back to a league baseline total when no market total is present.
            baseline_total = ScoreProjector.baseline_total(league=game.sport)
            baseline_line = _round_to_half(baseline_total)
            diff = float(projection.total_points) - baseline_line
            pick = f"{'Over' if diff > 0 else 'Under'} {baseline_line:.1f} (model baseline)"

            ai_conf = float(model_probs.get("ai_confidence") or 30.0)
            confidence = clamp(45.0 + abs(diff) * 4.0 + (ai_conf - 50.0) * 0.15, 10.0, 90.0)
            rationale = (
                f"No market total is available, so we're comparing the model's projected total ({projection.total_points}) "
                f"to a league baseline ({baseline_line:.1f})."
            )
            return {"pick": pick, "confidence": float(round(confidence, 1)), "rationale": rationale}

        try:
            total_f = float(total_line)
        except Exception:
            return {"pick": "Total not available", "confidence": 0.0, "rationale": "No usable total line is available for this matchup right now."}

        diff = float(projection.total_points) - total_f
        pick = f"{'Over' if diff > 0 else 'Under'} {total_f:.1f}"

        ai_conf = float(model_probs.get("ai_confidence") or 30.0)
        confidence = clamp(50.0 + abs(diff) * 6.0 + (ai_conf - 50.0) * 0.20, 10.0, 95.0)
        rationale = f"Our projection totals {projection.total_points} points versus a posted total of {total_f:.1f}."
        return {"pick": pick, "confidence": float(round(confidence, 1)), "rationale": rationale}

    def build_best_bets(
        self,
        *,
        game: Game,
        spread_pick: Dict[str, Any],
        total_pick: Dict[str, Any],
        model_probs: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        home_prob = float(model_probs.get("home_win_prob") or 0.52)
        away_prob = float(model_probs.get("away_win_prob") or 0.48)
        ml_team = game.home_team if home_prob >= away_prob else game.away_team
        ml_conf = float(model_probs.get("ai_confidence") or 30.0)

        return [
            {"bet_type": "Spread", **spread_pick},
            {"bet_type": "Total", **total_pick},
            {
                "bet_type": "Moneyline",
                "pick": f"{ml_team} ML",
                "confidence": float(round(clamp(ml_conf, 10.0, 95.0), 1)),
                "rationale": "Back the side with the higher modeled win probability.",
            },
        ]

    @staticmethod
    def build_same_game_parlays(*, game: Game, spread_pick: Dict[str, Any], total_pick: Dict[str, Any]) -> Dict[str, Any]:
        matchup = f"{game.away_team} @ {game.home_team}"
        spread_side = spread_pick.get("pick", "")
        total_direction = total_pick.get("pick", "")
        
        legs = [
            {"matchup": matchup, "pick": spread_side, "odds": "", "confidence": spread_pick.get("confidence", 0)},
            {"matchup": matchup, "pick": total_direction, "odds": "", "confidence": total_pick.get("confidence", 0)},
        ]
        
        # Calculate correlation matrix
        correlation_matrix = CorePickBuilders._calculate_correlation_matrix(
            spread_side=spread_side,
            total_direction=total_direction,
        )
        
        # Calculate hit probability (product of individual confidences, adjusted for correlation)
        spread_conf = spread_pick.get("confidence", 50) / 100.0
        total_conf = total_pick.get("confidence", 50) / 100.0
        correlation_factor = correlation_matrix.get("overall_correlation", 0.0)
        
        # Adjust for correlation: positive correlation reduces independent probability
        if correlation_factor > 0:
            # Positive correlation means if one hits, the other is more likely
            # But for parlay, we want independent probability
            adjusted_prob = (spread_conf * total_conf) * (1.0 - correlation_factor * 0.3)
        else:
            # Negative correlation increases independent probability slightly
            adjusted_prob = (spread_conf * total_conf) * (1.0 + abs(correlation_factor) * 0.1)
        
        hit_probability = max(0.0, min(1.0, adjusted_prob))
        combined_confidence = (spread_pick.get("confidence", 0) + total_pick.get("confidence", 0)) / 2.0
        
        return {
            "safe_3_leg": {
                "legs": legs[:2],
                "hit_probability": round(hit_probability, 3),
                "confidence": round(combined_confidence, 1),
                "correlation_warning": correlation_matrix.get("warning"),
            },
            "balanced_6_leg": {"legs": [], "hit_probability": 0.0, "confidence": 0.0},
            "degen_10_20_leg": {"legs": [], "hit_probability": 0.0, "confidence": 0.0},
            "correlation_matrix": correlation_matrix,
        }
    
    @staticmethod
    def _calculate_correlation_matrix(
        *,
        spread_side: str,
        total_direction: str,
    ) -> Dict[str, Any]:
        """Calculate correlation between spread and total picks."""
        # Extract team and direction from spread (e.g., "Team Name +3.5" or "Team Name -3.5")
        spread_team_favored = "+" not in spread_side or spread_side.count("+") == 0
        total_over = "Over" in total_direction
        
        # Correlation logic:
        # - If favorite covers spread AND over hits = positive correlation (blowout with scoring)
        # - If favorite covers spread AND under hits = negative correlation (blowout with defense)
        # - If underdog covers spread AND over hits = positive correlation (upset with scoring)
        # - If underdog covers spread AND under hits = negative correlation (upset with defense)
        
        correlation = 0.0
        warning = None
        
        # Simplified: if both favor offense (over) or both favor defense (under)
        if spread_team_favored and total_over:
            correlation = 0.4  # Moderate positive (favorite wins big, high scoring)
            warning = "Favorite covering with Over suggests positive correlation - both outcomes favor offensive dominance"
        elif spread_team_favored and not total_over:
            correlation = -0.3  # Negative (favorite wins big, low scoring)
            warning = "Favorite covering with Under suggests negative correlation - defensive blowout scenario"
        elif not spread_team_favored and total_over:
            correlation = 0.3  # Positive (upset with scoring)
            warning = "Underdog covering with Over suggests positive correlation - upset with high scoring"
        elif not spread_team_favored and not total_over:
            correlation = -0.2  # Slight negative (upset with defense)
            warning = "Underdog covering with Under suggests slight negative correlation - defensive upset scenario"
        
        return {
            "spread_total_correlation": round(correlation, 2),
            "overall_correlation": round(correlation, 2),
            "warning": warning,
            "interpretation": "positive" if correlation > 0.2 else "negative" if correlation < -0.2 else "neutral",
        }


