#!/usr/bin/env python3
"""
Smoke test: /healthz, /readyz, /api/sports.
Fails loudly if /sports is missing sport_state or is_enabled.
Usage: python scripts/smoke_test.py
       API_BASE_URL=https://api.example.com python scripts/smoke_test.py
"""

from __future__ import annotations

import os
import sys

try:
    import httpx
except ImportError:
    print("pip install httpx", file=sys.stderr)
    sys.exit(1)

BASE_URL = os.environ.get("API_BASE_URL", "https://api.parlaygorilla.com").rstrip("/")
TIMEOUT = 15.0


def main() -> int:
    errors = []

    # 1) /healthz
    try:
        r = httpx.get(f"{BASE_URL}/healthz", timeout=TIMEOUT)
        if r.status_code != 200:
            errors.append(f"/healthz: HTTP {r.status_code}")
        else:
            data = r.json()
            if not data.get("ok"):
                errors.append(f"/healthz: ok not true: {data}")
    except Exception as e:
        errors.append(f"/healthz: {e}")

    # 2) /readyz
    try:
        r = httpx.get(f"{BASE_URL}/readyz", timeout=TIMEOUT)
        if r.status_code != 200:
            errors.append(f"/readyz: HTTP {r.status_code} (not ready)")
        else:
            data = r.json()
            if not data.get("ok"):
                errors.append(f"/readyz: ok not true: {data}")
    except Exception as e:
        errors.append(f"/readyz: {e}")

    # 3) /api/sports — must include sport_state and is_enabled per item
    try:
        r = httpx.get(f"{BASE_URL}/api/sports", timeout=TIMEOUT)
        if r.status_code != 200:
            errors.append(f"/api/sports: HTTP {r.status_code}")
        else:
            items = r.json()
            if not isinstance(items, list):
                errors.append(f"/api/sports: expected list, got {type(items)}")
            else:
                for i, item in enumerate(items):
                    if not isinstance(item, dict):
                        errors.append(f"/api/sports[{i}]: expected object, got {type(item)}")
                        continue
                    if "sport_state" not in item:
                        errors.append(f"/api/sports[{i}]: missing sport_state (slug={item.get('slug')})")
                    if "is_enabled" not in item:
                        errors.append(f"/api/sports[{i}]: missing is_enabled (slug={item.get('slug')})")
    except Exception as e:
        errors.append(f"/api/sports: {e}")

    if errors:
        print("SMOKE TEST FAILED", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("SMOKE TEST OK: /healthz, /readyz, /api/sports (sport_state + is_enabled)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
