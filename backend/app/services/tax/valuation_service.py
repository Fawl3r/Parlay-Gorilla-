"""USD valuation service for tax reporting.

This is used to snapshot fair-market-value (FMV) inputs at payout time,
especially for crypto payouts.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

import httpx

from app.services.tax.valuation_quote import UsdValuationQuote

logger = logging.getLogger(__name__)


class UsdValuationService:
    """Fetches/derives USD-per-asset quotes for tax snapshots."""

    _STABLECOINS = {"USDC", "USDT", "DAI"}

    def __init__(
        self,
        *,
        external_quotes_enabled: bool = True,
        timeout_seconds: float = 3.0,
    ):
        self.external_quotes_enabled = external_quotes_enabled
        self.timeout_seconds = timeout_seconds

    async def quote_usd_per_asset(self, asset_symbol: str) -> UsdValuationQuote:
        """Return a USD-per-asset quote suitable for persisting as a tax snapshot."""
        symbol = (asset_symbol or "").strip().upper()
        now = datetime.now(timezone.utc)

        if not symbol:
            raise ValueError("asset_symbol is required")

        # For stablecoins, we prefer a live quote (if enabled), but fall back to peg.
        if symbol in self._STABLECOINS:
            if self.external_quotes_enabled:
                quote = await self._try_coinbase_spot(symbol)
                if quote:
                    return quote

            return UsdValuationQuote(
                asset_symbol=symbol,
                usd_per_asset=Decimal("1.0"),
                source="stablecoin_peg",
                as_of=now,
                raw={"note": "Fallback peg valuation (1.0) used"},
            )

        # Non-stable assets: require external quote for now.
        if self.external_quotes_enabled:
            quote = await self._try_coinbase_spot(symbol)
            if quote:
                return quote

        raise ValueError(f"Unsupported asset_symbol for valuation: {symbol}")

    async def _try_coinbase_spot(self, asset_symbol: str) -> Optional[UsdValuationQuote]:
        """Attempt to fetch a spot USD quote from Coinbase public API (no key required)."""
        symbol = asset_symbol.upper()
        url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
        now = datetime.now(timezone.utc)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.get(url, headers={"Accept": "application/json"})

            if resp.status_code != 200:
                logger.warning(
                    "Coinbase spot quote failed: status=%s asset=%s body=%s",
                    resp.status_code,
                    symbol,
                    resp.text[:500],
                )
                return None

            payload: Dict[str, Any] = resp.json()
            amount_str = (
                payload.get("data", {}) or {}
            ).get("amount")
            if not amount_str:
                logger.warning("Coinbase spot quote missing amount: asset=%s payload=%s", symbol, payload)
                return None

            try:
                usd_per_asset = Decimal(str(amount_str))
            except (InvalidOperation, TypeError):
                logger.warning("Coinbase spot quote invalid amount: asset=%s amount=%s", symbol, amount_str)
                return None

            if usd_per_asset <= 0:
                logger.warning("Coinbase spot quote non-positive: asset=%s amount=%s", symbol, usd_per_asset)
                return None

            return UsdValuationQuote(
                asset_symbol=symbol,
                usd_per_asset=usd_per_asset,
                source="coinbase_spot",
                as_of=now,
                raw=payload,
            )
        except Exception as exc:
            logger.warning("Coinbase spot quote error: asset=%s err=%s", symbol, exc)
            return None


