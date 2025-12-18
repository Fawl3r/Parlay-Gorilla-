"""
Backfill progress checker.

Counts processed games by sport and season (year) and shows ATS/O/U coverage.
"""

import asyncio
from collections import defaultdict
from typing import Dict, Any

from sqlalchemy import select, func

from app.database.session import AsyncSessionLocal
from app.models.game_results import GameResult


async def fetch_progress() -> Dict[str, Any]:
    """
    Aggregate backfill progress grouped by sport and season year.
    Returns a dict structure suitable for printing or JSON.
    """
    async with AsyncSessionLocal() as db:
        stmt = (
            select(
                GameResult.sport,
                func.extract("year", GameResult.game_date).label("year"),
                func.count(GameResult.id).label("games_total"),
                func.count(GameResult.home_covered_spread).label("games_with_ats"),
                func.count(GameResult.total_over_under).label("games_with_ou"),
            )
            .group_by(GameResult.sport, func.extract("year", GameResult.game_date))
            .order_by(GameResult.sport, func.extract("year", GameResult.game_date))
        )
        result = await db.execute(stmt)

        progress: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(dict)
        totals = {"games_total": 0, "games_with_ats": 0, "games_with_ou": 0}

        for row in result.fetchall():
            sport = row.sport
            year = str(int(row.year))
            games_total = int(row.games_total or 0)
            games_with_ats = int(row.games_with_ats or 0)
            games_with_ou = int(row.games_with_ou or 0)

            progress[sport][year] = {
                "games_total": games_total,
                "games_with_ats": games_with_ats,
                "games_with_ou": games_with_ou,
            }

            totals["games_total"] += games_total
            totals["games_with_ats"] += games_with_ats
            totals["games_with_ou"] += games_with_ou

        return {"progress": progress, "totals": totals}


def print_progress(data: Dict[str, Any]) -> None:
    """Pretty-print progress to console."""
    progress = data["progress"]
    totals = data["totals"]

    print("\n=== BACKFILL PROGRESS ===")
    for sport in sorted(progress.keys()):
        print(f"\n{sport}")
        for year in sorted(progress[sport].keys()):
            stats = progress[sport][year]
            games = stats["games_total"]
            ats = stats["games_with_ats"]
            ou = stats["games_with_ou"]
            ats_pct = f"{(ats / games * 100):.1f}%" if games else "0%"
            ou_pct = f"{(ou / games * 100):.1f}%" if games else "0%"
            print(
                f"  {year}: {games} games "
                f"({ats} ATS, {ou} O/U) "
                f"[ATS {ats_pct}, O/U {ou_pct}]"
            )

    print("\nTotals:")
    print(
        f"  Games: {totals['games_total']}, "
        f"ATS: {totals['games_with_ats']}, "
        f"O/U: {totals['games_with_ou']}"
    )
    print("=========================\n")


async def main():
    data = await fetch_progress()
    print_progress(data)


if __name__ == "__main__":
    asyncio.run(main())

