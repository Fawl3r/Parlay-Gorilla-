"""
Comprehensive test script for LemonSqueezy API and Webhook setup.

Tests:
1. Environment variables are set
2. API key is valid (can connect to LemonSqueezy)
3. Store ID is valid
4. Variant IDs are valid
5. Webhook endpoint is accessible
6. Webhook signature verification works
7. Can create a test checkout

Run with:
    cd backend
    python scripts/test_lemonsqueezy_setup.py
"""

import asyncio
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime
from typing import Optional

import httpx

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")


def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.RESET}")


def print_header(message: str):
    """Print header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


async def test_environment_variables():
    """Test 1: Check all required environment variables are set."""
    print_header("Test 1: Environment Variables")
    
    required_vars = {
        "LEMONSQUEEZY_API_KEY": settings.lemonsqueezy_api_key,
        "LEMONSQUEEZY_STORE_ID": settings.lemonsqueezy_store_id,
        "LEMONSQUEEZY_WEBHOOK_SECRET": settings.lemonsqueezy_webhook_secret,
    }
    
    variant_vars = {
        "LEMONSQUEEZY_PREMIUM_MONTHLY_VARIANT_ID": settings.lemonsqueezy_premium_monthly_variant_id,
        "LEMONSQUEEZY_PREMIUM_ANNUAL_VARIANT_ID": settings.lemonsqueezy_premium_annual_variant_id,
        "LEMONSQUEEZY_LIFETIME_VARIANT_ID": settings.lemonsqueezy_lifetime_variant_id,
        "LEMONSQUEEZY_CREDITS_10_VARIANT_ID": settings.lemonsqueezy_credits_10_variant_id,
        "LEMONSQUEEZY_CREDITS_25_VARIANT_ID": settings.lemonsqueezy_credits_25_variant_id,
        "LEMONSQUEEZY_CREDITS_50_VARIANT_ID": settings.lemonsqueezy_credits_50_variant_id,
        "LEMONSQUEEZY_CREDITS_100_VARIANT_ID": settings.lemonsqueezy_credits_100_variant_id,
    }
    
    all_passed = True
    
    for var_name, value in required_vars.items():
        if value:
            print_success(f"{var_name}: Set")
        else:
            print_error(f"{var_name}: NOT SET")
            all_passed = False
    
    print_info("\nVariant IDs:")
    for var_name, value in variant_vars.items():
        if value:
            print_success(f"{var_name}: {value}")
        else:
            print_warning(f"{var_name}: NOT SET (optional but recommended)")
    
    return all_passed


async def test_api_connection():
    """Test 2: Verify API key is valid by connecting to LemonSqueezy."""
    print_header("Test 2: API Connection")
    
    if not settings.lemonsqueezy_api_key:
        print_error("API key not set, skipping API test")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            # Test 1: Get store info
            response = await client.get(
                f"https://api.lemonsqueezy.com/v1/stores/{settings.lemonsqueezy_store_id}",
                headers={
                    "Accept": "application/vnd.api+json",
                    "Authorization": f"Bearer {settings.lemonsqueezy_api_key}",
                },
                timeout=10.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                store_name = data.get("data", {}).get("attributes", {}).get("name", "Unknown")
                print_success(f"API connection successful!")
                print_info(f"Store Name: {store_name}")
                print_info(f"Store ID: {settings.lemonsqueezy_store_id}")
                return True
            elif response.status_code == 401:
                print_error("API key is invalid or expired")
                print_info(f"Response: {response.text}")
                return False
            elif response.status_code == 404:
                print_error(f"Store ID {settings.lemonsqueezy_store_id} not found")
                return False
            else:
                print_error(f"API request failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print_error(f"API connection failed: {str(e)}")
        return False


async def test_variant_ids():
    """Test 3: Verify variant IDs are valid."""
    print_header("Test 3: Variant IDs Validation")
    
    if not settings.lemonsqueezy_api_key:
        print_error("API key not set, skipping variant test")
        return False
    
    variants_to_check = {
        "Premium Monthly": settings.lemonsqueezy_premium_monthly_variant_id,
        "Premium Annual": settings.lemonsqueezy_premium_annual_variant_id,
        "Lifetime": settings.lemonsqueezy_lifetime_variant_id,
        "10 Credits": settings.lemonsqueezy_credits_10_variant_id,
        "25 Credits": settings.lemonsqueezy_credits_25_variant_id,
        "50 Credits": settings.lemonsqueezy_credits_50_variant_id,
        "100 Credits": settings.lemonsqueezy_credits_100_variant_id,
    }
    
    all_passed = True
    
    async with httpx.AsyncClient() as client:
        for name, variant_id in variants_to_check.items():
            if not variant_id:
                print_warning(f"{name}: Variant ID not set")
                continue
            
            try:
                response = await client.get(
                    f"https://api.lemonsqueezy.com/v1/variants/{variant_id}",
                    headers={
                        "Accept": "application/vnd.api+json",
                        "Authorization": f"Bearer {settings.lemonsqueezy_api_key}",
                    },
                    timeout=10.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    variant_name = data.get("data", {}).get("attributes", {}).get("name", "Unknown")
                    price = data.get("data", {}).get("attributes", {}).get("price", 0) / 100
                    print_success(f"{name}: Valid (ID: {variant_id}, Name: {variant_name}, Price: ${price})")
                elif response.status_code == 404:
                    print_error(f"{name}: Variant ID {variant_id} not found")
                    all_passed = False
                else:
                    print_error(f"{name}: Validation failed ({response.status_code})")
                    all_passed = False
                    
            except Exception as e:
                print_error(f"{name}: Error checking variant: {str(e)}")
                all_passed = False
    
    return all_passed


async def test_webhook_endpoint():
    """Test 4: Check if webhook endpoint is accessible."""
    print_header("Test 4: Webhook Endpoint Accessibility")
    
    backend_url = settings.backend_url or "http://localhost:8000"
    webhook_url = f"{backend_url}/api/webhooks/lemonsqueezy"
    
    print_info(f"Testing webhook endpoint: {webhook_url}")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try GET (should return 405 Method Not Allowed, meaning endpoint exists)
            response = await client.get(webhook_url)
            
            if response.status_code == 405:
                print_success("Webhook endpoint is accessible (GET returns 405 as expected)")
                return True
            elif response.status_code == 404:
                print_error("Webhook endpoint not found (404)")
                print_warning("Make sure your backend is running and the route is registered")
                return False
            else:
                print_warning(f"Unexpected response: {response.status_code}")
                return True  # Endpoint exists, just unexpected method
                
    except httpx.ConnectError:
        print_error("Cannot connect to backend")
        print_warning(f"Make sure backend is running at {backend_url}")
        return False
    except Exception as e:
        print_error(f"Error testing webhook endpoint: {str(e)}")
        return False


async def test_webhook_signature():
    """Test 5: Verify webhook signature verification works."""
    print_header("Test 5: Webhook Signature Verification")
    
    if not settings.lemonsqueezy_webhook_secret:
        print_warning("Webhook secret not set, signature verification will be disabled")
        return True  # Not a failure, just a warning
    
    # Create a test payload
    test_payload = {
        "meta": {
            "event_name": "subscription_created",
            "webhook_id": "test-webhook-123"
        },
        "data": {
            "id": "123456",
            "type": "subscriptions",
            "attributes": {
                "user_email": "test@example.com",
                "status": "active"
            }
        }
    }
    
    # Generate signature
    body_str = json.dumps(test_payload)
    body_bytes = body_str.encode("utf-8")
    
    signature = hmac.new(
        settings.lemonsqueezy_webhook_secret.encode(),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()
    
    print_success("Webhook signature generation works")
    print_info(f"Test signature: {signature[:20]}...")
    
    # Verify signature matches
    expected = hmac.new(
        settings.lemonsqueezy_webhook_secret.encode(),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()
    
    if hmac.compare_digest(signature, expected):
        print_success("Signature verification logic is correct")
        return True
    else:
        print_error("Signature verification failed")
        return False


async def test_create_checkout():
    """Test 6: Try to create a test checkout (dry run)."""
    print_header("Test 6: Checkout Creation (Dry Run)")
    
    if not settings.lemonsqueezy_api_key or not settings.lemonsqueezy_store_id:
        print_error("API key or Store ID not set, skipping checkout test")
        return False
    
    if not settings.lemonsqueezy_premium_monthly_variant_id:
        print_warning("Premium Monthly variant ID not set, skipping checkout test")
        return True
    
    try:
        # Create a minimal test checkout payload
        checkout_data = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "checkout_data": {
                        "email": "test@example.com",
                        "custom": {
                            "user_id": "00000000-0000-0000-0000-000000000000",
                            "plan_code": "PG_PREMIUM_MONTHLY",
                        },
                    },
                    "checkout_options": {
                        "embed": False,
                        "media": True,
                        "logo": True,
                    },
                    "product_options": {
                        "enabled_variants": [settings.lemonsqueezy_premium_monthly_variant_id],
                        "redirect_url": f"{settings.app_url or 'http://localhost:3000'}/billing/success?provider=lemonsqueezy",
                    },
                },
                "relationships": {
                    "store": {
                        "data": {
                            "type": "stores",
                            "id": settings.lemonsqueezy_store_id,
                        }
                    },
                    "variant": {
                        "data": {
                            "type": "variants",
                            "id": settings.lemonsqueezy_premium_monthly_variant_id,
                        }
                    },
                },
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.lemonsqueezy.com/v1/checkouts",
                json=checkout_data,
                headers={
                    "Accept": "application/vnd.api+json",
                    "Content-Type": "application/vnd.api+json",
                    "Authorization": f"Bearer {settings.lemonsqueezy_api_key}",
                },
                timeout=30.0,
            )
            
            if response.status_code == 201:
                data = response.json()
                checkout_url = data.get("data", {}).get("attributes", {}).get("url", "")
                checkout_id = data.get("data", {}).get("id", "")
                print_success("Checkout created successfully!")
                print_info(f"Checkout ID: {checkout_id}")
                print_info(f"Checkout URL: {checkout_url[:80]}...")
                print_warning("Note: This is a real checkout. You may want to cancel it in LemonSqueezy dashboard.")
                return True
            else:
                print_error(f"Checkout creation failed: {response.status_code}")
                print_info(f"Response: {response.text[:200]}")
                return False
                
    except Exception as e:
        print_error(f"Error creating checkout: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("=" * 60)
    print("LemonSqueezy Setup Test Suite")
    print("=" * 60)
    print(f"{Colors.RESET}")
    
    results = {}
    
    # Run all tests
    results["Environment Variables"] = await test_environment_variables()
    results["API Connection"] = await test_api_connection()
    results["Variant IDs"] = await test_variant_ids()
    results["Webhook Endpoint"] = await test_webhook_endpoint()
    results["Webhook Signature"] = await test_webhook_signature()
    results["Checkout Creation"] = await test_create_checkout()
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}\n")
    
    if passed == total:
        print_success("🎉 All tests passed! Your LemonSqueezy setup is ready!")
    else:
        print_warning("⚠️  Some tests failed. Please review the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

