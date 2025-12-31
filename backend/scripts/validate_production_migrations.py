#!/usr/bin/env python3
"""
Production validation script for Alembic migrations.

Tests production API endpoints to verify:
1. Auth endpoints no longer return 500 (schema errors)
2. Schema columns exist (indirectly via successful auth responses)
3. Service is running and responsive
"""

import json
import sys
import time
import urllib.error
import urllib.request
from typing import Dict, Any


PRODUCTION_API_URL = "https://api.parlaygorilla.com"


def test_endpoint(
    method: str,
    path: str,
    data: Dict[str, Any] = None,
    expected_status: int = None,
) -> tuple[int, str]:
    """Test an API endpoint and return status code and response body."""
    url = f"{PRODUCTION_API_URL}{path}"
    
    if data:
        req_data = json.dumps(data).encode()
        req = urllib.request.Request(
            url, data=req_data, headers={"Content-Type": "application/json"}, method=method
        )
    else:
        req = urllib.request.Request(url, method=method)
    
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        status = resp.status
        body = resp.read().decode()
        return status, body
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            body = e.read().decode()
        except:
            body = f"HTTP {status} (could not read body)"
        return status, body
    except Exception as e:
        return 0, f"Error: {str(e)}"


def check_health() -> bool:
    """Check if the API is healthy and responsive."""
    print("=" * 60)
    print("1. Testing Health Endpoint")
    print("=" * 60)
    
    status, body = test_endpoint("GET", "/health")
    
    if status == 200:
        print(f"✅ Health check passed (Status: {status})")
        print(f"   Response: {body[:100]}")
        return True
    else:
        print(f"❌ Health check failed (Status: {status})")
        print(f"   Response: {body[:200]}")
        return False


def test_login_endpoint() -> bool:
    """Test login endpoint - should NOT return 500 if schema is correct."""
    print("\n" + "=" * 60)
    print("2. Testing Login Endpoint (Schema Validation)")
    print("=" * 60)
    
    # Use invalid credentials - should get 401, not 500
    status, body = test_endpoint(
        "POST",
        "/api/auth/login",
        {"email": "nonexistent@example.com", "password": "wrongpassword"},
    )
    
    print(f"Status: {status}")
    print(f"Response: {body[:300]}")
    
    if status == 500:
        if "premium_custom_builder_used" in body or "UndefinedColumnError" in body:
            print("\n❌ SCHEMA ERROR DETECTED!")
            print("   The database is missing required columns.")
            print("   Migrations have NOT been applied.")
            return False
        else:
            print("\n⚠️  500 error, but not schema-related")
            print("   Could be a different issue. Check logs.")
            return False
    elif status == 401:
        print("\n✅ Schema OK!")
        print("   401 = authentication failed (expected with wrong credentials)")
        print("   This means the database schema is correct.")
        return True
    elif status == 422:
        print("\n✅ Schema OK!")
        print("   422 = validation error (expected with invalid input)")
        print("   This means the database schema is correct.")
        return True
    else:
        print(f"\n⚠️  Unexpected status: {status}")
        return False


def test_register_endpoint() -> bool:
    """Test register endpoint - should NOT return 500 if schema is correct."""
    print("\n" + "=" * 60)
    print("3. Testing Register Endpoint (Schema Validation)")
    print("=" * 60)
    
    # Use a unique email each time
    import random
    test_email = f"testvalidation{random.randint(10000, 99999)}@example.com"
    
    status, body = test_endpoint(
        "POST",
        "/api/auth/register",
        {
            "email": test_email,
            "password": "testpass123",
            "username": f"testuser{random.randint(10000, 99999)}",
        },
    )
    
    print(f"Status: {status}")
    print(f"Response: {body[:300]}")
    
    if status == 500:
        if "premium_custom_builder_used" in body or "UndefinedColumnError" in body:
            print("\n❌ SCHEMA ERROR DETECTED!")
            print("   The database is missing required columns.")
            print("   Migrations have NOT been applied.")
            return False
        else:
            print("\n⚠️  500 error, but not schema-related")
            print("   Could be a different issue. Check logs.")
            return False
    elif status == 201 or status == 200:
        print("\n✅ Schema OK!")
        print("   Registration succeeded - schema is correct.")
        return True
    elif status == 400 or status == 422:
        # Could be duplicate email or validation error - both mean schema is OK
        print("\n✅ Schema OK!")
        print("   400/422 = validation/duplicate error (schema is correct)")
        return True
    else:
        print(f"\n⚠️  Unexpected status: {status}")
        return False


def main():
    """Run all production validation tests."""
    print("\n" + "=" * 60)
    print("PRODUCTION MIGRATION VALIDATION")
    print("=" * 60)
    print(f"API URL: {PRODUCTION_API_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print()
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", check_health()))
    
    # Test 2: Login endpoint
    results.append(("Login Endpoint", test_login_endpoint()))
    
    # Test 3: Register endpoint
    results.append(("Register Endpoint", test_register_endpoint()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All tests passed! Migrations appear to be applied correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Migrations may not have been applied.")
        print("\nNext steps:")
        print("1. Check Render logs for migration output")
        print("2. Manually run: alembic upgrade head (in Render Shell)")
        print("3. Verify database schema using SQL queries")
        return 1


if __name__ == "__main__":
    sys.exit(main())

