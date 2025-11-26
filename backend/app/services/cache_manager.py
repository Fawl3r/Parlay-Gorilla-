"""Advanced caching manager for parlay calculations"""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import hashlib
import json

from app.models.parlay_cache import ParlayCache


class CacheManager:
    """Manages caching for parlay calculations and other expensive operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # In-memory cache for frequently accessed data
        self._memory_cache: Dict[str, Any] = {}
        self._memory_cache_ttl: Dict[str, datetime] = {}
    
    def _generate_cache_key(self, num_legs: int, risk_profile: str, sport: str = "NFL") -> str:
        """Generate a unique cache key"""
        key_data = f"{num_legs}:{risk_profile}:{sport}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_cached_parlay(
        self,
        num_legs: int,
        risk_profile: str,
        sport: str = "NFL",
        max_age_hours: int = 6
    ) -> Optional[Dict]:
        """
        Get cached parlay data if available and not expired
        
        Args:
            num_legs: Number of legs
            risk_profile: Risk profile
            sport: Sport type
            max_age_hours: Maximum age of cache in hours
            
        Returns:
            Cached parlay data or None if not found/expired
        """
        # Check in-memory cache first
        cache_key = self._generate_cache_key(num_legs, risk_profile, sport)
        if cache_key in self._memory_cache:
            if cache_key in self._memory_cache_ttl:
                if self._memory_cache_ttl[cache_key] > datetime.now(timezone.utc):
                    return self._memory_cache[cache_key]
                else:
                    # Expired, remove from memory
                    del self._memory_cache[cache_key]
                    del self._memory_cache_ttl[cache_key]
        
        # Check database cache
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        result = await self.db.execute(
            select(ParlayCache)
            .where(ParlayCache.num_legs == num_legs)
            .where(ParlayCache.risk_profile == risk_profile)
            .where(ParlayCache.sport == sport)
            .where(ParlayCache.expires_at > datetime.now(timezone.utc))
            .where(ParlayCache.cached_at > cutoff_time)
            .order_by(ParlayCache.cached_at.desc())
            .limit(1)
        )
        cached = result.scalar_one_or_none()
        
        if cached:
            # Update hit count
            cached.hit_count += 1
            await self.db.commit()
            
            # Store in memory cache for faster access
            self._memory_cache[cache_key] = cached.cached_parlay_data
            self._memory_cache_ttl[cache_key] = cached.expires_at
            
            return cached.cached_parlay_data
        
        return None
    
    async def set_cached_parlay(
        self,
        num_legs: int,
        risk_profile: str,
        parlay_data: Dict,
        sport: str = "NFL",
        ttl_hours: int = 6
    ):
        """
        Cache parlay data
        
        Args:
            num_legs: Number of legs
            risk_profile: Risk profile
            parlay_data: Full parlay data to cache
            sport: Sport type
            ttl_hours: Time to live in hours
        """
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        
        # Store in database cache
        cache_entry = ParlayCache(
            num_legs=num_legs,
            risk_profile=risk_profile,
            sport=sport,
            cached_parlay_data=parlay_data,
            expires_at=expires_at,
        )
        self.db.add(cache_entry)
        
        # Store in memory cache
        cache_key = self._generate_cache_key(num_legs, risk_profile, sport)
        self._memory_cache[cache_key] = parlay_data
        self._memory_cache_ttl[cache_key] = expires_at
        
        await self.db.commit()
    
    async def clear_expired_cache(self):
        """Remove expired cache entries from database"""
        result = await self.db.execute(
            delete(ParlayCache)
            .where(ParlayCache.expires_at < datetime.now(timezone.utc))
        )
        await self.db.commit()
        return result.rowcount
    
    async def clear_cache_for_params(
        self,
        num_legs: Optional[int] = None,
        risk_profile: Optional[str] = None,
        sport: Optional[str] = None
    ):
        """Clear cache entries matching specific parameters"""
        query = delete(ParlayCache)
        
        if num_legs is not None:
            query = query.where(ParlayCache.num_legs == num_legs)
        if risk_profile is not None:
            query = query.where(ParlayCache.risk_profile == risk_profile)
        if sport is not None:
            query = query.where(ParlayCache.sport == sport)
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        # Clear memory cache if matching
        keys_to_remove = []
        for key in self._memory_cache.keys():
            # Simple check - in production, might want more sophisticated matching
            keys_to_remove.append(key)
        
        for key in keys_to_remove:
            if key in self._memory_cache:
                del self._memory_cache[key]
            if key in self._memory_cache_ttl:
                del self._memory_cache_ttl[key]
        
        return result.rowcount
    
    def clear_memory_cache(self):
        """Clear all in-memory cache"""
        self._memory_cache.clear()
        self._memory_cache_ttl.clear()


# Function-level caching decorators
def cached_async_result(ttl_seconds: int = 3600):
    """
    Decorator for caching async function results in memory
    Note: This is a simple implementation. For production, consider using aiocache
    """
    def decorator(func):
        cache = {}
        cache_times = {}
        
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check if cached and not expired
            if cache_key in cache:
                if cache_key in cache_times:
                    age = (datetime.now(timezone.utc) - cache_times[cache_key]).total_seconds()
                    if age < ttl_seconds:
                        return cache[cache_key]
                    else:
                        # Expired
                        del cache[cache_key]
                        del cache_times[cache_key]
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            cache[cache_key] = result
            cache_times[cache_key] = datetime.now(timezone.utc)
            
            return result
        
        return wrapper
    return decorator

