"""Affiliate tax reporting service (PayPal + crypto payouts).

This service is designed to make year-end reporting straightforward by:
- Summarizing total payouts per affiliate for a tax year (USD)
- Providing payout-level ledger lines including crypto valuation snapshots

Note: This is tooling to help generate accurate inputs for tax filing.
You should still review with a tax professional for your jurisdiction.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate import Affiliate
from app.models.affiliate_payout import AffiliatePayout, PayoutStatus
from app.models.user import User


def _tax_year_range_utc(tax_year: int) -> Tuple[datetime, datetime]:
    start = datetime(tax_year, 1, 1, tzinfo=timezone.utc)
    end = datetime(tax_year + 1, 1, 1, tzinfo=timezone.utc)
    return start, end


def _usd(value: Optional[Decimal]) -> Decimal:
    return value if value is not None else Decimal("0")


@dataclass(frozen=True)
class AffiliateTaxSummary:
    affiliate_id: str
    user_id: str
    email: str
    legal_name: Optional[str]
    business_name: Optional[str]
    tax_form_type: Optional[str]
    tax_form_status: str
    tax_id_type: Optional[str]
    tax_id_number: Optional[str]
    address_street: Optional[str]
    address_city: Optional[str]
    address_state: Optional[str]
    address_zip: Optional[str]
    address_country: Optional[str]
    total_tax_amount_usd: Decimal
    total_gross_amount_usd: Decimal
    payout_count: int

    def to_dict(self, *, include_tin: bool) -> Dict[str, Any]:
        return {
            "affiliate_id": self.affiliate_id,
            "user_id": self.user_id,
            "email": self.email,
            "legal_name": self.legal_name,
            "business_name": self.business_name,
            "tax_form_type": self.tax_form_type,
            "tax_form_status": self.tax_form_status,
            "tax_id_type": self.tax_id_type,
            "tax_id_number": self.tax_id_number if include_tin else None,
            "address": {
                "street": self.address_street,
                "city": self.address_city,
                "state": self.address_state,
                "zip": self.address_zip,
                "country": self.address_country,
            },
            "totals": {
                "tax_amount_usd": float(self.total_tax_amount_usd),
                "gross_amount_usd": float(self.total_gross_amount_usd),
                "payout_count": self.payout_count,
            },
        }


class AffiliateTaxReportService:
    """Builds affiliate payout summaries for tax workflows."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_payout_ledger_lines(self, tax_year: int) -> List[Dict[str, Any]]:
        """Return payout-level ledger lines for the year (for audit trail / accountant export)."""
        start, end = _tax_year_range_utc(tax_year)

        rows = (
            await self.db.execute(
                select(AffiliatePayout, Affiliate, User)
                .join(Affiliate, Affiliate.id == AffiliatePayout.affiliate_id)
                .join(User, User.id == Affiliate.user_id)
                .where(
                    and_(
                        AffiliatePayout.status == PayoutStatus.COMPLETED.value,
                        AffiliatePayout.completed_at.is_not(None),
                        AffiliatePayout.completed_at >= start,
                        AffiliatePayout.completed_at < end,
                    )
                )
                .order_by(AffiliatePayout.completed_at.asc())
            )
        ).all()

        lines: List[Dict[str, Any]] = []
        for payout, affiliate, user in rows:
            lines.append(
                {
                    "tax_year": tax_year,
                    "payout_id": str(payout.id),
                    "completed_at": payout.completed_at.isoformat() if payout.completed_at else None,
                    "affiliate_id": str(affiliate.id),
                    "user_id": str(user.id),
                    "email": user.email,
                    "payout_method": payout.payout_method,
                    "gross_amount_usd": float(payout.amount),
                    "tax_amount_usd": float(payout.tax_amount_usd) if payout.tax_amount_usd is not None else float(payout.amount),
                    "asset_symbol": payout.asset_symbol,
                    "asset_amount": float(payout.asset_amount) if payout.asset_amount is not None else None,
                    "asset_chain": payout.asset_chain,
                    "transaction_hash": payout.transaction_hash,
                    "valuation_usd_per_asset": float(payout.valuation_usd_per_asset) if payout.valuation_usd_per_asset is not None else None,
                    "valuation_source": payout.valuation_source,
                    "valuation_at": payout.valuation_at.isoformat() if payout.valuation_at else None,
                    "provider_payout_id": payout.provider_payout_id,
                }
            )

        return lines

    async def build_1099_nec_summaries(
        self,
        *,
        tax_year: int,
        minimum_usd: Decimal = Decimal("600.00"),
        include_tin: bool = False,
    ) -> Dict[str, Any]:
        """Build year-end 1099-style summaries (US persons) + flags for missing tax info.

        Returns a dict containing:
        - `tax_year`
        - `minimum_usd`
        - `generated_at`
        - `us_affiliates` (candidates >= minimum)
        - `below_threshold`
        - `non_us_affiliates`
        - `missing_tax_info` (needs W-9/W-8BEN verification)
        """
        start, end = _tax_year_range_utc(tax_year)

        rows = (
            await self.db.execute(
                select(AffiliatePayout, Affiliate, User)
                .join(Affiliate, Affiliate.id == AffiliatePayout.affiliate_id)
                .join(User, User.id == Affiliate.user_id)
                .where(
                    and_(
                        AffiliatePayout.status == PayoutStatus.COMPLETED.value,
                        AffiliatePayout.completed_at.is_not(None),
                        AffiliatePayout.completed_at >= start,
                        AffiliatePayout.completed_at < end,
                    )
                )
            )
        ).all()

        # Aggregate per affiliate
        agg: Dict[str, Dict[str, Any]] = {}
        for payout, affiliate, user in rows:
            aff_id = str(affiliate.id)
            bucket = agg.get(aff_id)
            if not bucket:
                bucket = {
                    "affiliate": affiliate,
                    "user": user,
                    "gross_total": Decimal("0"),
                    "tax_total": Decimal("0"),
                    "count": 0,
                }
                agg[aff_id] = bucket

            bucket["gross_total"] += _usd(payout.amount)
            bucket["tax_total"] += _usd(payout.tax_amount_usd) if payout.tax_amount_usd is not None else _usd(payout.amount)
            bucket["count"] += 1

        us_affiliates: List[AffiliateTaxSummary] = []
        below_threshold: List[AffiliateTaxSummary] = []
        non_us_affiliates: List[AffiliateTaxSummary] = []
        missing_tax_info: List[AffiliateTaxSummary] = []

        for aff_id, bucket in agg.items():
            affiliate: Affiliate = bucket["affiliate"]
            user: User = bucket["user"]
            gross_total: Decimal = bucket["gross_total"]
            tax_total: Decimal = bucket["tax_total"]
            count: int = bucket["count"]

            summary = AffiliateTaxSummary(
                affiliate_id=aff_id,
                user_id=str(user.id),
                email=user.email,
                legal_name=affiliate.legal_name,
                business_name=affiliate.business_name,
                tax_form_type=affiliate.tax_form_type,
                tax_form_status=affiliate.tax_form_status,
                tax_id_type=affiliate.tax_id_type,
                tax_id_number=affiliate.tax_id_number,
                address_street=affiliate.tax_address_street,
                address_city=affiliate.tax_address_city,
                address_state=affiliate.tax_address_state,
                address_zip=affiliate.tax_address_zip,
                address_country=affiliate.tax_address_country,
                total_tax_amount_usd=tax_total,
                total_gross_amount_usd=gross_total,
                payout_count=count,
            )

            # Flag missing / unverified tax info when above threshold
            if tax_total >= minimum_usd and affiliate.tax_form_status != "verified":
                missing_tax_info.append(summary)

            # Route into US vs non-US buckets
            if affiliate.tax_form_type == "w8ben":
                non_us_affiliates.append(summary)
            else:
                # Treat w9 or unknown as US bucket for review
                if tax_total >= minimum_usd:
                    us_affiliates.append(summary)
                else:
                    below_threshold.append(summary)

        # Sort descending by tax total for convenience
        us_affiliates.sort(key=lambda s: s.total_tax_amount_usd, reverse=True)
        below_threshold.sort(key=lambda s: s.total_tax_amount_usd, reverse=True)
        non_us_affiliates.sort(key=lambda s: s.total_tax_amount_usd, reverse=True)
        missing_tax_info.sort(key=lambda s: s.total_tax_amount_usd, reverse=True)

        return {
            "tax_year": tax_year,
            "minimum_usd": float(minimum_usd),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "us_affiliates": [s.to_dict(include_tin=include_tin) for s in us_affiliates],
            "below_threshold": [s.to_dict(include_tin=include_tin) for s in below_threshold],
            "non_us_affiliates": [s.to_dict(include_tin=include_tin) for s in non_us_affiliates],
            "missing_tax_info": [s.to_dict(include_tin=include_tin) for s in missing_tax_info],
            "counts": {
                "total_affiliates_with_payouts": len(agg),
                "us_above_threshold": len(us_affiliates),
                "us_below_threshold": len(below_threshold),
                "non_us": len(non_us_affiliates),
                "missing_tax_info": len(missing_tax_info),
            },
        }


