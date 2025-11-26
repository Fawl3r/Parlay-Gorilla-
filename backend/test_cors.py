"""Test CORS configuration"""

import asyncio
import httpx
import pytest


@pytest.mark.asyncio
async def test_cors():
    """Test CORS headers"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Testing CORS Configuration")
    print("=" * 60)
    
    # Test OPTIONS request (preflight)
    print("\n1. Testing OPTIONS (preflight) request...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.options(
                f"{base_url}/api/parlay/suggest",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                }
            )
            print(f"   Status: {response.status_code}")
            print(f"   Headers:")
            for key, value in response.headers.items():
                if "access-control" in key.lower() or "cors" in key.lower():
                    print(f"     {key}: {value}")
            
            if "access-control-allow-origin" in response.headers:
                print("   ✓ CORS headers present")
            else:
                print("   ✗ CORS headers missing")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test actual POST request
    print("\n2. Testing POST request with Origin header...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/api/parlay/suggest",
                json={"num_legs": 3, "risk_profile": "balanced"},
                headers={
                    "Origin": "http://localhost:3000",
                    "Content-Type": "application/json",
                }
            )
            print(f"   Status: {response.status_code}")
            print(f"   CORS Headers:")
            for key, value in response.headers.items():
                if "access-control" in key.lower():
                    print(f"     {key}: {value}")
            
            if response.status_code == 200:
                print("   ✓ Request successful")
            else:
                print(f"   ✗ Request failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_cors())

