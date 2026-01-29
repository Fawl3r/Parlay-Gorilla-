#!/usr/bin/env python3
"""
Operator verification: parlay generation health and suggest endpoint.

1) GET /api/health/parlay-generation?sport=... (no auth)
2) Optional: POST /api/auth/login with env creds, then POST /api/parlay/suggest for NFL + one other sport
3) Prints window, games_in_window, markets, placeholder_count, candidate_leg_count; reason_code + key counts from suggest

Usage:
  python scripts/verify_parlay_candidates.py
  BACKEND_URL=https://api.example.com python scripts/verify_parlay_candidates.py
  VERIFY_LOGIN_EMAIL=user@example.com VERIFY_LOGIN_PASSWORD=secret BACKEND_URL=http://localhost:8000 python scripts/verify_parlay_candidates.py
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
VERIFY_LOGIN_EMAIL = os.getenv("VERIFY_LOGIN_EMAIL", "").strip()
VERIFY_LOGIN_PASSWORD = os.getenv("VERIFY_LOGIN_PASSWORD", "").strip()
SPORTS = ["NFL", "NBA"]


def get_health_parlay(sport: str) -> Dict[str, Any]:
    r = httpx.get(f"{BACKEND_URL}/api/health/parlay-generation", params={"sport": sport}, timeout=30.0)
    r.raise_for_status()
    return r.json()


def login() -> Optional[str]:
    if not VERIFY_LOGIN_EMAIL or not VERIFY_LOGIN_PASSWORD:
        return None
    r = httpx.post(
        f"{BACKEND_URL}/api/auth/login",
        json={"email": VERIFY_LOGIN_EMAIL, "password": VERIFY_LOGIN_PASSWORD},
        timeout=15.0,
    )
    if r.status_code != 200:
        print(f"Login failed: {r.status_code} {r.text[:200]}")
        return None
    data = r.json()
    return data.get("access_token") or data.get("token") or data.get("jwt")


def suggest_parlay(sport: str, token: str) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"sport": sport, "num_legs": 3, "risk_profile": "balanced"}
    r = httpx.post(
        f"{BACKEND_URL}/api/parlay/suggest",
        json=payload,
        headers=headers,
        timeout=60.0,
    )
    return {"status_code": r.status_code, "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else {"detail": r.text[:500]}}


def main() -> int:
    print(f"Backend: {BACKEND_URL}")
    print("=" * 60)

    for sport in SPORTS:
        try:
            data = get_health_parlay(sport)
            window = data.get("window", {})
            print(f"\n[{sport}] /health/parlay-generation")
            print(f"  window: {window.get('start')} .. {window.get('end')} (mode={window.get('mode')})")
            print(f"  games_in_window: {data.get('games_in_window')}")
            print(f"  markets: games_with_markets={data.get('markets_coverage', {}).get('games_with_markets')}, total_markets={data.get('markets_coverage', {}).get('total_markets')}")
            print(f"  placeholder_count: {data.get('placeholder_count')}")
            print(f"  candidate_leg_count: {data.get('candidate_leg_count')}")
        except Exception as e:
            print(f"\n[{sport}] /health/parlay-generation error: {e}")
            return 1

    token = login()
    if token:
        print("\n" + "=" * 60)
        print("Parlay suggest (authenticated)")
        for sport in SPORTS:
            try:
                out = suggest_parlay(sport, token)
                sc = out["status_code"]
                body = out["body"]
                reason_code = body.get("reason_code") or body.get("detail") or (body.get("error_code") if isinstance(body.get("detail"), dict) else None)
                if isinstance(body.get("detail"), dict):
                    reason_code = body["detail"].get("reason_code") or body["detail"].get("error_code") or str(body["detail"])[:80]
                elif isinstance(body.get("detail"), str):
                    reason_code = body["detail"][:80]
                legs = body.get("legs") or []
                print(f"\n[{sport}] POST /parlay/suggest -> {sc}")
                print(f"  reason_code / detail: {reason_code}")
                print(f"  legs: {len(legs)}")
                if legs:
                    print(f"  first_leg game: {legs[0].get('game', {}).get('home_team')} vs {legs[0].get('game', {}).get('away_team')}")
            except Exception as e:
                print(f"\n[{sport}] suggest error: {e}")
    else:
        print("\n(Skip parlay/suggest: set VERIFY_LOGIN_EMAIL and VERIFY_LOGIN_PASSWORD to run authenticated suggest)")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
