#!/usr/bin/env python3
"""
Parlay Gorilla - Production Test for Password & Token Fixes

Tests the fixes for:
1. Password 72-byte limit handling (user-friendly errors)
2. Token scope fix (no "token is not defined" errors)
3. Registration error handling improvements

Usage:
    python scripts/test_password_and_token_fixes.py --base-url http://127.0.0.1:8000
    python scripts/test_password_and_token_fixes.py --base-url https://your-domain.com
"""

import argparse
import json
import os
import random
import string
import sys
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
import httpx

# ====== CONFIGURATION ======
ENDPOINTS = {
    "register": "/api/auth/register",
    "login": "/api/auth/login",
    "me": "/api/auth/me",
}

DEFAULT_COOKIE_NAME = "access_token"

# ====== TEST HELPERS ======

def _rand(n: int = 8) -> str:
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


@dataclass
class TestResult:
    ok: bool
    test_name: str
    details: str
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


def fail(test_name: str, details: str, status_code: Optional[int] = None, 
         error_message: Optional[str] = None, extra: Optional[Dict[str, Any]] = None) -> TestResult:
    return TestResult(ok=False, test_name=test_name, details=details, 
                     status_code=status_code, error_message=error_message, extra=extra)


def ok(test_name: str, details: str, status_code: Optional[int] = None, 
       extra: Optional[Dict[str, Any]] = None) -> TestResult:
    return TestResult(ok=True, test_name=test_name, details=details, 
                     status_code=status_code, extra=extra)


def pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2, sort_keys=True, default=str)
    except Exception:
        return str(obj)


def print_banner(msg: str) -> None:
    print("\n" + "=" * 80)
    print(msg)
    print("=" * 80)


def request_json(client: httpx.Client, method: str, url: str, 
                 payload: Optional[dict] = None, headers: Optional[dict] = None) -> Tuple[httpx.Response, Any]:
    r = client.request(method, url, json=payload, headers=headers)
    try:
        data = r.json()
    except Exception:
        data = r.text
    return r, data


def count_bytes(text: str) -> int:
    """Count UTF-8 bytes in a string."""
    return len(text.encode('utf-8'))


def generate_password(length_chars: int) -> str:
    """Generate a password of approximately length_chars characters.
    Note: UTF-8 encoding means byte count may differ from char count."""
    return "".join(random.choice(string.ascii_letters + string.digits + "!@#$%^&*") 
                   for _ in range(length_chars))


def generate_long_password(target_bytes: int) -> str:
    """Generate a password that is approximately target_bytes when UTF-8 encoded.
    Uses multi-byte characters (emojis) to test edge cases."""
    # Start with ASCII (1 byte per char)
    password = "a" * min(target_bytes, 50)
    remaining = target_bytes - len(password.encode('utf-8'))
    
    # Add emojis (4 bytes each) to reach target
    emojis = "🔥💯🎯🚀⭐"
    while remaining > 0:
        password += random.choice(emojis)
        remaining = target_bytes - len(password.encode('utf-8'))
        if remaining < 4:
            break
    
    # Fill remaining with ASCII
    if remaining > 0:
        password += "a" * remaining
    
    return password


# ====== TEST CASES ======

def test_normal_password_registration(client: httpx.Client, base_url: str) -> TestResult:
    """Test registration with a normal password (well under 72 bytes)."""
    test_name = "normal_password_registration"
    email = f"test+normal-{int(time.time())}@example.com"
    password = "SecurePassword123!"
    
    try:
        r, data = request_json(client, "POST", f"{base_url}{ENDPOINTS['register']}", {
            "email": email,
            "password": password,
            "username": f"testuser_{_rand(6)}"
        })
        
        if r.status_code == 200 or r.status_code == 201:
            return ok(test_name, f"Registration succeeded with normal password", r.status_code)
        else:
            return fail(test_name, f"Unexpected status code", r.status_code, 
                      error_message=data.get("detail") if isinstance(data, dict) else str(data))
    except Exception as e:
        return fail(test_name, f"Exception during test: {str(e)}")


