"""Quick non-interactive test: verify API-Sports is working."""

import asyncio
from app.services.apisports.client import get_apisports_client
from app.services.apisports.quota_manager import get_quota_manager


async def main():
    print("Testing API-Sports configuration...")
    
    client = get_apisports_client()
    if not client.is_configured():
        print("ERROR: Client not configured (missing API key or base URL)")
        return
    
    quota = get_quota_manager()
    remaining = await quota.remaining_async()
    used = await quota.used_today_async()
    
    print(f"Quota: {used} used, {remaining} remaining")
    
    if remaining <= 0:
        print("WARNING: Quota exhausted")
        return
    
    print("\nMaking test request (EPL fixtures for today)...")
    result = await client.get_fixtures(league_id=39, from_date="2025-01-28", to_date="2025-01-29")
    
    if result:
        fixtures = result.get("response", [])
        print(f"SUCCESS! Got {len(fixtures)} fixtures")
        if fixtures:
            first = fixtures[0]
            teams = first.get("teams", {})
            home = teams.get("home", {}).get("name", "N/A")
            away = teams.get("away", {}).get("name", "N/A")
            print(f"Sample: {home} vs {away}")
    else:
        print("FAILED: Request returned None (check logs)")
        return
    
    remaining_after = await quota.remaining_async()
    used_after = await quota.used_today_async()
    print(f"\nQuota after: {used_after} used, {remaining_after} remaining")
    print("API-Sports is working!")


if __name__ == "__main__":
    asyncio.run(main())
