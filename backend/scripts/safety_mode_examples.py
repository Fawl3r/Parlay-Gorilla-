"""
Emit actual JSON for GET /ops/safety and example parlay responses (GREEN / YELLOW / RED).
Run from backend: python scripts/safety_mode_examples.py

Requires: DATABASE_URL and THE_ODDS_API_KEY in env (or .env) so the app loads.
"""

import json
import os
import sys

# Run from backend directory; ensure app is importable
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
os.chdir(backend_dir)
if not os.path.exists("app/main.py"):
    print("Run from backend: cd backend && python scripts/safety_mode_examples.py", file=sys.stderr)
    sys.exit(1)

def main():
    from starlette.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # --- 1) GET /ops/safety (actual response) ---
    print("=== GET /ops/safety (local) ===\n")
    r = client.get("/ops/safety")
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text}
    print(json.dumps(body, indent=2))
    print("\n")

    # --- 2) Force YELLOW: set very old refresh timestamps (no patch) ---
    from app.core import telemetry
    telemetry.set("last_successful_odds_refresh_at", 1.0)
    telemetry.set("last_successful_games_refresh_at", 1.0)
    r2 = client.get("/ops/safety")
    snap_yellow = r2.json()
    print("=== GET /ops/safety (forced YELLOW via stale refresh) ===\n")
    print(json.dumps(snap_yellow, indent=2))
    print("\n")

    # --- 3) Force RED: exceed error_count_5m threshold ---
    for _ in range(30):
        telemetry.inc("error_count_5m")
    r3 = client.get("/ops/safety")
    snap_red = r3.json()
    print("=== GET /ops/safety (forced RED via error_count_5m) ===\n")
    print(json.dumps(snap_red, indent=2))
    print("\n")

    # --- 4) Example parlay response bodies ---
    print("=== Example parlay responses ===\n")
    print("RED (503) — from POST /api/parlay/suggest when state is RED:")
    red_body = {
        "safety_mode": "RED",
        "message": "Parlay generation temporarily paused for data reliability. Try again soon.",
        "reasons": snap_red.get("reasons", []),
    }
    print(json.dumps(red_body, indent=2))
    print("\nYELLOW (200) — excerpt added to normal ParlayResponse:")
    yellow_excerpt = {
        "safety_mode": "YELLOW",
        "warning": "Limited data mode.",
        "reasons": snap_yellow.get("reasons", [])[:3],
        "...": "rest: id, legs, parlay_hit_prob, overall_confidence, etc.",
    }
    print(json.dumps(yellow_excerpt, indent=2))
    print("\nGREEN (200): normal ParlayResponse; safety_mode, warning, reasons are null/absent.")


if __name__ == "__main__":
    main()
