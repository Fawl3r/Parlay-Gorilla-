"""Fetch budget manager - rate limit external API calls with TTL tracking."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class FetchBudgetTracking(Base):
    """Database model for tracking fetch budgets."""
    
    __tablename__ = "fetch_budget_tracking"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    fetch_key = Column(String, unique=True, nullable=False, index=True)
    last_fetched_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ttl_seconds = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FetchBudgetManager:
    """Manage fetch budgets with DB-first, in-memory fallback."""
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self._db = db
        self._memory_cache: Dict[str, datetime] = {}
        self._use_db = db is not None
    
    async def should_fetch(self, key: str, ttl_seconds: int) -> bool:
        """
        Check if a fetch is allowed based on TTL.
        
        Args:
            key: Fetch key (e.g., "odds:{game_id}")
            ttl_seconds: Time-to-live in seconds
            
        Returns:
            True if fetch is allowed, False if still within TTL
        """
        if self._use_db:
            try:
                result = await self._db.execute(
                    select(FetchBudgetTracking).where(FetchBudgetTracking.fetch_key == key)
                )
                record = result.scalar_one_or_none()
                
                if record:
                    elapsed = (datetime.now(tz=timezone.utc) - record.last_fetched_at).total_seconds()
                    if elapsed < record.ttl_seconds:
                        return False
                return True
            except Exception:
                # DB unavailable, fall back to memory
                self._use_db = False
        
        # In-memory fallback
        if key in self._memory_cache:
            last_fetched = self._memory_cache[key]
            elapsed = (datetime.now(tz=timezone.utc) - last_fetched).total_seconds()
            if elapsed < ttl_seconds:
                return False
        
        return True
    
    async def mark_fetched(self, key: str, ttl_seconds: int) -> None:
        """
        Mark a fetch as completed.
        
        Args:
            key: Fetch key
            ttl_seconds: TTL to store for this key
        """
        now = datetime.now(tz=timezone.utc)
        
        if self._use_db:
            try:
                result = await self._db.execute(
                    select(FetchBudgetTracking).where(FetchBudgetTracking.fetch_key == key)
                )
                record = result.scalar_one_or_none()
                
                if record:
                    record.last_fetched_at = now
                    record.ttl_seconds = ttl_seconds
                else:
                    record = FetchBudgetTracking(
                        fetch_key=key,
                        last_fetched_at=now,
                        ttl_seconds=ttl_seconds,
                    )
                    self._db.add(record)
                
                await self._db.commit()
            except Exception:
                # DB unavailable, fall back to memory
                self._use_db = False
        
        # Always update memory cache (for fallback or hybrid)
        self._memory_cache[key] = now
