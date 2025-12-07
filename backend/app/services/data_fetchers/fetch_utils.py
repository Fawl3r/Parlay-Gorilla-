"""
Utility classes for data fetching with rate limiting, caching, and fallback.

Provides:
- RateLimitedFetcher: Base class with rate limiting and caching
- Fallback logic when primary sources fail
- Stale cache support as last resort
"""

import asyncio
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Awaitable
from datetime import datetime, timedelta
from functools import wraps
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    
    Args:
        calls_per_minute: Maximum calls allowed per minute
    """
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.tokens = calls_per_minute
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, timeout: float = 30.0) -> bool:
        """
        Acquire a token for making an API call.
        Blocks if rate limit exceeded, up to timeout.
        
        Returns:
            True if token acquired, raises RateLimitError on timeout
        """
        start_time = time.time()
        
        while True:
            async with self._lock:
                # Refill tokens based on time elapsed
                now = time.time()
                elapsed = now - self.last_refill
                refill_amount = (elapsed / 60.0) * self.calls_per_minute
                self.tokens = min(self.calls_per_minute, self.tokens + refill_amount)
                self.last_refill = now
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
            
            # Check timeout
            if time.time() - start_time > timeout:
                raise RateLimitError(f"Rate limit timeout after {timeout}s")
            
            # Wait and retry
            await asyncio.sleep(0.1)


class InMemoryCache:
    """
    Simple in-memory cache with TTL support.
    
    Note: In production, use Redis for distributed caching.
    """
    
    def __init__(self):
        self._cache: Dict[str, tuple[Any, float, float]] = {}  # key -> (value, expires_at, stored_at)
        self._lock = asyncio.Lock()
    
    async def get(self, key: str, allow_stale: bool = False) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            allow_stale: If True, return expired values as fallback
        
        Returns:
            Cached value or None
        """
        async with self._lock:
            if key not in self._cache:
                return None
            
            value, expires_at, stored_at = self._cache[key]
            now = time.time()
            
            if now < expires_at:
                return value
            
            if allow_stale:
                logger.warning(f"Returning stale cache for {key} (expired {now - expires_at:.0f}s ago)")
                return value
            
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        Set a value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 5 minutes)
        """
        async with self._lock:
            now = time.time()
            self._cache[key] = (value, now + ttl, now)
    
    async def delete(self, key: str) -> None:
        """Delete a key from cache"""
        async with self._lock:
            self._cache.pop(key, None)
    
    async def clear_expired(self) -> int:
        """Clear all expired entries. Returns count of cleared entries."""
        async with self._lock:
            now = time.time()
            expired_keys = [k for k, (_, exp, _) in self._cache.items() if now >= exp]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)


class RateLimitedFetcher:
    """
    Base class for all data fetchers with rate limiting, caching, and fallback.
    
    Features:
    - Rate limiting (configurable calls per minute)
    - In-memory caching with TTL
    - Fallback chain when primary source fails
    - Stale cache as last resort
    
    Usage:
        class MyFetcher(RateLimitedFetcher):
            async def _fetch_from_primary(self, key):
                # Primary API call
                pass
            
            async def _fetch_from_fallback(self, key):
                # Fallback API call
                pass
    """
    
    def __init__(
        self,
        calls_per_minute: int = 60,
        cache_ttl_seconds: int = 300,
        name: str = "fetcher"
    ):
        self.rate_limiter = RateLimiter(calls_per_minute)
        self.cache = InMemoryCache()
        self.cache_ttl = cache_ttl_seconds
        self.name = name
    
    def _make_cache_key(self, *args, **kwargs) -> str:
        """Generate a cache key from function arguments"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return f"{self.name}:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def fetch_with_fallback(
        self,
        cache_key: str,
        primary_fn: Callable[[], Awaitable[T]],
        fallback_fn: Optional[Callable[[], Awaitable[T]]] = None,
        cache_ttl: Optional[int] = None
    ) -> Optional[T]:
        """
        Fetch data with caching, rate limiting, and fallback.
        
        Args:
            cache_key: Key for caching the result
            primary_fn: Async function to fetch from primary source
            fallback_fn: Optional async function for fallback source
            cache_ttl: Optional TTL override
        
        Returns:
            Fetched data or None if all sources fail
        """
        ttl = cache_ttl or self.cache_ttl
        
        # 1. Check cache first
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # 2. Try primary source with rate limiting
        try:
            await self.rate_limiter.acquire()
            result = await primary_fn()
            if result is not None:
                await self.cache.set(cache_key, result, ttl=ttl)
                return result
        except RateLimitError as e:
            logger.warning(f"[{self.name}] Rate limit hit: {e}")
        except asyncio.TimeoutError:
            logger.warning(f"[{self.name}] Primary source timeout")
        except Exception as e:
            logger.warning(f"[{self.name}] Primary fetch failed: {e}")
        
        # 3. Try fallback source
        if fallback_fn:
            try:
                await self.rate_limiter.acquire()
                result = await fallback_fn()
                if result is not None:
                    await self.cache.set(cache_key, result, ttl=ttl)
                    return result
            except Exception as e:
                logger.warning(f"[{self.name}] Fallback fetch failed: {e}")
        
        # 4. Last resort: return stale cache
        stale = await self.cache.get(cache_key, allow_stale=True)
        if stale is not None:
            logger.info(f"[{self.name}] Using stale cache for {cache_key}")
            return stale
        
        return None
    
    async def fetch_batch(
        self,
        items: list,
        fetch_fn: Callable[[Any], Awaitable[T]],
        max_concurrent: int = 5
    ) -> Dict[Any, T]:
        """
        Fetch multiple items with controlled concurrency.
        
        Args:
            items: List of items to fetch
            fetch_fn: Async function that takes an item and returns data
            max_concurrent: Maximum concurrent requests
        
        Returns:
            Dict mapping items to their fetched data
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def fetch_one(item):
            async with semaphore:
                try:
                    results[item] = await fetch_fn(item)
                except Exception as e:
                    logger.error(f"[{self.name}] Batch fetch error for {item}: {e}")
                    results[item] = None
        
        await asyncio.gather(*[fetch_one(item) for item in items])
        return results


def cached(ttl_seconds: int = 300):
    """
    Decorator for caching async function results.
    
    Usage:
        @cached(ttl_seconds=600)
        async def get_team_stats(team_name: str) -> Dict:
            ...
    """
    cache = InMemoryCache()
    
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            key_data = json.dumps({
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs
            }, sort_keys=True, default=str)
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                await cache.set(cache_key, result, ttl=ttl_seconds)
            
            return result
        
        return wrapper
    return decorator

