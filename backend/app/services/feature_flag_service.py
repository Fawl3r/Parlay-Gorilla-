"""
Feature Flag Service for managing feature toggles.

Provides:
- CRUD operations for feature flags
- User-specific flag checks
- Caching for performance
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import uuid

from app.models.feature_flag import FeatureFlag
from app.models.user import User


# In-memory cache for feature flags (simple TTL cache)
_flag_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamp: Optional[datetime] = None
CACHE_TTL_SECONDS = 60  # Refresh cache every 60 seconds


class FeatureFlagService:
    """
    Service for managing feature flags.
    
    Features:
    - Toggle flags on/off
    - User-specific targeting
    - Simple in-memory caching
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==========================================
    # Flag CRUD
    # ==========================================
    
    async def get_all_flags(self) -> List[FeatureFlag]:
        """Get all feature flags."""
        result = await self.db.execute(
            select(FeatureFlag).order_by(FeatureFlag.key)
        )
        return list(result.scalars().all())
    
    async def get_flag(self, key: str) -> Optional[FeatureFlag]:
        """Get a single feature flag by key."""
        result = await self.db.execute(
            select(FeatureFlag).where(FeatureFlag.key == key)
        )
        return result.scalar_one_or_none()
    
    async def create_flag(
        self,
        key: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        enabled: bool = False,
        category: Optional[str] = None,
        targeting_rules: Optional[Dict[str, Any]] = None,
    ) -> FeatureFlag:
        """Create a new feature flag."""
        flag = FeatureFlag(
            id=uuid.uuid4(),
            key=key,
            name=name or key,
            description=description,
            enabled=enabled,
            category=category,
            targeting_rules=targeting_rules,
        )
        
        self.db.add(flag)
        await self.db.commit()
        await self.db.refresh(flag)
        
        # Invalidate cache
        self._invalidate_cache()
        
        return flag
    
    async def update_flag(
        self,
        key: str,
        enabled: Optional[bool] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        targeting_rules: Optional[Dict[str, Any]] = None,
    ) -> Optional[FeatureFlag]:
        """Update an existing feature flag."""
        flag = await self.get_flag(key)
        if not flag:
            return None
        
        if enabled is not None:
            flag.enabled = enabled
        if name is not None:
            flag.name = name
        if description is not None:
            flag.description = description
        if category is not None:
            flag.category = category
        if targeting_rules is not None:
            flag.targeting_rules = targeting_rules
        
        await self.db.commit()
        await self.db.refresh(flag)
        
        # Invalidate cache
        self._invalidate_cache()
        
        return flag
    
    async def delete_flag(self, key: str) -> bool:
        """Delete a feature flag."""
        flag = await self.get_flag(key)
        if not flag:
            return False
        
        await self.db.delete(flag)
        await self.db.commit()
        
        # Invalidate cache
        self._invalidate_cache()
        
        return True
    
    async def toggle_flag(self, key: str) -> Optional[FeatureFlag]:
        """Toggle a feature flag on/off."""
        flag = await self.get_flag(key)
        if not flag:
            return None
        
        flag.enabled = not flag.enabled
        await self.db.commit()
        await self.db.refresh(flag)
        
        # Invalidate cache
        self._invalidate_cache()
        
        return flag
    
    # ==========================================
    # Flag Checking
    # ==========================================
    
    async def is_enabled(self, key: str, user: Optional[User] = None) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            key: Feature flag key
            user: Optional user for targeting rules
        
        Returns:
            True if enabled for the user, False otherwise
        """
        # Try cache first
        cached = await self._get_from_cache(key)
        if cached is not None:
            if user and cached.get("targeting_rules"):
                return self._check_targeting(cached["targeting_rules"], user)
            return cached.get("enabled", False)
        
        # Fetch from database
        flag = await self.get_flag(key)
        if not flag:
            return False
        
        # Update cache
        await self._refresh_cache()
        
        # Check user targeting
        if user:
            return flag.is_enabled_for_user(user)
        
        return flag.enabled
    
    async def get_flags_for_user(self, user: User) -> Dict[str, bool]:
        """
        Get all feature flags evaluated for a specific user.
        
        Returns:
            Dict mapping flag key to enabled status for the user
        """
        flags = await self.get_all_flags()
        return {
            flag.key: flag.is_enabled_for_user(user)
            for flag in flags
        }
    
    async def get_enabled_flags(self) -> List[str]:
        """Get list of all enabled flag keys."""
        result = await self.db.execute(
            select(FeatureFlag.key).where(FeatureFlag.enabled == True)
        )
        return [row[0] for row in result.all()]
    
    # ==========================================
    # Caching
    # ==========================================
    
    async def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get flag from cache if valid."""
        global _flag_cache, _cache_timestamp
        
        if not _cache_timestamp:
            return None
        
        # Check if cache is stale
        if (datetime.utcnow() - _cache_timestamp).total_seconds() > CACHE_TTL_SECONDS:
            return None
        
        return _flag_cache.get(key)
    
    async def _refresh_cache(self) -> None:
        """Refresh the flag cache from database."""
        global _flag_cache, _cache_timestamp
        
        flags = await self.get_all_flags()
        _flag_cache = {
            flag.key: {
                "enabled": flag.enabled,
                "targeting_rules": flag.targeting_rules,
            }
            for flag in flags
        }
        _cache_timestamp = datetime.utcnow()
    
    def _invalidate_cache(self) -> None:
        """Invalidate the cache."""
        global _cache_timestamp
        _cache_timestamp = None
    
    def _check_targeting(self, rules: Dict[str, Any], user: User) -> bool:
        """Check if user matches targeting rules."""
        if not rules:
            return True
        
        # Check plan targeting
        if "plans" in rules:
            if user.plan not in rules["plans"]:
                return False
        
        # Check role targeting
        if "roles" in rules:
            if user.role not in rules["roles"]:
                return False
        
        # Check specific user targeting
        if "user_ids" in rules:
            if str(user.id) not in rules["user_ids"]:
                return False
        
        return True

