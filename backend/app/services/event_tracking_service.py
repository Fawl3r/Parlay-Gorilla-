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

    # ==========================================
    # AI Picks Health (internal dashboard)
    # ==========================================

    async def get_ai_picks_health_aggregates(
        self,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Aggregate event counts for the internal AI Picks Health dashboard.
        Uses app_events table; works with both SQLite and PostgreSQL.
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        counts = await self.get_event_counts(start_date=start_date, end_date=end_date)

        app_opened = counts.get("app_opened", 0)
        attempt = counts.get("ai_picks_generate_attempt", 0)
        success = counts.get("ai_picks_generate_success", 0)
        fail = counts.get("ai_picks_generate_fail", 0)
        total_outcomes = success + fail
        success_rate = (success / total_outcomes * 100) if total_outcomes else 0.0

        # Beginner vs standard: break down success/fail by metadata.beginner_mode
        beginner_success = 0
        beginner_fail = 0
        standard_success = 0
        standard_fail = 0
        for etype in ("ai_picks_generate_success", "ai_picks_generate_fail"):
            events = await self.get_events(
                event_type=etype,
                start_date=start_date,
                end_date=end_date,
                limit=50_000,
            )
            for e in events:
                is_beginner = (e.metadata_ or {}).get("beginner_mode") is True
                if etype == "ai_picks_generate_success":
                    if is_beginner:
                        beginner_success += 1
                    else:
                        standard_success += 1
                else:
                    if is_beginner:
                        beginner_fail += 1
                    else:
                        standard_fail += 1

        b_total = beginner_success + beginner_fail
        s_total = standard_success + standard_fail
        beginner_success_rate = (beginner_success / b_total * 100) if b_total else 0.0
        standard_success_rate = (standard_success / s_total * 100) if s_total else 0.0

        # Fail reasons: ai_picks_generate_fail_reason metadata.reason
        fail_reason_counts: Dict[str, int] = {}
        fail_reason_events = await self.get_events(
            event_type="ai_picks_generate_fail_reason",
            start_date=start_date,
            end_date=end_date,
            limit=20_000,
        )
        for e in fail_reason_events:
            reason = (e.metadata_ or {}).get("reason") or "unknown"
            fail_reason_counts[reason] = fail_reason_counts.get(reason, 0) + 1
        spec_reasons = ("NO_ODDS", "OUTSIDE_WEEK", "STATUS_NOT_UPCOMING", "PLAYER_PROPS_DISABLED", "legacy_422", "unknown")
        fail_reasons_top = [{"reason": r, "count": fail_reason_counts.get(r, 0)} for r in spec_reasons]
        # Append any other reasons from data (e.g. insufficient_candidates) sorted by count
        others = [
            (r, c) for r, c in fail_reason_counts.items()
            if r not in spec_reasons
        ]
        for r, c in sorted(others, key=lambda x: -x[1]):
            fail_reasons_top.append({"reason": r, "count": c})

        # Quick actions: ai_picks_quick_action_clicked metadata.action_id
        quick_action_counts: Dict[str, int] = {}
        for aid in ("ml_only", "all_upcoming", "lower_legs", "enable_props", "single_sport"):
            quick_action_counts[aid] = 0
        quick_events = await self.get_events(
            event_type="ai_picks_quick_action_clicked",
            start_date=start_date,
            end_date=end_date,
            limit=20_000,
        )
        for e in quick_events:
            aid = (e.metadata_ or {}).get("action_id") or "unknown"
            quick_action_counts[aid] = quick_action_counts.get(aid, 0) + 1
        quick_actions = [
            {"action_id": aid, "clicked": quick_action_counts.get(aid, 0)}
            for aid in ("ml_only", "all_upcoming", "lower_legs", "enable_props", "single_sport")
        ]

        # Graduation: beginner_graduation_nudge_shown, beginner_graduation_nudge_clicked metadata.action
        nudge_shown = counts.get("beginner_graduation_nudge_shown", 0)
        nudge_clicked_events = await self.get_events(
            event_type="beginner_graduation_nudge_clicked",
            start_date=start_date,
            end_date=end_date,
            limit=10_000,
        )
        nudge_clicked_profile = sum(1 for e in nudge_clicked_events if (e.metadata_ or {}).get("action") == "profile")
        nudge_clicked_dismiss = sum(1 for e in nudge_clicked_events if (e.metadata_ or {}).get("action") == "dismiss")
        nudge_ctr = (nudge_clicked_profile + nudge_clicked_dismiss) / nudge_shown * 100 if nudge_shown else 0.0

        # Premium
        upsell_shown = counts.get("premium_upsell_shown", 0)
        upgrade_clicked = counts.get("premium_upgrade_clicked", 0)
        premium_ctr = upgrade_clicked / upsell_shown * 100 if upsell_shown else 0.0

        return {
            "window_days": days,
            "totals": {
                "app_opened": app_opened,
                "ai_picks_generate_attempt": attempt,
                "ai_picks_generate_success": success,
                "ai_picks_generate_fail": fail,
            },
            "success_rate": round(success_rate, 1),
            "beginner": {
                "success": beginner_success,
                "fail": beginner_fail,
                "success_rate": round(beginner_success_rate, 1),
            },
            "standard": {
                "success": standard_success,
                "fail": standard_fail,
                "success_rate": round(standard_success_rate, 1),
            },
            "fail_reasons_top": fail_reasons_top,
            "quick_actions": quick_actions,
            "graduation": {
                "nudge_shown": nudge_shown,
                "nudge_clicked_profile": nudge_clicked_profile,
                "nudge_clicked_dismiss": nudge_clicked_dismiss,
                "ctr": round(nudge_ctr, 1),
            },
            "premium": {
                "upsell_shown": upsell_shown,
                "upgrade_clicked": upgrade_clicked,
                "ctr": round(premium_ctr, 1),
            },
        }