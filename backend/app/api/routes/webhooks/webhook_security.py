"""
Webhook security helpers (signature + safe ID parsing).

Single responsibility:
- Provide reusable HMAC-SHA256 signature verification helpers for webhook routes.
- Provide safe UUID parsing to prevent webhook routes from crashing on malformed payloads.
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class WebhookHmacSha256Signature:
    """
    Coinbase Commerce + LemonSqueezy both use a hex-encoded HMAC-SHA256 of the raw request body.

    IMPORTANT: Signatures must be computed from the **raw body bytes** exactly as received.
    """

    secret: str

    def expected_hexdigest(self, body: bytes) -> str:
        return hmac.new(self.secret.encode(), body, hashlib.sha256).hexdigest()

    def matches(self, *, body: bytes, provided_signature: Optional[str]) -> bool:
        provided = (provided_signature or "").strip()
        if not provided:
            return False
        expected = self.expected_hexdigest(body)
        return hmac.compare_digest(expected, provided)


class WebhookUuidParser:
    """Safe UUID parsing for webhook metadata/custom_data fields."""

    @staticmethod
    def try_parse(value: Optional[str]) -> Optional[uuid.UUID]:
        if not value:
            return None
        try:
            return uuid.UUID(str(value))
        except Exception:
            return None





