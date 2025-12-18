"""Small value object representing an asset USD valuation quote."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class UsdValuationQuote:
    """Represents a USD-per-asset valuation snapshot used for tax reporting."""

    asset_symbol: str
    usd_per_asset: Decimal
    source: str
    as_of: datetime
    raw: Optional[Dict[str, Any]] = None


