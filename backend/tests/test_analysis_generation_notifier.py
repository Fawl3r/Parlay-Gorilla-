from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_analysis_generation_notifier_builds_payload_and_sends(db, monkeypatch):
    from app.core.config import settings
    from app.models.push_subscription import PushSubscription
    from app.services.notifications.analysis_generation_notifier import AnalysisGenerationNotifier
    from app.services.notifications.web_push_sender import WebPushSendSummary, WebPushSender

    monkeypatch.setattr(settings, "web_push_enabled", True)
    monkeypatch.setattr(settings, "web_push_vapid_public_key", "test_public")
    monkeypatch.setattr(settings, "web_push_vapid_private_key", "test_private")
    monkeypatch.setattr(settings, "web_push_subject", "mailto:test@example.com")

    sub = PushSubscription(
        endpoint="https://example.com/push/endpoint-1",
        p256dh="p256dh",
        auth="auth",
        expiration_time=datetime.utcnow() + timedelta(days=30),
        user_agent="pytest",
    )
    db.add(sub)
    await db.commit()

    captured = {}

    async def _fake_send_to_subscriptions(self: WebPushSender, *, subscriptions, payload):
        captured["payload"] = payload
        subs = list(subscriptions)
        return WebPushSendSummary(attempted=len(subs), sent=len(subs), invalid_removed=0, failed=0)

    monkeypatch.setattr(WebPushSender, "send_to_subscriptions", _fake_send_to_subscriptions)

    result = await AnalysisGenerationNotifier(db).notify_batch(generated_count=12)
    assert result.generated_count == 12
    assert result.attempted == 1
    assert result.sent == 1

    payload = captured.get("payload") or {}
    assert payload.get("title")
    assert "12" in str(payload.get("body"))
    assert payload.get("url") == "/analysis"
    assert payload.get("tag") == "analysis-generated"


@pytest.mark.asyncio
async def test_analysis_generation_notifier_noop_when_disabled(db, monkeypatch):
    from app.core.config import settings
    from app.services.notifications.analysis_generation_notifier import AnalysisGenerationNotifier

    monkeypatch.setattr(settings, "web_push_enabled", False)
    res = await AnalysisGenerationNotifier(db).notify_batch(generated_count=5)
    assert res.generated_count == 5
    assert res.attempted == 0
    assert res.sent == 0


