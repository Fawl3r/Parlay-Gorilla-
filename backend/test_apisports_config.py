"""Quick test script to verify API-Sports configuration and connectivity."""

import asyncio
import sys
from app.services.apisports.client import get_apisports_client
from app.services.apisports.quota_manager import get_quota_manager
from app.core.config import settings


async def test_config():
    """Test API-Sports configuration and optionally make a test request."""
    print("=" * 60)
    print("API-Sports Configuration Test")
    print("=" * 60)
    
    # Check config
    api_key = getattr(settings, "api_sports_api_key", None) or ""
    base_url = getattr(settings, "apisports_base_url", "")
    daily_quota = getattr(settings, "apisports_daily_quota", 100)
    
    print(f"\n[OK] API Key: {'SET' if api_key else 'NOT SET'} ({'*' * 20 if api_key else 'N/A'})")
    print(f"[OK] Base URL: {base_url or 'NOT SET'}")
    print(f"[OK] Daily Quota: {daily_quota}")
    
    # Check client
    client = get_apisports_client()
    is_configured = client.is_configured()
    print(f"\n[OK] Client Configured: {is_configured}")
    
    if not is_configured:
        print("\n[ERROR] Client not configured. Check:")
        print("  - API_SPORTS_API_KEY is set in .env")
        print("  - APISPORTS_BASE_URL is set (default: https://v3.football.api-sports.io)")
        return False
    
    # Check quota
    quota = get_quota_manager()
    remaining = await quota.remaining_async()
    used = await quota.used_today_async()
    circuit_open = await quota.is_circuit_open()
    
    print(f"\n[OK] Quota Status:")
    print(f"  - Used Today: {used}")
    print(f"  - Remaining: {remaining}")
    print(f"  - Circuit Breaker: {'OPEN' if circuit_open else 'CLOSED'}")
    
    if remaining <= 0:
        print("\n[WARNING] Quota exhausted for today!")
        return False
    
    if circuit_open:
        print("\n[WARNING] Circuit breaker is open (API failures detected)")
        return False
    
    # Optional: Test a small request (uses 1 quota)
    print("\n" + "=" * 60)
    print("Test Request (Optional)")
    print("=" * 60)
    print("\nThis will use 1 API call from your daily quota.")
    response = input("Make a test request? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\nMaking test request to /status endpoint...")
        # API-Sports has a /status endpoint that doesn't count against quota
        # But we'll use a small fixtures call for a known league (EPL = 39)
        result = await client.get_fixtures(league_id=39, from_date="2025-01-28", to_date="2025-01-29")
        
        if result:
            print("[OK] Request successful!")
            response_data = result.get("response", [])
            print(f"  - Fixtures returned: {len(response_data)}")
            if response_data:
                first = response_data[0]
                fixture = first.get("fixture", {})
                teams = first.get("teams", {})
                print(f"  - Sample fixture: {teams.get('home', {}).get('name', 'N/A')} vs {teams.get('away', {}).get('name', 'N/A')}")
                print(f"  - Date: {fixture.get('date', 'N/A')}")
        else:
            print("[ERROR] Request failed (check logs for details)")
            return False
        
        # Check quota after
        remaining_after = await quota.remaining_async()
        used_after = await quota.used_today_async()
        print(f"\n[OK] Quota After Request:")
        print(f"  - Used: {used_after} (was {used})")
        print(f"  - Remaining: {remaining_after} (was {remaining})")
    else:
        print("\nSkipping test request.")
    
    print("\n" + "=" * 60)
    print("[OK] Configuration check complete!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_config())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
