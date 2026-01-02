"""
Webhook signature verification tests.

Why this exists:
- The test suite forces webhook secrets to empty strings in `backend/conftest.py` so most
  integration tests don't require signature headers.
- Production MUST verify signatures. These tests explicitly enable secrets and ensure
  both Coinbase Commerce and LemonSqueezy handlers enforce HMAC verification.

NOTE: Coinbase Commerce tests are disabled for LemonSqueezy compliance.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid

import pytest
from httpx import AsyncClient

from app.core.config import settings


def _hmac_sha256_hex(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


# Coinbase Commerce webhook test disabled for LemonSqueezy compliance
# @pytest.mark.asyncio
# async def test_coinbase_webhook_signature_required_when_secret_set(client: AsyncClient, monkeypatch):
#     secret = f"cb_whsec_{uuid.uuid4()}"
#     monkeypatch.setattr(settings, "coinbase_commerce_webhook_secret", secret)
#
#     payload = {
#         "id": f"cb_evt_{uuid.uuid4()}",
#         "event": {
#             "type": "charge:pending",
#             "data": {
#                 "id": f"cb_charge_{uuid.uuid4()}",
#                 "metadata": {},
#             },
#         },
#     }
#     body = json.dumps(payload).encode("utf-8")
#     signature = _hmac_sha256_hex(secret, body)
#
#     ok = await client.post(
#         "/api/webhooks/coinbase",
#         content=body,
#         headers={
#             "Content-Type": "application/json",
#             "X-CC-Webhook-Signature": signature,
#         },
#     )
#     assert ok.status_code == 200
#
#     missing = await client.post(
#         "/api/webhooks/coinbase",
#         content=body,
#         headers={"Content-Type": "application/json"},
#     )
#     assert missing.status_code == 401
#
#     bad = await client.post(
#         "/api/webhooks/coinbase",
#         content=body,
#         headers={
#             "Content-Type": "application/json",
#             "X-CC-Webhook-Signature": "bad-signature",
#         },
#     )
#     assert bad.status_code == 401


@pytest.mark.asyncio
async def test_lemonsqueezy_webhook_signature_required_when_secret_set(client: AsyncClient, monkeypatch):
    secret = f"ls_whsec_{uuid.uuid4()}"
    monkeypatch.setattr(settings, "lemonsqueezy_webhook_secret", secret)

    payload = {
        "meta": {"event_name": "unknown_event", "webhook_id": f"ls_evt_{uuid.uuid4()}"},
        "data": {"id": f"ls_data_{uuid.uuid4()}", "attributes": {}},
    }
    body = json.dumps(payload).encode("utf-8")
    signature = _hmac_sha256_hex(secret, body)

    ok = await client.post(
        "/api/webhooks/lemonsqueezy",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": signature,
        },
    )
    assert ok.status_code == 200

    missing = await client.post(
        "/api/webhooks/lemonsqueezy",
        content=body,
        headers={"Content-Type": "application/json"},
    )
    assert missing.status_code == 401

    bad = await client.post(
        "/api/webhooks/lemonsqueezy",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": "bad-signature",
        },
    )
    assert bad.status_code == 401


