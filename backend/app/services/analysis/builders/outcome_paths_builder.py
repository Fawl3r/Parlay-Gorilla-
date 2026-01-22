"""Outcome paths builder - deterministic game script probabilities."""

from __future__ import annotations

from typing import Any, Dict, Optional


class OutcomePathsBuilder:
    """Build outcome path probabilities based on odds and game context."""

    @staticmethod
    def build(
        *,
        odds_snapshot: Dict[str, Any],
        model_probs: Dict[str, Any],
        spread: Optional[float] = None,
        total: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate outcome path probabilities deterministically.
        
        Args:
            odds_snapshot: Odds data with home_ml, away_ml, home_implied_prob, away_implied_prob
            model_probs: Model probabilities with home_win_prob, away_win_prob
            spread: Home spread point (absolute value used)
            total: Total line
            
        Returns:
            Dict with home_control_script, shootout_script, variance_upset_script
        """
        # Extract implied probabilities (vig-removed if available, else use raw)
        home_implied = odds_snapshot.get("home_implied_prob")
        away_implied = odds_snapshot.get("away_implied_prob")
        
        # Fallback to model probabilities if odds not available
        if home_implied is None or away_implied is None:
            home_implied = float(model_probs.get("home_win_prob", 0.5))
            away_implied = float(model_probs.get("away_win_prob", 0.5))
        
        # Normalize to sum to 1.0
        total_implied = home_implied + away_implied
        if total_implied > 0:
            home_implied = home_implied / total_implied
            away_implied = away_implied / total_implied
        else:
            home_implied = 0.5
            away_implied = 0.5
        
        # Extract spread and total
        if spread is None:
            spread = abs(odds_snapshot.get("home_spread_point") or 0.0)
        else:
            spread = abs(spread)
            
        if total is None:
            total = odds_snapshot.get("total_line")
            if total is None:
                # Use league baseline if no total available
                total = 45.0  # Default NFL baseline
            total = float(total)
        
        # Determine favorite and underdog
        favorite_prob = max(home_implied, away_implied)
        underdog_prob = min(home_implied, away_implied)
        
        # Calculate how "live" the underdog is (closer ML = more live)
        ml_closeness = 1.0 - abs(favorite_prob - underdog_prob)  # 0.0 = blowout, 1.0 = coin flip
        
        # Heuristic 1: Home Control Script
        # Higher probability when: large spread, low total, favorite has high win prob
        control_base = favorite_prob * 0.4  # Base from favorite probability
        spread_factor = min(spread / 10.0, 1.0) * 0.3  # Larger spread = more control
        total_factor = max(0, (50.0 - total) / 50.0) * 0.3  # Lower total = more control
        home_control_prob = min(0.85, control_base + spread_factor + total_factor)
        
        # Heuristic 2: Shootout Script
        # Higher probability when: high total, close game (both teams can score)
        shootout_base = (total / 60.0) * 0.4  # Higher total = more shootout potential
        close_game_factor = ml_closeness * 0.3  # Closer game = both teams scoring
        pace_factor = min(total / 50.0, 1.0) * 0.3  # High totals suggest pace
        shootout_prob = min(0.85, shootout_base + close_game_factor + pace_factor)
        
        # Heuristic 3: Variance Upset Script
        # Higher probability when: close ML, high total volatility, underdog has decent chance
        upset_base = underdog_prob * 0.4  # Underdog probability
        ml_volatility = ml_closeness * 0.3  # Close ML = more variance potential
        total_volatility = max(0, (total - 40.0) / 30.0) * 0.3  # Higher totals = more variance
        variance_upset_prob = min(0.85, upset_base + ml_volatility + total_volatility)
        
        # Normalize to sum to 1.0
        total_prob = home_control_prob + shootout_prob + variance_upset_prob
        if total_prob > 0:
            home_control_prob = home_control_prob / total_prob
            shootout_prob = shootout_prob / total_prob
            variance_upset_prob = variance_upset_prob / total_prob
        else:
            # Fallback equal distribution
            home_control_prob = 0.33
            shootout_prob = 0.33
            variance_upset_prob = 0.34
        
        # Build descriptions
        home_control_desc = (
            f"The favorite is projected to control the game flow with a {spread:.1f}-point spread. "
            f"Lower total ({total:.1f}) suggests a slower-paced, defensive game."
        )
        
        shootout_desc = (
            f"High total ({total:.1f}) and close moneyline suggest both teams will score. "
            f"Game flow favors offensive production over defensive stops."
        )
        
        upset_desc = (
            f"Close moneyline and underdog probability ({underdog_prob:.1%}) create variance potential. "
            f"Higher total ({total:.1f}) increases scoring volatility and upset likelihood."
        )
        
        from app.services.analysis.builders.nlg_explanation_builder import NLGExplanationBuilder
        
        explanation = NLGExplanationBuilder.build_outcome_path_explanation(
            home_control_prob=home_control_prob,
            shootout_prob=shootout_prob,
            variance_upset_prob=variance_upset_prob,
        )
        
        return {
            "home_control_script": {
                "probability": round(home_control_prob, 3),
                "description": home_control_desc,
                "recommended_angles": ["spread", "under", "team_total_under"],
            },
            "shootout_script": {
                "probability": round(shootout_prob, 3),
                "description": shootout_desc,
                "recommended_angles": ["over", "team_total_over", "alt_over"],
            },
            "variance_upset_script": {
                "probability": round(variance_upset_prob, 3),
                "description": upset_desc,
                "recommended_angles": ["dog_ml", "dog_spread", "alt_spread"],
            },
            "explanation": explanation,
        }
