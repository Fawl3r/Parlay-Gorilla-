"""Market disagreement builder - detect sharp vs public, volatility."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.market import Market


class MarketDisagreementBuilder:
    """Build market disagreement analysis from odds across multiple books."""

    @staticmethod
    def build(
        *,
        odds_snapshot: Dict[str, Any],
        model_probs: Dict[str, Any],
        markets: Optional[List[Market]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate market disagreement/variance across books.
        
        Args:
            odds_snapshot: Primary odds snapshot (from OddsSnapshotBuilder)
            model_probs: Model probabilities
            markets: Optional list of all markets to analyze variance across books
            
        Returns:
            Dict with spread_variance, total_variance, books_split_summary, flag
        """
        # If we have markets, calculate variance across books
        spread_points: List[float] = []
        total_lines: List[float] = []
        
        if markets:
            for market in markets:
                if market.market_type == "spreads":
                    # Extract spread point from odds outcomes
                    for odd in (market.odds or []):
                        outcome = str(odd.outcome or "")
                        # Parse spread from outcome like "Team Name +3.5"
                        import re
                        match = re.search(r"([+-]?\d+(?:\.\d+)?)\s*$", outcome)
                        if match:
                            try:
                                point = float(match.group(1))
                                spread_points.append(point)
                            except (ValueError, TypeError):
                                pass
                
                elif market.market_type == "totals":
                    # Extract total line from odds outcomes
                    for odd in (market.odds or []):
                        outcome = str(odd.outcome or "")
                        # Parse total from outcome like "Over 44.5" or "44.5"
                        import re
                        match = re.search(r"(\d+\.?\d*)", outcome)
                        if match:
                            try:
                                total = float(match.group(1))
                                total_lines.append(total)
                            except (ValueError, TypeError):
                                pass
        
        # If no markets provided or no data extracted, use snapshot
        if not spread_points and odds_snapshot.get("home_spread_point") is not None:
            spread_points = [float(odds_snapshot["home_spread_point"])]
        
        if not total_lines and odds_snapshot.get("total_line") is not None:
            total_lines = [float(odds_snapshot["total_line"])]
        
        # Calculate variance
        spread_variance_level = MarketDisagreementBuilder._calculate_variance(spread_points)
        total_variance_level = MarketDisagreementBuilder._calculate_variance(total_lines)
        
        # Build summary text
        spread_range = max(spread_points) - min(spread_points) if spread_points else 0.0
        total_range = max(total_lines) - min(total_lines) if total_lines else 0.0
        
        books_split_summary = MarketDisagreementBuilder._build_summary(
            spread_range=spread_range,
            total_range=total_range,
            num_books=len(set(m.book for m in (markets or []))) if markets else 1,
        )
        
        # Determine flag
        flag = MarketDisagreementBuilder._determine_flag(
            spread_variance=spread_variance_level,
            total_variance=total_variance_level,
            model_probs=model_probs,
            odds_snapshot=odds_snapshot,
        )
        
        from app.services.analysis.builders.nlg_explanation_builder import NLGExplanationBuilder
        
        explanation = NLGExplanationBuilder.build_market_disagreement_explanation(
            flag=flag,
            spread_variance=spread_variance_level,
            total_variance=total_variance_level,
            books_split_summary=books_split_summary,
        )
        
        # Detect sharp money indicator
        sharp_indicator = MarketDisagreementBuilder._detect_sharp_money(
            flag=flag,
            model_probs=model_probs,
            odds_snapshot=odds_snapshot,
            markets=markets,
        )
        
        return {
            "spread_variance": spread_variance_level,
            "total_variance": total_variance_level,
            "books_split_summary": books_split_summary,
            "flag": flag,
            "explanation": explanation,
            "sharp_indicator": sharp_indicator,
        }
    
    @staticmethod
    def _calculate_variance(values: List[float]) -> str:
        """Calculate variance level from list of values."""
        if not values or len(values) < 2:
            return "low"
        
        value_range = max(values) - min(values)
        
        if value_range < 1.0:
            return "low"
        elif value_range < 2.0:
            return "med"
        else:
            return "high"
    
    @staticmethod
    def _build_summary(spread_range: float, total_range: float, num_books: int) -> str:
        """Build descriptive summary of book splits."""
        if num_books < 2:
            return "Single book available; consensus cannot be determined."
        
        parts = []
        if spread_range > 0.1:
            parts.append(f"Spread differs by {spread_range:.1f} points across books")
        if total_range > 0.1:
            parts.append(f"totals vary by {total_range:.1f}")
        
        if parts:
            return "; ".join(parts) + "."
        else:
            return "Books are in consensus on spread and total."
    
    @staticmethod
    def _determine_flag(
        *,
        spread_variance: str,
        total_variance: str,
        model_probs: Dict[str, Any],
        odds_snapshot: Dict[str, Any],
    ) -> str:
        """Determine market flag: consensus, volatile, or sharp_vs_public."""
        # High variance in either spread or total = volatile
        if spread_variance == "high" or total_variance == "high":
            return "volatile"
        
        # Check if model edge opposes consensus
        home_model_prob = float(model_probs.get("home_win_prob", 0.5))
        home_market_prob = float(odds_snapshot.get("home_implied_prob", 0.5))
        
        # Normalize market prob
        away_market_prob = float(odds_snapshot.get("away_implied_prob", 0.5))
        market_total = home_market_prob + away_market_prob
        if market_total > 0:
            home_market_prob = home_market_prob / market_total
        
        # Model edge > 5% difference from market
        model_edge = abs(home_model_prob - home_market_prob)
        
        # If model disagrees significantly and variance is low = sharp vs public
        if model_edge > 0.05 and spread_variance == "low" and total_variance == "low":
            return "sharp_vs_public"
        
        return "consensus"
    
    @staticmethod
    def _detect_sharp_money(
        *,
        flag: str,
        model_probs: Dict[str, Any],
        odds_snapshot: Dict[str, Any],
        markets: Optional[List[Market]] = None,
    ) -> Dict[str, Any]:
        """Detect sharp money indicators from line movement and book splits."""
        sharp_signals = []
        confidence = "low"
        
        # Signal 1: Model edge > 5% and low variance = sharp vs public
        if flag == "sharp_vs_public":
            home_model_prob = float(model_probs.get("home_win_prob", 0.5))
            home_market_prob = float(odds_snapshot.get("home_implied_prob", 0.5))
            away_market_prob = float(odds_snapshot.get("away_implied_prob", 0.5))
            market_total = home_market_prob + away_market_prob
            if market_total > 0:
                home_market_prob = home_market_prob / market_total
            
            model_edge = abs(home_model_prob - home_market_prob)
            if model_edge > 0.05:
                sharp_signals.append("Model shows significant edge over market consensus")
                confidence = "medium"
        
        # Signal 2: Line movement toward model = sharp money
        if flag == "volatile":
            sharp_signals.append("Line movement suggests sharp action")
            confidence = "medium"
        
        # Signal 3: Book splits on key numbers = sharp shopping
        if markets:
            spread_books = [m for m in markets if m.market_type == "spreads"]
            if len(spread_books) >= 3:
                sharp_signals.append("Multiple books offer line shopping opportunities")
        
        return {
            "has_sharp_signals": len(sharp_signals) > 0,
            "signals": sharp_signals,
            "confidence": confidence,
            "summary": "; ".join(sharp_signals) if sharp_signals else "No clear sharp money signals detected",
        }
    
    @staticmethod
    def _detect_sharp_money(
        *,
        flag: str,
        model_probs: Dict[str, Any],
        odds_snapshot: Dict[str, Any],
        markets: Optional[List[Market]] = None,
    ) -> Dict[str, Any]:
        """Detect sharp money indicators from line movement and book splits."""
        sharp_signals = []
        confidence = "low"
        
        # Signal 1: Model edge > 5% and low variance = sharp vs public
        if flag == "sharp_vs_public":
            home_model_prob = float(model_probs.get("home_win_prob", 0.5))
            home_market_prob = float(odds_snapshot.get("home_implied_prob", 0.5))
            away_market_prob = float(odds_snapshot.get("away_implied_prob", 0.5))
            market_total = home_market_prob + away_market_prob
            if market_total > 0:
                home_market_prob = home_market_prob / market_total
            
            model_edge = abs(home_model_prob - home_market_prob)
            if model_edge > 0.05:
                sharp_signals.append("Model shows significant edge over market consensus")
                confidence = "medium"
        
        # Signal 2: Line movement toward model = sharp money
        # (This would require odds history - simplified for now)
        if flag == "volatile":
            sharp_signals.append("Line movement suggests sharp action")
            confidence = "medium"
        
        # Signal 3: Book splits on key numbers = sharp shopping
        if markets:
            spread_books = [m for m in markets if m.market_type == "spreads"]
            if len(spread_books) >= 3:
                # Multiple books with different lines = sharp shopping opportunity
                sharp_signals.append("Multiple books offer line shopping opportunities")
                if confidence == "low":
                    confidence = "low"
        
        return {
            "has_sharp_signals": len(sharp_signals) > 0,
            "signals": sharp_signals,
            "confidence": confidence,
            "summary": "; ".join(sharp_signals) if sharp_signals else "No clear sharp money signals detected",
        }
