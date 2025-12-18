import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime, timezone

from app.services.tax.affiliate_tax_report_service import AffiliateTaxReportService


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


def _mock_payout(*, amount: str, tax_amount_usd: str | None, completed_at: datetime):
    payout = MagicMock()
    payout.amount = Decimal(amount)
    payout.tax_amount_usd = Decimal(tax_amount_usd) if tax_amount_usd is not None else None
    payout.status = "completed"
    payout.completed_at = completed_at
    payout.payout_method = "paypal"
    payout.asset_symbol = "USD"
    payout.asset_amount = Decimal(amount)
    payout.asset_chain = None
    payout.transaction_hash = None
    payout.valuation_usd_per_asset = Decimal("1.0")
    payout.valuation_source = "usd"
    payout.valuation_at = completed_at
    payout.provider_payout_id = "provider_1"
    payout.id = "payout_1"
    return payout


def _mock_affiliate(*, affiliate_id: str, user_id: str, tax_form_type: str | None, tax_form_status: str):
    affiliate = MagicMock()
    affiliate.id = affiliate_id
    affiliate.user_id = user_id
    affiliate.legal_name = "Test Legal"
    affiliate.business_name = None
    affiliate.tax_form_type = tax_form_type
    affiliate.tax_form_status = tax_form_status
    affiliate.tax_id_type = "ssn"
    affiliate.tax_id_number = "123456789"
    affiliate.tax_address_street = "1 Main St"
    affiliate.tax_address_city = "City"
    affiliate.tax_address_state = "ST"
    affiliate.tax_address_zip = "12345"
    affiliate.tax_address_country = "US"
    return affiliate


def _mock_user(*, user_id: str, email: str):
    user = MagicMock()
    user.id = user_id
    user.email = email
    return user


@pytest.mark.asyncio
async def test_build_1099_nec_summaries_groups_by_affiliate_and_flags_missing_tax_info():
    db = AsyncMock()

    # Create 3 affiliates with payouts in the same tax year
    ts = datetime(2025, 6, 1, tzinfo=timezone.utc)

    # US verified affiliate above threshold
    aff_us_ok = _mock_affiliate(affiliate_id="aff_us_ok", user_id="user1", tax_form_type="w9", tax_form_status="verified")
    user1 = _mock_user(user_id="user1", email="user1@example.com")
    p1 = _mock_payout(amount="500.00", tax_amount_usd="500.00", completed_at=ts)
    p2 = _mock_payout(amount="200.00", tax_amount_usd="199.50", completed_at=ts)

    # Non-US affiliate (w8ben)
    aff_non_us = _mock_affiliate(affiliate_id="aff_non_us", user_id="user2", tax_form_type="w8ben", tax_form_status="verified")
    user2 = _mock_user(user_id="user2", email="user2@example.com")
    p3 = _mock_payout(amount="700.00", tax_amount_usd="700.00", completed_at=ts)

    # US affiliate above threshold but missing verification
    aff_us_missing = _mock_affiliate(affiliate_id="aff_us_missing", user_id="user3", tax_form_type="w9", tax_form_status="submitted")
    user3 = _mock_user(user_id="user3", email="user3@example.com")
    p4 = _mock_payout(amount="800.00", tax_amount_usd="800.00", completed_at=ts)

    rows = [
        (p1, aff_us_ok, user1),
        (p2, aff_us_ok, user1),
        (p3, aff_non_us, user2),
        (p4, aff_us_missing, user3),
    ]

    db.execute = AsyncMock(return_value=_FakeResult(rows))

    service = AffiliateTaxReportService(db)
    report = await service.build_1099_nec_summaries(tax_year=2025, minimum_usd=Decimal("600.00"), include_tin=False)

    assert report["tax_year"] == 2025
    assert report["counts"]["total_affiliates_with_payouts"] == 3
    assert report["counts"]["us_above_threshold"] == 2  # includes missing verification affiliate for review
    assert report["counts"]["non_us"] == 1
    assert report["counts"]["missing_tax_info"] == 1

    # Missing tax info should include aff_us_missing
    missing = report["missing_tax_info"]
    assert len(missing) == 1
    assert missing[0]["affiliate_id"] == "aff_us_missing"


