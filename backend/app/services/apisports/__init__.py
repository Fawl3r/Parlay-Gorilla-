"""API-Sports integration: quota-safe, DB-first, 100 req/day."""

from app.services.apisports.quota_manager import QuotaManager, get_quota_manager
from app.services.apisports.soft_rate_limiter import SoftRateLimiter, get_soft_rate_limiter
from app.services.apisports.client import ApiSportsClient, get_apisports_client
from app.services.apisports.team_mapper import ApiSportsTeamMapper, get_team_mapper
from app.services.apisports.data_adapter import ApiSportsDataAdapter

__all__ = [
    "QuotaManager",
    "get_quota_manager",
    "SoftRateLimiter",
    "get_soft_rate_limiter",
    "ApiSportsClient",
    "get_apisports_client",
    "ApiSportsTeamMapper",
    "get_team_mapper",
    "ApiSportsDataAdapter",
]
