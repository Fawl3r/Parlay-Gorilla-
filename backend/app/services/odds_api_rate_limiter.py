"""
Rate limiter and request deduplication for The Odds API.

Prevents unnecessary API calls by:
1. Deduplicating concurrent requests for the same sport
2. Enforcing minimum time between API calls
3. Tracking quota usage from response headers
4. Caching responses longer to reduce API calls
"""

import asyncio
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class OddsAPIRateLimiter:
    """
    Rate limiter for The Odds API with request deduplication.
    
    Features:
    - Prevents duplicate concurrent requests for the same sport
    - Enforces minimum time between API calls (5 minutes per sport)
    - Tracks quota usage from response headers
    - Warns when quota is low
    """
    
    def __init__(self):
        # Track in-flight requests by sport
        self._in_flight: Dict[str, asyncio.Task] = {}
        self._in_flight_lock = asyncio.Lock()
        
        # Track last API call time per sport (to prevent rapid refreshes)
        self._last_call_time: Dict[str, datetime] = {}
        ttl_seconds = int(getattr(settings, "odds_api_cache_ttl_seconds", 172800) or 172800)
        # With a 48h policy, we treat the call interval as the cache TTL.
        self._min_call_interval = timedelta(seconds=ttl_seconds)
        
        # Track quota usage
        self._quota_remaining: Optional[int] = None
        self._quota_used: Optional[int] = None
        self._quota_last_updated: Optional[datetime] = None
        
        # Cache successful responses temporarily to avoid duplicate calls
        self._response_cache: Dict[str, Tuple[any, datetime]] = {}
        self._cache_ttl = timedelta(seconds=ttl_seconds)
    
    async def acquire(
        self, 
        sport_key: str, 
        force: bool = False
    ) -> bool:
        """
        Acquire permission to make an API call for a sport.
        
        Returns:
            True if call should proceed, False if should use cache/duplicate
        """
        async with self._in_flight_lock:
            # Check if there's already an in-flight request for this sport
            if sport_key in self._in_flight:
                task = self._in_flight[sport_key]
                if not task.done():
                    logger.info(f"[RATE_LIMITER] Request for {sport_key} already in-flight, deduplicating")
                    return False  # Don't make duplicate call
            
            # Check minimum interval between calls
            if not force and sport_key in self._last_call_time:
                time_since_last = datetime.utcnow() - self._last_call_time[sport_key]
                if time_since_last < self._min_call_interval:
                    remaining = self._min_call_interval - time_since_last
                    logger.info(
                        f"[RATE_LIMITER] Rate limit: {sport_key} called {time_since_last.total_seconds():.0f}s ago, "
                        f"wait {remaining.total_seconds():.0f}s more"
                    )
                    return False
            
            # Check quota
            if self._quota_remaining is not None and self._quota_remaining <= 10:
                logger.warning(
                    f"[RATE_LIMITER] Low quota remaining: {self._quota_remaining}. "
                    f"Blocking API call to preserve quota."
                )
                return False
            
            # Allow the call
            return True
    
    async def register_request(self, sport_key: str, task: asyncio.Task):
        """Register an in-flight request."""
        async with self._in_flight_lock:
            self._in_flight[sport_key] = task
            
            # Clean up when task completes
            def cleanup(_):
                async def _cleanup():
                    async with self._in_flight_lock:
                        if sport_key in self._in_flight:
                            del self._in_flight[sport_key]
                asyncio.create_task(_cleanup())
            
            task.add_done_callback(cleanup)
    
    def record_call(self, sport_key: str, response_headers: Optional[Dict] = None):
        """Record that an API call was made and update quota info."""
        self._last_call_time[sport_key] = datetime.utcnow()
        
        if response_headers:
            remaining = response_headers.get("x-requests-remaining")
            used = response_headers.get("x-requests-used")
            
            if remaining is not None:
                try:
                    self._quota_remaining = int(remaining)
                except (ValueError, TypeError):
                    pass
            
            if used is not None:
                try:
                    self._quota_used = int(used)
                except (ValueError, TypeError):
                    pass
            
            self._quota_last_updated = datetime.utcnow()
            
            # Log quota status
            if self._quota_remaining is not None:
                if self._quota_remaining < 50:
                    logger.warning(
                        f"[RATE_LIMITER] Quota low: {self._quota_remaining} remaining, "
                        f"{self._quota_used} used"
                    )
                else:
                    logger.info(
                        f"[RATE_LIMITER] Quota: {self._quota_remaining} remaining, "
                        f"{self._quota_used} used"
                    )
    
    def cache_response(self, sport_key: str, response_data: any):
        """Cache a successful API response."""
        self._response_cache[sport_key] = (response_data, datetime.utcnow())
    
    def get_cached_response(self, sport_key: str) -> Optional[any]:
        """Get cached response if still valid."""
        if sport_key not in self._response_cache:
            return None
        
        data, cached_at = self._response_cache[sport_key]
        age = datetime.utcnow() - cached_at
        
        if age < self._cache_ttl:
            logger.info(f"[RATE_LIMITER] Using cached response for {sport_key} (age: {age.total_seconds():.0f}s)")
            return data
        
        # Cache expired
        del self._response_cache[sport_key]
        return None
    
    def get_quota_status(self) -> Dict[str, any]:
        """Get current quota status."""
        return {
            "remaining": self._quota_remaining,
            "used": self._quota_used,
            "last_updated": self._quota_last_updated.isoformat() if self._quota_last_updated else None,
        }
    
    def get_time_until_next_call(self, sport_key: str) -> Optional[float]:
        """Get seconds until next call is allowed for a sport."""
        if sport_key not in self._last_call_time:
            return 0.0
        
        time_since_last = datetime.utcnow() - self._last_call_time[sport_key]
        if time_since_last >= self._min_call_interval:
            return 0.0
        
        remaining = self._min_call_interval - time_since_last
        return remaining.total_seconds()
    
    def clear_all_caches(self):
        """Clear all caches and reset call times to allow immediate API calls."""
        self._response_cache.clear()
        self._last_call_time.clear()
        logger.info("[RATE_LIMITER] Cleared all caches and call times")


# Global instance
_global_rate_limiter: Optional[OddsAPIRateLimiter] = None


def get_rate_limiter() -> OddsAPIRateLimiter:
    """Get the global rate limiter instance."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = OddsAPIRateLimiter()
    return _global_rate_limiter

