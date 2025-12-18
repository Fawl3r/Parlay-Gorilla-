import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.services.tax.valuation_service import UsdValuationService
from app.services.tax.valuation_quote import UsdValuationQuote


@pytest.mark.asyncio
async def test_usdc_valuation_falls_back_to_peg_when_external_disabled():
    service = UsdValuationService(external_quotes_enabled=False)
    quote = await service.quote_usd_per_asset("USDC")

    assert isinstance(quote, UsdValuationQuote)
    assert quote.asset_symbol == "USDC"
    assert quote.usd_per_asset == Decimal("1.0")
    assert quote.source == "stablecoin_peg"
    assert quote.as_of.tzinfo is not None


@pytest.mark.asyncio
async def test_usdc_valuation_uses_coinbase_when_available(monkeypatch):
    async def _fake_coinbase(_symbol: str):
        return UsdValuationQuote(
            asset_symbol="USDC",
            usd_per_asset=Decimal("1.001"),
            source="coinbase_spot",
            as_of=datetime(2025, 1, 1, tzinfo=timezone.utc),
            raw={"data": {"amount": "1.001"}},
        )

    service = UsdValuationService(external_quotes_enabled=True)
    monkeypatch.setattr(service, "_try_coinbase_spot", _fake_coinbase)

    quote = await service.quote_usd_per_asset("USDC")

    assert quote.source == "coinbase_spot"
    assert quote.usd_per_asset == Decimal("1.001")


