"""Admin tax reporting routes (affiliate payouts)."""

from __future__ import annotations

import csv
import io
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.admin.auth import require_admin
from app.core.dependencies import get_db
from app.models.user import User
from app.services.tax.affiliate_tax_report_service import AffiliateTaxReportService


router = APIRouter()


def _csv_response(*, filename: str, csv_text: str) -> Response:
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/affiliates/1099-nec")
async def get_affiliate_1099_nec_summary(
    tax_year: int = Query(..., ge=2000, le=2100),
    minimum_usd: float = Query(600.0, ge=0),
    include_tin: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """JSON summary for 1099-NEC style reporting (plus flags for missing tax info)."""
    service = AffiliateTaxReportService(db)
    return await service.build_1099_nec_summaries(
        tax_year=tax_year,
        minimum_usd=Decimal(str(minimum_usd)),
        include_tin=include_tin,
    )


@router.get("/affiliates/1099-nec.csv")
async def export_affiliate_1099_nec_csv(
    tax_year: int = Query(..., ge=2000, le=2100),
    minimum_usd: float = Query(600.0, ge=0),
    include_tin: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """CSV export of 1099-NEC candidate summaries."""
    service = AffiliateTaxReportService(db)
    report = await service.build_1099_nec_summaries(
        tax_year=tax_year,
        minimum_usd=Decimal(str(minimum_usd)),
        include_tin=include_tin,
    )

    output = io.StringIO()
    fieldnames = [
        "tax_year",
        "affiliate_id",
        "user_id",
        "email",
        "legal_name",
        "business_name",
        "tax_form_type",
        "tax_form_status",
        "tax_id_type",
        "tax_id_number",
        "address_street",
        "address_city",
        "address_state",
        "address_zip",
        "address_country",
        "total_tax_amount_usd",
        "total_gross_amount_usd",
        "payout_count",
        "is_above_threshold",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    def _write_rows(items: list[dict], is_above_threshold: bool) -> None:
        for item in items:
            addr = item.get("address", {}) or {}
            totals = item.get("totals", {}) or {}
            writer.writerow(
                {
                    "tax_year": report["tax_year"],
                    "affiliate_id": item.get("affiliate_id"),
                    "user_id": item.get("user_id"),
                    "email": item.get("email"),
                    "legal_name": item.get("legal_name"),
                    "business_name": item.get("business_name"),
                    "tax_form_type": item.get("tax_form_type"),
                    "tax_form_status": item.get("tax_form_status"),
                    "tax_id_type": item.get("tax_id_type"),
                    "tax_id_number": item.get("tax_id_number") if include_tin else "",
                    "address_street": addr.get("street"),
                    "address_city": addr.get("city"),
                    "address_state": addr.get("state"),
                    "address_zip": addr.get("zip"),
                    "address_country": addr.get("country"),
                    "total_tax_amount_usd": totals.get("tax_amount_usd"),
                    "total_gross_amount_usd": totals.get("gross_amount_usd"),
                    "payout_count": totals.get("payout_count"),
                    "is_above_threshold": is_above_threshold,
                }
            )

    _write_rows(report.get("us_affiliates", []), True)
    _write_rows(report.get("below_threshold", []), False)
    _write_rows(report.get("non_us_affiliates", []), False)

    filename = f"affiliate-1099-nec-summary-{tax_year}.csv"
    return _csv_response(filename=filename, csv_text=output.getvalue())


@router.get("/affiliates/payout-ledger")
async def get_affiliate_payout_ledger(
    tax_year: int = Query(..., ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """JSON payout-level ledger lines (includes crypto valuation snapshot columns)."""
    service = AffiliateTaxReportService(db)
    return {"tax_year": tax_year, "lines": await service.list_payout_ledger_lines(tax_year)}


@router.get("/affiliates/payout-ledger.csv")
async def export_affiliate_payout_ledger_csv(
    tax_year: int = Query(..., ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """CSV payout-level ledger lines (includes crypto valuation snapshot columns)."""
    service = AffiliateTaxReportService(db)
    lines = await service.list_payout_ledger_lines(tax_year)

    output = io.StringIO()
    if not lines:
        # Still return header-only CSV for consistency
        fieldnames = [
            "tax_year",
            "payout_id",
            "completed_at",
            "affiliate_id",
            "user_id",
            "email",
            "payout_method",
            "gross_amount_usd",
            "tax_amount_usd",
            "asset_symbol",
            "asset_amount",
            "asset_chain",
            "transaction_hash",
            "valuation_usd_per_asset",
            "valuation_source",
            "valuation_at",
            "provider_payout_id",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        return _csv_response(filename=f"affiliate-payout-ledger-{tax_year}.csv", csv_text=output.getvalue())

    fieldnames = list(lines[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(lines)

    filename = f"affiliate-payout-ledger-{tax_year}.csv"
    return _csv_response(filename=filename, csv_text=output.getvalue())


