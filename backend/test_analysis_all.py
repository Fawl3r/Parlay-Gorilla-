"""
Comprehensive test suite for the Analysis System

Run with: python test_analysis_all.py
Or with pytest: pytest test_analysis_all.py -v
"""

import asyncio
import sys
import traceback
from datetime import datetime
import os
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text):
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}{text}{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")


def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_section(text):
    print(f"\n{BOLD}--- {text} ---{RESET}\n")


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors = []

    def add_pass(self, name):
        self.passed += 1
        print_success(name)

    def add_fail(self, name, error):
        self.failed += 1
        self.errors.append((name, error))
        print_error(f"{name}: {error}")

    def add_warning(self, name):
        self.warnings += 1
        print_warning(name)

    def summary(self):
        print_header("Test Summary")
        print(f"Passed: {GREEN}{self.passed}{RESET}")
        print(f"Failed: {RED}{self.failed}{RESET}")
        print(f"Warnings: {YELLOW}{self.warnings}{RESET}")
        
        if self.errors:
            print(f"\n{RED}Failed tests:{RESET}")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        
        return self.failed == 0


results = TestResults()


# =============================================================================
# ENV HELPERS (Tunnel-friendly)
# =============================================================================

def _load_env_if_present(env_path: Path) -> None:
    """
    Best-effort `.env` loader so test scripts work without manual exports.

    - Does NOT override already-set environment variables.
    - Ignores comments and blank lines.
    """
    try:
        if not env_path.exists():
            return
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)
    except Exception:
        # Non-fatal; tests can still run with defaults.
        return


def _resolve_backend_base_url() -> str:
    """
    Resolve the backend base URL for live server tests.

    Priority:
    - PG_BACKEND_URL (used by tunnel workflows)
    - NEXT_PUBLIC_API_URL (frontend tunnel config)
    - BACKEND_URL (backend .env)
    - localhost default
    """
    return (
        os.environ.get("PG_BACKEND_URL")
        or os.environ.get("NEXT_PUBLIC_API_URL")
        or os.environ.get("BACKEND_URL")
        or "http://localhost:8000"
    )


# =============================================================================
# MODEL TESTS
# =============================================================================

def test_models():
    print_section("Model Tests")
    
    try:
        from app.models.game_analysis import GameAnalysis
        results.add_pass("GameAnalysis model imports")
    except Exception as e:
        results.add_fail("GameAnalysis model imports", str(e))
        return
    
    try:
        assert hasattr(GameAnalysis, 'id')
        assert hasattr(GameAnalysis, 'slug')
        assert hasattr(GameAnalysis, 'analysis_content')
        assert hasattr(GameAnalysis, 'seo_metadata')
        results.add_pass("GameAnalysis has all required fields")
    except AssertionError as e:
        results.add_fail("GameAnalysis fields", str(e))
    
    try:
        from app.models.team_stats import TeamStats
        assert hasattr(TeamStats, 'ats_wins')
        assert hasattr(TeamStats, 'over_wins')
        results.add_pass("TeamStats has ATS/O-U trend fields")
    except Exception as e:
        results.add_fail("TeamStats ATS/O-U fields", str(e))
    
    try:
        from app.models import GameAnalysis as GA
        assert GA is not None
        results.add_pass("GameAnalysis registered in models __init__")
    except Exception as e:
        results.add_fail("GameAnalysis in __init__", str(e))


# =============================================================================
# SCHEMA TESTS
# =============================================================================

def test_schemas():
    print_section("Schema Tests")
    
    try:
        from app.schemas.analysis import (
            GameAnalysisResponse,
            GameAnalysisListItem,
            SpreadPick,
            TotalPick,
            BestBet,
            ModelWinProbability,
        )
        results.add_pass("All analysis schemas import")
    except Exception as e:
        results.add_fail("Analysis schemas import", str(e))
        return
    
    try:
        pick = SpreadPick(pick="Home -3.5", confidence=72, rationale="Test")
        assert pick.confidence == 72
        results.add_pass("SpreadPick schema validation")
    except Exception as e:
        results.add_fail("SpreadPick validation", str(e))
    
    try:
        bet = BestBet(bet_type="Spread", pick="Home -3.5", confidence=72, rationale="Test")
        assert bet.bet_type == "Spread"
        results.add_pass("BestBet schema validation")
    except Exception as e:
        results.add_fail("BestBet validation", str(e))
    
    try:
        prob = ModelWinProbability(home_win_prob=0.6, away_win_prob=0.4, explanation="Test")
        assert prob.home_win_prob == 0.6
        results.add_pass("ModelWinProbability schema validation")
    except Exception as e:
        results.add_fail("ModelWinProbability validation", str(e))


# =============================================================================
# SERVICE TESTS
# =============================================================================

