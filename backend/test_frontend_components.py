"""
Verify frontend components exist and are properly structured

Run with: python test_frontend_components.py
"""

import os
import sys
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


def check_file_exists(path: str, description: str) -> bool:
    """Check if a file exists"""
    full_path = Path(__file__).parent.parent / path
    if full_path.exists():
        print_success(f"{description}: {path}")
        return True
    else:
        print_error(f"{description}: {path} NOT FOUND")
        return False


def check_file_contains(path: str, content: str, description: str) -> bool:
    """Check if a file contains specific content"""
    full_path = Path(__file__).parent.parent / path
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            if content in file_content:
                print_success(f"{description}")
                return True
            else:
                print_error(f"{description} - content not found")
                return False
    except Exception as e:
        print_error(f"{description} - {e}")
        return False


def main():
    print_header("Frontend Component Verification")
    
    passed = 0
    failed = 0
    
    # Analysis page components
    print(f"\n{BOLD}--- Analysis Page Components ---{RESET}\n")
    
    components = [
        ("frontend/app/analysis/page.tsx", "Analysis index page"),
        ("frontend/app/analysis/[slug]/page.tsx", "Dynamic analysis page route"),
        ("frontend/app/analysis/[slug]/AnalysisPageClient.tsx", "Analysis page client component"),
    ]
    
    for path, desc in components:
        if check_file_exists(path, desc):
            passed += 1
        else:
            failed += 1
    
    # Analysis UI components
    print(f"\n{BOLD}--- Analysis UI Components ---{RESET}\n")
    
    ui_components = [
        ("frontend/components/analysis/MatchupHero.tsx", "MatchupHero component"),
        ("frontend/components/analysis/KeyNumbersBar.tsx", "KeyNumbersBar component"),
        ("frontend/components/analysis/GameBreakdown.tsx", "GameBreakdown component"),
        ("frontend/components/analysis/BestBetsSection.tsx", "BestBetsSection component"),
        ("frontend/components/analysis/SameGameParlays.tsx", "SameGameParlays component"),
        ("frontend/components/analysis/TrendsSection.tsx", "TrendsSection component"),
        ("frontend/components/analysis/WeatherInsights.tsx", "WeatherInsights component"),
    ]
    
    for path, desc in ui_components:
        if check_file_exists(path, desc):
            passed += 1
        else:
            failed += 1
    
    # Ad slot component
    print(f"\n{BOLD}--- Ad Slot Component ---{RESET}\n")
    
    if check_file_exists("frontend/components/ads/AdSlot.tsx", "AdSlot component"):
        passed += 1
    else:
        failed += 1
    
    # API client updates
    print(f"\n{BOLD}--- API Client Updates ---{RESET}\n")
    
    api_checks = [
        ("frontend/lib/api.ts", "GameAnalysisResponse", "GameAnalysisResponse type defined"),
        ("frontend/lib/api.ts", "getAnalysis", "getAnalysis function defined"),
        ("frontend/lib/api.ts", "listUpcomingAnalyses", "listUpcomingAnalyses function defined"),
    ]
    
    for path, content, desc in api_checks:
        if check_file_contains(path, content, desc):
            passed += 1
        else:
            failed += 1
    
    # Header navigation
    print(f"\n{BOLD}--- Navigation Updates ---{RESET}\n")
    
    if check_file_contains("frontend/components/Header.tsx", "/analysis", "Analysis link in Header"):
        passed += 1
    else:
        failed += 1
    
    # Summary
    print_header("Verification Summary")
    print(f"Passed: {GREEN}{passed}{RESET}")
    print(f"Failed: {RED}{failed}{RESET}")
    
    if failed == 0:
        print(f"\n{GREEN}{BOLD}All frontend components verified!{RESET}")
        return 0
    else:
        print(f"\n{RED}{BOLD}Some components are missing!{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

