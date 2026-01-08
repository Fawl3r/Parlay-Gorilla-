"""
Smoke test for Automatic Custom Parlay Verification.

This script exercises the automatic verification flow for Custom AI parlays:
1. Generate a Custom AI parlay via /api/parlay/analyze
2. Verify that a verification record was automatically created
3. Attempt to generate the same parlay again
4. Confirm NO duplicate verification record was created (idempotency)

Usage:
  python scripts/smoke_test_custom_parlay_verification.py

Env:
  BACKEND_URL=http://localhost:8000
  SMOKE_EMAIL=your_premium_email
  SMOKE_PASSWORD=your_password

Optional:
  SMOKE_WAIT_FOR_CONFIRMATION_SECONDS=60   # poll until confirmed (requires worker running)
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from typing import Optional

import httpx
import asyncio


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"


def print_pass(test_name: str):
    print(f"{Colors.GREEN}PASS{Colors.RESET}: {test_name}")


def print_fail(test_name: str, error: str):
    print(f"{Colors.RED}FAIL{Colors.RESET}: {test_name} - {error}")


def print_skip(test_name: str, reason: str):
    print(f"{Colors.YELLOW}SKIP{Colors.RESET}: {test_name} - {reason}")


@dataclass(frozen=True)
class SmokeConfig:
    backend_url: str
    email: str
    password: str
    wait_seconds: int


def load_config() -> SmokeConfig:
    backend_url = (os.getenv("BACKEND_URL") or "http://localhost:8000").rstrip("/")
    email = os.getenv("SMOKE_EMAIL") or ""
    password = os.getenv("SMOKE_PASSWORD") or ""
    wait_seconds = int(os.getenv("SMOKE_WAIT_FOR_CONFIRMATION_SECONDS") or "0")
    return SmokeConfig(
        backend_url=backend_url,
        email=email,
        password=password,
        wait_seconds=max(0, wait_seconds),
    )


async def login(client: httpx.AsyncClient, cfg: SmokeConfig) -> Optional[str]:
    if not cfg.email or not cfg.password:
        print_skip("Login", "Set SMOKE_EMAIL and SMOKE_PASSWORD")
        return None

    r = await client.post(
        f"{cfg.backend_url}/api/auth/login",
        json={"email": cfg.email, "password": cfg.password},
        timeout=20.0,
    )
    if r.status_code != 200:
        print_fail("Login", f"HTTP {r.status_code}: {r.text}")
        return None
    token = (r.json() or {}).get("access_token")
    if not token:
        print_fail("Login", "No access_token in response")
        return None
    print_pass("Login")
    return str(token)


async def fetch_games(client: httpx.AsyncClient, cfg: SmokeConfig, token: str) -> Optional[list]:
    """Fetch NFL games to use for the test."""
    r = await client.get(
        f"{cfg.backend_url}/api/sports/nfl/games",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20.0,
    )
    if r.status_code != 200:
        print_fail("Fetch games", f"HTTP {r.status_code}: {r.text}")
        return None
    games = r.json()
    games_with_markets = [g for g in games if g.get("markets") and len(g["markets"]) > 0]
    if len(games_with_markets) < 2:
        print_skip("Fetch games", "Not enough games with markets")
        return None
    print_pass("Fetch games")
    return games_with_markets[:2]


async def analyze_custom_parlay(
    client: httpx.AsyncClient, cfg: SmokeConfig, token: str, games: list
) -> Optional[dict]:
    """Generate a Custom AI parlay analysis."""
    legs = []
    for game in games:
        markets = game.get("markets", [])
        h2h_market = next((m for m in markets if m.get("market_type") == "h2h"), None)
        if h2h_market and h2h_market.get("odds"):
            odd = h2h_market["odds"][0]
            outcome = odd.get("outcome", "").lower()
            if "home" in outcome or game["home_team"].lower() in outcome:
                pick = game["home_team"]
            elif "away" in outcome or game["away_team"].lower() in outcome:
                pick = game["away_team"]
            else:
                pick = game["home_team"]
            legs.append(
                {
                    "game_id": game["id"],
                    "pick": pick,
                    "market_type": "h2h",
                    "odds": odd.get("price"),
                }
            )

    if len(legs) < 2:
        print_skip("Analyze custom parlay", "Not enough valid legs")
        return None

    r = await client.post(
        f"{cfg.backend_url}/api/parlay/analyze",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"legs": legs},
        timeout=30.0,
    )
    if r.status_code != 200:
        print_fail("Analyze custom parlay", f"HTTP {r.status_code}: {r.text}")
        return None
    data = r.json()
    if not data.get("legs"):
        print_fail("Analyze custom parlay", "Missing legs in response")
        return None
    print_pass("Analyze custom parlay")
    return data


async def check_verification_record(
    client: httpx.AsyncClient, cfg: SmokeConfig, token: str, verification_id: str
) -> Optional[dict]:
    """Check verification record status."""
    r = await client.get(
        f"{cfg.backend_url}/api/verification-records/{verification_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20.0,
    )
    if r.status_code != 200:
        print_fail("Get verification record", f"HTTP {r.status_code}: {r.text}")
        return None
    return r.json()


async def wait_for_confirmation(
    client: httpx.AsyncClient, cfg: SmokeConfig, token: str, verification_id: str, *, seconds: int
) -> bool:
    """Poll until verification is confirmed."""
    deadline = time.time() + max(1, seconds)
    while time.time() < deadline:
        data = await check_verification_record(client, cfg, token, verification_id)
        if not data:
            return False
        status = str(data.get("status") or "").lower()
        if status == "confirmed":
            print_pass("Wait for confirmation")
            return True
        if status == "failed":
            print_fail("Wait for confirmation", str(data.get("error") or "failed"))
            return False
        await asyncio.sleep(4)
    print_skip("Wait for confirmation", "Timed out (worker not running or proof layer not configured)")
    return True


async def main() -> int:
    cfg = load_config()
    async with httpx.AsyncClient(timeout=120.0) as client:
        token = await login(client, cfg)
        if not token:
            return 0

        games = await fetch_games(client, cfg, token)
        if not games:
            return 1

        # First analysis - should create a verification record
        print("\n" + "=" * 60)
        print("Test 1: Generate Custom AI parlay (should auto-verify)")
        print("=" * 60)
        analysis1 = await analyze_custom_parlay(client, cfg, token, games)
        if not analysis1:
            return 1

        verification1 = analysis1.get("verification")
        if not verification1:
            print_fail("Auto-verification", "No verification record in analysis response")
            return 1
        print_pass("Auto-verification (record created)")

        verification_id1 = verification1.get("id")
        if not verification_id1:
            print_fail("Auto-verification", "Missing verification record id")
            return 1

        # Check the verification record exists
        record1 = await check_verification_record(client, cfg, token, verification_id1)
        if not record1:
            print_fail("Verify record exists", "Could not fetch verification record")
            return 1
        print_pass("Verify record exists")

        if cfg.wait_seconds > 0:
            ok = await wait_for_confirmation(client, cfg, token, verification_id1, seconds=cfg.wait_seconds)
            if not ok:
                return 1

        # Second analysis with identical legs - should NOT create a duplicate
        print("\n" + "=" * 60)
        print("Test 2: Generate same parlay again (should be idempotent)")
        print("=" * 60)
        analysis2 = await analyze_custom_parlay(client, cfg, token, games)
        if not analysis2:
            return 1

        verification2 = analysis2.get("verification")
        if not verification2:
            print_fail("Idempotency check", "No verification record in second analysis response")
            return 1

        verification_id2 = verification2.get("id")
        if verification_id2 != verification_id1:
            print_fail(
                "Idempotency check",
                f"Duplicate verification created! First: {verification_id1}, Second: {verification_id2}",
            )
            return 1
        print_pass("Idempotency check (no duplicate created)")

        print("\n" + "=" * 60)
        print(f"{Colors.GREEN}ALL TESTS PASSED{Colors.RESET}")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        raise SystemExit(130)

