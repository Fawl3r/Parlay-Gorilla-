#!/usr/bin/env python3
"""
Smoke test: /healthz, /readyz, /api/sports.
Fails loudly if /sports is missing sport_state, is_enabled, or slug.
Availability contract: every UI tab id (analysis hub) exists in /api/sports slugs.
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

# Analysis hub tab ids; each must exist in /api/sports slugs (lowercased). Keeps UI/API in sync.
EXPECTED_ANALYSIS_HUB_TAB_IDS = ["nfl", "nba", "nhl", "mlb", "ncaaf", "ncaab", "epl", "mls"]


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

    # 3) /api/sports — availability contract: slug, sport_state, is_enabled; short cache; tab ids exist
    try:
        r = httpx.get(f"{BASE_URL}/api/sports", timeout=TIMEOUT)
        if r.status_code != 200:
            errors.append(f"/api/sports: HTTP {r.status_code}")
        else:
            cache_control = r.headers.get("Cache-Control", "")
            if "max-age=60" not in cache_control:
                errors.append(f"/api/sports: expected max-age=60 in Cache-Control, got {cache_control!r}")
            items = r.json()
            if not isinstance(items, list):
                errors.append(f"/api/sports: expected list, got {type(items)}")
            else:
                slugs_lower = set()
                for i, item in enumerate(items):
                    if not isinstance(item, dict):
                        errors.append(f"/api/sports[{i}]: expected object, got {type(item)}")
                        continue
                    if "slug" not in item:
                        errors.append(f"/api/sports[{i}]: missing slug")
                    if "sport_state" not in item:
                        errors.append(f"/api/sports[{i}]: missing sport_state (slug={item.get('slug')})")
                    if "is_enabled" not in item:
                        errors.append(f"/api/sports[{i}]: missing is_enabled (slug={item.get('slug')})")
                    slugs_lower.add((item.get("slug") or "").lower())
                for tab_id in EXPECTED_ANALYSIS_HUB_TAB_IDS:
                    if tab_id.lower() not in slugs_lower:
                        errors.append(
                            f"/api/sports: availability contract broken — UI tab id {tab_id!r} not in slugs. "
                            "Add to backend or remove from frontend SPORT_TABS."
                        )
    except Exception as e:
        errors.append(f"/api/sports: {e}")

    if errors:
        print("SMOKE TEST FAILED", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("SMOKE TEST OK: /healthz, /readyz, /api/sports (slug, sport_state, is_enabled, cache, tab ids)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
