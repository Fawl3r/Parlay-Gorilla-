"""
Repository for `UsageLimit` persistence and idempotent creation.

Extracted from `subscription_service.py` to keep files small and responsibilities focused.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import logging
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage_limit import UsageLimit

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UsageLimitRepository:
    db: AsyncSession

    async def get_or_create_today(self, user_id: str) -> UsageLimit:
        """Get or create usage record for today."""
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.error("Invalid user_id format: %s", user_id)
            raise ValueError(f"Invalid user_id: {user_id}")

        today = date.today()

        try:
            result = await self.db.execute(
                select(UsageLimit).where(and_(UsageLimit.user_id == user_uuid, UsageLimit.date == today))
            )
            usage = result.scalar_one_or_none()

            if usage:
                return usage

            usage = UsageLimit(
                id=uuid.uuid4(),
                user_id=user_uuid,
                date=today,
                free_parlays_generated=0,
            )
            self.db.add(usage)
            try:
                await self.db.commit()
                await self.db.refresh(usage)
                return usage
            except Exception as commit_error:
                await self.db.rollback()

                # Handle race condition where another request created the row.
                error_str = str(commit_error).lower()
                if "unique" in error_str or "duplicate" in error_str:
                    result = await self.db.execute(
                        select(UsageLimit).where(and_(UsageLimit.user_id == user_uuid, UsageLimit.date == today))
                    )
                    usage = result.scalar_one_or_none()
                    if usage:
                        return usage

                logger.error("Error creating usage record: %s", commit_error)
                raise
        except Exception as e:
            logger.error("Database error in get_or_create_today for user %s: %s", user_id, e)
            import traceback

            logger.error(traceback.format_exc())
            raise


