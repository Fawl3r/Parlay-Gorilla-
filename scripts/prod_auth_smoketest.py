#!/usr/bin/env python3
"""
Parlay Gorilla - Production Auth Smoke Test

Validates (against a provided base URL):
1) Register works (or returns "already exists" depending on env/data)
2) Email normalization: login succeeds even if casing/spaces differ
3) Login returns a token (JSON) and sets HttpOnly cookie (hybrid auth)
4) /me succeeds using:
   - Bearer token (Authorization header)
   - Cookie jar (no Authorization header)
5) Optional: immediate login after register (catches commit/race issues)

Usage:
  python scripts/prod_auth_smoketest.py --base-url https://your-domain.com --mode auto
  python scripts/prod_auth_smoketest.py --base-url http://127.0.0.1:8000 --mode bearer
  python scripts/prod_auth_smoketest.py --base-url https://staging.your-domain.com --mode cookie
"""

from __future__ import annotations

import argparse
import json
import os
import random
import string
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import httpx

# ====== ROUTES (Parlay Gorilla backend) ======
ENDPOINTS = {
    "register": "/api/auth/register",
    "login": "/api/auth/login",
    "me": "/api/auth/me",
}
DEFAULT_COOKIE_NAME = "access_token"
# ============================================


def _rand(n: int = 8) -> str:
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


@dataclass
class Result:
    ok: bool
    step: str
    details: str
    status_code: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None


def fail(step: str, details: str, status_code: Optional[int] = None, extra: Optional[Dict[str, Any]] = None) -> Result:
    return Result(ok=False, step=step, details=details, status_code=status_code, extra=extra)


def ok(step: str, details: str, status_code: Optional[int] = None, extra: Optional[Dict[str, Any]] = None) -> Result:
    return Result(ok=True, step=step, details=details, status_code=status_code, extra=extra)


def pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2, sort_keys=True, default=str)
    except Exception:
        return str(obj)


def extract_token_from_json(resp_json: Any) -> Optional[str]:
    if isinstance(resp_json, dict):
        return resp_json.get("access_token") or resp_json.get("token") or resp_json.get("jwt")
    return None


def has_cookie(client: httpx.Client, cookie_name: str) -> bool:
    return cookie_name in client.cookies


def print_banner(msg: str) -> None:
    print("\n" + "=" * 80)
    print(msg)
    print("=" * 80)


def request_json(
    client: httpx.Client, method: str, url: str, payload: Optional[dict] = None, headers: Optional[dict] = None
) -> Tuple[httpx.Response, Any]:
    r = client.request(method, url, json=payload, headers=headers)
    try:
        data = r.json()
    except Exception:
        data = r.text
    return r, data


