"""
Smoke test for Verification Records.

This script exercises the end-to-end API contract for user-initiated verification records.

Usage:
  python scripts/smoke_test_verification.py

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
        print_skip("Login", "Set SMOKE_EMAIL and SMOKE_PASSWORD (must be a Premium account for verification)")
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


async def save_custom_parlay(client: httpx.AsyncClient, cfg: SmokeConfig, token: str) -> Optional[dict]:
    r = await client.post(
        f"{cfg.backend_url}/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Smoke Test Verification",
            "legs": [
                {
                    "game_id": "00000000-0000-0000-0000-000000000001",
                    "pick": "home",
                    "market_type": "spreads",
                    "point": -3.5,
                }
            ],
        },
        timeout=30.0,
    )
    if r.status_code != 200:
        print_fail("Save custom parlay", f"HTTP {r.status_code}: {r.text}")
        return None
    data = r.json()
    saved_id = data.get("id")
    if not saved_id:
        print_fail("Save custom parlay", "Missing id in response")
        return None
    print_pass("Save custom parlay")
    return data


async def queue_verification(client: httpx.AsyncClient, cfg: SmokeConfig, token: str, saved_id: str) -> Optional[dict]:
    r = await client.post(
        f"{cfg.backend_url}/api/parlays/{saved_id}/verification/queue",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    )
    if r.status_code == 402:
        print_skip("Queue verification", "Premium required or quota/credits not available for this account")
        return None
    if r.status_code != 200:
        print_fail("Queue verification", f"HTTP {r.status_code}: {r.text}")
        return None

    data = r.json()
    if not data.get("id"):
        print_fail("Queue verification", "Missing verification record id in response")
        return None
    print_pass("Queue verification")
    return data


async def get_verification(client: httpx.AsyncClient, cfg: SmokeConfig, token: str, record_id: str) -> Optional[dict]:
    r = await client.get(
        f"{cfg.backend_url}/api/verification-records/{record_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20.0,
    )
    if r.status_code != 200:
        print_fail("Get verification record", f"HTTP {r.status_code}: {r.text}")
        return None
    data = r.json()
    print_pass("Get verification record")
    return data


async def wait_for_confirmation(
    client: httpx.AsyncClient, cfg: SmokeConfig, token: str, record_id: str, *, seconds: int
) -> bool:
    deadline = time.time() + max(1, seconds)
    while time.time() < deadline:
        data = await get_verification(client, cfg, token, record_id)
        if not data:
            return False
        status = str(data.get("status") or "").lower()
        if status == "confirmed":
            receipt = data.get("receipt_id")
            if not receipt:
                print_fail("Wait for confirmation", "Confirmed but missing receipt_id")
                return False
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
    async with httpx.AsyncClient() as client:
        token = await login(client, cfg)
        if not token:
            return 0

        saved = await save_custom_parlay(client, cfg, token)
        if not saved:
            return 1

        record = await queue_verification(client, cfg, token, str(saved["id"]))
        if not record:
            return 0

        record_id = str(record["id"])
        data = await get_verification(client, cfg, token, record_id)
        if not data:
            return 1

        if cfg.wait_seconds > 0:
            ok = await wait_for_confirmation(client, cfg, token, record_id, seconds=cfg.wait_seconds)
            return 0 if ok else 1

        return 0


if __name__ == "__main__":
    try:
        import asyncio

        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        raise SystemExit(130)


