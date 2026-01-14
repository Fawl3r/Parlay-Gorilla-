"""
Repository for `UsageLimit` persistence and idempotent creation.

Extracted from `subscription_service.py` to keep files small and responsibilities focused.

Now handles rolling 7-day windows instead of daily limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import logging
import uuid

from sqlalchemy import and_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage_limit import UsageLimit

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UsageLimitRepository:
    db: AsyncSession

    async def get_or_create_weekly(self, user_id: str) -> UsageLimit:
        """
        Get or create usage record for rolling 7-day window.
        
        If no record exists or the window has expired (7 days passed), creates/resets a new window.
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.error("Invalid user_id format: %s", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        now = datetime.now(timezone.utc)
        today = now.date()

        try:
            # Get the most recent usage record for this user
            result = await self.db.execute(
                select(UsageLimit)
                .where(UsageLimit.user_id == user_uuid)
                .order_by(desc(UsageLimit.date))
                .limit(1)
            )
            usage = result.scalar_one_or_none()

            # If no record exists, create one
            if not usage:
                usage = await self._create_new_usage(user_uuid, now, today)
                return usage

            # Check if window has expired (7 days passed)
            if usage.is_window_expired(days=7):
                # Reset the window
                usage.reset_window()
                self.db.add(usage)
                try:
                    await self.db.commit()
                    await self.db.refresh(usage)
                    return usage
                except Exception as commit_error:
                    await self.db.rollback()
                    # Handle race condition - another request may have reset it
                    result = await self.db.execute(
                        select(UsageLimit)
                        .where(UsageLimit.user_id == user_uuid)
                        .order_by(desc(UsageLimit.date))
                        .limit(1)
                    )
                    usage = result.scalar_one_or_none()
                    if usage and not usage.is_window_expired(days=7):
                        return usage
                    # If still expired, create new
                    return await self._create_new_usage(user_uuid, now, today)

            # Window is still active, return existing record
            return usage

        except Exception as e:
            logger.error("Database error in get_or_create_weekly for user %s: %s", user_id, e)
            import traceback
            logger.error(traceback.format_exc())
            raise

    async def _create_new_usage(self, user_uuid: uuid.UUID, now: datetime, today: date) -> UsageLimit:
        """Create a new usage record with fresh 7-day window."""
        usage = UsageLimit(
            id=uuid.uuid4(),
            user_id=user_uuid,
            date=today,
            first_usage_at=now,
            free_parlays_generated=0,
            custom_parlays_built=0,
        )
        self.db.add(usage)
        try:
            await self.db.commit()
            await self.db.refresh(usage)
            return usage
        except Exception as commit_error:
            await self.db.rollback()
            # Handle race condition where another request created the row
            error_str = str(commit_error).lower()
            if "unique" in error_str or "duplicate" in error_str:
                result = await self.db.execute(
                    select(UsageLimit)
                    .where(UsageLimit.user_id == user_uuid)
                    .order_by(desc(UsageLimit.date))
                    .limit(1)
                )
                existing = result.scalar_one_or_none()
                if existing:
                    return existing
            logger.error("Error creating usage record: %s", commit_error)
            raise

    async def get_or_create_today(self, user_id: str) -> UsageLimit:
        """
        Legacy method for backward compatibility.
        Now delegates to get_or_create_weekly for rolling 7-day window.
        """
        return await self.get_or_create_weekly(user_id)


