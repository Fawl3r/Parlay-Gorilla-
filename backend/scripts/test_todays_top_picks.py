"""
Test Today's Top Picks endpoint and pipeline.

Usage:
  # Test against a running backend (default http://localhost:8000)
  python scripts/test_todays_top_picks.py

  # Test against production
  BASE_URL=https://api.parlaygorilla.com python scripts/test_todays_top_picks.py

  # Inline pipeline check (no server; uses DB from backend/.env)
  python scripts/test_todays_top_picks.py --inline
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend root so we can import app
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


def _fetch_url(url: str, timeout: float = 30) -> dict:
    try:
        import urllib.request
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"_error": str(e)}


async def _run_inline():
    """Call the same pipeline as the endpoint (get_candidate_legs) and print counts."""
    from datetime import datetime, timezone
    from app.database.session import AsyncSessionLocal
    from app.services.probability_engine import get_probability_engine

    sports = ["NFL", "NBA", "NHL", "MLB"]
    now = datetime.now(timezone.utc)
    total = 0
    async with AsyncSessionLocal() as db:
        for sport in sports:
            try:
                engine = get_probability_engine(db, sport)
                candidates = await engine.get_candidate_legs(
                    sport=sport,
                    min_confidence=0.0,
                    max_legs=200,
                    week=None,
                    include_player_props=False,
                    now_utc=now,
                )
                n = len(candidates or [])
                total += n
                print(f"  {sport}: {n} candidate legs")
                if n and total <= 20:
                    c = (candidates or [])[0]
                    print(f"    sample: game_id={c.get('game_id')} game={c.get('game')} conf={c.get('confidence_score')}")
            except Exception as e:
                print(f"  {sport}: error - {e}")
        print(f"  Total: {total} candidate legs")
    return total


def main():
    parser = argparse.ArgumentParser(description="Test Today's Top Picks")
    parser.add_argument("--inline", action="store_true", help="Run pipeline inline (no HTTP)")
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://localhost:8000"), help="API base URL")
    args = parser.parse_args()

    if args.inline:
        print("Running inline pipeline (DB from backend/.env)...")
        total = asyncio.run(_run_inline())
        if total == 0:
            print("FAIL: no candidate legs from pipeline (check DB and odds data)")
            sys.exit(1)
        print("OK: pipeline returned candidate legs")
        sys.exit(0)

    url = args.base_url.rstrip("/") + "/api/public/todays-top-picks"
    print(f"GET {url}")
    data = _fetch_url(url)
    if "_error" in data:
        print(f"FAIL: {data['_error']}")
        sys.exit(1)
    picks = data.get("picks") or []
    print(f"Response: as_of={data.get('as_of')} date={data.get('date')} picks={len(picks)}")
    for i, p in enumerate(picks[:5]):
        print(f"  [{i+1}] {p.get('sport')} {p.get('matchup')} conf={p.get('confidence')} {p.get('market')} {p.get('selection')}")
    if len(picks) > 5:
        print(f"  ... and {len(picks) - 5} more")
    if not picks:
        print("FAIL: no picks returned (expected at least one when games are available)")
        sys.exit(1)
    print("OK: top picks endpoint returned picks")
    sys.exit(0)


if __name__ == "__main__":
    main()
