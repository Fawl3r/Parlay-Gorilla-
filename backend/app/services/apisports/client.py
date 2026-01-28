"""
API-Sports HTTP client: quota + rate limit before each request, retries, timeouts.

User-facing endpoints must NEVER call this; only background refresh job does.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.services.apisports.quota_manager import get_quota_manager
from app.services.apisports.soft_rate_limiter import get_soft_rate_limiter

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0
MAX_RETRIES = 3
RETRY_BACKOFF = 1.0


class ApiSportsClient:
    """
    Central HTTP client for API-Sports.
    - Checks QuotaManager.can_spend(1) and SoftRateLimiter.acquire() before request.
    - Calls QuotaManager.spend(1) after success.
    - Retries with exponential backoff, timeout 10s, no key in logs.
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self._base_url = (base_url or getattr(settings, "apisports_base_url", "")).rstrip("/")
        self._api_key = api_key or getattr(settings, "api_sports_api_key") or ""
        self._timeout = timeout
        self._quota = get_quota_manager()
        self._rate_limiter = get_soft_rate_limiter()

    def is_configured(self) -> bool:
        return bool((self._api_key or "").strip() and (self._base_url or "").strip())

    async def _before_request(self, n: int = 1) -> bool:
        """Return True if we may make n requests (quota + circuit + rate limit)."""
        if not await self._quota.can_spend(n):
            logger.info("ApiSportsClient: quota or circuit breaker blocks request")
            return False
        if not await self._rate_limiter.acquire(timeout_seconds=25.0):
            logger.info("ApiSportsClient: rate limiter no token")
            return False
        return True

    async def _after_success(self, n: int = 1) -> None:
        await self._quota.spend(n)
        await self._quota.record_success()

    async def _after_failure(self) -> None:
        await self._quota.record_failure()

    async def request(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        *,
        method: str = "GET",
    ) -> Optional[dict[str, Any]]:
        """
        Perform one API-Sports request. Path is e.g. /fixtures.
        Returns parsed JSON or None on failure. Never leaks API key in logs.
        """
        if not self.is_configured():
            logger.warning("ApiSportsClient: not configured (missing key or base URL)")
            return None
        if not await self._before_request(1):
            return None

        url = f"{self._base_url}{path}" if path.startswith("/") else f"{self._base_url}/{path}"
        headers = {"x-apisports-key": self._api_key}
        last_error: Optional[Exception] = None

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.request(
                        method,
                        url,
                        params=params or {},
                        headers=headers,
                    )
                if resp.status_code == 200:
                    data = resp.json()
                    await self._after_success(1)
                    logger.info(
                        "ApiSportsClient: %s %s -> %s (attempt %s)",
                        method,
                        path[:64],
                        resp.status_code,
                        attempt + 1,
                    )
                    return data
                if resp.status_code == 429:
                    await self._after_failure()
                    logger.warning("ApiSportsClient: 429 rate limit at %s", path[:64])
                    return None
                if resp.status_code >= 500:
                    last_error = Exception(f"API-Sports {resp.status_code}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_BACKOFF * (2 ** attempt))
                        continue
                await self._after_failure()
                logger.warning(
                    "ApiSportsClient: %s %s -> %s",
                    method,
                    path[:64],
                    resp.status_code,
                )
                return None
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning("ApiSportsClient: timeout %s", path[:64])
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_BACKOFF * (2 ** attempt))
                    continue
                await self._after_failure()
                return None
            except Exception as e:
                last_error = e
                logger.warning("ApiSportsClient: request failed %s: %s", path[:64], str(e)[:100])
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_BACKOFF * (2 ** attempt))
                    continue
                await self._after_failure()
                return None

        return None

    async def get_fixtures(
        self,
        league_id: int,
        season: Optional[int] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """GET /fixtures with league and optional season/date range."""
        params: dict[str, Any] = {"league": league_id}
        if season is not None:
            params["season"] = season
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return await self.request("/fixtures", params=params)

    async def get_team_statistics(self, fixture_id: int, team_id: int) -> Optional[dict[str, Any]]:
        """GET /fixtures/statistics (team stats for a fixture)."""
        return await self.request("/fixtures/statistics", params={"fixture": fixture_id})

    async def get_standings(self, league_id: int, season: int) -> Optional[dict[str, Any]]:
        """GET /standings."""
        return await self.request("/standings", params={"league": league_id, "season": season})

    async def get_injuries(self, league_id: int, season: int) -> Optional[dict[str, Any]]:
        """GET /injuries (if supported by plan)."""
        return await self.request("/injuries", params={"league": league_id, "season": season})


_apisports_client: Optional[ApiSportsClient] = None


def get_apisports_client() -> ApiSportsClient:
    global _apisports_client
    if _apisports_client is None:
        _apisports_client = ApiSportsClient()
    return _apisports_client
