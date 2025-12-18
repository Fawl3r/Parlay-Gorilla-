"""Web Push sending logic (pywebpush wrapper).

This module keeps pywebpush usage isolated so:
- other services can send Web Push notifications without dealing with low-level details
- we can centralize error handling (e.g., remove expired subscriptions on 404/410)
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable

from app.models.push_subscription import PushSubscription
from app.services.notifications.push_subscription_repository import PushSubscriptionRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebPushCredentials:
    vapid_private_key: str
    vapid_subject: str


@dataclass(frozen=True)
class WebPushSendSummary:
    attempted: int
    sent: int
    invalid_removed: int
    failed: int


class WebPushSender:
    def __init__(
        self,
        *,
        credentials: WebPushCredentials,
        repo: PushSubscriptionRepository,
        concurrency: int = 8,
    ):
        self._credentials = credentials
        self._repo = repo
        self._concurrency = max(1, int(concurrency or 1))

    async def send_to_subscriptions(
        self,
        *,
        subscriptions: Iterable[PushSubscription],
        payload: Dict[str, Any],
    ) -> WebPushSendSummary:
        subs = list(subscriptions)
        if not subs:
            return WebPushSendSummary(attempted=0, sent=0, invalid_removed=0, failed=0)

        data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        sem = asyncio.Semaphore(self._concurrency)

        async def _send_one(sub: PushSubscription) -> tuple[str, str]:
            async with sem:
                return await self._send_single(endpoint=sub.endpoint, p256dh=sub.p256dh, auth=sub.auth, data=data)

        tasks = [asyncio.create_task(_send_one(s)) for s in subs]
        results = await asyncio.gather(*tasks)

        sent = sum(1 for _, status in results if status == "sent")
        failed = sum(1 for _, status in results if status == "failed")
        invalid_endpoints = [endpoint for endpoint, status in results if status == "invalid"]

        invalid_removed = 0
        if invalid_endpoints:
            try:
                invalid_removed = await self._repo.delete_by_endpoints(endpoints=invalid_endpoints)
            except Exception as exc:
                logger.warning("Failed to remove invalid push subscriptions: %s", exc)

        return WebPushSendSummary(
            attempted=len(subs),
            sent=sent,
            invalid_removed=invalid_removed,
            failed=failed,
        )

    async def _send_single(
        self,
        *,
        endpoint: str,
        p256dh: str,
        auth: str,
        data: str,
    ) -> tuple[str, str]:
        try:
            from pywebpush import WebPushException, webpush  # type: ignore
        except ModuleNotFoundError:
            # Fail open: this keeps the app importable even if optional dependency
            # isn't installed (e.g., minimal dev/test environments).
            logger.error("pywebpush is not installed; cannot send Web Push notifications")
            return endpoint, "failed"

        subscription_info = {
            "endpoint": endpoint,
            "keys": {"p256dh": p256dh, "auth": auth},
        }
        try:
            await asyncio.to_thread(
                webpush,
                subscription_info=subscription_info,
                data=data,
                vapid_private_key=self._credentials.vapid_private_key,
                vapid_claims={"sub": self._credentials.vapid_subject},
            )
            return endpoint, "sent"
        except WebPushException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (404, 410):
                return endpoint, "invalid"
            logger.info("Web push failed for endpoint=%s status=%s", endpoint[:64], status)
            return endpoint, "failed"
        except Exception as exc:
            logger.info("Web push failed for endpoint=%s error=%s", endpoint[:64], exc)
            return endpoint, "failed"