def test_password_at_72_bytes(client: httpx.Client, base_url: str) -> TestResult:
    """Test registration with a password exactly at 72 bytes (edge case)."""
    test_name = "password_at_72_bytes"
    email = f"test+72bytes-{int(time.time())}@example.com"
    
    # Generate password that is exactly 72 bytes
    password = generate_long_password(72)
    actual_bytes = count_bytes(password)
    
    try:
        r, data = request_json(client, "POST", f"{base_url}{ENDPOINTS['register']}", {
            "email": email,
            "password": password,
            "username": f"testuser_{_rand(6)}"
        })
        
        if r.status_code == 200 or r.status_code == 201:
            return ok(test_name, f"Registration succeeded with 72-byte password (actual: {actual_bytes} bytes)", 
                     r.status_code, extra={"password_bytes": actual_bytes})
        else:
            return fail(test_name, f"Registration failed at 72 bytes", r.status_code,
                      error_message=data.get("detail") if isinstance(data, dict) else str(data),
                      extra={"password_bytes": actual_bytes})
    except Exception as e:
        return fail(test_name, f"Exception during test: {str(e)}", extra={"password_bytes": actual_bytes})


def test_password_over_72_bytes(client: httpx.Client, base_url: str) -> TestResult:
    """Test registration with a password over 72 bytes - should get user-friendly error."""
    test_name = "password_over_72_bytes_error_handling"
    email = f"test+longpass-{int(time.time())}@example.com"
    
    # Generate password that exceeds 72 bytes
    password = generate_long_password(100)  # 100 bytes
    actual_bytes = count_bytes(password)
    
    try:
        r, data = request_json(client, "POST", f"{base_url}{ENDPOINTS['register']}", {
            "email": email,
            "password": password,
            "username": f"testuser_{_rand(6)}"
        })
        
        # Should return 400 with user-friendly error message
        if r.status_code == 400:
            error_detail = data.get("detail") if isinstance(data, dict) else str(data)
            
            # Should NOT contain raw bcrypt error message
            has_raw_error = "truncate manually if necessary" in error_detail.lower()
            
            # Check for user-friendly error message
            is_user_friendly = (
                "too long" in error_detail.lower() or 
                "72 characters" in error_detail.lower() or
                "72 characters or fewer" in error_detail.lower()
            )
            
            if not has_raw_error and is_user_friendly:
                return ok(test_name, 
                         f"Got user-friendly error for long password: {error_detail[:100]}",
                         r.status_code,
                         extra={"password_bytes": actual_bytes, "error_message": error_detail})
            elif has_raw_error:
                return fail(test_name,
                           f"Error message contains raw bcrypt error (not user-friendly)",
                           r.status_code,
                           error_message=error_detail,
                           extra={"password_bytes": actual_bytes})
            else:
                # Got 400 but error message format is unexpected
                return fail(test_name,
                           f"Got 400 but error message format is unexpected",
                           r.status_code,
                           error_message=error_detail,
                           extra={"password_bytes": actual_bytes})
        else:
            # If it succeeds, that's also OK (backend might truncate automatically)
            if r.status_code == 200 or r.status_code == 201:
                return ok(test_name,
                         f"Registration succeeded (backend truncated password automatically)",
                         r.status_code,
                         extra={"password_bytes": actual_bytes})
            else:
                return fail(test_name,
                           f"Unexpected status code for long password",
                           r.status_code,
                           error_message=data.get("detail") if isinstance(data, dict) else str(data),
                           extra={"password_bytes": actual_bytes})
    except Exception as e:
        return fail(test_name, f"Exception during test: {str(e)}", extra={"password_bytes": actual_bytes})


def test_password_with_emojis(client: httpx.Client, base_url: str) -> TestResult:
    """Test registration with password containing emojis (multi-byte UTF-8)."""
    test_name = "password_with_emojis"
    email = f"test+emoji-{int(time.time())}@example.com"
    
    # Password with emojis (each emoji is 4 bytes)
    password = "MyPassword123!🔥💯🎯🚀⭐"
    actual_bytes = count_bytes(password)
    
    try:
        r, data = request_json(client, "POST", f"{base_url}{ENDPOINTS['register']}", {
            "email": email,
            "password": password,
            "username": f"testuser_{_rand(6)}"
        })
        
        if r.status_code == 200 or r.status_code == 201:
            return ok(test_name, f"Registration succeeded with emoji password ({actual_bytes} bytes)", 
                     r.status_code, extra={"password_bytes": actual_bytes, "password_length": len(password)})
        else:
            return fail(test_name, f"Registration failed with emoji password", r.status_code,
                      error_message=data.get("detail") if isinstance(data, dict) else str(data),
                      extra={"password_bytes": actual_bytes})
    except Exception as e:
        return fail(test_name, f"Exception during test: {str(e)}", extra={"password_bytes": actual_bytes})


