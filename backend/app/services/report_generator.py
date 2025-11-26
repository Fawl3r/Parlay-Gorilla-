"""Service for generating reports and exports"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import csv
import io

from app.models.user import User
from app.models.parlay import Parlay
from app.models.parlay_results import ParlayResult
from app.services.parlay_tracker import ParlayTrackerService
from app.services.statistics_engine import StatisticsEngine


class ReportGeneratorService:
    """Service for generating reports and exports"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tracker = ParlayTrackerService(db)
        self.stats = StatisticsEngine(db)
    
    async def generate_user_report_csv(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Generate CSV report of user's parlays
        
        Returns:
            CSV string
        """
        query = select(Parlay).where(Parlay.user_id == user_id)
        
        if start_date:
            query = query.where(Parlay.created_at >= start_date)
        if end_date:
            query = query.where(Parlay.created_at <= end_date)
        
        query = query.order_by(Parlay.created_at.desc())
        
        result = await self.db.execute(query)
        parlays = result.scalars().all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Parlay ID",
            "Created At",
            "Number of Legs",
            "Risk Profile",
            "Hit Probability",
            "AI Summary",
            "Status"
        ])
        
        # Data rows
        for parlay in parlays:
            # Check if resolved
            result = await self.db.execute(
                select(ParlayResult).where(ParlayResult.parlay_id == str(parlay.id))
            )
            parlay_result = result.scalar_one_or_none()
            
            status = "Pending"
            if parlay_result:
                if parlay_result.hit is True:
                    status = "Won"
                elif parlay_result.hit is False:
                    status = "Lost"
            
            writer.writerow([
                str(parlay.id),
                parlay.created_at.isoformat() if parlay.created_at else "",
                parlay.num_legs,
                parlay.risk_profile,
                float(parlay.parlay_hit_prob),
                parlay.ai_summary or "",
                status
            ])
        
        return output.getvalue()
    
    async def generate_performance_summary(
        self,
        user_id: str
    ) -> Dict:
        """Generate performance summary for a user"""
        # Get user's parlays
        result = await self.db.execute(
            select(Parlay).where(Parlay.user_id == user_id)
        )
        parlays = result.scalars().all()
        
        # Get resolved results
        parlay_ids = [str(p.id) for p in parlays]
        if not parlay_ids:
            return {
                "total_parlays": 0,
                "resolved": 0,
                "won": 0,
                "lost": 0,
                "win_rate": 0.0
            }
        
        result = await self.db.execute(
            select(ParlayResult).where(ParlayResult.parlay_id.in_(parlay_ids))
        )
        results = result.scalars().all()
        
        resolved = len(results)
        won = sum(1 for r in results if r.hit is True)
        lost = sum(1 for r in results if r.hit is False)
        
        return {
            "total_parlays": len(parlays),
            "resolved": resolved,
            "won": won,
            "lost": lost,
            "win_rate": won / resolved if resolved > 0 else 0.0,
            "pending": len(parlays) - resolved
        }
    
    async def generate_weekly_summary(
        self,
        user_id: str
    ) -> Dict:
        """Generate weekly performance summary"""
        from datetime import timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Get stats for the week
        stats = await self.tracker.get_parlay_performance_stats(
            start_date=start_date,
            end_date=end_date
        )
        
        # Get user's parlays for the week
        result = await self.db.execute(
            select(Parlay)
            .where(Parlay.user_id == user_id)
            .where(Parlay.created_at >= start_date)
            .where(Parlay.created_at <= end_date)
        )
        parlays = result.scalars().all()
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_parlays": len(parlays),
            "performance": stats,
            "top_performing_parlay": None  # Can be extended
        }

