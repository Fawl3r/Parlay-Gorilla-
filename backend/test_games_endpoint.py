"""Test script to debug games endpoint"""

import asyncio
import httpx
import time
from datetime import datetime

import pytest


@pytest.mark.asyncio
async def test_games_endpoint():
    """Test the games endpoint with timing"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Testing NFL Games Endpoint")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start = time.time()
            response = await client.get(f"{base_url}/health")
            elapsed = time.time() - start
            print(f"   Status: {response.status_code}")
            print(f"   Time: {elapsed:.2f}s")
            if response.status_code == 200:
                print(f"   Response: {response.json()}")
    except httpx.ConnectError as e:
        print(f"   ERROR: Cannot connect to server. Is it running?")
        print(f"   Start with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # Test 2: Games endpoint
    print("\n2. Testing games endpoint...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            start = time.time()
            print(f"   Request started at: {datetime.now().strftime('%H:%M:%S')}")
            response = await client.get(f"{base_url}/api/sports/nfl/games")
            elapsed = time.time() - start
            print(f"   Status: {response.status_code}")
            print(f"   Time: {elapsed:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Games returned: {len(data)}")
                if data:
                    print(f"   First game: {data[0].get('home_team')} vs {data[0].get('away_team')}")
                    print(f"   Markets in first game: {len(data[0].get('markets', []))}")
                else:
                    print("   WARNING: Empty response!")
            else:
                print(f"   ERROR: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
    except httpx.TimeoutException:
        print("   ERROR: Request timed out after 60 seconds")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Games endpoint with refresh
    print("\n3. Testing games endpoint with refresh=true...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            start = time.time()
            print(f"   Request started at: {datetime.now().strftime('%H:%M:%S')}")
            response = await client.get(f"{base_url}/api/sports/nfl/games?refresh=true")
            elapsed = time.time() - start
            print(f"   Status: {response.status_code}")
            print(f"   Time: {elapsed:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Games returned: {len(data)}")
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_games_endpoint())