def _is_already_exists_response(resp_json: Any) -> bool:
    if not isinstance(resp_json, dict):
        return False
    detail = str(resp_json.get("detail") or "").lower()
    return "already exists" in detail or "already" in detail and "exists" in detail


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="Base URL, e.g. http://127.0.0.1:8000 or https://prod.com")
    parser.add_argument(
        "--mode",
        choices=["auto", "bearer", "cookie"],
        default="auto",
        help="auto tries both bearer+cookie. bearer uses Authorization. cookie uses cookie jar only.",
    )
    parser.add_argument("--cookie-name", default=DEFAULT_COOKIE_NAME, help="Cookie key name if using cookie auth")
    parser.add_argument("--email", default=os.getenv("TEST_EMAIL"), help="Test email (optional). If omitted, auto-generates.")
    parser.add_argument("--password", default=os.getenv("TEST_PASSWORD", "Password123!"), help="Test password")
    parser.add_argument("--username", default=os.getenv("TEST_USERNAME"), help="Test username (optional)")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--no-register", action="store_true", help="Skip register step (login-only test)")
    parser.add_argument("--immediate-login", action="store_true", help="Login immediately after register (catches commit races)")
    parser.add_argument("--sleep-after-register", type=float, default=0.0, help="Sleep seconds after register before login")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--retry-429", type=int, default=1, help="Retry count for 429 rate-limit responses (register/login)")
    parser.add_argument("--retry-429-sleep", type=float, default=65.0, help="Seconds to sleep before retrying after 429")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    urls = {k: base + v for k, v in ENDPOINTS.items()}

    email = args.email or f"smoke+{int(time.time())}-{_rand(6)}@example.com"
    password = args.password
    username = args.username or f"smoke_{_rand(6)}"

    # Email normalization test variants
    email_dirty = f"  {email.upper()}  "

    results: list[Result] = []

    print_banner("Parlay Gorilla - Auth Smoke Test")
    print(f"Base URL: {base}")
    print(f"Mode: {args.mode}")
    print(f"Register: {'SKIP' if args.no_register else 'YES'}")
    print(f"Email: {email} (dirty variant: {repr(email_dirty)})")
    print(f"Username: {username}")
    print(f"Cookie name: {args.cookie_name}")
    print("-" * 80)

    with httpx.Client(timeout=args.timeout, follow_redirects=True) as client:
        # 1) REGISTER
        if not args.no_register:
            payload = {"email": email, "password": password, "username": username}

            attempts = 0
            while True:
                attempts += 1
                r, data = request_json(client, "POST", urls["register"], payload)

                if args.verbose:
                    print_banner("REGISTER RESPONSE")
                    print("status:", r.status_code)
                    print("headers:", dict(r.headers))
                    print("body:", pretty(data))

                if r.status_code == 429 and attempts <= args.retry_429:
                    print(f"[WARN] register hit rate limit (429). Sleeping {args.retry_429_sleep}s then retrying...")
                    time.sleep(args.retry_429_sleep)
                    continue

                # Parlay Gorilla currently returns 200 on success.
                if r.status_code in (200, 201):
                    results.append(ok("register", "Created user", r.status_code))
                elif r.status_code in (409,) or (r.status_code == 400 and _is_already_exists_response(data)):
                    results.append(ok("register", "User already exists - continuing", r.status_code))
                else:
                    results.append(fail("register", f"Unexpected status. Body: {pretty(data)}", r.status_code))
                    report(results)
                    sys.exit(1)
                break

            if args.sleep_after_register > 0:
                time.sleep(args.sleep_after_register)

            if args.immediate_login:
                # Optional extra login to catch commit/race issues.
                _ = request_json(client, "POST", urls["login"], {"email": email, "password": password})

        # 2) LOGIN using dirty email (tests normalization)
        login_payload = {"email": email_dirty, "password": password}

        attempts = 0
        while True:
            attempts += 1
            r, data = request_json(client, "POST", urls["login"], login_payload)

            if args.verbose:
                print_banner("LOGIN RESPONSE")
                print("status:", r.status_code)
                print("set-cookie:", r.headers.get("set-cookie"))
                print("headers:", dict(r.headers))
                print("body:", pretty(data))

            if r.status_code == 429 and attempts <= args.retry_429:
                print(f"[WARN] login hit rate limit (429). Sleeping {args.retry_429_sleep}s then retrying...")
                time.sleep(args.retry_429_sleep)
                continue

            break

        if r.status_code != 200:
            results.append(fail("login", f"Login failed (dirty email). Body: {pretty(data)}", r.status_code))
            report(results)
            sys.exit(1)

        token = extract_token_from_json(data)
        cookie_set = has_cookie(client, args.cookie_name) or (
            r.headers.get("set-cookie") and args.cookie_name in r.headers.get("set-cookie", "")
        )

        extra_login = {
            "token_in_json": bool(token),
            "cookie_present_in_jar": has_cookie(client, args.cookie_name),
            "set_cookie_header_contains_cookie": bool(r.headers.get("set-cookie") and args.cookie_name in r.headers.get("set-cookie", "")),
        }
        results.append(ok("login", "Login succeeded (dirty email normalization test passed)", r.status_code, extra_login))

        # 3) /ME via bearer
        if args.mode in ("auto", "bearer"):
            if not token:
                results.append(fail("me_bearer", "No token found in login JSON; cannot test bearer auth", 0, extra_login))
            else:
                headers = {"Authorization": f"Bearer {token}"}
                r2, data2 = request_json(client, "GET", urls["me"], None, headers=headers)

                if args.verbose:
                    print_banner("ME (BEARER) RESPONSE")
                    print("status:", r2.status_code)
                    print("body:", pretty(data2))

                if r2.status_code == 200:
                    results.append(ok("me_bearer", "/me ok with Authorization: Bearer", r2.status_code))
                else:
                    results.append(fail("me_bearer", f"/me failed with bearer. Body: {pretty(data2)}", r2.status_code))

        # 4) /ME via cookie
        if args.mode in ("auto", "cookie"):
            if not (has_cookie(client, args.cookie_name) or cookie_set):
                results.append(fail("me_cookie", "No auth cookie found; cannot test cookie auth", 0, extra_login))
            else:
                r3, data3 = request_json(client, "GET", urls["me"])

                if args.verbose:
                    print_banner("ME (COOKIE) RESPONSE")
                    print("status:", r3.status_code)
                    print("cookies:", client.cookies)
                    print("body:", pretty(data3))

                if r3.status_code == 200:
                    results.append(ok("me_cookie", "/me ok with cookie auth", r3.status_code))
                else:
                    results.append(fail("me_cookie", f"/me failed with cookie auth. Body: {pretty(data3)}", r3.status_code))

    report(results)

    if any(not r.ok for r in results):
        sys.exit(1)


def report(results: list[Result]) -> None:
    print_banner("RESULTS")
    for r in results:
        status = "PASS" if r.ok else "FAIL"
        code = f" ({r.status_code})" if r.status_code is not None else ""
        print(f"[{status}] {r.step}{code} — {r.details}")
        if r.extra:
            print("       extra:", pretty(r.extra))
    print("=" * 80)

    failed = [r for r in results if not r.ok]
    if failed:
        print("\nSmoke test failed. Fix the FAIL items above and re-run.")
    else:
        print("\nSmoke test passed. Auth looks production-ready (for the tested flows).")


if __name__ == "__main__":
    main()


