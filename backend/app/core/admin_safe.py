"""
Admin API safety layer.

Centralizes safe fallback responses and error handling so no admin endpoint
can return HTTP 500 or unhandled exceptions. Use when:
- Database tables are missing
- Queries return empty/NULL
- Redis or external deps are down
"""

from __future__ import annotations

from typing import Any, Dict, List


# Safe fallbacks that satisfy frontend and never null/undefined

SAFE_METRICS_OVERVIEW: Dict[str, Any] = {
    "total_users": 0,
    "dau": 0,
    "total_parlays": 0,
    "model_accuracy": None,
    "total_revenue": 0,
    "api_health": {
        "total_logs": 0,
        "errors": 0,
        "error_rate": 0,
        "status": "healthy",
    },
    "period": {"start": "", "end": ""},
}

SAFE_METRICS_USERS: Dict[str, Any] = {
    "total_users": 0,
    "new_users": 0,
    "dau": 0,
    "wau": 0,
    "mau": 0,
    "users_by_plan": {},
    "users_by_role": {},
    "active_vs_inactive": {"active": 0, "inactive": 0},
    "signups_over_time": [],
}

SAFE_METRICS_USAGE: Dict[str, Any] = {
    "analysis_views": 0,
    "parlay_sessions": 0,
    "upset_finder_usage": 0,
    "parlays_by_type": {},
    "parlays_by_sport": {},
    "avg_legs": {"avg": 0, "min": 0, "max": 0},
    "feature_usage": {},
}

SAFE_METRICS_REVENUE: Dict[str, Any] = {
    "total_revenue": 0,
    "revenue_by_plan": {},
    "active_subscriptions": 0,
    "new_subscriptions": 0,
    "churned_subscriptions": 0,
    "conversion_rate": 0,
    "revenue_over_time": [],
    "recent_payments": [],
}

SAFE_METRICS_TEMPLATES: Dict[str, Any] = {
    "clicks_by_template": {},
    "applied_by_template": {},
    "partial_by_template": {},
    "partial_rate_by_template": {},
    "period": {"start": "", "end": ""},
}

SAFE_LOGS_LIST: List[Dict[str, Any]] = []

SAFE_LOGS_STATS: Dict[str, Any] = {
    "total": 0,
    "by_source": {},
    "by_level": {},
    "error_rate": 0.0,
}

SAFE_LOGS_SOURCES: List[str] = []

SAFE_SAFETY: Dict[str, Any] = {
    "health_score": 100,
    "state": "UNKNOWN",
    "recommended_action": "No telemetry available",
    "reasons": [],
    "telemetry": {},
    "events": [],
}

SAFE_MODEL_PERFORMANCE: Dict[str, Any] = {
    "model_version": "",
    "lookback_days": 30,
    "sport_filter": None,
    "metrics": {},
}

SAFE_PAYMENTS_LIST: List[Dict[str, Any]] = []
SAFE_PAYMENTS_STATS: Dict[str, Any] = {
    "time_range": "30d",
    "total_revenue": 0.0,
    "by_status": {},
    "by_provider": {},
}

SAFE_SUBSCRIPTIONS_LIST: List[Dict[str, Any]] = []

SAFE_EVENTS_LIST: List[Dict[str, Any]] = []
SAFE_EVENTS_COUNTS: Dict[str, Any] = {}
SAFE_EVENTS_TRAFFIC: Dict[str, Any] = {
    "unique_sessions": 0,
    "top_pages": [],
    "referrer_breakdown": {},
    "event_counts": {},
}

SAFE_USERS_LIST: Dict[str, Any] = {
    "users": [],
    "total": 0,
    "page": 1,
    "page_size": 20,
    "total_pages": 0,
}

SAFE_APISPORTS_QUOTA: Dict[str, Any] = {
    "used_today": 0,
    "remaining": 100,
    "circuit_open": False,
    "daily_limit": 100,
}

SAFE_APISPORTS_REFRESH: Dict[str, Any] = {"used": 0, "remaining": 100, "refreshed": {}}
