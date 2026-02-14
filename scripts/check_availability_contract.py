#!/usr/bin/env python3
"""
CI/local smoke: GET /ops/availability-contract. Fails if contract is broken.

Requires OPS_DEBUG_ENABLED=true on the backend. In CI, run with backend up and
OPS_DEBUG_ENABLED=true (and optionally OPS_DEBUG_TOKEN).

Usage:
  python scripts/check_availability_contract.py
  python scripts/check_availability_contract.py --base-url http://localhost:8000
  OPS_DEBUG_TOKEN=secret python scripts/check_availability_contract.py --token secret

Exit codes: 0 ok, 1 contract broken, 2 forbidden/403. 404 -> 0 only if ALLOW_OPS_DISABLED=true.

CI: Do NOT set ALLOW_OPS_DISABLED=true in CI. Use it only for local/prod checks where the
ops endpoint may be intentionally disabled; otherwise the check would silently pass when
the endpoint is missing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

try:
    import httpx
except ImportError:
    print("pip install httpx", file=sys.stderr)
    sys.exit(1)

TIMEOUT = 10.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check /ops/availability-contract")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("BASE_URL", "http://localhost:8000"),
        help="Backend base URL (default: BASE_URL env or http://localhost:8000)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("OPS_DEBUG_TOKEN"),
        help="X-Ops-Token (default: OPS_DEBUG_TOKEN env)",
    )
    args = parser.parse_args()
    base_url = (args.base_url or "").rstrip("/")
    token = args.token
    allow_ops_disabled = os.environ.get("ALLOW_OPS_DISABLED", "").lower() in ("1", "true", "yes")

    url = f"{base_url}/ops/availability-contract"
    headers = {}
    if token:
        headers["X-Ops-Token"] = token

    try:
        r = httpx.get(url, headers=headers or None, timeout=TIMEOUT)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if r.status_code == 404:
        print("ops debug disabled (404)")
        if allow_ops_disabled:
            return 0
        print("Set OPS_DEBUG_ENABLED=true on the backend, or ALLOW_OPS_DISABLED=true to pass anyway.", file=sys.stderr)
        return 1

    if r.status_code == 403:
        print("Forbidden (403). Set X-Ops-Token / OPS_DEBUG_TOKEN if the backend requires it.", file=sys.stderr)
        return 2

    if r.status_code != 200:
        print(f"ERROR: {r.status_code} {r.text[:200]}", file=sys.stderr)
        return 1

    try:
        data = r.json()
    except Exception as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        return 1

    if data.get("ok") is True:
        counts = data.get("counts", {})
        print(f"Availability contract OK: {counts.get('sports', 0)} sports, {counts.get('enabled', 0)} enabled.")
        return 0

    print("Availability contract FAILED:", file=sys.stderr)
    issues = data.get("issues", {})
    if issues.get("missing_required"):
        print("  missing_required:", json.dumps(issues["missing_required"], indent=4), file=sys.stderr)
    if issues.get("type_errors"):
        print("  type_errors:", json.dumps(issues["type_errors"], indent=4), file=sys.stderr)
    if issues.get("duplicate_slugs"):
        print("  duplicate_slugs:", issues["duplicate_slugs"], file=sys.stderr)
    if issues.get("unknown_sport_state_values"):
        print("  unknown_sport_state_values:", json.dumps(issues["unknown_sport_state_values"], indent=4), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
