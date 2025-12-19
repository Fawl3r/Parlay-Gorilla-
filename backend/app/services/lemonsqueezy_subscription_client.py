"""
LemonSqueezy API client for subscription lifecycle operations.

Currently supports:
- Cancelling a subscription (stops future renewals; access remains until period end).

Docs:
- https://docs.lemonsqueezy.com/api/subscriptions/cancel-subscription
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

import httpx

logger = logging.getLogger(__name__)


class LemonSqueezyApiError(RuntimeError):
    """Raised when LemonSqueezy API returns a non-success response."""

    def __init__(self, status_code: int, message: str, response_text: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


@dataclass(frozen=True)
class LemonSqueezySubscriptionClient:
    api_key: str
    timeout_seconds: float = 30.0

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def cancel_subscription(self, subscription_id: str) -> dict:
        """
        Cancel an active subscription in LemonSqueezy.

        This stops future renewals. The subscription remains valid until `ends_at`.
        """
        subscription_id = (subscription_id or "").strip()
        if not subscription_id:
            raise ValueError("subscription_id is required")

        url = f"https://api.lemonsqueezy.com/v1/subscriptions/{subscription_id}"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.delete(url, headers=self._headers())

        if resp.status_code < 200 or resp.status_code >= 300:
            # LemonSqueezy returns JSON:API error payloads; include raw text for logs.
            logger.warning(
                "LemonSqueezy cancel_subscription failed (status=%s, subscription_id=%s): %s",
                resp.status_code,
                subscription_id,
                resp.text,
            )
            raise LemonSqueezyApiError(
                status_code=resp.status_code,
                message="LemonSqueezy API error while cancelling subscription",
                response_text=resp.text,
            )

        try:
            return resp.json()
        except Exception as exc:  # pragma: no cover (defensive)
            raise LemonSqueezyApiError(
                status_code=resp.status_code,
                message="Invalid JSON returned by LemonSqueezy API",
                response_text=resp.text,
            ) from exc


