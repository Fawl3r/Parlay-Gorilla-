"""PayPal Payouts API client (affiliate payouts).

Separated from `payout_service.py` to keep files small and responsibilities focused.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)


class PayPalPayoutsClient:
    """Small client for PayPal OAuth + Payouts API."""

    def __init__(
        self,
        *,
        environment: str,
        client_id: Optional[str],
        client_secret: Optional[str],
        timeout_seconds: float = 30.0,
    ):
        self.environment = environment
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout_seconds = timeout_seconds

    @property
    def _base_url(self) -> str:
        return "https://api-m.paypal.com" if self.environment == "production" else "https://api-m.sandbox.paypal.com"

    def is_configured(self) -> bool:
        return bool((self.client_id or "").strip() and (self.client_secret or "").strip())

    async def get_access_token(self) -> Optional[str]:
        """Get PayPal OAuth access token."""
        if not self.is_configured():
            logger.error("PayPal credentials not configured")
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self._base_url}/v1/oauth2/token",
                    data={"grant_type": "client_credentials"},
                    auth=(self.client_id, self.client_secret),
                    headers={
                        "Accept": "application/json",
                        "Accept-Language": "en_US",
                    },
                )

            if response.status_code != 200:
                logger.error("PayPal OAuth error: %s - %s", response.status_code, response.text[:500])
                return None

            data = response.json()
            return data.get("access_token")
        except Exception as exc:
            logger.error("Error getting PayPal access token: %s", exc, exc_info=True)
            return None

    async def create_payout(
        self,
        *,
        access_token: str,
        recipient_email: str,
        amount: float,
        currency: str,
        note: str,
        sender_batch_id: str,
    ) -> Dict[str, Any]:
        """Create a PayPal payout batch with a single recipient item."""
        try:
            payout_data = {
                "sender_batch_header": {
                    "sender_batch_id": sender_batch_id,
                    "email_subject": "Your affiliate commission payout",
                    "email_message": f"You have received ${amount:.2f} in affiliate commissions from Parlay Gorilla.",
                },
                "items": [
                    {
                        "recipient_type": "EMAIL",
                        "amount": {
                            "value": f"{amount:.2f}",
                            "currency": currency,
                        },
                        "receiver": recipient_email,
                        "note": note,
                        "sender_item_id": sender_batch_id,
                    }
                ],
            }

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self._base_url}/v1/payments/payouts",
                    json=payout_data,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {access_token}",
                    },
                )

            if response.status_code in (200, 201):
                data = response.json()
                batch_id = (data.get("batch_header", {}) or {}).get("payout_batch_id")
                return {"success": True, "batch_id": batch_id, "response": data}

            return {
                "success": False,
                "error": f"PayPal API error: {response.status_code}",
                "details": response.text[:2000],
            }
        except Exception as exc:
            logger.error("Error creating PayPal payout: %s", exc, exc_info=True)
            return {"success": False, "error": str(exc)}


