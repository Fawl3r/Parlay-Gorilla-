"""
Quick parlay endpoint timing repro.

Purpose:
- Reproduce and time backend parlay endpoints without relying on the frontend.
- Useful while working on timeout/performance fixes.

Usage (from repo root):
  python scripts/repro_parlay_time.py

Notes:
- Creates a throwaway test user via /api/auth/register to obtain a JWT.
- Then calls:
  - POST /api/parlay/suggest
  - POST /api/parlay/suggest/triple
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class ReproConfig:
    base_url: str = "http://127.0.0.1:8000"
    request_timeout_seconds: float = 220.0
    register_timeout_seconds: float = 30.0
    sport: str = "NFL"
    num_legs: int = 3
    risk_profile: str = "balanced"


def _truncate(text: str, limit: int = 400) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _register_and_get_token(cfg: ReproConfig) -> str:
    email = f"perf-{int(time.time())}@example.com"
    password = "Passw0rd!"

    with httpx.Client(timeout=cfg.register_timeout_seconds) as client:
        r = client.post(
            f"{cfg.base_url}/api/auth/register",
            json={"email": email, "password": password},
        )
        print(f"[register] status={r.status_code}")
        if not r.is_success:
            raise RuntimeError(_truncate(r.text))
        data = r.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError("No access_token returned from /api/auth/register")
        return str(token)


def _time_post(client: httpx.Client, url: str, payload: dict) -> tuple[int, float, str]:
    start = time.time()
    r = client.post(url, json=payload)
    elapsed = time.time() - start
    return r.status_code, elapsed, r.text


def main() -> None:
    cfg = ReproConfig()
    token = _register_and_get_token(cfg)

    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=cfg.request_timeout_seconds, headers=headers) as client:
        status, elapsed, body = _time_post(
            client,
            f"{cfg.base_url}/api/parlay/suggest",
            {
                "num_legs": cfg.num_legs,
                "risk_profile": cfg.risk_profile,
                "sports": [cfg.sport],
            },
        )
        print(f"[suggest] status={status} elapsed_s={elapsed:.2f}")
        print(_truncate(body))

        status, elapsed, body = _time_post(
            client,
            f"{cfg.base_url}/api/parlay/suggest/triple",
            {"sports": [cfg.sport]},
        )
        print(f"[triple] status={status} elapsed_s={elapsed:.2f}")
        print(_truncate(body))


if __name__ == "__main__":
    main()


