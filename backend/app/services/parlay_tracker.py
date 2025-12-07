"""Service for tracking parlay results and performance"""

from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from decimal import Decimal

from app.models.parlay import Parlay
from app.models.parlay_results import ParlayResult
from app.models.game import Game
from app.models.game_results import GameResult


class ParlayTrackerService:
    """Service for tracking parlay outcomes and calculating performance metrics"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def resolve_parlay_result(
        self,
        parlay_id: str,
        leg_results: List[Dict]
    ) -> ParlayResult:
        """
        Resolve a parlay result based on actual game outcomes
        
        Args:
            parlay_id: ID of the parlay to resolve
            leg_results: List of dicts with leg outcomes
                Format: [{"leg_id": "...", "hit": True/False, ...}]
        
        Returns:
            Updated ParlayResult
        """
        # Get parlay
        result = await self.db.execute(
            select(Parlay).where(Parlay.id == parlay_id)
        )
        parlay = result.scalar_one_or_none()
        
        if not parlay:
            raise ValueError(f"Parlay {parlay_id} not found")
        
        # Get or create parlay result
        result = await self.db.execute(
            select(ParlayResult).where(ParlayResult.parlay_id == parlay_id)
        )
        parlay_result = result.scalar_one_or_none()
        
        if not parlay_result:
            parlay_result = ParlayResult(
                parlay_id=parlay_id,
                num_legs=parlay.num_legs,
                risk_profile=parlay.risk_profile,
                predicted_probability=float(parlay.parlay_hit_prob),
                predicted_confidence=0.0,  # Will calculate from legs
            )
            self.db.add(parlay_result)
        
        # Calculate results
        legs_hit = sum(1 for leg in leg_results if leg.get("hit", False))
        legs_missed = len(leg_results) - legs_hit
        hit = legs_hit == parlay.num_legs  # All legs must hit for parlay to win
        
        # Update parlay result
        parlay_result.hit = hit
        parlay_result.legs_hit = legs_hit
        parlay_result.legs_missed = legs_missed
        parlay_result.leg_results = leg_results
        parlay_result.resolved_at = datetime.now(timezone.utc)
        
        # Calculate actual probability (based on individual leg outcomes)
        if leg_results:
            actual_prob = 1.0
            for leg in leg_results:
                # If leg hit, use its probability; if missed, use (1 - probability)
                leg_prob = leg.get("probability", 0.5)
                if leg.get("hit", False):
                    actual_prob *= leg_prob
                else:
                    actual_prob *= (1 - leg_prob)
            parlay_result.actual_probability = actual_prob
        
        # Calculate calibration error
        parlay_result.calibration_error = abs(
            parlay_result.predicted_probability - (parlay_result.actual_probability or 0.0)
        )
        
        await self.db.commit()
        await self.db.refresh(parlay_result)
        
        return parlay_result
    
    async def get_parlay_performance_stats(
        self,
        risk_profile: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Get performance statistics for resolved parlays
        
        Args:
            risk_profile: Filter by risk profile (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            user_id: Filter by user ID (optional, but required for authenticated endpoints)
        
        Returns:
            Dictionary with performance metrics
        """
        # Join ParlayResult with Parlay to filter by user_id
        query = (
            select(ParlayResult)
            .join(Parlay, ParlayResult.parlay_id == Parlay.id)
            .where(ParlayResult.hit.isnot(None))
        )
        
        if user_id:
            query = query.where(Parlay.user_id == user_id)
        if risk_profile:
            query = query.where(ParlayResult.risk_profile == risk_profile)
        if start_date:
            query = query.where(ParlayResult.created_at >= start_date)
        if end_date:
            query = query.where(ParlayResult.created_at <= end_date)
        
        result = await self.db.execute(query)
        results = result.scalars().all()
        
        if not results:
            return {
                "total_parlays": 0,
                "hits": 0,
                "misses": 0,
                "hit_rate": 0.0,
                "avg_predicted_prob": 0.0,
                "avg_actual_prob": 0.0,
                "avg_calibration_error": 0.0,
            }
        
        total = len(results)
        hits = sum(1 for r in results if r.hit)
        misses = total - hits
        
        avg_predicted = sum(r.predicted_probability for r in results) / total
        avg_actual = sum(r.actual_probability or 0.0 for r in results) / total
        avg_calibration = sum(r.calibration_error or 0.0 for r in results) / total
        
        return {
            "total_parlays": total,
            "hits": hits,
            "misses": misses,
            "hit_rate": hits / total if total > 0 else 0.0,
            "avg_predicted_prob": avg_predicted,
            "avg_actual_prob": avg_actual,
            "avg_calibration_error": avg_calibration,
        }
    
    async def get_user_parlay_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Parlay]:
        """Get a user's parlay history"""
        result = await self.db.execute(
            select(Parlay)
            .where(Parlay.user_id == user_id)
            .order_by(Parlay.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def auto_resolve_parlays(self):
        """
        Automatically resolve parlays based on game results
        This should be called periodically via background job
        """
        # Get all unresolved parlays with games that have finished
        # This is a simplified version - in production, you'd want more sophisticated matching
        result = await self.db.execute(
            select(Parlay)
            .where(Parlay.created_at < datetime.now(timezone.utc) - timedelta(hours=4))
            .limit(100)  # Process in batches
        )
        parlays = result.scalars().all()
        
        resolved_count = 0
        for parlay in parlays:
            # Check if all games in parlay have results
            # This is simplified - you'd need to match legs to games
            # For now, we'll just mark as needing manual resolution
            pass
        
        return resolved_count

