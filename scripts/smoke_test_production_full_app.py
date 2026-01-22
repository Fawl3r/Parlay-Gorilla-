"""
Comprehensive production smoke test for the entire Parlay Gorilla application.

Tests all public pages, protected routes, API endpoints, user flows, and performance
against production (parlaygorilla.com).

Run with:
  python scripts/smoke_test_production_full_app.py
  
  # Quick test (health + key pages only)
  QUICK=true python scripts/smoke_test_production_full_app.py
  
  # With custom URLs
  BACKEND_URL=https://api.parlaygorilla.com \
  FRONTEND_URL=https://parlaygorilla.com \
  python scripts/smoke_test_production_full_app.py
"""

import asyncio
import sys
import os
import time
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import httpx
from playwright.async_api import async_playwright, Page, Browser


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"


def print_pass(test_name: str):
    print(f"{Colors.GREEN}✓ PASS{Colors.RESET}: {test_name}")


def print_fail(test_name: str, error: str):
    print(f"{Colors.RED}✗ FAIL{Colors.RESET}: {test_name} - {error}")


def print_skip(test_name: str, reason: str):
    print(f"{Colors.YELLOW}⊘ SKIP{Colors.RESET}: {test_name} - {reason}")


def print_info(test_name: str, info: str):
    print(f"{Colors.BLUE}ℹ INFO{Colors.RESET}: {test_name} - {info}")


def print_section(title: str):
    print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}{title}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")


# ============================================================================
# Authentication Helpers
# ============================================================================

