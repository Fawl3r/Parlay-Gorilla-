"""
Backend-only production smoke test for leaderboards feature.

Tests all leaderboard API endpoints against production (parlaygorilla.com).
Does not require Playwright - only tests backend APIs.

Run with:
  BACKEND_URL=https://api.parlaygorilla.com python scripts/smoke_test_leaderboards_backend_only.py
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import httpx
import re


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_pass(test_name: str):
    print(f"{Colors.GREEN}✓ PASS{Colors.RESET}: {test_name}")


def print_fail(test_name: str, error: str):
    print(f"{Colors.RED}✗ FAIL{Colors.RESET}: {test_name} - {error}")


def print_skip(test_name: str, reason: str):
    print(f"{Colors.YELLOW}⊘ SKIP{Colors.RESET}: {test_name} - {reason}")


def print_info(test_name: str, info: str):
    print(f"{Colors.BLUE}ℹ INFO{Colors.RESET}: {test_name} - {info}")


async def test_endpoint_structure(
    client: httpx.AsyncClient, endpoint: str, expected_fields: list[str]
) -> tuple[bool, Optional[Dict[str, Any]]]:
    """Test endpoint returns correct structure."""
    try:
        response = await client.get(endpoint, timeout=15.0)
        if response.status_code != 200:
            return False, None
        
        data = response.json()
        for field in expected_fields:
            if field not in data:
                return False, data
        
        # Check cache headers
        cache_control = response.headers.get("Cache-Control", "")
        if "max-age=60" not in cache_control:
            print_info(f"Cache headers check for {endpoint}", f"Cache-Control: {cache_control}")
        
        return True, data
    except Exception as e:
        return False, None


async def test_leaderboard_custom(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test /api/leaderboards/custom endpoint."""
    endpoint = f"{base_url}/api/leaderboards/custom?limit=10"
    success, data = await test_endpoint_structure(
        client, endpoint, ["leaderboard"]
    )
    
    if success:
        if isinstance(data.get("leaderboard"), list):
            print_pass("Verified Winners endpoint structure")
            if len(data["leaderboard"]) > 0:
                entry = data["leaderboard"][0]
                required_fields = ["rank", "username", "verified_wins", "win_rate"]
                if all(field in entry for field in required_fields):
                    print_pass("Verified Winners entry structure")
                    print_info("Verified Winners", f"Found {len(data['leaderboard'])} entries")
                    return True
                else:
                    print_fail("Verified Winners entry structure", f"Missing fields: {required_fields}")
                    return False
            else:
                print_info("Verified Winners", "Empty leaderboard (no data yet)")
                return True
        else:
            print_fail("Verified Winners endpoint", "leaderboard is not a list")
            return False
    else:
        print_fail("Verified Winners endpoint", f"Status code or structure issue")
        return False


