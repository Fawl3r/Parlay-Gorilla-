"""Advanced parlay types: same-game parlays, round robins, teasers"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from itertools import combinations
import math

from app.services.probability_engine import get_probability_engine


class ParlayVariantService:
    """Service for generating advanced parlay types"""
    
    def __init__(self, db: AsyncSession, sport: str = "NFL"):
        self.db = db
        self.sport = sport
        self.prob_engine = get_probability_engine(db, sport)
    
    async def build_same_game_parlay(
        self,
        game_id: str,
        num_legs: int,
        market_types: Optional[List[str]] = None
    ) -> Dict:
        """
        Build a parlay using multiple markets from the same game
        
        Args:
            game_id: Game ID to build parlay from
            num_legs: Number of legs (markets) to include
            market_types: Preferred market types (h2h, spreads, totals)
        
        Returns:
            Dictionary with same-game parlay data
        """
        # Get all markets for this game
        from app.models.game import Game
        from app.models.market import Market
        from app.models.odds import Odds
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        result = await self.db.execute(
            select(Game)
            .where(Game.id == game_id)
            .options(selectinload(Game.markets).selectinload(Market.odds))
        )
        game = result.scalar_one_or_none()
        
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        # Filter markets by type if specified
        markets = game.markets
        if market_types:
            markets = [m for m in markets if m.market_type in market_types]
        
        if len(markets) < num_legs:
            raise ValueError(f"Not enough markets in game. Found {len(markets)}, need {num_legs}")
        
        # Get candidate legs from this game
        candidate_legs = []
        for market in markets[:num_legs * 2]:  # Get more candidates
            for odds in market.odds:
                leg_prob = await self.prob_engine.calculate_leg_probability_from_odds(
                    odds_obj=odds,
                    market_id=str(market.id),
                    outcome=odds.outcome,
                    home_team=game.home_team,
                    away_team=game.away_team,
                    game_start_time=game.start_time,
                    market_type=market.market_type
                )
                
                if leg_prob.get("confidence_score", 0) >= 40:  # Lower threshold for same-game
                    candidate_legs.append(leg_prob)
        
        # Select best legs
        candidate_legs.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
        selected_legs = candidate_legs[:num_legs]
        
        if len(selected_legs) < num_legs:
            raise ValueError(f"Not enough valid legs. Found {len(selected_legs)}, need {num_legs}")
        
        # Calculate parlay probability
        leg_probs = [leg["adjusted_prob"] for leg in selected_legs]
        parlay_prob = self.prob_engine.calculate_parlay_probability(leg_probs)
        
        # Build legs data
        legs_data = []
        for leg in selected_legs:
            legs_data.append({
                "market_id": str(leg.get("market_id", "")),
                "outcome": str(leg.get("outcome", "")),
                "game": f"{game.away_team} @ {game.home_team}",
                "home_team": game.home_team,
                "away_team": game.away_team,
                "market_type": str(leg.get("market_type", "")),
                "odds": str(leg.get("odds", "")),
                "probability": float(leg.get("adjusted_prob", 0.0)),
                "confidence": float(leg.get("confidence_score", 0.0)),
            })
        
        return {
            "legs": legs_data,
            "num_legs": num_legs,
            "parlay_hit_prob": float(parlay_prob),
            "parlay_type": "same_game",
            "game_id": str(game_id),
            "overall_confidence": float(sum(leg.get("confidence_score", 0.0) for leg in selected_legs) / num_legs),
        }
    
    async def build_round_robin(
        self,
        num_legs: int,
        risk_profile: str = "balanced"
    ) -> Dict:
        """
        Build a round robin parlay (all possible combinations)
        
        For example, 3-leg round robin creates:
        - 3 two-leg parlays
        - 1 three-leg parlay
        
        Args:
            num_legs: Number of legs to combine
            risk_profile: Risk profile for leg selection
        
        Returns:
            Dictionary with round robin data
        """
        # Get candidate legs
        from app.services.parlay_builder import ParlayBuilderService
        builder = ParlayBuilderService(self.db)
        
        min_confidence = builder._get_min_confidence(risk_profile)
        candidates = await self.prob_engine.get_candidate_legs(
            min_confidence=min_confidence,
            max_legs=200
        )
        
        if len(candidates) < num_legs:
            raise ValueError(f"Not enough candidates. Found {len(candidates)}, need {num_legs}")
        
        # Select legs
        selected_legs = await builder._select_legs_optimized(candidates, num_legs, risk_profile)
        
        # Generate all combinations (2-leg, 3-leg, ..., num_legs-leg)
        round_robin_parlays = []
        
        for r in range(2, num_legs + 1):
            for combo in combinations(selected_legs, r):
                leg_probs = [leg["adjusted_prob"] for leg in combo]
                parlay_prob = self.prob_engine.calculate_parlay_probability(leg_probs)
                
                round_robin_parlays.append({
                    "legs": [{
                        "market_id": str(leg.get("market_id", "")),
                        "outcome": str(leg.get("outcome", "")),
                        "game": str(leg.get("game", "")),
                        "market_type": str(leg.get("market_type", "")),
                        "odds": str(leg.get("odds", "")),
                        "probability": float(leg.get("adjusted_prob", 0.0)),
                        "confidence": float(leg.get("confidence_score", 0.0)),
                    } for leg in combo],
                    "num_legs": r,
                    "parlay_hit_prob": float(parlay_prob),
                })
        
        total_parlays = len(round_robin_parlays)
        total_cost = total_parlays  # Assuming $1 per parlay
        
        return {
            "parlay_type": "round_robin",
            "base_legs": num_legs,
            "total_parlays": total_parlays,
            "parlays": round_robin_parlays,
            "estimated_cost": total_cost,
        }
    
    async def build_teaser(
        self,
        num_legs: int,
        points_adjustment: float = 6.0,  # Points to add/subtract
        risk_profile: str = "balanced"
    ) -> Dict:
        """
        Build a teaser parlay (adjusted spreads/totals)
        
        Args:
            num_legs: Number of legs
            points_adjustment: Points to adjust (typically 6, 6.5, or 10)
            risk_profile: Risk profile
        
        Returns:
            Dictionary with teaser parlay data
        """
        # Get candidate legs (prefer spreads and totals)
        from app.services.parlay_builder import ParlayBuilderService
        builder = ParlayBuilderService(self.db)
        
        min_confidence = builder._get_min_confidence(risk_profile)
        candidates = await self.prob_engine.get_candidate_legs(
            min_confidence=min_confidence,
            max_legs=200
        )
        
        # Filter for spreads and totals only
        spread_totals = [c for c in candidates if c.get("market_type") in ["spreads", "totals"]]
        
        if len(spread_totals) < num_legs:
            raise ValueError(f"Not enough spread/total markets. Found {len(spread_totals)}, need {num_legs}")
        
        # Select legs
        selected_legs = await builder._select_legs_optimized(spread_totals, num_legs, risk_profile)
        
        # Adjust probabilities based on points adjustment
        # More points = better probability but worse odds
        teaser_legs = []
        for leg in selected_legs:
            original_prob = leg.get("adjusted_prob", 0.5)
            # Simple adjustment: add 10-15% probability boost for teaser
            # In production, use more sophisticated calculation
            teaser_prob = min(0.95, original_prob + (points_adjustment / 10.0) * 0.1)
            
            teaser_legs.append({
                "market_id": str(leg.get("market_id", "")),
                "outcome": str(leg.get("outcome", "")),
                "game": str(leg.get("game", "")),
                "market_type": str(leg.get("market_type", "")),
                "odds": str(leg.get("odds", "")),
                "original_probability": float(original_prob),
                "teaser_probability": float(teaser_prob),
                "probability": float(teaser_prob),  # Use teaser prob for parlay calc
                "points_adjustment": points_adjustment,
                "confidence": float(leg.get("confidence_score", 0.0)),
            })
        
        # Calculate parlay probability
        leg_probs = [leg["probability"] for leg in teaser_legs]
        parlay_prob = self.prob_engine.calculate_parlay_probability(leg_probs)
        
        return {
            "legs": teaser_legs,
            "num_legs": num_legs,
            "parlay_hit_prob": float(parlay_prob),
            "parlay_type": "teaser",
            "points_adjustment": points_adjustment,
            "overall_confidence": float(sum(leg.get("confidence_score", 0.0) for leg in selected_legs) / num_legs),
        }