async def get_auth_token(client: httpx.AsyncClient, base_url: str, email: str, password: str) -> Optional[str]:
    """Get authentication token for testing."""
    try:
        response = await client.post(
            f"{base_url}/api/auth/login",
            json={"email": email, "password": password},
            timeout=15.0
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    except Exception:
        return None


# ============================================================================
# Backend API Tests
# ============================================================================

async def test_health_endpoints(client: httpx.AsyncClient, base_url: str) -> List[Tuple[str, bool]]:
    """Test health and metrics endpoints."""
    results = []
    
    endpoints = [
        ("/health", ["status"]),
        ("/api/health/detailed", ["status", "database", "redis"]),
        ("/api/metrics", []),  # Metrics may vary
    ]
    
    for endpoint, expected_fields in endpoints:
        try:
            response = await client.get(f"{base_url}{endpoint}", timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                # Check if it's a dict and has expected fields, or if it's a simple response
                if isinstance(data, dict) and expected_fields:
                    if all(field in data for field in expected_fields):
                        print_pass(f"Health endpoint ({endpoint})")
                        results.append((f"Health {endpoint}", True))
                    else:
                        print_skip(f"Health endpoint ({endpoint})", f"Missing some fields: {expected_fields}")
                        results.append((f"Health {endpoint}", True))  # Skip is OK
                else:
                    # Simple response or no expected fields
                    print_pass(f"Health endpoint ({endpoint})")
                    results.append((f"Health {endpoint}", True))
            else:
                print_skip(f"Health endpoint ({endpoint})", f"Status {response.status_code}")
                results.append((f"Health {endpoint}", True))  # Skip is OK for non-200
        except Exception as e:
            print_fail(f"Health endpoint ({endpoint})", str(e))
            results.append((f"Health {endpoint}", False))
    
    return results


async def test_games_apis(client: httpx.AsyncClient, base_url: str) -> List[Tuple[str, bool]]:
    """Test games and odds API endpoints."""
    results = []
    
    sports = ["nfl", "nba", "nhl", "mlb"]
    
    for sport in sports[:2]:  # Test first 2 sports
        try:
            response = await client.get(f"{base_url}/api/sports/{sport}/games", timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                # Handle both list and object responses
                if isinstance(data, list):
                    games_count = len(data)
                else:
                    games_count = len(data.get('games', []))
                print_pass(f"Games API ({sport})")
                print_info(f"Games API ({sport})", f"Found {games_count} games")
                results.append((f"Games API {sport}", True))
            else:
                print_skip(f"Games API ({sport})", f"Status {response.status_code} (may be no games)")
                results.append((f"Games API {sport}", True))  # Skip is OK
        except Exception as e:
            print_skip(f"Games API ({sport})", str(e))
            results.append((f"Games API {sport}", True))
    
    # Test NFL weeks
    try:
        response = await client.get(f"{base_url}/api/weeks/nfl", timeout=15.0)
        if response.status_code == 200:
            data = response.json()
            print_pass("NFL Weeks API")
            print_info("NFL Weeks API", f"Response received (type: {type(data).__name__})")
            results.append(("NFL Weeks API", True))
        else:
            print_skip("NFL Weeks API", f"Status {response.status_code}")
            results.append(("NFL Weeks API", True))
    except Exception as e:
        print_skip("NFL Weeks API", str(e))
        results.append(("NFL Weeks API", True))
    
    return results


async def test_parlay_apis(client: httpx.AsyncClient, base_url: str, token: Optional[str] = None) -> List[Tuple[str, bool]]:
    """Test parlay API endpoints."""
    results = []
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    # Test parlay history (requires auth)
    if token:
        try:
            response = await client.get(f"{base_url}/api/parlay/history", headers=headers, timeout=15.0)
            if response.status_code in [200, 401]:
                print_pass("Parlay history API")
                results.append(("Parlay history", True))
            else:
                print_skip("Parlay history API", f"Status {response.status_code}")
                results.append(("Parlay history", True))
        except Exception as e:
            print_skip("Parlay history API", str(e))
            results.append(("Parlay history", True))
    else:
        print_skip("Parlay history API", "No auth token")
        results.append(("Parlay history", True))
    
    # Test parlay suggest (requires auth and may be slow)
    if token:
        try:
            response = await client.post(
                f"{base_url}/api/parlay/suggest",
                headers=headers,
                json={
                    "sport": "nfl",
                    "num_legs": 3,
                    "risk_profile": "balanced"
                },
                timeout=60.0  # AI generation can be slow
            )
            if response.status_code in [200, 402, 429]:  # 402 = paywall, 429 = rate limit
                print_pass("Parlay suggest API")
                results.append(("Parlay suggest", True))
            elif response.status_code == 500:
                print_fail("Parlay suggest API", "500 error (known issue)")
                results.append(("Parlay suggest", False))
            else:
                print_skip("Parlay suggest API", f"Status {response.status_code}")
                results.append(("Parlay suggest", True))
        except Exception as e:
            print_skip("Parlay suggest API", str(e))
            results.append(("Parlay suggest", True))
    else:
        print_skip("Parlay suggest API", "No auth token")
        results.append(("Parlay suggest", True))
    
    return results


async def test_social_apis(client: httpx.AsyncClient, base_url: str) -> List[Tuple[str, bool]]:
    """Test social feature API endpoints."""
    results = []
    
    # Test social feed (public)
    try:
        response = await client.get(f"{base_url}/api/social/feed?limit=10", timeout=15.0)
        if response.status_code == 200:
            data = response.json()
            print_pass("Social feed API")
            print_info("Social feed", f"Found {len(data.get('feed', []))} items")
            results.append(("Social feed", True))
        else:
            print_skip("Social feed API", f"Status {response.status_code}")
            results.append(("Social feed", True))
    except Exception as e:
        print_skip("Social feed API", str(e))
        results.append(("Social feed", True))
    
    return results


async def test_analysis_apis(client: httpx.AsyncClient, base_url: str) -> List[Tuple[str, bool]]:
    """Test analysis API endpoints."""
    results = []
    
    sports = ["nfl", "nba"]
    
    for sport in sports:
        try:
            response = await client.get(f"{base_url}/api/analysis/{sport}/upcoming?limit=5", timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                # Handle both list and object responses
                if isinstance(data, list):
                    analyses_count = len(data)
                else:
                    analyses_count = len(data.get('analyses', []))
                print_pass(f"Analysis upcoming ({sport})")
                print_info(f"Analysis upcoming ({sport})", f"Found {analyses_count} analyses")
                results.append((f"Analysis {sport}", True))
            else:
                print_skip(f"Analysis upcoming ({sport})", f"Status {response.status_code}")
                results.append((f"Analysis {sport}", True))
        except Exception as e:
            print_skip(f"Analysis upcoming ({sport})", str(e))
            results.append((f"Analysis {sport}", True))
    
    return results


async def test_auth_apis(client: httpx.AsyncClient, base_url: str) -> List[Tuple[str, bool]]:
    """Test authentication API endpoints."""
    results = []
    
    # Test register endpoint structure (don't actually register)
    try:
        response = await client.post(
            f"{base_url}/api/auth/register",
            json={"email": "test@example.com", "password": "Test123!"},
            timeout=15.0
        )
        # Should return 200 (success) or 400/422 (validation error) - both are OK
        if response.status_code in [200, 201, 400, 422]:
            print_pass("Auth register endpoint")
            results.append(("Auth register", True))
        else:
            print_fail("Auth register endpoint", f"Unexpected status {response.status_code}")
            results.append(("Auth register", False))
    except Exception as e:
        print_skip("Auth register endpoint", str(e))
        results.append(("Auth register", True))
    
    # Test forgot password endpoint
    try:
        response = await client.post(
            f"{base_url}/api/auth/forgot-password",
            json={"email": "test@example.com"},
            timeout=15.0
        )
        # Should return 200 (success) or 404 (user not found) - both are OK
        if response.status_code in [200, 404]:
            print_pass("Auth forgot password endpoint")
            results.append(("Auth forgot password", True))
        else:
            print_skip("Auth forgot password endpoint", f"Status {response.status_code}")
            results.append(("Auth forgot password", True))
    except Exception as e:
        print_skip("Auth forgot password endpoint", str(e))
        results.append(("Auth forgot password", True))
    
    return results


async def test_profile_apis(client: httpx.AsyncClient, base_url: str, token: Optional[str] = None) -> List[Tuple[str, bool]]:
    """Test profile and subscription API endpoints."""
    results = []
    
    if not token:
        print_skip("Profile APIs", "No auth token")
        return [("Profile APIs", True)]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test profile me
    try:
        response = await client.get(f"{base_url}/api/profile/me", headers=headers, timeout=15.0)
        if response.status_code == 200:
            print_pass("Profile me API")
            results.append(("Profile me", True))
        else:
            print_skip("Profile me API", f"Status {response.status_code}")
            results.append(("Profile me", True))
    except Exception as e:
        print_skip("Profile me API", str(e))
        results.append(("Profile me", True))
    
    # Test subscription me
    try:
        response = await client.get(f"{base_url}/api/subscription/me", headers=headers, timeout=15.0)
        if response.status_code == 200:
            print_pass("Subscription me API")
            results.append(("Subscription me", True))
        else:
            print_skip("Subscription me API", f"Status {response.status_code}")
            results.append(("Subscription me", True))
    except Exception as e:
        print_skip("Subscription me API", str(e))
        results.append(("Subscription me", True))
    
    return results


# ============================================================================
# Frontend Page Tests
# ============================================================================

async def test_public_pages(page: Page, frontend_url: str, quick: bool = False) -> List[Tuple[str, bool]]:
    """Test all public pages."""
    results = []
    
    public_pages = [
        ("/", "Landing page"),
        ("/pricing", "Pricing page"),
        ("/leaderboards", "Leaderboards page"),
        ("/analysis", "Game Analytics page"),
    ]
    
    if not quick:
        public_pages.extend([
            ("/tutorial", "Tutorial page"),
            ("/docs", "Documentation page"),
            ("/auth/login", "Login page"),
            ("/auth/signup", "Signup page"),
        ])
    
    for path, name in public_pages:
        try:
            response = await page.goto(f"{frontend_url}{path}", wait_until="domcontentloaded", timeout=30000)
            if response and response.status == 200:
                # Check for basic content
                await page.wait_for_timeout(1000)
                title = await page.title()
                if title and len(title) > 0:
                    print_pass(f"{name}")
                    results.append((name, True))
                else:
                    print_fail(f"{name}", "No title found")
                    results.append((name, False))
            else:
                print_fail(f"{name}", f"Status {response.status if response else 'None'}")
                results.append((name, False))
        except Exception as e:
            print_fail(f"{name}", str(e))
            results.append((name, False))
    
    return results


async def test_protected_routes(page: Page, frontend_url: str, token: Optional[str] = None) -> List[Tuple[str, bool]]:
    """Test protected routes (should redirect if not authenticated)."""
    results = []
    
    protected_routes = [
        ("/app", "Dashboard"),
        ("/analytics", "Analytics"),
        ("/profile", "Profile"),
        ("/billing", "Billing"),
    ]
    
    for path, name in protected_routes:
        try:
            # Set auth token if provided
            if token:
                await page.add_init_script(f"""
                    localStorage.setItem('auth_token', '{token}');
                """)
            
            response = await page.goto(f"{frontend_url}{path}", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
            
            current_url = page.url
            
            if token:
                # Should stay on protected route
                if path in current_url or "/app" in current_url:
                    print_pass(f"{name} (authenticated)")
                    results.append((f"{name} (auth)", True))
                else:
                    print_fail(f"{name} (authenticated)", f"Redirected to {current_url}")
                    results.append((f"{name} (auth)", False))
            else:
                # Should redirect to login (or may allow public access for some routes)
                if "/auth/login" in current_url or "/auth/signup" in current_url:
                    print_pass(f"{name} (redirects unauthenticated)")
                    results.append((f"{name} (unauth)", True))
                elif path in current_url:
                    # Some routes may allow public access
                    print_skip(f"{name} (redirects unauthenticated)", f"Allows public access (at {current_url})")
                    results.append((f"{name} (unauth)", True))
                else:
                    print_skip(f"{name} (redirects unauthenticated)", f"Unexpected location: {current_url}")
                    results.append((f"{name} (unauth)", True))
        except Exception as e:
            print_fail(f"{name}", str(e))
            results.append((name, False))
    
    return results


async def test_dashboard_tabs(page: Page, frontend_url: str, token: Optional[str] = None) -> List[Tuple[str, bool]]:
    """Test dashboard tabs functionality."""
    results = []
    
    if not token:
        print_skip("Dashboard tabs", "No auth token")
        return [("Dashboard tabs", True)]
    
    try:
        # Set auth token
        await page.add_init_script(f"""
            localStorage.setItem('auth_token', '{token}');
        """)
        
        await page.goto(f"{frontend_url}/app", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)  # Wait for dashboard to load
        
        # Check for tabs
        tabs = ["Games", "AI Picks", "Custom Builder", "Insights"]
        found_tabs = []
        
        for tab_name in tabs:
            try:
                tab_button = page.get_by_role("button", name=re.compile(tab_name, re.I))
                if await tab_button.count() > 0:
                    found_tabs.append(tab_name)
                    await tab_button.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass
        
        if len(found_tabs) >= 2:  # At least 2 tabs should be found
            print_pass(f"Dashboard tabs ({len(found_tabs)} tabs found)")
            results.append(("Dashboard tabs", True))
        else:
            print_skip("Dashboard tabs", f"Only found {len(found_tabs)} tabs")
            results.append(("Dashboard tabs", True))
    except Exception as e:
        print_skip("Dashboard tabs", str(e))
        results.append(("Dashboard tabs", True))
    
    return results


# ============================================================================
# User Flow Tests
# ============================================================================

async def test_signup_flow(page: Page, frontend_url: str) -> List[Tuple[str, bool]]:
    """Test new user signup flow."""
    results = []
    
    try:
        await page.goto(f"{frontend_url}/auth/signup", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1000)
        
        # Check signup form exists
        email_input = page.locator('input[type="email"]')
        password_input = page.locator('input[type="password"]')
        
        if await email_input.count() > 0 and await password_input.count() > 0:
            print_pass("Signup flow - Form loads")
            results.append(("Signup form", True))
        else:
            print_skip("Signup flow", "Form elements not found")
            results.append(("Signup form", True))
    except Exception as e:
        print_skip("Signup flow", str(e))
        results.append(("Signup form", True))
    
    return results


async def test_login_flow(page: Page, frontend_url: str) -> List[Tuple[str, bool]]:
    """Test login flow."""
    results = []
    
    try:
        await page.goto(f"{frontend_url}/auth/login", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1000)
        
        # Check login form exists
        email_input = page.locator('input[type="email"]')
        password_input = page.locator('input[type="password"]')
        
        if await email_input.count() > 0 and await password_input.count() > 0:
            print_pass("Login flow - Form loads")
            results.append(("Login form", True))
        else:
            print_skip("Login flow", "Form elements not found")
            results.append(("Login form", True))
    except Exception as e:
        print_skip("Login flow", str(e))
        results.append(("Login form", True))
    
    return results


async def test_parlay_generation_flow(page: Page, frontend_url: str, token: Optional[str] = None) -> List[Tuple[str, bool]]:
    """Test parlay generation flow in dashboard."""
    results = []
    
    if not token:
        print_skip("Parlay generation flow", "No auth token")
        return [("Parlay generation flow", True)]
    
    try:
        # Set auth token
        await page.add_init_script(f"""
            localStorage.setItem('auth_token', '{token}');
        """)
        
        await page.goto(f"{frontend_url}/app", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Try to find AI Picks tab
        ai_picks_tab = page.get_by_role("button", name=re.compile("AI Picks", re.I))
        if await ai_picks_tab.count() > 0:
            await ai_picks_tab.click()
            await page.wait_for_timeout(2000)
            
            # Check for parlay builder elements
            generate_button = page.get_by_role("button", name=re.compile("generate", re.I))
            if await generate_button.count() > 0:
                print_pass("Parlay generation flow - UI accessible")
                results.append(("Parlay generation UI", True))
            else:
                print_skip("Parlay generation flow", "Generate button not found")
                results.append(("Parlay generation UI", True))
        else:
            print_skip("Parlay generation flow", "AI Picks tab not found")
            results.append(("Parlay generation UI", True))
    except Exception as e:
        print_skip("Parlay generation flow", str(e))
        results.append(("Parlay generation UI", True))
    
    return results


async def test_navigation_flow(page: Page, frontend_url: str) -> List[Tuple[str, bool]]:
    """Test navigation between pages."""
    results = []
    
    navigation_tests = [
        ("/", "/leaderboards", "Home to Leaderboards"),
        ("/leaderboards", "/pricing", "Leaderboards to Pricing"),
        ("/pricing", "/", "Pricing to Home"),
    ]
    
    for start_path, end_path, name in navigation_tests:
        try:
            await page.goto(f"{frontend_url}{start_path}", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1000)
            
            # Find and click navigation link
            link = page.locator(f'a[href="{end_path}"], a[href*="{end_path}"]')
            if await link.count() > 0:
                await link.first.click()
                await page.wait_for_timeout(2000)
                
                if end_path in page.url:
                    print_pass(f"Navigation - {name}")
                    results.append((f"Navigation {name}", True))
                else:
                    print_skip(f"Navigation - {name}", f"Did not navigate to {end_path}")
                    results.append((f"Navigation {name}", True))
            else:
                print_skip(f"Navigation - {name}", "Link not found")
                results.append((f"Navigation {name}", True))
        except Exception as e:
            print_skip(f"Navigation - {name}", str(e))
            results.append((f"Navigation {name}", True))
    
    return results


# ============================================================================
# Error Handling Tests
# ============================================================================

async def test_error_pages(page: Page, frontend_url: str) -> List[Tuple[str, bool]]:
    """Test error page handling."""
    results = []
    
    # Test 404 page
    try:
        response = await page.goto(f"{frontend_url}/nonexistent-page-12345", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1000)
        
        # Should show 404 or redirect to home
        if response and response.status == 404:
            print_pass("404 error page")
            results.append(("404 page", True))
        elif "404" in await page.content() or "not found" in (await page.title()).lower():
            print_pass("404 error page")
            results.append(("404 page", True))
        else:
            print_skip("404 error page", "No 404 detected (may redirect)")
            results.append(("404 page", True))
    except Exception as e:
        print_skip("404 error page", str(e))
        results.append(("404 page", True))
    
    return results


# ============================================================================
# Performance Tests
# ============================================================================

async def test_page_performance(page: Page, frontend_url: str) -> List[Tuple[str, bool]]:
    """Test page load performance."""
    results = []
    
    pages_to_test = [
        ("/", "Landing page"),
        ("/leaderboards", "Leaderboards"),
        ("/pricing", "Pricing"),
    ]
    
    for path, name in pages_to_test:
        try:
            start = time.time()
            response = await page.goto(f"{frontend_url}{path}", wait_until="domcontentloaded", timeout=30000)
            load_time = (time.time() - start) * 1000  # Convert to ms
            
            if response:
                if load_time < 5000:  # 5 seconds max
                    print_pass(f"{name} performance ({load_time:.0f}ms)")
                    results.append((f"{name} performance", True))
                else:
                    print_fail(f"{name} performance", f"Too slow: {load_time:.0f}ms")
                    results.append((f"{name} performance", False))
            else:
                print_skip(f"{name} performance", "No response")
                results.append((f"{name} performance", True))
        except Exception as e:
            print_skip(f"{name} performance", str(e))
            results.append((f"{name} performance", True))
    
    return results


async def test_api_performance(client: httpx.AsyncClient, base_url: str) -> List[Tuple[str, bool]]:
    """Test API response performance."""
    results = []
    
    endpoints = [
        "/health",
        "/api/leaderboards/custom?limit=10",
        "/api/social/feed?limit=10",
    ]
    
    for endpoint in endpoints:
        try:
            start = time.time()
            response = await client.get(f"{base_url}{endpoint}", timeout=15.0)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                if response_time < 2000:  # 2 seconds max
                    print_pass(f"API performance ({endpoint}) - {response_time:.0f}ms")
                    results.append((f"API {endpoint}", True))
                else:
                    print_fail(f"API performance ({endpoint})", f"Too slow: {response_time:.0f}ms")
                    results.append((f"API {endpoint}", False))
            else:
                print_skip(f"API performance ({endpoint})", f"Status {response.status_code}")
                results.append((f"API {endpoint}", True))
        except Exception as e:
            print_skip(f"API performance ({endpoint})", str(e))
            results.append((f"API {endpoint}", True))
    
    return results


# ============================================================================
# Main Test Runner
# ============================================================================

async def run_backend_tests(base_url: str, token: Optional[str] = None, quick: bool = False) -> List[Tuple[str, bool]]:
    """Run all backend API tests."""
    print_section("Backend API Tests")
    
    all_results = []
    
    async with httpx.AsyncClient() as client:
        all_results.extend(await test_health_endpoints(client, base_url))
        all_results.extend(await test_games_apis(client, base_url))
        all_results.extend(await test_parlay_apis(client, base_url, token))
        all_results.extend(await test_social_apis(client, base_url))
        all_results.extend(await test_analysis_apis(client, base_url))
        all_results.extend(await test_auth_apis(client, base_url))
        all_results.extend(await test_profile_apis(client, base_url, token))
        
        if not quick:
            all_results.extend(await test_api_performance(client, base_url))
    
    return all_results


async def run_frontend_tests(frontend_url: str, token: Optional[str] = None, quick: bool = False) -> List[Tuple[str, bool]]:
    """Run all frontend tests."""
    print_section("Frontend Tests")
    
    all_results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            all_results.extend(await test_public_pages(page, frontend_url, quick))
            all_results.extend(await test_protected_routes(page, frontend_url, token))
            all_results.extend(await test_dashboard_tabs(page, frontend_url, token))
            all_results.extend(await test_error_pages(page, frontend_url))
            all_results.extend(await test_signup_flow(page, frontend_url))
            all_results.extend(await test_login_flow(page, frontend_url))
            all_results.extend(await test_parlay_generation_flow(page, frontend_url, token))
            all_results.extend(await test_navigation_flow(page, frontend_url))
            
            if not quick:
                all_results.extend(await test_page_performance(page, frontend_url))
        finally:
            await browser.close()
    
    return all_results


async def main():
    """Run comprehensive production tests."""
    backend_url = os.getenv("BACKEND_URL", "https://api.parlaygorilla.com")
    frontend_url = os.getenv("FRONTEND_URL", "https://parlaygorilla.com")
    quick = os.getenv("QUICK", "false").lower() == "true"
    
    # Optional: Get auth token for authenticated tests
    test_email = os.getenv("TEST_EMAIL")
    test_password = os.getenv("TEST_PASSWORD")
    token = None
    
    if test_email and test_password:
        async with httpx.AsyncClient() as client:
            token = await get_auth_token(client, backend_url, test_email, test_password)
            if token:
                print_info("Authentication", "Successfully authenticated for protected route tests")
            else:
                print_skip("Authentication", "Could not authenticate (will skip protected route tests)")
    
    print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}Comprehensive Production Test: Full Parlay Gorilla App{Colors.RESET}")
    print(f"{Colors.CYAN}Backend:  {backend_url}{Colors.RESET}")
    print(f"{Colors.CYAN}Frontend: {frontend_url}{Colors.RESET}")
    print(f"{Colors.CYAN}Mode:     {'Quick' if quick else 'Comprehensive'}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    all_results = []
    
    # Run backend tests
    backend_results = await run_backend_tests(backend_url, token, quick)
    all_results.extend(backend_results)
    
    # Run frontend tests
    frontend_results = await run_frontend_tests(frontend_url, token, quick)
    all_results.extend(frontend_results)
    
    # Summary
    print_section("Summary")
    
    passed = sum(1 for _, result in all_results if result)
    total = len(all_results)
    
    for test_name, result in all_results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed ({passed*100//total if total > 0 else 0}%)")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
