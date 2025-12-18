"""Repository for Web Push subscriptions.

Responsibilities:
- Upsert (create/update) subscriptions by endpoint
- Delete subscriptions (unsubscribe + invalid endpoints)
- List subscriptions for sending notifications
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.push_subscription import PushSubscription


class PushSubscriptionRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def upsert(
        self,
        *,
        endpoint: str,
        p256dh: str,
        auth: str,
        expiration_time: Optional[datetime],
        user_agent: Optional[str],
    ) -> PushSubscription:
        result = await self._db.execute(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint).limit(1)
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            existing = PushSubscription(
                endpoint=endpoint,
                p256dh=p256dh,
                auth=auth,
                expiration_time=expiration_time,
                user_agent=user_agent,
            )
            self._db.add(existing)
        else:
            existing.p256dh = p256dh
            existing.auth = auth
            existing.expiration_time = expiration_time
            if user_agent:
                existing.user_agent = user_agent

        await self._db.commit()
        await self._db.refresh(existing)
        return existing

    async def delete_by_endpoint(self, *, endpoint: str) -> int:
        result = await self._db.execute(
            delete(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )
        await self._db.commit()
        return int(result.rowcount or 0)

    async def delete_by_endpoints(self, *, endpoints: List[str]) -> int:
        if not endpoints:
            return 0
        result = await self._db.execute(
            delete(PushSubscription).where(PushSubscription.endpoint.in_(endpoints))
        )
        await self._db.commit()
        return int(result.rowcount or 0)

    async def list_all(self, *, limit: int = 5000) -> List[PushSubscription]:
        result = await self._db.execute(select(PushSubscription).limit(limit))
        return list(result.scalars().all())