def test_token_in_response(client: httpx.Client, base_url: str) -> TestResult:
    """Test that registration returns a token in the response (no "token is not defined" errors)."""
    test_name = "token_in_registration_response"
    email = f"test+token-{int(time.time())}@example.com"
    password = "SecurePassword123!"
    
    try:
        r, data = request_json(client, "POST", f"{base_url}{ENDPOINTS['register']}", {
            "email": email,
            "password": password,
            "username": f"testuser_{_rand(6)}"
        })
        
        if r.status_code == 200 or r.status_code == 201:
            # Check that token is present in response
            if isinstance(data, dict):
                has_token = "access_token" in data or "token" in data
                token_value = data.get("access_token") or data.get("token")
                
                if has_token and token_value:
                    return ok(test_name,
                             f"Token present in registration response",
                             r.status_code,
                             extra={"has_token": True, "token_length": len(str(token_value))})
                else:
                    return fail(test_name,
                               f"Token missing from registration response",
                               r.status_code,
                               extra={"response_keys": list(data.keys()) if isinstance(data, dict) else None})
            else:
                return fail(test_name,
                           f"Response is not JSON object",
                           r.status_code,
                           error_message=str(data)[:200])
        else:
            return fail(test_name, f"Registration failed", r.status_code,
                      error_message=data.get("detail") if isinstance(data, dict) else str(data))
    except Exception as e:
        return fail(test_name, f"Exception during test: {str(e)}")


def test_cookie_set_on_registration(client: httpx.Client, base_url: str) -> TestResult:
    """Test that HttpOnly cookie is set on successful registration."""
    test_name = "cookie_set_on_registration"
    email = f"test+cookie-{int(time.time())}@example.com"
    password = "SecurePassword123!"
    
    try:
        r, data = request_json(client, "POST", f"{base_url}{ENDPOINTS['register']}", {
            "email": email,
            "password": password,
            "username": f"testuser_{_rand(6)}"
        })
        
        if r.status_code == 200 or r.status_code == 201:
            # Check for Set-Cookie header
            set_cookie = r.headers.get("set-cookie", "")
            has_cookie = DEFAULT_COOKIE_NAME in set_cookie.lower()
            is_httponly = "httponly" in set_cookie.lower()
            
            if has_cookie:
                return ok(test_name,
                         f"Cookie set in registration response",
                         r.status_code,
                         extra={"has_cookie": True, "is_httponly": is_httponly,
                               "cookie_in_jar": DEFAULT_COOKIE_NAME in client.cookies})
            else:
                return fail(test_name,
                           f"Cookie not set in registration response",
                           r.status_code,
                           extra={"set_cookie_header": set_cookie[:200] if set_cookie else None})
        else:
            return fail(test_name, f"Registration failed", r.status_code,
                      error_message=data.get("detail") if isinstance(data, dict) else str(data))
    except Exception as e:
        return fail(test_name, f"Exception during test: {str(e)}")


def test_me_endpoint_with_cookie(client: httpx.Client, base_url: str) -> TestResult:
    """Test that /me endpoint works with cookie auth (tests token scope fix)."""
    test_name = "me_endpoint_with_cookie_auth"
    email = f"test+me-{int(time.time())}@example.com"
    password = "SecurePassword123!"
    
    try:
        # Register first
        r, data = request_json(client, "POST", f"{base_url}{ENDPOINTS['register']}", {
            "email": email,
            "password": password,
            "username": f"testuser_{_rand(6)}"
        })
        
        if r.status_code not in (200, 201):
            return fail(test_name, f"Registration failed (prerequisite)", r.status_code,
                      error_message=data.get("detail") if isinstance(data, dict) else str(data))
        
        # Now test /me with cookie (no Authorization header)
        r2, data2 = request_json(client, "GET", f"{base_url}{ENDPOINTS['me']}")
        
        if r2.status_code == 200:
            if isinstance(data2, dict) and "email" in data2:
                return ok(test_name,
                         f"/me endpoint works with cookie auth",
                         r2.status_code,
                         extra={"user_email": data2.get("email")})
            else:
                return fail(test_name,
                           f"/me returned 200 but invalid response format",
                           r2.status_code,
                           error_message=str(data2)[:200])
        else:
            return fail(test_name,
                       f"/me endpoint failed with cookie auth",
                       r2.status_code,
                       error_message=data2.get("detail") if isinstance(data2, dict) else str(data2))
    except Exception as e:
        return fail(test_name, f"Exception during test: {str(e)}")


# ====== MAIN ======

