"""
Event Tracking Service for analytics.

Handles:
- Storing app events (page views, clicks, interactions)
- Storing parlay-specific events
- Querying events for analytics
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, distinct
import uuid

from app.models.app_event import AppEvent
from app.models.parlay_event import ParlayEvent


class EventTrackingService:
    """
    Service for tracking and querying analytics events.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==========================================
    # Event Creation
    # ==========================================
    
    async def track_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        page_url: Optional[str] = None,
    ) -> AppEvent:
        """
        Track a generic app event.
        
        Args:
            event_type: Type of event (view_analysis, build_parlay, etc.)
            user_id: Optional user ID if authenticated
            session_id: Session identifier for anonymous tracking
            metadata: Additional event data as JSON
            ip_address: Client IP address
            user_agent: Client user agent string
            referrer: HTTP referrer
            page_url: Current page URL
        
        Returns:
            Created AppEvent
        """
        event = AppEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            user_id=uuid.UUID(user_id) if user_id else None,
            session_id=session_id,
            metadata_=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            page_url=page_url,
        )
        
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        
        return event
    
    async def track_parlay_event(
        self,
        parlay_type: str,
        legs_count: int,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        parlay_id: Optional[str] = None,
        sport_filters: Optional[List[str]] = None,
        expected_value: Optional[float] = None,
        combined_odds: Optional[float] = None,
        hit_probability: Optional[float] = None,
        legs_breakdown: Optional[Dict[str, int]] = None,
        was_saved: bool = False,
        was_shared: bool = False,
        build_method: Optional[str] = None,
    ) -> ParlayEvent:
        """
        Track a parlay-specific event.
        
        Args:
            parlay_type: Type of parlay (safe, balanced, degen, custom)
            legs_count: Number of legs in the parlay
            user_id: Optional user ID
            session_id: Session identifier
            parlay_id: ID of saved parlay if applicable
            sport_filters: Sports included
            expected_value: Calculated EV
            combined_odds: Combined odds
            hit_probability: Probability of hitting
            legs_breakdown: Breakdown by market type
            was_saved: Whether parlay was saved
            was_shared: Whether parlay was shared
            build_method: How parlay was built
        
        Returns:
            Created ParlayEvent
        """
        event = ParlayEvent(
            id=uuid.uuid4(),
            parlay_type=parlay_type,
            legs_count=legs_count,
            user_id=uuid.UUID(user_id) if user_id else None,
            session_id=session_id,
            parlay_id=uuid.UUID(parlay_id) if parlay_id else None,
            sport_filters=sport_filters,
            expected_value=expected_value,
            combined_odds=combined_odds,
            hit_probability=hit_probability,
            legs_breakdown=legs_breakdown,
            was_saved=was_saved,
            was_shared=was_shared,
            build_method=build_method,
        )
        
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        
        return event
    
    # ==========================================
    # Event Querying
    # ==========================================
    
    async def get_events(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AppEvent]:
        """
        Query app events with filters.
        """
        query = select(AppEvent)
        
        conditions = []
        if event_type:
            conditions.append(AppEvent.event_type == event_type)
        if user_id:
            conditions.append(AppEvent.user_id == uuid.UUID(user_id))
        if start_date:
            conditions.append(AppEvent.created_at >= start_date)
        if end_date:
            conditions.append(AppEvent.created_at <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(AppEvent.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_parlay_events(
        self,
        parlay_type: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_legs: Optional[int] = None,
        max_legs: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ParlayEvent]:
        """
        Query parlay events with filters.
        """
        query = select(ParlayEvent)
        
        conditions = []
        if parlay_type:
            conditions.append(ParlayEvent.parlay_type == parlay_type)
        if user_id:
            conditions.append(ParlayEvent.user_id == uuid.UUID(user_id))
        if start_date:
            conditions.append(ParlayEvent.created_at >= start_date)
        if end_date:
            conditions.append(ParlayEvent.created_at <= end_date)
        if min_legs:
            conditions.append(ParlayEvent.legs_count >= min_legs)
        if max_legs:
            conditions.append(ParlayEvent.legs_count <= max_legs)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(ParlayEvent.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_event_counts(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Get counts of events by type.
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        result = await self.db.execute(
            select(AppEvent.event_type, func.count(AppEvent.id)).where(
                and_(
                    AppEvent.created_at >= start_date,
                    AppEvent.created_at <= end_date
                )
            ).group_by(AppEvent.event_type)
        )
        
        return {row[0]: row[1] for row in result.all()}
    
    async def get_unique_sessions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Get count of unique sessions in period.
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=1)
        
        result = await self.db.execute(
            select(func.count(distinct(AppEvent.session_id))).where(
                and_(
                    AppEvent.created_at >= start_date,
                    AppEvent.created_at <= end_date,
                    AppEvent.session_id.isnot(None)
                )
            )
        )
        
        return result.scalar() or 0
    
    async def get_top_pages(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get top viewed pages.
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        result = await self.db.execute(
            select(AppEvent.page_url, func.count(AppEvent.id).label('views')).where(
                and_(
                    AppEvent.created_at >= start_date,
                    AppEvent.created_at <= end_date,
                    AppEvent.page_url.isnot(None)
                )
            ).group_by(AppEvent.page_url).order_by(
                func.count(AppEvent.id).desc()
            ).limit(limit)
        )
        
        return [{"page": row[0], "views": row[1]} for row in result.all()]
    
    async def get_referrer_breakdown(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Get referrer breakdown.
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        result = await self.db.execute(
            select(AppEvent.referrer, func.count(AppEvent.id)).where(
                and_(
                    AppEvent.created_at >= start_date,
                    AppEvent.created_at <= end_date,
                )
            ).group_by(AppEvent.referrer)
        )
        
        breakdown = {}
        for row in result.all():
            referrer = row[0] or "direct"
            # Categorize referrers
            if "google" in referrer.lower():
                category = "search"
            elif "facebook" in referrer.lower() or "twitter" in referrer.lower():
                category = "social"
            elif referrer == "direct":
                category = "direct"
            else:
                category = "other"
            breakdown[category] = breakdown.get(category, 0) + row[1]
        
        return breakdown

