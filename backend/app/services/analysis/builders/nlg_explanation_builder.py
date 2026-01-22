"""Template-based NLG (Natural Language Generation) for explanations."""

from typing import Dict, Any, Optional, List


class NLGExplanationBuilder:
    """Generate human-readable explanations using templates and data."""
    
    @staticmethod
    def build_pick_explanation(
        *,
        pick_type: str,  # "spread" or "total"
        side: str,  # "home", "away", "over", "under"
        confidence: float,  # 0-100
        model_prob: float,  # 0-1
        market_prob: float,  # 0-1
        edge: float,  # model_prob - market_prob
        key_stats: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build explanation for a pick using templates."""
        
        edge_pct = edge * 100
        confidence_level = "high" if confidence >= 70 else "medium" if confidence >= 50 else "low"
        
        # Base explanation
        if pick_type == "spread":
            team_side = "home team" if side == "home" else "away team"
            explanation = f"The model favors the {team_side} to cover the spread"
        else:  # total
            explanation = f"The model favors the {side.upper()}"
        
        # Add confidence
        if confidence_level == "high":
            explanation += f" with {confidence_level} confidence ({confidence:.0f}%)"
        else:
            explanation += f" with {confidence_level} confidence"
        
        # Add edge if significant
        if abs(edge_pct) >= 5:
            if edge_pct > 0:
                explanation += f". The model sees a {abs(edge_pct):.1f}% edge over the market"
            else:
                explanation += f". The model is {abs(edge_pct):.1f}% more conservative than the market"
        
        # Add key stat if available
        if key_stats:
            top_stat = key_stats.get("top_stat")
            if top_stat:
                explanation += f". {top_stat}"
        
        return explanation
    
    @staticmethod
    def build_confidence_explanation(
        *,
        confidence_total: float,  # 0-100
        market_agreement: float,  # 0-30
        statistical_edge: float,  # 0-30
        situational_edge: float,  # 0-20
        data_quality: float,  # 0-20
    ) -> str:
        """Build explanation for confidence breakdown."""
        
        if confidence_total >= 80:
            level = "very high"
        elif confidence_total >= 65:
            level = "high"
        elif confidence_total >= 50:
            level = "moderate"
        else:
            level = "low"
        
        explanation = f"Overall confidence is {level} ({confidence_total:.0f}%)"
        
        # Add contributing factors
        factors = []
        if market_agreement >= 20:
            factors.append("strong market agreement")
        if statistical_edge >= 20:
            factors.append("clear statistical edge")
        if situational_edge >= 15:
            factors.append("favorable situational factors")
        if data_quality >= 15:
            factors.append("high-quality data")
        
        if factors:
            explanation += f", driven by {', '.join(factors)}"
        
        return explanation
    
    @staticmethod
    def build_market_disagreement_explanation(
        *,
        flag: str,  # "consensus", "volatile", "sharp_vs_public"
        spread_variance: str,  # "low", "med", "high"
        total_variance: str,  # "low", "med", "high"
        books_split_summary: str,
    ) -> str:
        """Build explanation for market disagreement."""
        
        if flag == "consensus":
            explanation = "Books are in consensus on this game"
        elif flag == "volatile":
            explanation = "Market is showing volatility with significant line movement"
        else:  # sharp_vs_public
            explanation = "Sharp money and public betting are split on this game"
        
        # Add variance details
        if spread_variance == "high" or total_variance == "high":
            explanation += ". High variance across books suggests uncertainty"
        elif spread_variance == "med" or total_variance == "med":
            explanation += ". Moderate variance indicates some disagreement"
        
        if books_split_summary:
            explanation += f". {books_split_summary}"
        
        return explanation
    
    @staticmethod
    def build_outcome_path_explanation(
        *,
        home_control_prob: float,
        shootout_prob: float,
        variance_upset_prob: float,
    ) -> str:
        """Build explanation for outcome paths."""
        
        # Find dominant path
        paths = [
            ("home control", home_control_prob),
            ("shootout", shootout_prob),
            ("variance upset", variance_upset_prob),
        ]
        paths.sort(key=lambda x: x[1], reverse=True)
        
        dominant_path, dominant_prob = paths[0]
        explanation = f"The most likely outcome path is {dominant_path} ({dominant_prob:.0f}% probability)"
        
        # Add secondary path if significant
        if paths[1][1] >= 0.25:
            explanation += f", with {paths[1][0]} also possible ({paths[1][1]:.0f}%)"
        
        return explanation