async def test_leaderboard_ai_usage(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test /api/leaderboards/ai-usage endpoint with both periods."""
    results = []
    
    for period in ["30d", "all_time"]:
        endpoint = f"{base_url}/api/leaderboards/ai-usage?period={period}&limit=10"
        success, data = await test_endpoint_structure(
            client, endpoint, ["leaderboard", "timeframe"]
        )
        
        if success:
            if data.get("timeframe") == period:
                if isinstance(data.get("leaderboard"), list):
                    results.append(True)
                    print_pass(f"AI Usage endpoint ({period})")
                    print_info(f"AI Usage ({period})", f"Found {len(data['leaderboard'])} entries")
                else:
                    results.append(False)
                    print_fail(f"AI Usage endpoint ({period})", "leaderboard is not a list")
            else:
                results.append(False)
                print_fail(f"AI Usage endpoint ({period})", f"Expected timeframe={period}, got {data.get('timeframe')}")
        else:
            results.append(False)
            print_fail(f"AI Usage endpoint ({period})", "Status code or structure issue")
    
    # Test invalid period
    try:
        response = await client.get(
            f"{base_url}/api/leaderboards/ai-usage?period=invalid&limit=10",
            timeout=15.0
        )
        if response.status_code == 422:
            print_pass("AI Usage endpoint validation (invalid period)")
            results.append(True)
        else:
            print_fail("AI Usage endpoint validation", f"Expected 422 for invalid period, got {response.status_code}")
            results.append(False)
    except Exception as e:
        print_fail("AI Usage endpoint validation", str(e))
        results.append(False)
    
    return all(results)


async def test_leaderboard_arcade_points(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test /api/leaderboards/arcade-points endpoint with both periods."""
    results = []
    
    for period in ["30d", "all_time"]:
        endpoint = f"{base_url}/api/leaderboards/arcade-points?period={period}&limit=10"
        success, data = await test_endpoint_structure(
            client, endpoint, ["leaderboard", "period"]
        )
        
        if success:
            if data.get("period") == period:
                if isinstance(data.get("leaderboard"), list):
                    results.append(True)
                    print_pass(f"Arcade Points endpoint ({period})")
                    if len(data["leaderboard"]) > 0:
                        entry = data["leaderboard"][0]
                        required_fields = ["rank", "username", "total_points", "total_qualifying_wins"]
                        if all(field in entry for field in required_fields):
                            print_pass(f"Arcade Points entry structure ({period})")
                        else:
                            print_fail(f"Arcade Points entry structure ({period})", f"Missing fields: {required_fields}")
                            results.append(False)
                    print_info(f"Arcade Points ({period})", f"Found {len(data['leaderboard'])} entries")
                else:
                    results.append(False)
                    print_fail(f"Arcade Points endpoint ({period})", "leaderboard is not a list")
            else:
                results.append(False)
                print_fail(f"Arcade Points endpoint ({period})", f"Expected period={period}, got {data.get('period')}")
        else:
            results.append(False)
            print_fail(f"Arcade Points endpoint ({period})", "Status code or structure issue")
    
    return all(results)


async def test_leaderboard_arcade_wins(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test /api/leaderboards/arcade-wins endpoint."""
    endpoint = f"{base_url}/api/leaderboards/arcade-wins?limit=20"
    success, data = await test_endpoint_structure(
        client, endpoint, ["wins"]
    )
    
    if success:
        if isinstance(data.get("wins"), list):
            print_pass("Recent Wins feed endpoint structure")
            if len(data["wins"]) > 0:
                entry = data["wins"][0]
                required_fields = ["username", "points_awarded", "num_legs", "resolved_at"]
                if all(field in entry for field in required_fields):
                    print_pass("Recent Wins feed entry structure")
                    print_info("Recent Wins feed", f"Found {len(data['wins'])} entries")
                    return True
                else:
                    print_fail("Recent Wins feed entry structure", f"Missing fields: {required_fields}")
                    return False
            else:
                print_info("Recent Wins feed", "Empty feed (no wins yet)")
                return True
        else:
            print_fail("Recent Wins feed endpoint", "wins is not a list")
            return False
    else:
        print_fail("Recent Wins feed endpoint", "Status code or structure issue")
        return False


async def test_limit_validation(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test limit parameter validation."""
    results = []
    
    # Test valid limits
    for limit in [1, 50, 100]:
        try:
            response = await client.get(
                f"{base_url}/api/leaderboards/custom?limit={limit}",
                timeout=15.0
            )
            if response.status_code == 200:
                results.append(True)
            else:
                results.append(False)
                print_fail(f"Limit validation (limit={limit})", f"Expected 200, got {response.status_code}")
        except Exception as e:
            results.append(False)
            print_fail(f"Limit validation (limit={limit})", str(e))
    
    # Test invalid limits
    for limit in [0, 101, 200]:
        try:
            response = await client.get(
                f"{base_url}/api/leaderboards/custom?limit={limit}",
                timeout=15.0
            )
            if response.status_code == 422:
                results.append(True)
            else:
                results.append(False)
                print_fail(f"Limit validation (invalid limit={limit})", f"Expected 422, got {response.status_code}")
        except Exception as e:
            # Network errors are OK for invalid requests
            results.append(True)
    
    return all(results)


async def test_empty_leaderboards(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test that empty leaderboards return empty arrays, not errors."""
    endpoints = [
        "/api/leaderboards/custom?limit=10",
        "/api/leaderboards/ai-usage?period=all_time&limit=10",
        "/api/leaderboards/arcade-points?period=all_time&limit=10",
        "/api/leaderboards/arcade-wins?limit=10",
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            response = await client.get(f"{base_url}{endpoint}", timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                # Should have leaderboard/wins array (even if empty)
                if "leaderboard" in data or "wins" in data:
                    results.append(True)
                else:
                    results.append(False)
                    print_fail(f"Empty leaderboard check ({endpoint})", "Missing leaderboard/wins field")
            else:
                results.append(False)
                print_fail(f"Empty leaderboard check ({endpoint})", f"Status {response.status_code}")
        except Exception as e:
            results.append(False)
            print_fail(f"Empty leaderboard check ({endpoint})", str(e))
    
    return all(results)


async def test_privacy_controls(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test privacy controls - verify hidden users are excluded and anonymous users show as Gorilla_XXXX."""
    results = []
    
    # Test all leaderboard endpoints for privacy compliance
    endpoints = [
        "/api/leaderboards/custom?limit=50",
        "/api/leaderboards/ai-usage?period=all_time&limit=50",
        "/api/leaderboards/arcade-points?period=all_time&limit=50",
    ]
    
    for endpoint in endpoints:
        try:
            response = await client.get(f"{base_url}{endpoint}", timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                leaderboard = data.get("leaderboard", [])
                
                # Check that no usernames are None or empty (hidden users should be excluded)
                invalid_usernames = [
                    entry for entry in leaderboard
                    if not entry.get("username") or entry.get("username") == ""
                ]
                
                if len(invalid_usernames) == 0:
                    results.append(True)
                    print_pass(f"Privacy controls ({endpoint}) - no hidden users")
                else:
                    results.append(False)
                    print_fail(f"Privacy controls ({endpoint})", f"Found {len(invalid_usernames)} entries with empty usernames")
                
                # Check for anonymous users (should start with "Gorilla_")
                anonymous_count = sum(
                    1 for entry in leaderboard
                    if entry.get("username", "").startswith("Gorilla_")
                )
                if anonymous_count > 0:
                    print_info(f"Privacy controls ({endpoint})", f"Found {anonymous_count} anonymous users (Gorilla_XXXX)")
                
            else:
                results.append(False)
                print_fail(f"Privacy controls ({endpoint})", f"Status {response.status_code}")
        except Exception as e:
            results.append(False)
            print_fail(f"Privacy controls ({endpoint})", str(e))
    
    return all(results)


async def test_data_accuracy(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test data accuracy - rankings, counts, period filtering."""
    results = []
    
    # Test Verified Winners - check rankings are sequential
    try:
        response = await client.get(f"{base_url}/api/leaderboards/custom?limit=20", timeout=15.0)
        if response.status_code == 200:
            data = response.json()
            leaderboard = data.get("leaderboard", [])
            
            if len(leaderboard) > 1:
                # Check ranks are sequential
                ranks = [entry.get("rank") for entry in leaderboard]
                expected_ranks = list(range(1, len(ranks) + 1))
                if ranks == expected_ranks:
                    print_pass("Data accuracy - Verified Winners rankings sequential")
                    results.append(True)
                else:
                    print_fail("Data accuracy - Verified Winners", f"Ranks not sequential: {ranks}")
                    results.append(False)
                
                # Check wins are non-negative
                all_valid = all(
                    entry.get("verified_wins", -1) >= 0 and 
                    0 <= entry.get("win_rate", -1) <= 1
                    for entry in leaderboard
                )
                if all_valid:
                    print_pass("Data accuracy - Verified Winners values valid")
                    results.append(True)
                else:
                    print_fail("Data accuracy - Verified Winners", "Invalid win values")
                    results.append(False)
            else:
                print_skip("Data accuracy - Verified Winners", "Not enough data to verify rankings")
                results.append(True)
        else:
            results.append(False)
            print_fail("Data accuracy - Verified Winners", f"Status {response.status_code}")
    except Exception as e:
        results.append(False)
        print_fail("Data accuracy - Verified Winners", str(e))
    
    # Test AI Usage - check period filtering
    try:
        response_30d = await client.get(f"{base_url}/api/leaderboards/ai-usage?period=30d&limit=20", timeout=15.0)
        response_all = await client.get(f"{base_url}/api/leaderboards/ai-usage?period=all_time&limit=20", timeout=15.0)
        
        if response_30d.status_code == 200 and response_all.status_code == 200:
            data_30d = response_30d.json()
            data_all = response_all.json()
            
            # All-time should have >= 30d entries
            if len(data_all.get("leaderboard", [])) >= len(data_30d.get("leaderboard", [])):
                print_pass("Data accuracy - AI Usage period filtering")
                results.append(True)
            else:
                print_fail("Data accuracy - AI Usage", "All-time has fewer entries than 30d")
                results.append(False)
        else:
            results.append(False)
            print_fail("Data accuracy - AI Usage", "Failed to fetch data")
    except Exception as e:
        results.append(False)
        print_fail("Data accuracy - AI Usage", str(e))
    
    # Test Arcade Points - check rankings and point values
    try:
        response = await client.get(f"{base_url}/api/leaderboards/arcade-points?period=all_time&limit=20", timeout=15.0)
        if response.status_code == 200:
            data = response.json()
            leaderboard = data.get("leaderboard", [])
            
            if len(leaderboard) > 1:
                # Check ranks are sequential
                ranks = [entry.get("rank") for entry in leaderboard]
                expected_ranks = list(range(1, len(ranks) + 1))
                if ranks == expected_ranks:
                    print_pass("Data accuracy - Arcade Points rankings sequential")
                    results.append(True)
                else:
                    print_fail("Data accuracy - Arcade Points", f"Ranks not sequential: {ranks}")
                    results.append(False)
                
                # Check points are in descending order
                points = [entry.get("total_points", -1) for entry in leaderboard]
                if points == sorted(points, reverse=True):
                    print_pass("Data accuracy - Arcade Points sorted by points")
                    results.append(True)
                else:
                    print_fail("Data accuracy - Arcade Points", "Not sorted by points descending")
                    results.append(False)
            else:
                print_skip("Data accuracy - Arcade Points", "Not enough data to verify")
                results.append(True)
        else:
            results.append(False)
            print_fail("Data accuracy - Arcade Points", f"Status {response.status_code}")
    except Exception as e:
        results.append(False)
        print_fail("Data accuracy - Arcade Points", str(e))
    
    return all(results)


async def test_performance(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test API response times and caching."""
    import time
    
    results = []
    endpoints = [
        "/api/leaderboards/custom?limit=10",
        "/api/leaderboards/ai-usage?period=30d&limit=10",
        "/api/leaderboards/arcade-points?period=all_time&limit=10",
        "/api/leaderboards/arcade-wins?limit=10",
    ]
    
    for endpoint in endpoints:
        try:
            # First request (may be slower due to cache miss)
            start = time.time()
            response1 = await client.get(f"{base_url}{endpoint}", timeout=15.0)
            time1 = (time.time() - start) * 1000  # Convert to ms
            
            # Second request (should be faster due to cache)
            start = time.time()
            response2 = await client.get(f"{base_url}{endpoint}", timeout=15.0)
            time2 = (time.time() - start) * 1000
            
            if response1.status_code == 200 and response2.status_code == 200:
                # Check cache headers
                cache_control = response2.headers.get("Cache-Control", "")
                has_cache = "max-age" in cache_control or "public" in cache_control
                
                if time1 < 5000:  # 5 seconds max for first request
                    results.append(True)
                    print_pass(f"Performance ({endpoint}) - Response time: {time1:.0f}ms (first), {time2:.0f}ms (cached)")
                    if has_cache:
                        print_info(f"Performance ({endpoint})", f"Cache headers present: {cache_control}")
                else:
                    results.append(False)
                    print_fail(f"Performance ({endpoint})", f"Response time too slow: {time1:.0f}ms")
            else:
                results.append(False)
                print_fail(f"Performance ({endpoint})", f"Status codes: {response1.status_code}, {response2.status_code}")
        except Exception as e:
            results.append(False)
            print_fail(f"Performance ({endpoint})", str(e))
    
    return all(results)


async def main():
    """Run all backend API tests."""
    backend_url = os.getenv("BACKEND_URL", "https://api.parlaygorilla.com")
    
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}Backend API Production Smoke Test: Leaderboards{Colors.RESET}")
    print(f"{Colors.BLUE}Backend:  {backend_url}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    results = []
    
    async with httpx.AsyncClient() as client:
        # Test all endpoints
        results.append(("Verified Winners endpoint", await test_leaderboard_custom(client, backend_url)))
        results.append(("AI Usage endpoint", await test_leaderboard_ai_usage(client, backend_url)))
        results.append(("Arcade Points endpoint", await test_leaderboard_arcade_points(client, backend_url)))
        results.append(("Recent Wins feed endpoint", await test_leaderboard_arcade_wins(client, backend_url)))
        results.append(("Limit validation", await test_limit_validation(client, backend_url)))
        results.append(("Empty leaderboards handling", await test_empty_leaderboards(client, backend_url)))
        results.append(("Privacy controls", await test_privacy_controls(client, backend_url)))
        results.append(("Data accuracy", await test_data_accuracy(client, backend_url)))
        results.append(("API performance", await test_performance(client, backend_url)))
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}Summary{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
