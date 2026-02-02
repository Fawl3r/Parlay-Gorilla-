"""
Admin Metrics Service for aggregating analytics data.

Provides metrics for:
- User analytics (DAU/WAU/MAU, signups, retention)
- Usage analytics (feature usage, parlay stats)
- Revenue analytics (payments, subscriptions)
- Model performance (accuracy, calibration)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, distinct
from sqlalchemy.sql import text

from app.database.session import is_sqlite
from app.models.user import User
from app.models.app_event import AppEvent
from app.models.parlay_event import ParlayEvent
from app.models.parlay import Parlay
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome
from app.models.system_log import SystemLog


class AdminMetricsService:
    """
    Service for aggregating admin dashboard metrics.
    
    All methods accept time_range parameters for flexible date filtering.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==========================================
    # Overview Metrics
    # ==========================================
    
    async def get_overview_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get high-level overview metrics for the admin dashboard.
        
        Returns:
            - total_users: Total registered users
            - dau: Daily active users (for the period)
            - total_parlays: Parlays generated in period
            - model_accuracy: Overall model accuracy (last 30 days)
            - total_revenue: Revenue in period
            - api_health: Error rate summary
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # Get metrics in parallel-style queries
        total_users = await self._get_total_users()
        dau = await self._get_active_users(start_date, end_date, "day")
        total_parlays = await self._get_parlay_count(start_date, end_date)
        model_accuracy = await self._get_model_accuracy()
        total_revenue = await self._get_total_revenue(start_date, end_date)
        api_health = await self._get_api_health(start_date, end_date)
        
        return {
            "total_users": total_users,
            "dau": dau,
            "total_parlays": total_parlays,
            "model_accuracy": model_accuracy,
            "total_revenue": total_revenue,
            "api_health": api_health,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            }
        }
    
    # ==========================================
    # User Metrics
    # ==========================================
    
    async def get_user_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get detailed user analytics.
        
        Returns:
            - total_users
            - new_users (in period)
            - dau, wau, mau
            - users_by_plan
            - users_by_role
            - active_vs_inactive
            - signups_over_time
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        total_users = await self._get_total_users()
        new_users = await self._get_new_users(start_date, end_date)
        
        # Active user metrics
        now = datetime.utcnow()
        dau = await self._get_active_users(now - timedelta(days=1), now, "day")
        wau = await self._get_active_users(now - timedelta(days=7), now, "week")
        mau = await self._get_active_users(now - timedelta(days=30), now, "month")
        
        users_by_plan = await self._get_users_by_plan()
        users_by_role = await self._get_users_by_role()
        active_vs_inactive = await self._get_active_vs_inactive()
        signups_over_time = await self._get_signups_over_time(start_date, end_date)
        
        return {
            "total_users": total_users,
            "new_users": new_users,
            "dau": dau,
            "wau": wau,
            "mau": mau,
            "users_by_plan": users_by_plan,
            "users_by_role": users_by_role,
            "active_vs_inactive": active_vs_inactive,
            "signups_over_time": signups_over_time,
        }
    
    # ==========================================
    # Usage Metrics
    # ==========================================
    
    async def get_usage_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get feature usage analytics.
        
        Returns:
            - analysis_views: Game analysis page views
            - parlay_sessions: Parlay builder sessions
            - parlays_by_type: Breakdown by safe/balanced/degen/custom
            - parlays_by_sport: Usage per sport
            - avg_legs: Average legs per parlay
            - upset_finder_usage: Upset finder click count
            - feature_usage: General feature breakdown
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        analysis_views = await self._get_event_count("view_analysis", start_date, end_date)
        parlay_sessions = await self._get_event_count("build_parlay", start_date, end_date)
        upset_finder_usage = await self._get_event_count("click_upset_finder", start_date, end_date)
        
        parlays_by_type = await self._get_parlays_by_type(start_date, end_date)
        parlays_by_sport = await self._get_parlays_by_sport(start_date, end_date)
        avg_legs = await self._get_avg_legs(start_date, end_date)
        
        # Feature usage breakdown
        feature_usage = await self._get_feature_usage(start_date, end_date)
        
        return {
            "analysis_views": analysis_views,
            "parlay_sessions": parlay_sessions,
            "upset_finder_usage": upset_finder_usage,
            "parlays_by_type": parlays_by_type,
            "parlays_by_sport": parlays_by_sport,
            "avg_legs": avg_legs,
            "feature_usage": feature_usage,
        }

    # ==========================================
    # Custom Builder Templates Metrics
    # ==========================================

    async def get_template_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get Custom Builder QuickStart template analytics.

        Returns:
            - clicks_by_template: { template_id: count } for custom_builder_template_clicked
            - applied_by_template: { template_id: count } for custom_builder_template_applied
            - partial_by_template: { template_id: count } for custom_builder_template_partial
            - partial_rate_by_template: { template_id: rate } where rate = partial / (applied + partial)
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        result = await self.db.execute(
            select(AppEvent.event_type, AppEvent.metadata_).where(
                and_(
                    AppEvent.event_type.in_(
                        [
                            "custom_builder_template_clicked",
                            "custom_builder_template_applied",
                            "custom_builder_template_partial",
                        ]
                    ),
                    AppEvent.created_at >= start_date,
                    AppEvent.created_at <= end_date,
                )
            )
        )
        rows = result.all()

        clicks_by_template: Dict[str, int] = {}
        applied_by_template: Dict[str, int] = {}
        partial_by_template: Dict[str, int] = {}

        for event_type, metadata in rows:
            meta = metadata or {}
            template_id = meta.get("template_id") or "unknown"
            if event_type == "custom_builder_template_clicked":
                clicks_by_template[template_id] = clicks_by_template.get(template_id, 0) + 1
            elif event_type == "custom_builder_template_applied":
                applied_by_template[template_id] = applied_by_template.get(template_id, 0) + 1
            elif event_type == "custom_builder_template_partial":
                partial_by_template[template_id] = partial_by_template.get(template_id, 0) + 1

        all_template_ids = set(clicks_by_template) | set(applied_by_template) | set(partial_by_template)
        partial_rate_by_template: Dict[str, float] = {}
        for tid in all_template_ids:
            applied = applied_by_template.get(tid, 0)
            partial = partial_by_template.get(tid, 0)
            total = applied + partial
            partial_rate_by_template[tid] = round(partial / total * 100, 2) if total > 0 else 0.0

        return {
            "clicks_by_template": clicks_by_template,
            "applied_by_template": applied_by_template,
            "partial_by_template": partial_by_template,
            "partial_rate_by_template": partial_rate_by_template,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    # ==========================================
    # Revenue Metrics
    # ==========================================
    
    async def get_revenue_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get revenue and subscription analytics.
        
        Returns:
            - total_revenue
            - revenue_by_plan
            - active_subscriptions
            - new_subscriptions
            - churned_subscriptions
            - conversion_rate
            - revenue_over_time
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        total_revenue = await self._get_total_revenue(start_date, end_date)
        revenue_by_plan = await self._get_revenue_by_plan(start_date, end_date)
        
        active_subscriptions = await self._get_active_subscriptions()
        new_subscriptions = await self._get_new_subscriptions(start_date, end_date)
        churned = await self._get_churned_subscriptions(start_date, end_date)
        
        conversion_rate = await self._get_conversion_rate()
        revenue_over_time = await self._get_revenue_over_time(start_date, end_date)
        recent_payments = await self._get_recent_payments(limit=20)
        
        return {
            "total_revenue": total_revenue,
            "revenue_by_plan": revenue_by_plan,
            "active_subscriptions": active_subscriptions,
            "new_subscriptions": new_subscriptions,
            "churned_subscriptions": churned,
            "conversion_rate": conversion_rate,
            "revenue_over_time": revenue_over_time,
            "recent_payments": recent_payments,
        }
    
    # ==========================================
    # Private Helper Methods
    # ==========================================
    
    async def _get_total_users(self) -> int:
        result = await self.db.execute(select(func.count(User.id)))
        return result.scalar() or 0
    
    async def _get_new_users(self, start: datetime, end: datetime) -> int:
        result = await self.db.execute(
            select(func.count(User.id)).where(
                and_(User.created_at >= start, User.created_at <= end)
            )
        )
        return result.scalar() or 0
    
    async def _get_active_users(self, start: datetime, end: datetime, period: str) -> int:
        # Count users with login in period (exclude NULL last_login)
        result = await self.db.execute(
            select(func.count(distinct(User.id))).where(
                and_(
                    User.last_login.isnot(None),
                    User.last_login >= start,
                    User.last_login <= end
                )
            )
        )
        return result.scalar() or 0
    
    async def _get_users_by_plan(self) -> Dict[str, int]:
        result = await self.db.execute(
            select(User.plan, func.count(User.id)).group_by(User.plan)
        )
        return {row[0]: row[1] for row in result.all()}
    
    async def _get_users_by_role(self) -> Dict[str, int]:
        result = await self.db.execute(
            select(User.role, func.count(User.id)).group_by(User.role)
        )
        return {row[0]: row[1] for row in result.all()}
    
    async def _get_active_vs_inactive(self) -> Dict[str, int]:
        result = await self.db.execute(
            select(User.is_active, func.count(User.id)).group_by(User.is_active)
        )
        counts = {row[0]: row[1] for row in result.all()}
        return {
            "active": counts.get(True, 0),
            "inactive": counts.get(False, 0),
        }
    
    async def _get_signups_over_time(self, start: datetime, end: datetime) -> List[Dict]:
        # Group signups by day - SQLite compatible
        if is_sqlite:
            # SQLite uses strftime for date grouping
            result = await self.db.execute(
                text("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM users
                    WHERE created_at >= :start AND created_at <= :end
                    GROUP BY DATE(created_at)
                    ORDER BY DATE(created_at)
                """),
                {"start": start, "end": end}
            )
            return [{"date": f"{row[0]}T00:00:00", "count": row[1]} for row in result.all()]
        else:
            # PostgreSQL uses date_trunc
            result = await self.db.execute(
                select(
                    func.date_trunc('day', User.created_at).label('date'),
                    func.count(User.id).label('count')
                ).where(
                    and_(User.created_at >= start, User.created_at <= end)
                ).group_by(
                    func.date_trunc('day', User.created_at)
                ).order_by(
                    func.date_trunc('day', User.created_at)
                )
            )
            return [{"date": row[0].isoformat(), "count": row[1]} for row in result.all()]
    
    async def _get_parlay_count(self, start: datetime, end: datetime) -> int:
        result = await self.db.execute(
            select(func.count(Parlay.id)).where(
                and_(Parlay.created_at >= start, Parlay.created_at <= end)
            )
        )
        return result.scalar() or 0
    
    async def _get_model_accuracy(self) -> Optional[float]:
        # Get accuracy from last 30 days of predictions
        cutoff = datetime.utcnow() - timedelta(days=30)
        result = await self.db.execute(
            select(func.avg(case((PredictionOutcome.was_correct, 1), else_=0))).where(
                PredictionOutcome.resolved_at >= cutoff
            )
        )
        accuracy = result.scalar()
        return round(accuracy * 100, 2) if accuracy else None
    
    async def _get_total_revenue(self, start: datetime, end: datetime) -> float:
        result = await self.db.execute(
            select(func.sum(Payment.amount)).where(
                and_(
                    Payment.status == 'paid',
                    Payment.paid_at >= start,
                    Payment.paid_at <= end
                )
            )
        )
        return float(result.scalar() or 0)
    
    async def _get_api_health(self, start: datetime, end: datetime) -> Dict[str, Any]:
        # Count errors vs total logs
        result = await self.db.execute(
            select(
                SystemLog.level,
                func.count(SystemLog.id)
            ).where(
                SystemLog.created_at >= start
            ).group_by(SystemLog.level)
        )
        
        counts = {row[0]: row[1] for row in result.all()}
        total = sum(counts.values())
        errors = counts.get('error', 0) + counts.get('critical', 0)
        
        return {
            "total_logs": total,
            "errors": errors,
            "error_rate": round(errors / total * 100, 2) if total > 0 else 0,
            "status": "healthy" if (total == 0 or errors / total < 0.05) else "degraded",
        }
    
    async def _get_event_count(self, event_type: str, start: datetime, end: datetime) -> int:
        result = await self.db.execute(
            select(func.count(AppEvent.id)).where(
                and_(
                    AppEvent.event_type == event_type,
                    AppEvent.created_at >= start,
                    AppEvent.created_at <= end
                )
            )
        )
        return result.scalar() or 0
    
    async def _get_parlays_by_type(self, start: datetime, end: datetime) -> Dict[str, int]:
        result = await self.db.execute(
            select(Parlay.risk_profile, func.count(Parlay.id)).where(
                and_(Parlay.created_at >= start, Parlay.created_at <= end)
            ).group_by(Parlay.risk_profile)
        )
        return {row[0]: row[1] for row in result.all()}
    
    async def _get_parlays_by_sport(self, start: datetime, end: datetime) -> Dict[str, int]:
        # This would require parsing the legs JSON - simplified version
        result = await self.db.execute(
            select(func.count(ParlayEvent.id)).where(
                and_(ParlayEvent.created_at >= start, ParlayEvent.created_at <= end)
            )
        )
        total = result.scalar() or 0
        # TODO: Implement proper sport breakdown from parlay legs
        return {"total": total}
    
    async def _get_avg_legs(self, start: datetime, end: datetime) -> Dict[str, float]:
        result = await self.db.execute(
            select(
                func.avg(Parlay.num_legs),
                func.min(Parlay.num_legs),
                func.max(Parlay.num_legs)
            ).where(
                and_(Parlay.created_at >= start, Parlay.created_at <= end)
            )
        )
        row = result.first()
        if row:
            return {
                "avg": round(row[0] or 0, 2),
                "min": row[1] or 0,
                "max": row[2] or 0,
            }
        return {"avg": 0, "min": 0, "max": 0}
    
    async def _get_feature_usage(self, start: datetime, end: datetime) -> Dict[str, int]:
        result = await self.db.execute(
            select(AppEvent.event_type, func.count(AppEvent.id)).where(
                and_(AppEvent.created_at >= start, AppEvent.created_at <= end)
            ).group_by(AppEvent.event_type)
        )
        return {row[0]: row[1] for row in result.all()}
    
    async def _get_revenue_by_plan(self, start: datetime, end: datetime) -> Dict[str, float]:
        result = await self.db.execute(
            select(Payment.plan, func.sum(Payment.amount)).where(
                and_(
                    Payment.status == 'paid',
                    Payment.paid_at >= start,
                    Payment.paid_at <= end
                )
            ).group_by(Payment.plan)
        )
        return {row[0]: float(row[1]) for row in result.all()}
    
    async def _get_active_subscriptions(self) -> int:
        result = await self.db.execute(
            select(func.count(Subscription.id)).where(
                Subscription.status == 'active'
            )
        )
        return result.scalar() or 0
    
    async def _get_new_subscriptions(self, start: datetime, end: datetime) -> int:
        result = await self.db.execute(
            select(func.count(Subscription.id)).where(
                and_(
                    Subscription.created_at >= start,
                    Subscription.created_at <= end
                )
            )
        )
        return result.scalar() or 0
    
    async def _get_churned_subscriptions(self, start: datetime, end: datetime) -> int:
        result = await self.db.execute(
            select(func.count(Subscription.id)).where(
                and_(
                    Subscription.cancelled_at >= start,
                    Subscription.cancelled_at <= end
                )
            )
        )
        return result.scalar() or 0
    
    async def _get_conversion_rate(self) -> float:
        # Ratio of paid users to total users
        total = await self._get_total_users()
        result = await self.db.execute(
            select(func.count(User.id)).where(
                User.plan.in_(['standard', 'elite'])
            )
        )
        paid = result.scalar() or 0
        return round(paid / total * 100, 2) if total > 0 else 0
    
    async def _get_revenue_over_time(self, start: datetime, end: datetime) -> List[Dict]:
        # SQLite compatible date grouping
        if is_sqlite:
            result = await self.db.execute(
                text("""
                    SELECT DATE(paid_at) as date, SUM(amount) as amount
                    FROM payments
                    WHERE status = 'paid' AND paid_at >= :start AND paid_at <= :end
                    GROUP BY DATE(paid_at)
                    ORDER BY DATE(paid_at)
                """),
                {"start": start, "end": end}
            )
            return [{"date": f"{row[0]}T00:00:00", "amount": float(row[1] or 0)} for row in result.all()]
        else:
            result = await self.db.execute(
                select(
                    func.date_trunc('day', Payment.paid_at).label('date'),
                    func.sum(Payment.amount).label('amount')
                ).where(
                    and_(
                        Payment.status == 'paid',
                        Payment.paid_at >= start,
                        Payment.paid_at <= end
                    )
                ).group_by(
                    func.date_trunc('day', Payment.paid_at)
                ).order_by(
                    func.date_trunc('day', Payment.paid_at)
                )
            )
            return [{"date": row[0].isoformat(), "amount": float(row[1])} for row in result.all()]
    
    async def _get_recent_payments(self, limit: int = 20) -> List[Dict]:
        result = await self.db.execute(
            select(Payment).order_by(Payment.created_at.desc()).limit(limit)
        )
        payments = result.scalars().all()
        return [
            {
                "id": str(p.id),
                "user_id": str(p.user_id),
                "amount": float(p.amount),
                "currency": p.currency,
                "plan": p.plan,
                "provider": p.provider,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments
        ]

