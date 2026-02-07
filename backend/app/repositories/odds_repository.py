"""
Minimal odds data for candidate leg building (avoids loading full ORM graphs).
"""

from __future__ import annotations

from typing import Any, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.market import Market
from app.models.odds import Odds

# Preferred bookmakers for best odds (same order as OddsSnapshotBuilder).
PREFERRED_BOOKS = ["draftkings", "fanduel", "betmgm", "caesars", "pointsbet", "betrivers"]


async def fetch_minimal_odds_rows(
    db: AsyncSession,
    *,
    game_ids: List[Any],
    allowed_market_keys: List[str],
    max_books: int = 6,
    max_rows: int | None = None,
) -> List[dict]:
    """
    Fetch minimal odds rows for the given games and market types.

    Returns list of dicts with: game_id, market_id, market_type, book, outcome,
    price, decimal_price, implied_prob, created_at.
    Filters to preferred books, keeps best odds per (game, market_type, outcome),
    and caps total rows at max_rows (default parlay_max_odds_rows_processed).
    """
    if not game_ids:
        return []
    max_rows = max_rows if max_rows is not None else getattr(settings, "parlay_max_odds_rows_processed", 600)
    books = [b.lower() for b in PREFERRED_BOOKS[: max_books]]

    # Raw rows: join markets + odds, filter by game_id, market_type, book.
    q = (
        select(
            Market.game_id,
            Market.id.label("market_id"),
            Market.market_type,
            Market.book,
            Odds.outcome,
            Odds.price,
            Odds.decimal_price,
            Odds.implied_prob,
            Odds.created_at,
        )
        .select_from(Odds)
        .join(Market, Odds.market_id == Market.id)
        .where(Market.game_id.in_(game_ids))
        .where(Market.market_type.in_(allowed_market_keys))
        .where(func.lower(Market.book).in_(books))
        .order_by(Market.game_id, Market.market_type, Odds.outcome, Odds.implied_prob.desc())
    )
    result = await db.execute(q)
    rows = result.all()

    # Keep best row per (game_id, market_type, outcome) up to max_rows.
    seen: set[tuple[Any, str, str]] = set()
    out: List[dict] = []
    for r in rows:
        if len(out) >= max_rows:
            break
        key = (r.game_id, r.market_type or "", r.outcome or "")
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "game_id": r.game_id,
            "market_id": r.market_id,
            "market_type": r.market_type,
            "book": r.book,
            "outcome": r.outcome,
            "price": r.price,
            "decimal_price": float(r.decimal_price) if r.decimal_price is not None else 0.0,
            "implied_prob": float(r.implied_prob) if r.implied_prob is not None else 0.0,
            "created_at": r.created_at,
        })
    return out
