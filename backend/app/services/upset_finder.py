"""
Gorilla Upset Finder

Identifies high-value underdog plays ("Gorilla Upsets") where:
- Model probability significantly exceeds implied probability (edge > threshold)
- Underdog has positive expected value
- Risk is tiered (low, medium, high) for different parlay strategies

These upset candidates can boost parlay payouts while maintaining positive EV.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.model_config import UPSET_CONFIG
from app.services.probability_engine import get_probability_engine

logger = logging.getLogger(__name__)


@dataclass
class UpsetCandidate:
    """
    Represents a potential upset pick identified by the model.
    
    Attributes:
        team: The underdog team
        opponent: The favored team
        sport: Sport code
        market_type: h2h, spread, or total
        model_prob: Model's predicted probability
        implied_prob: Market-implied probability
        edge: Model advantage (model_prob - implied_prob)
        odds: American odds
        risk_tier: low, medium, or high
        confidence_score: Model's confidence (0-100)
        ev: Expected value
        game_time: Scheduled game time
        reasoning: Brief explanation of why this is an upset candidate
    """
    team: str
    opponent: str
    sport: str
    market_type: str
    model_prob: float
    implied_prob: float
    edge: float
    odds: int
    risk_tier: str
    confidence_score: float
    ev: float
    game_id: Optional[str] = None
    game_time: Optional[datetime] = None
    reasoning: str = ""
    
    @property
    def plus_money(self) -> bool:
        """Check if this is a plus-money underdog"""
        return self.odds > 0
    
    @property
    def edge_percentage(self) -> float:
        """Edge as a percentage"""
        return self.edge * 100
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "team": self.team,
            "opponent": self.opponent,
            "sport": self.sport,
            "market_type": self.market_type,
            "model_prob": round(self.model_prob, 4),
            "implied_prob": round(self.implied_prob, 4),
            "edge": round(self.edge, 4),
            "edge_percentage": round(self.edge_percentage, 2),
            "odds": self.odds,
            "risk_tier": self.risk_tier,
            "confidence_score": round(self.confidence_score, 1),
            "ev": round(self.ev, 4),
            "plus_money": self.plus_money,
            "game_id": self.game_id,
            "game_time": self.game_time.isoformat() if self.game_time else None,
            "reasoning": self.reasoning,
        }


class UpsetFinderService:
    """
    Gorilla Upset Finder - identifies high-value underdog plays.
    
    Strategy:
    1. Find all underdog legs (implied prob < 50%, typically plus money)
    2. Filter for positive edge (model_prob > implied_prob)
    3. Calculate EV for each candidate
    4. Tier by risk level based on probability and odds
    5. Return ranked list with reasoning
    """
    
    def __init__(self, db: AsyncSession, sport: str = "NFL"):
        self.db = db
        self.sport = sport.upper()
        self.prob_engine = get_probability_engine(db, sport)
        self.config = UPSET_CONFIG
    
    async def find_upsets(
        self,
        min_edge: float = None,
        max_results: int = 20,
        risk_tier: Optional[str] = None,
        week: Optional[int] = None,
    ) -> List[UpsetCandidate]:
        """
        Find upset candidates from available betting markets.
        
        Args:
            min_edge: Minimum edge threshold (default from config)
            max_results: Maximum candidates to return
            risk_tier: Filter by risk tier (low, medium, high)
            week: NFL week number filter
        
        Returns:
            List of UpsetCandidate objects sorted by EV
        """
        min_edge = min_edge or self.config["min_edge_threshold"]
        
        logger.info(f"[UpsetFinder] Searching for upsets in {self.sport} with min_edge={min_edge}")
        
        # Get all candidate legs from probability engine
        candidates = await self.prob_engine.get_candidate_legs(
            sport=self.sport,
            min_confidence=0,  # We'll filter ourselves
            max_legs=500,
            week=week,
        )
        
        logger.info(f"[UpsetFinder] Found {len(candidates)} total candidates")
        
        # Filter and process candidates
        upsets = []
        
        for leg in candidates:
            # Check if this is an underdog play
            implied_prob = leg.get("implied_prob", 0.5)
            model_prob = leg.get("adjusted_prob", leg.get("model_prob", implied_prob))
            odds = leg.get("odds", 0)
            
            # Skip if not an underdog (implied prob > 50% or minus money)
            if implied_prob > 0.50 or odds < 0:
                continue
            
            # Calculate edge
            edge = model_prob - implied_prob
            
            # Skip if edge below threshold
            if edge < min_edge:
                continue
            
            # Calculate EV
            ev = self._calculate_ev(model_prob, odds)
            
            # Skip negative EV
            if ev < 0:
                continue
            
            # Determine risk tier
            tier = self._determine_risk_tier(model_prob, odds)
            
            # Apply risk tier filter if specified
            if risk_tier and tier != risk_tier.lower():
                continue
            
            # Build reasoning
            reasoning = self._generate_reasoning(leg, model_prob, implied_prob, edge, tier)
            
            # Parse teams from leg data
            outcome = leg.get("outcome", "")
            home_team = leg.get("home_team", "")
            away_team = leg.get("away_team", "")
            
            # Determine which team is the upset candidate
            is_home_pick = "home" in outcome.lower()
            team = home_team if is_home_pick else away_team
            opponent = away_team if is_home_pick else home_team
            
            # Parse game time
            game_time = leg.get("game_time") or leg.get("commence_time")
            if isinstance(game_time, str):
                try:
                    game_time = datetime.fromisoformat(game_time.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    game_time = None
            
            upset = UpsetCandidate(
                team=team,
                opponent=opponent,
                sport=self.sport,
                market_type=leg.get("market_type", "h2h"),
                model_prob=model_prob,
                implied_prob=implied_prob,
                edge=edge,
                odds=int(odds) if odds else 100,
                risk_tier=tier,
                confidence_score=leg.get("confidence_score", 50.0),
                ev=ev,
                game_id=str(leg.get("game_id", "")),
                game_time=game_time,
                reasoning=reasoning,
            )
            
            upsets.append(upset)
        
        # Sort by EV (highest first)
        upsets.sort(key=lambda x: x.ev, reverse=True)
        
        logger.info(f"[UpsetFinder] Found {len(upsets)} upset candidates")
        
        return upsets[:max_results]
    
    def _calculate_ev(self, model_prob: float, odds: int) -> float:
        """
        Calculate expected value for a bet.
        
        EV = (model_prob * payout) - ((1 - model_prob) * stake)
        
        For $100 stake:
        - Plus money: payout = odds (e.g., +150 pays $150)
        - Minus money: payout = 100 / |odds| * 100
        """
        if odds > 0:
            payout = odds
        else:
            payout = (100 / abs(odds)) * 100
        
        # EV as percentage of stake
        ev = (model_prob * payout / 100) - (1 - model_prob)
        
        return ev
    
    def _determine_risk_tier(self, model_prob: float, odds: int) -> str:
        """
        Determine risk tier based on probability and odds.
        
        - Low: Higher probability underdogs (45-50% prob, lower plus money)
        - Medium: Moderate underdogs (35-45% prob, medium plus money)
        - High: Long shot underdogs (<35% prob, high plus money)
        """
        thresholds = self.config["risk_tier_thresholds"]
        
        for tier_name in ["low", "medium", "high"]:
            tier = thresholds[tier_name]
            if model_prob >= tier["min_prob"] and odds <= tier["max_odds"]:
                return tier_name
        
        return "high"  # Default to high risk
    
    def _generate_reasoning(
        self,
        leg: Dict,
        model_prob: float,
        implied_prob: float,
        edge: float,
        tier: str
    ) -> str:
        """Generate a brief explanation of why this is an upset candidate"""
        parts = []
        
        # Edge explanation
        edge_pct = edge * 100
        parts.append(f"Model sees {edge_pct:.1f}% edge over the market")
        
        # Probability comparison
        model_pct = model_prob * 100
        implied_pct = implied_prob * 100
        parts.append(f"({model_pct:.0f}% vs {implied_pct:.0f}% implied)")
        
        # Risk tier context
        if tier == "low":
            parts.append("Lower-risk upset candidate")
        elif tier == "medium":
            parts.append("Moderate-risk value play")
        else:
            parts.append("High-risk longshot with upside")
        
        # Confidence note
        confidence = leg.get("confidence_score", 50)
        if confidence >= 70:
            parts.append("High model confidence")
        elif confidence >= 55:
            parts.append("Solid model confidence")
        
        return ". ".join(parts) + "."
    
    async def get_upsets_for_parlay(
        self,
        parlay_type: str = "balanced",
        num_upsets: int = None,
        week: Optional[int] = None,
    ) -> List[UpsetCandidate]:
        """
        Get upset candidates specifically for parlay building.
        
        Args:
            parlay_type: safe, balanced, or degen
            num_upsets: Max upsets to include (default from config)
            week: NFL week filter
        
        Returns:
            List of upset candidates appropriate for the parlay type
        """
        max_upsets = self.config["max_upsets_by_parlay_type"]
        num_upsets = num_upsets or max_upsets.get(parlay_type.lower(), 3)
        
        # Adjust edge threshold by parlay type
        if parlay_type.lower() == "safe":
            min_edge = 0.08  # Higher edge requirement for safe parlays
            risk_tier = "low"
        elif parlay_type.lower() == "balanced":
            min_edge = 0.05
            risk_tier = None  # Allow all tiers
        else:  # degen
            min_edge = 0.03  # Lower threshold, more upsets
            risk_tier = None
        
        # Find candidates
        upsets = await self.find_upsets(
            min_edge=min_edge,
            max_results=num_upsets * 2,  # Get extras for filtering
            risk_tier=risk_tier,
            week=week,
        )
        
        # For safe parlays, prefer low-risk candidates
        if parlay_type.lower() == "safe":
            upsets = [u for u in upsets if u.risk_tier == "low"]
        
        # For degen parlays, sort by potential payout (higher odds)
        if parlay_type.lower() == "degen":
            upsets.sort(key=lambda x: x.odds, reverse=True)
        
        return upsets[:num_upsets]
    
    async def analyze_game_upset_potential(
        self,
        game_id: str,
        home_team: str,
        away_team: str,
    ) -> Dict:
        """
        Analyze a specific game for upset potential.
        
        Returns detailed analysis of both teams' upset potential.
        """
        # Get candidate legs for this game
        candidates = await self.prob_engine.get_candidate_legs(
            sport=self.sport,
            min_confidence=0,
            max_legs=100,
        )
        
        # Filter for this game
        game_legs = [
            leg for leg in candidates
            if (leg.get("home_team", "").lower() in home_team.lower() or
                leg.get("away_team", "").lower() in away_team.lower())
        ]
        
        analysis = {
            "game_id": game_id,
            "home_team": home_team,
            "away_team": away_team,
            "upset_candidates": [],
            "summary": "",
        }
        
        for leg in game_legs:
            implied_prob = leg.get("implied_prob", 0.5)
            model_prob = leg.get("adjusted_prob", implied_prob)
            odds = leg.get("odds", 0)
            
            # Only analyze underdog side
            if implied_prob > 0.50:
                continue
            
            edge = model_prob - implied_prob
            
            if edge > self.config["min_edge_threshold"]:
                ev = self._calculate_ev(model_prob, odds)
                tier = self._determine_risk_tier(model_prob, odds)
                
                analysis["upset_candidates"].append({
                    "side": leg.get("outcome", ""),
                    "market_type": leg.get("market_type", "h2h"),
                    "model_prob": round(model_prob, 3),
                    "implied_prob": round(implied_prob, 3),
                    "edge": round(edge, 3),
                    "odds": odds,
                    "ev": round(ev, 3),
                    "risk_tier": tier,
                })
        
        # Generate summary
        if analysis["upset_candidates"]:
            best = max(analysis["upset_candidates"], key=lambda x: x["ev"])
            analysis["summary"] = (
                f"Best upset potential: {best['side']} at {'+' if best['odds'] > 0 else ''}{best['odds']} "
                f"with {best['edge'] * 100:.1f}% edge and {best['ev'] * 100:.1f}% EV"
            )
        else:
            analysis["summary"] = "No significant upset potential identified"
        
        return analysis


# Factory function
def get_upset_finder(db: AsyncSession, sport: str = "NFL") -> UpsetFinderService:
    """Get an instance of the upset finder service"""
    return UpsetFinderService(db, sport)

