"""Check 2025 NFL (or other sport) data availability from API-Sports cache.

Sportsradar has been removed. This script uses the API-Sports repository (DB cache).
Run the API-Sports refresh/backfill first so the DB has fixtures for 2025.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import async_session_maker
from app.repositories.sports_data_repository import SportsDataRepository


async def check_2025_data():
    """Check 2025 fixture data in API-Sports cache (DB)."""
    print("\n" + "=" * 60)
    print("CHECKING 2025 DATA (API-Sports cache)")
    print("=" * 60 + "\n")

    from_ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
    to_ts = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    async with async_session_maker() as db:
        repo = SportsDataRepository(db)
        fixtures = await repo.get_fixtures(
            sport="nfl",
            from_date=from_ts,
            to_date=to_ts,
        )
        if fixtures:
            print(f"[OK] Found {len(fixtures)} NFL fixtures in cache for 2025")
            dates = sorted(set(getattr(f, "date", None) for f in fixtures))
            dates = [d for d in dates if d is not None]
            if dates:
                print(f"  Date range: {dates[0]} to {dates[-1]}")
        else:
            print("[INFO] No 2025 NFL fixtures in API-Sports cache.")
            print("       Run SportsRefreshService/backfill with API_SPORTS_API_KEY set to populate.")

    print(f"\nCurrent date: {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(check_2025_data())
