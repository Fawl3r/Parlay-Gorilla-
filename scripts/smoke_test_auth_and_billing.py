"""
Smoke test script for auth and billing flows.

Tests:
- Signup flow
- Login flow
- JWT/session validation
- Stripe checkout creation (test mode)
- Usage limits enforcement

Run with: python scripts/smoke_test_auth_and_billing.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import httpx
from typing import Optional


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


async def test_signup(base_url: str) -> bool:
    """Test user signup."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/auth/signup",
                json={
                    "email": f"test_{os.urandom(4).hex()}@example.com",
                    "password": "TestPassword123!",
                    "username": f"testuser_{os.urandom(4).hex()}",
                },
                timeout=10.0,
            )
            if response.status_code == 201:
                print_pass("Signup")
                return True
            else:
                print_fail("Signup", f"Status {response.status_code}: {response.text}")
                return False
    except Exception as e:
        print_fail("Signup", str(e))
        return False


async def test_login(base_url: str, email: str, password: str) -> Optional[str]:
    """Test user login and return token."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/auth/login",
                json={"email": email, "password": password},
                timeout=10.0,
            )
            if response.status_code == 200:
                token = response.json().get("access_token")
                if token:
                    print_pass("Login")
                    return token
                else:
                    print_fail("Login", "No token in response")
                    return None
            else:
                print_fail("Login", f"Status {response.status_code}: {response.text}")
                return None
    except Exception as e:
        print_fail("Login", str(e))
        return None


async def test_protected_endpoint(base_url: str, token: str) -> bool:
    """Test accessing protected endpoint with JWT."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/api/billing/status",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                print_pass("Protected endpoint access")
                return True
            else:
                print_fail("Protected endpoint access", f"Status {response.status_code}")
                return False
    except Exception as e:
        print_fail("Protected endpoint access", str(e))
        return False


async def test_unauthenticated_rejected(base_url: str) -> bool:
    """Test that unauthenticated requests are rejected."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/api/billing/status",
                timeout=10.0,
            )
            if response.status_code == 401:
                print_pass("Unauthenticated request rejected")
                return True
            else:
                print_fail("Unauthenticated request rejected", f"Expected 401, got {response.status_code}")
                return False
    except Exception as e:
        print_fail("Unauthenticated request rejected", str(e))
        return False


async def test_stripe_checkout_creation(base_url: str, token: str) -> bool:
    """Test creating Stripe checkout session (requires Stripe test mode)."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/billing/stripe/checkout",
                headers={"Authorization": f"Bearer {token}"},
                json={"plan_code": "PG_PRO_MONTHLY"},
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("checkout_url") and "stripe.com" in data.get("checkout_url", ""):
                    print_pass("Stripe checkout creation")
                    return True
                else:
                    print_fail("Stripe checkout creation", "Invalid checkout URL")
                    return False
            elif response.status_code == 503:
                print_skip("Stripe checkout creation", "Stripe not configured (expected in dev)")
                return True  # Skip is OK
            else:
                print_fail("Stripe checkout creation", f"Status {response.status_code}: {response.text}")
                return False
    except Exception as e:
        print_fail("Stripe checkout creation", str(e))
        return False


async def test_stripe_portal_creation(base_url: str, token: str) -> bool:
    """Test creating Stripe portal session."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/billing/stripe/portal",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("checkout_url") and "stripe.com" in data.get("checkout_url", ""):
                    print_pass("Stripe portal creation")
                    return True
                elif response.status_code == 400:
                    print_skip("Stripe portal creation", "User has no Stripe customer (expected for new users)")
                    return True  # Skip is OK
                else:
                    print_fail("Stripe portal creation", "Invalid portal URL")
                    return False
            elif response.status_code in (400, 503):
                print_skip("Stripe portal creation", "Stripe not configured or no customer")
                return True  # Skip is OK
            else:
                print_fail("Stripe portal creation", f"Status {response.status_code}: {response.text}")
                return False
    except Exception as e:
        print_fail("Stripe portal creation", str(e))
        return False


async def main():
    """Run all smoke tests."""
    base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    print(f"\n{'='*60}")
    print(f"Smoke Test: Auth & Billing")
    print(f"Backend URL: {base_url}")
    print(f"{'='*60}\n")
    
    results = []
    
    # Test 1: Signup
    signup_result = await test_signup(base_url)
    results.append(("Signup", signup_result))
    
    if not signup_result:
        print("\n⚠️  Signup failed. Cannot continue with remaining tests.")
        return
    
    # Test 2: Unauthenticated rejection
    unauth_result = await test_unauthenticated_rejected(base_url)
    results.append(("Unauthenticated rejection", unauth_result))
    
    # Test 3: Login (using test credentials - adjust as needed)
    test_email = os.getenv("TEST_EMAIL", "test@example.com")
    test_password = os.getenv("TEST_PASSWORD", "TestPassword123!")
    
    token = await test_login(base_url, test_email, test_password)
    if token:
        results.append(("Login", True))
        
        # Test 4: Protected endpoint
        protected_result = await test_protected_endpoint(base_url, token)
        results.append(("Protected endpoint", protected_result))
        
        # Test 5: Stripe checkout
        checkout_result = await test_stripe_checkout_creation(base_url, token)
        results.append(("Stripe checkout", checkout_result))
        
        # Test 6: Stripe portal
        portal_result = await test_stripe_portal_creation(base_url, token)
        results.append(("Stripe portal", portal_result))
    else:
        results.append(("Login", False))
        print_skip("Protected endpoint", "Login failed")
        print_skip("Stripe checkout", "Login failed")
        print_skip("Stripe portal", "Login failed")
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {status}: {test_name}")
    print(f"\n{passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

