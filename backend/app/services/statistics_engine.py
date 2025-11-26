"""Statistical analysis engine for parlay performance"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import numpy as np

from app.models.parlay_results import ParlayResult
from app.models.parlay import Parlay


class StatisticsEngine:
    """Engine for statistical analysis of parlay performance"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_performance_trends(
        self,
        days: int = 30,
        risk_profile: Optional[str] = None
    ) -> Dict:
        """
        Analyze performance trends over time
        
        Returns:
            Dictionary with trend analysis
        """
        start_date = datetime.now() - timedelta(days=days)
        
        query = select(ParlayResult).where(
            ParlayResult.created_at >= start_date
        )
        
        if risk_profile:
            query = query.where(ParlayResult.risk_profile == risk_profile)
        
        result = await self.db.execute(query)
        results = result.scalars().all()
        
        if not results:
            return {
                "total_parlays": 0,
                "trends": []
            }
        
        # Group by date
        daily_stats = {}
        for r in results:
            date_key = r.created_at.date() if r.created_at else datetime.now().date()
            if date_key not in daily_stats:
                daily_stats[date_key] = {"total": 0, "hits": 0, "misses": 0}
            
            daily_stats[date_key]["total"] += 1
            if r.hit is True:
                daily_stats[date_key]["hits"] += 1
            elif r.hit is False:
                daily_stats[date_key]["misses"] += 1
        
        # Calculate trends
        trends = []
        for date in sorted(daily_stats.keys()):
            stats = daily_stats[date]
            hit_rate = stats["hits"] / stats["total"] if stats["total"] > 0 else 0.0
            trends.append({
                "date": date.isoformat(),
                "total": stats["total"],
                "hits": stats["hits"],
                "misses": stats["misses"],
                "hit_rate": hit_rate
            })
        
        # Calculate overall stats
        total_hits = sum(1 for r in results if r.hit is True)
        total_misses = sum(1 for r in results if r.hit is False)
        overall_hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0.0
        
        return {
            "total_parlays": len(results),
            "overall_hit_rate": overall_hit_rate,
            "trends": trends,
            "period_days": days
        }
    
    async def get_risk_profile_comparison(self) -> Dict:
        """Compare performance across different risk profiles"""
        result = await self.db.execute(
            select(ParlayResult).where(ParlayResult.hit.isnot(None))
        )
        results = result.scalars().all()
        
        profiles = {}
        for r in results:
            if r.risk_profile not in profiles:
                profiles[r.risk_profile] = {
                    "total": 0,
                    "hits": 0,
                    "misses": 0,
                    "predicted_probs": [],
                    "actual_probs": []
                }
            
            profiles[r.risk_profile]["total"] += 1
            if r.hit is True:
                profiles[r.risk_profile]["hits"] += 1
            elif r.hit is False:
                profiles[r.risk_profile]["misses"] += 1
            
            profiles[r.risk_profile]["predicted_probs"].append(r.predicted_probability)
            if r.actual_probability:
                profiles[r.risk_profile]["actual_probs"].append(r.actual_probability)
        
        comparison = {}
        for profile, stats in profiles.items():
            hit_rate = stats["hits"] / stats["total"] if stats["total"] > 0 else 0.0
            avg_predicted = np.mean(stats["predicted_probs"]) if stats["predicted_probs"] else 0.0
            avg_actual = np.mean(stats["actual_probs"]) if stats["actual_probs"] else 0.0
            
            comparison[profile] = {
                "total": stats["total"],
                "hits": stats["hits"],
                "misses": stats["misses"],
                "hit_rate": float(hit_rate),
                "avg_predicted_prob": float(avg_predicted),
                "avg_actual_prob": float(avg_actual),
                "calibration_error": float(abs(avg_predicted - avg_actual)) if avg_actual > 0 else 0.0
            }
        
        return comparison
    
    async def get_leg_analysis(self) -> Dict:
        """Analyze individual leg performance"""
        result = await self.db.execute(
            select(ParlayResult)
            .where(ParlayResult.leg_results.isnot(None))
        )
        results = result.scalars().all()
        
        leg_stats = {
            "total_legs": 0,
            "legs_hit": 0,
            "legs_missed": 0,
            "by_market_type": {},
            "by_confidence_range": {}
        }
        
        for r in results:
            if not r.leg_results:
                continue
            
            for leg in r.leg_results:
                leg_stats["total_legs"] += 1
                if leg.get("hit", False):
                    leg_stats["legs_hit"] += 1
                else:
                    leg_stats["legs_missed"] += 1
                
                # Group by market type
                market_type = leg.get("market_type", "unknown")
                if market_type not in leg_stats["by_market_type"]:
                    leg_stats["by_market_type"][market_type] = {"total": 0, "hits": 0}
                leg_stats["by_market_type"][market_type]["total"] += 1
                if leg.get("hit", False):
                    leg_stats["by_market_type"][market_type]["hits"] += 1
                
                # Group by confidence range
                confidence = leg.get("confidence", 50.0)
                if confidence < 50:
                    range_key = "0-50"
                elif confidence < 70:
                    range_key = "50-70"
                else:
                    range_key = "70-100"
                
                if range_key not in leg_stats["by_confidence_range"]:
                    leg_stats["by_confidence_range"][range_key] = {"total": 0, "hits": 0}
                leg_stats["by_confidence_range"][range_key]["total"] += 1
                if leg.get("hit", False):
                    leg_stats["by_confidence_range"][range_key]["hits"] += 1
        
        # Calculate hit rates
        leg_stats["overall_hit_rate"] = (
            leg_stats["legs_hit"] / leg_stats["total_legs"]
            if leg_stats["total_legs"] > 0 else 0.0
        )
        
        for market_type in leg_stats["by_market_type"]:
            stats = leg_stats["by_market_type"][market_type]
            stats["hit_rate"] = stats["hits"] / stats["total"] if stats["total"] > 0 else 0.0
        
        for range_key in leg_stats["by_confidence_range"]:
            stats = leg_stats["by_confidence_range"][range_key]
            stats["hit_rate"] = stats["hits"] / stats["total"] if stats["total"] > 0 else 0.0
        
        return leg_stats
    
    async def get_parlay_size_analysis(self) -> Dict:
        """Analyze performance by parlay size (number of legs)"""
        result = await self.db.execute(
            select(ParlayResult).where(ParlayResult.hit.isnot(None))
        )
        results = result.scalars().all()
        
        by_size = {}
        for r in results:
            size = r.num_legs
            if size not in by_size:
                by_size[size] = {"total": 0, "hits": 0, "misses": 0}
            
            by_size[size]["total"] += 1
            if r.hit is True:
                by_size[size]["hits"] += 1
            elif r.hit is False:
                by_size[size]["misses"] += 1
        
        analysis = {}
        for size in sorted(by_size.keys()):
            stats = by_size[size]
            hit_rate = stats["hits"] / stats["total"] if stats["total"] > 0 else 0.0
            analysis[size] = {
                "total": stats["total"],
                "hits": stats["hits"],
                "misses": stats["misses"],
                "hit_rate": float(hit_rate)
            }
        
        return analysis