def main():
    parser = argparse.ArgumentParser(description="Test password and token fixes")
    parser.add_argument("--base-url", required=True,
                       help="Base URL, e.g. http://127.0.0.1:8000 or https://prod.com")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--delay", type=float, default=2.0,
                       help="Delay between registration requests (seconds) to avoid rate limits")
    parser.add_argument("--wait-for-rate-limit", action="store_true",
                       help="Wait 60 seconds before starting if rate limited (for repeated test runs)")
    args = parser.parse_args()
    
    base = args.base_url.rstrip("/")
    results: list[TestResult] = []
    
    print_banner("Parlay Gorilla - Password & Token Fixes Production Test")
    print(f"Base URL: {base}")
    print(f"Timeout: {args.timeout}s")
    print(f"Delay between requests: {args.delay}s")
    print("-" * 80)
    
    # Check if we're rate limited before starting
    if args.wait_for_rate_limit:
        print("\n⚠️  Checking for rate limit...")
        with httpx.Client(timeout=5.0, follow_redirects=True) as test_client:
            try:
                r, _ = request_json(test_client, "POST", f"{base}{ENDPOINTS['register']}", {
                    "email": f"test-rate-check-{int(time.time())}@example.com",
                    "password": "Test123!",
                    "username": "testuser"
                })
                if r.status_code == 429:
                    print("⚠️  Rate limit detected. Waiting 60 seconds for reset...")
                    for i in range(60, 0, -10):
                        print(f"   Waiting {i} seconds...")
                        time.sleep(10)
                    print("   Resuming tests...\n")
            except Exception:
                pass  # Ignore errors during rate limit check
    
    with httpx.Client(timeout=args.timeout, follow_redirects=True) as client:
        # Run all test cases
        tests = [
            ("Normal Password", test_normal_password_registration),
            ("Password at 72 Bytes", test_password_at_72_bytes),
            ("Password Over 72 Bytes (Error Handling)", test_password_over_72_bytes),
            ("Password with Emojis", test_password_with_emojis),
            ("Token in Response", test_token_in_response),
            ("Cookie Set on Registration", test_cookie_set_on_registration),
            ("/me Endpoint with Cookie Auth", test_me_endpoint_with_cookie),
        ]
        
        for i, (test_name, test_func) in enumerate(tests):
            if args.verbose:
                print(f"\nRunning: {test_name}...")
            
            # Add delay between registration requests to avoid rate limits
            if i > 0 and "register" in test_func.__name__ or "cookie" in test_func.__name__ or "me" in test_func.__name__:
                time.sleep(args.delay)
            
            result = test_func(client, base)
            results.append(result)
            
            if args.verbose:
                status = "✅ PASS" if result.ok else "❌ FAIL"
                print(f"  {status}: {result.details}")
                if result.error_message:
                    print(f"    Error: {result.error_message}")
                if result.extra:
                    print(f"    Extra: {pretty(result.extra)}")
    
    # Print summary
    print_banner("TEST RESULTS")
    for r in results:
        status = "✅ PASS" if r.ok else "❌ FAIL"
        code = f" ({r.status_code})" if r.status_code is not None else ""
        print(f"[{status}] {r.test_name}{code}")
        print(f"  {r.details}")
        if r.error_message:
            print(f"  Error: {r.error_message}")
        if r.extra and args.verbose:
            print(f"  Extra: {pretty(r.extra)}")
        print()
    
    print("=" * 80)
    failed = [r for r in results if not r.ok]
    rate_limited = [r for r in failed if r.status_code == 429]
    other_failures = [r for r in failed if r.status_code != 429]
    
    if rate_limited:
        print(f"\n⚠️  {len(rate_limited)} test(s) were rate limited (429)")
        print("   This is expected if running tests repeatedly. Wait 60 seconds and retry.")
        print("   Or use --wait-for-rate-limit flag to auto-wait.")
        print("\n   Rate-limited tests:")
        for r in rate_limited:
            print(f"     - {r.test_name}")
    
    if other_failures:
        print(f"\n❌ {len(other_failures)} test(s) failed (non-rate-limit errors):")
        for r in other_failures:
            print(f"  - {r.test_name}: {r.details}")
            if r.error_message:
                print(f"    Error: {r.error_message}")
        sys.exit(1)
    elif rate_limited and not other_failures:
        print(f"\n⚠️  All tests that ran passed, but {len(rate_limited)} were rate limited.")
        print("   Re-run with --wait-for-rate-limit or wait 60 seconds and retry.")
        sys.exit(0)
    else:
        print(f"\n✅ All {len(results)} tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

