"""Confidence breakdown builder - trust layer for analysis."""

from __future__ import annotations

from typing import Any, Dict


class ConfidenceBreakdownBuilder:
    """Build confidence breakdown from market, stats, situational, and data quality signals."""

    @staticmethod
    def build(
        *,
        market_probs: Dict[str, Any],
        model_probs: Dict[str, Any],
        matchup_data: Dict[str, Any],
        odds_snapshot: Dict[str, Any],
        previous_confidence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate confidence breakdown components.
        
        Args:
            market_probs: Market-implied probabilities (from odds)
            model_probs: Model-calculated probabilities
            matchup_data: Team stats, injuries, weather, etc.
            odds_snapshot: Odds data
            
        Returns:
            Dict with market_agreement, statistical_edge, situational_edge, data_quality, confidence_total
        """
        # 1. Market Agreement (0-30 points)
        # Compare model prob vs vig-free market prob
        home_model_prob = float(model_probs.get("home_win_prob", 0.5))
        away_model_prob = float(model_probs.get("away_win_prob", 0.5))
        
        home_market_prob = float(market_probs.get("home_implied_prob", 0.5))
        away_market_prob = float(market_probs.get("away_implied_prob", 0.5))
        
        # Normalize market probs if they don't sum to 1.0
        market_total = home_market_prob + away_market_prob
        if market_total > 0:
            home_market_prob = home_market_prob / market_total
            away_market_prob = away_market_prob / market_total
        else:
            home_market_prob = 0.5
            away_market_prob = 0.5
        
        # Calculate agreement (inverse of difference)
        home_diff = abs(home_model_prob - home_market_prob)
        away_diff = abs(away_model_prob - away_market_prob)
        avg_diff = (home_diff + away_diff) / 2.0
        
        # Agreement score: 0-30, where 0 difference = 30 points, 0.5 difference = 0 points
        market_agreement = max(0, 30.0 * (1.0 - (avg_diff * 2.0)))
        
        # 2. Statistical Edge (0-30 points)
        # Derived from stats delta (use win-prob calculation inputs)
        home_stats = matchup_data.get("home_team_stats") or {}
        away_stats = matchup_data.get("away_team_stats") or {}
        
        # Check if we have meaningful stats
        has_stats = bool(
            home_stats.get("offense") or home_stats.get("defense") or
            away_stats.get("offense") or away_stats.get("defense")
        )
        
        if has_stats:
            # Calculate edge from model confidence (which incorporates stats)
            ai_confidence = float(model_probs.get("ai_confidence", 30.0))
            # Map 0-100 confidence to 0-30 statistical edge
            statistical_edge = (ai_confidence / 100.0) * 30.0
        else:
            # No stats available = low edge
            statistical_edge = 5.0
        
        # 3. Situational Edge (0-20 points)
        # Rest/travel/weather/injuries contribution
        situational_score = 0.0
        
        # Rest days
        rest_home = matchup_data.get("rest_days_home")
        rest_away = matchup_data.get("rest_days_away")
        if rest_home is not None and rest_away is not None:
            rest_diff = abs(rest_home - rest_away)
            if rest_diff >= 2:
                situational_score += 5.0  # Significant rest advantage
            elif rest_diff >= 1:
                situational_score += 2.5
        
        # Travel distance
        travel = matchup_data.get("travel_distance")
        if travel is not None and travel > 1000:
            situational_score += 3.0  # Long travel = disadvantage
        
        # Weather
        weather = matchup_data.get("weather") or {}
        if weather.get("affects_game"):
            situational_score += 3.0  # Weather factor present
        
        # Injuries
        home_injuries = matchup_data.get("home_injuries") or {}
        away_injuries = matchup_data.get("away_injuries") or {}
        if isinstance(home_injuries, dict) and home_injuries.get("key_injuries"):
            situational_score += 2.0
        if isinstance(away_injuries, dict) and away_injuries.get("key_injuries"):
            situational_score += 2.0
        
        # Divisional matchup
        if matchup_data.get("is_divisional"):
            situational_score += 2.0
        
        situational_edge = min(20.0, situational_score)
        
        # 4. Data Quality (0-20 points)
        # Use trust_score from v2 platform if available, otherwise fallback to presence checks
        home_data_quality = matchup_data.get("home_data_quality")
        away_data_quality = matchup_data.get("away_data_quality")
        
        if home_data_quality or away_data_quality:
            # Use trust scores from v2 platform; don't zero out when only one team has a score
            home_trust = home_data_quality.get("trust_score", 0.0) if home_data_quality else 0.0
            away_trust = away_data_quality.get("trust_score", 0.0) if away_data_quality else 0.0
            trusts = [t for t in (home_trust, away_trust) if t > 0]
            avg_trust = sum(trusts) / len(trusts) if trusts else 0.0

            # Map trust_score (0.0-1.0) to data_quality points (0-20)
            data_quality = avg_trust * 20.0
            
            # Penalize for warnings
            home_warnings = home_data_quality.get("warnings", []) if home_data_quality else []
            away_warnings = away_data_quality.get("warnings", []) if away_data_quality else []
            all_warnings = set(home_warnings + away_warnings)
            
            if "season_inactive" in all_warnings:
                data_quality *= 0.7  # 30% penalty for off-season
            if "stale_data" in all_warnings or "very_stale_data" in all_warnings:
                data_quality *= 0.8  # 20% penalty for stale data
            if "incomplete_data" in all_warnings or "severely_incomplete_data" in all_warnings:
                data_quality *= 0.6  # 40% penalty for incomplete data
        else:
            # Fallback to legacy presence-based scoring
            data_quality = 0.0
            
            # Odds present
            if odds_snapshot.get("home_ml") or odds_snapshot.get("away_ml"):
                data_quality += 5.0
            
            # Stats present
            if has_stats:
                data_quality += 5.0
            
            # Injuries present
            if (isinstance(home_injuries, dict) and home_injuries) or \
               (isinstance(away_injuries, dict) and away_injuries):
                data_quality += 3.0
            
            # Weather present
            if weather and isinstance(weather, dict):
                data_quality += 2.0
            
            # Recent form present
            if home_stats.get("recent_form") or away_stats.get("recent_form"):
                data_quality += 2.0
            
            # Head-to-head present
            if matchup_data.get("head_to_head"):
                data_quality += 3.0
        
        data_quality = min(20.0, max(0.0, data_quality))
        
        # Total confidence
        confidence_total = market_agreement + statistical_edge + situational_edge + data_quality
        
        from app.services.analysis.builders.nlg_explanation_builder import NLGExplanationBuilder
        
        explanation = NLGExplanationBuilder.build_confidence_explanation(
            confidence_total=confidence_total,
            market_agreement=market_agreement,
            statistical_edge=statistical_edge,
            situational_edge=situational_edge,
            data_quality=data_quality,
        )
        
        # Calculate trend if previous confidence available
        trend = None
        if previous_confidence:
            prev_total = previous_confidence.get("confidence_total", 0)
            trend_value = confidence_total - prev_total
            if abs(trend_value) >= 2.0:
                trend = {
                    "direction": "up" if trend_value > 0 else "down",
                    "change": round(trend_value, 1),
                    "previous": round(prev_total, 1),
                }
        
        return {
            "market_agreement": round(market_agreement, 1),
            "statistical_edge": round(statistical_edge, 1),
            "situational_edge": round(situational_edge, 1),
            "data_quality": round(data_quality, 1),
            "confidence_total": round(confidence_total, 1),
            "explanation": explanation,
            "trend": trend,
        }
