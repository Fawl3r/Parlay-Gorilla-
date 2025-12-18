"""Notifier for analysis generation events (Web Push)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.notifications.push_subscription_repository import PushSubscriptionRepository
from app.services.notifications.web_push_sender import WebPushCredentials, WebPushSender, WebPushSendSummary

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalysisGenerationNotificationResult:
    generated_count: int
    attempted: int
    sent: int
    invalid_removed: int
    failed: int


class AnalysisGenerationNotifier:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def notify_batch(self, *, generated_count: int) -> AnalysisGenerationNotificationResult:
        if generated_count <= 0:
            return AnalysisGenerationNotificationResult(
                generated_count=0, attempted=0, sent=0, invalid_removed=0, failed=0
            )

        if not getattr(settings, "web_push_enabled", False):
            return AnalysisGenerationNotificationResult(
                generated_count=generated_count, attempted=0, sent=0, invalid_removed=0, failed=0
            )

        repo = PushSubscriptionRepository(self._db)
        subscriptions = await repo.list_all(limit=10_000)
        if not subscriptions:
            return AnalysisGenerationNotificationResult(
                generated_count=generated_count, attempted=0, sent=0, invalid_removed=0, failed=0
            )

        payload = self._build_payload(generated_count=generated_count)
        sender = WebPushSender(
            credentials=WebPushCredentials(
                vapid_private_key=settings.web_push_vapid_private_key,
                vapid_subject=settings.web_push_subject,
            ),
            repo=repo,
            concurrency=8,
        )

        summary: WebPushSendSummary = await sender.send_to_subscriptions(
            subscriptions=subscriptions,
            payload=payload,
        )
        logger.info(
            "[WEB_PUSH] analysis_generated=%s attempted=%s sent=%s invalid_removed=%s failed=%s",
            generated_count,
            summary.attempted,
            summary.sent,
            summary.invalid_removed,
            summary.failed,
        )

        return AnalysisGenerationNotificationResult(
            generated_count=generated_count,
            attempted=summary.attempted,
            sent=summary.sent,
            invalid_removed=summary.invalid_removed,
            failed=summary.failed,
        )

    @staticmethod
    def _build_payload(*, generated_count: int) -> dict:
        title = "New game analyses ready"
        body = f"{generated_count} new game analyses were generated. Tap to view."
        return {
            "title": title,
            "body": body,
            "url": "/analysis",
            "tag": "analysis-generated",
            "data": {"generated_count": int(generated_count)},
        }


