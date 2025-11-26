"""Test parlay endpoint directly to see actual error"""

import asyncio
import httpx
import json

import pytest


@pytest.mark.asyncio
async def test_parlay():
    """Test parlay endpoint directly"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Testing Parlay Endpoint Directly")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("\nSending POST request to /api/parlay/suggest...")
            response = await client.post(
                f"{base_url}/api/parlay/suggest",
                json={
                    "num_legs": 3,
                    "risk_profile": "balanced"
                },
                headers={
                    "Origin": "http://localhost:3000",
                    "Content-Type": "application/json",
                }
            )
            
            print(f"\nStatus: {response.status_code}")
            print(f"Headers:")
            for key, value in response.headers.items():
                if "access-control" in key.lower() or "content-type" in key.lower():
                    print(f"  {key}: {value}")
            
            print(f"\nResponse body:")
            try:
                data = response.json()
                print(json.dumps(data, indent=2))
            except:
                print(response.text[:500])
                
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_parlay())

