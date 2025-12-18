"""Test SportsRadar API endpoints to see what works with trial key"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SPORTSRADAR_API_KEY")
BASE_URL = "https://api.sportradar.us/nfl/official/trial/v7/en"

async def test_endpoint(endpoint: str, description: str):
    """Test a specific endpoint"""
    url = f"{BASE_URL}/{endpoint}"
    params = {"api_key": API_KEY}
    
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Endpoint: {endpoint}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ SUCCESS")
                # Show structure
                if isinstance(data, dict):
                    print(f"Top-level keys: {list(data.keys())[:10]}")
                    if 'games' in data:
                        print(f"Games found: {len(data.get('games', []))}")
                    if 'teams' in data:
                        print(f"Teams found: {len(data.get('teams', []))}")
                elif isinstance(data, list):
                    print(f"List with {len(data)} items")
            elif response.status_code == 403:
                error_text = response.text[:300]
                print(f"✗ 403 FORBIDDEN - Authentication Error")
                print(f"Response: {error_text}")
            elif response.status_code == 404:
                print(f"✗ 404 NOT FOUND - Endpoint doesn't exist")
            elif response.status_code == 429:
                print(f"✗ 429 RATE LIMIT - Too many requests")
            else:
                print(f"✗ ERROR {response.status_code}")
                print(f"Response: {response.text[:300]}")
                
    except httpx.TimeoutException:
        print(f"✗ TIMEOUT")
    except Exception as e:
        print(f"✗ ERROR: {e}")

async def main():
    """Test various SportsRadar endpoints"""
    print(f"\n{'='*60}")
    print("SPORTRADAR API TEST - Trial Key")
    print(f"{'='*60}")
    print(f"API Key: {API_KEY[:10]}..." if API_KEY else "NO API KEY")
    print(f"Base URL: {BASE_URL}")
    
    # Test endpoints from most basic to more specific
    endpoints_to_test = [
        # Basic info endpoints
        ("seasons.json", "List all seasons"),
        ("teams.json", "List all teams"),
        
        # Schedule endpoints (usually work with trial)
        ("games/2024/12/08/schedule.json", "Today's schedule"),
        ("games/2024/REG/15/schedule.json", "Week 15 schedule"),
        
        # Team endpoints
        ("teams/4254d319-1bc7-4f81-b4ab-b5c0b9db8cf9/profile.json", "Team Profile (Buccaneers)"),
        
        # Seasonal statistics (may not work with trial)
        ("seasons/2024/REG/teams/4254d319-1bc7-4f81-b4ab-b5c0b9db8cf9/statistics.json", "Seasonal Statistics (Buccaneers)"),
        
        # Current week/schedule
        ("games/2024/REG/schedule.json", "Current season schedule"),
    ]
    
    for endpoint, description in endpoints_to_test:
        await test_endpoint(endpoint, description)
        await asyncio.sleep(1)  # Rate limit protection
    
    print(f"\n{'='*60}")
    print("TESTING COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())