def test_services():
    print_section("Service Tests")
    
    # Stats Scraper
    try:
        from app.services.stats_scraper import StatsScraperService
        results.add_pass("StatsScraperService imports")
    except Exception as e:
        results.add_fail("StatsScraperService import", str(e))
        return
    
    try:
        from unittest.mock import MagicMock
        mock_db = MagicMock()
        scraper = StatsScraperService(mock_db)
        
        # Test weather assessment
        weather_data = {
            "weather": [{"main": "Rain"}],
            "wind": {"speed": 5},
            "main": {"temp": 65}
        }
        impact = scraper._assess_weather_impact(weather_data)
        assert len(impact) > 0
        results.add_pass("StatsScraperService weather assessment")
    except Exception as e:
        results.add_fail("StatsScraperService weather", str(e))
    
    # Analysis Generator
    try:
        from app.services.analysis_generator import AnalysisGeneratorService
        results.add_pass("AnalysisGeneratorService imports")
    except Exception as e:
        results.add_fail("AnalysisGeneratorService import", str(e))
        return
    
    try:
        from unittest.mock import MagicMock
        mock_db = MagicMock()
        generator = AnalysisGeneratorService(mock_db)
        
        # Test context building
        context = generator._build_analysis_context(
            home_team="Green Bay Packers",
            away_team="Chicago Bears",
            league="NFL",
            game_time=datetime.now(),
            matchup_data={"home_team_stats": None, "away_team_stats": None},
            odds_data={}
        )
        assert "Green Bay Packers" in context
        assert "Chicago Bears" in context
        results.add_pass("AnalysisGeneratorService context building")
    except Exception as e:
        results.add_fail("AnalysisGeneratorService context", str(e))
    
    try:
        formatted = generator._format_team_stats("Test Team", None)
        assert "not available" in formatted.lower()
        results.add_pass("AnalysisGeneratorService stats formatting")
    except Exception as e:
        results.add_fail("AnalysisGeneratorService formatting", str(e))


# =============================================================================
# API ROUTE TESTS
# =============================================================================

def test_api_routes():
    print_section("API Route Tests")
    
    try:
        from app.api.routes.analysis import router, _generate_slug
        results.add_pass("Analysis router imports")
    except Exception as e:
        results.add_fail("Analysis router import", str(e))
        return
    
    try:
        slug = _generate_slug(
            home_team="Green Bay Packers",
            away_team="Chicago Bears",
            league="NFL",
            game_time=datetime(2025, 12, 14, 13, 0, 0)
        )
        assert "nfl" in slug.lower()
        assert "bears" in slug.lower()
        assert "packers" in slug.lower()
        results.add_pass("Slug generation for NFL")
    except Exception as e:
        results.add_fail("Slug generation NFL", str(e))
    
    try:
        slug = _generate_slug(
            home_team="Lakers",
            away_team="Celtics",
            league="NBA",
            game_time=datetime(2025, 12, 14, 19, 0, 0)
        )
        assert "nba" in slug.lower()
        assert "2025-12-14" in slug
        results.add_pass("Slug generation for NBA")
    except Exception as e:
        results.add_fail("Slug generation NBA", str(e))
    
    try:
        from app.main import app
        routes = [route.path for route in app.routes]
        analysis_routes = [r for r in routes if "analysis" in r]
        assert len(analysis_routes) >= 3, f"Expected 3+ analysis routes, found {len(analysis_routes)}"
        results.add_pass(f"Analysis routes registered ({len(analysis_routes)} routes)")
    except Exception as e:
        results.add_fail("Analysis routes registration", str(e))


# =============================================================================
# SCHEDULER TESTS
# =============================================================================

def test_scheduler():
    print_section("Scheduler Tests")
    
    try:
        from app.services.scheduler import BackgroundScheduler, get_scheduler
        results.add_pass("Scheduler imports")
    except Exception as e:
        results.add_fail("Scheduler import", str(e))
        return
    
    try:
        scheduler = BackgroundScheduler()
        assert hasattr(scheduler, '_generate_upcoming_analyses')
        assert hasattr(scheduler, '_cleanup_expired_analyses')
        results.add_pass("Scheduler has analysis jobs")
    except Exception as e:
        results.add_fail("Scheduler analysis jobs", str(e))


# =============================================================================
# LIVE SERVER TESTS (Optional)
# =============================================================================

async def test_live_server():
    print_section("Live Server Tests (Optional)")
    
    import httpx

    # Load env files if present so tunnel URLs work without manual exports.
    # - backend/.env (common local setup)
    # - frontend/.env.local (tunnel setup script writes/uses this)
    repo_root = Path(__file__).resolve().parent
    _load_env_if_present(repo_root / ".env")
    _load_env_if_present(repo_root.parent / "frontend" / ".env.local")

    base_url = _resolve_backend_base_url()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                results.add_pass("Server is running and healthy")
            else:
                results.add_warning(f"Server responded with {response.status_code}")
                return
    except httpx.ConnectError:
        results.add_warning("Server not running - skipping live tests")
        return
    except Exception as e:
        results.add_warning(f"Server connection error: {e}")
        return
    
    # Test upcoming analyses endpoint
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/api/analysis/nfl/upcoming")
            if response.status_code == 200:
                data = response.json()
                results.add_pass(f"Upcoming analyses endpoint works ({len(data)} results)")
            else:
                results.add_warning(f"Upcoming analyses returned {response.status_code}")
    except Exception as e:
        results.add_warning(f"Upcoming analyses error: {e}")
    
    # Test 404 for non-existent analysis
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/api/analysis/nfl/non-existent-slug-12345")
            if response.status_code == 404:
                results.add_pass("Non-existent analysis returns 404")
            else:
                results.add_warning(f"Non-existent analysis returned {response.status_code}")
    except Exception as e:
        results.add_warning(f"404 test error: {e}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print_header("Parlay Gorilla Analysis System - Comprehensive Tests")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run all tests
    test_models()
    test_schemas()
    test_services()
    test_api_routes()
    test_scheduler()
    
    # Run live server tests
    try:
        asyncio.run(test_live_server())
    except Exception as e:
        results.add_warning(f"Live server tests failed: {e}")
    
    # Print summary
    success = results.summary()
    
    if success:
        print(f"\n{GREEN}{BOLD}All tests passed!{RESET}")
        sys.exit(0)
    else:
        print(f"\n{RED}{BOLD}Some tests failed!{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()

