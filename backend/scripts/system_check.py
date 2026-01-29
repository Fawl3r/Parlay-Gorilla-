"""
Comprehensive system check script for Parlay Gorilla backend.

This script validates:
- Environment variables
- Database connections
- API keys and external services
- Python dependencies
- Code compilation/imports
- Critical system components

Run: python scripts/system_check.py
"""

import asyncio
import importlib
import os
import sys
import traceback
from pathlib import Path
from typing import List, Tuple

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(message: str):
    print(f"{Colors.GREEN}✓{Colors.END} {message}")

def print_error(message: str):
    print(f"{Colors.RED}✗{Colors.END} {message}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ{Colors.END} {message}")

def print_header(message: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


class SystemChecker:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.success_count = 0
        
    def check(self, name: str, test_func, *args, **kwargs):
        """Run a check and track results"""
        try:
            result = test_func(*args, **kwargs)
            if result:
                print_success(name)
                self.success_count += 1
                return True
            else:
                print_error(name)
                self.errors.append(name)
                return False
        except Exception as e:
            print_error(f"{name}: {str(e)}")
            self.errors.append(f"{name}: {str(e)}")
            return False
    
    def check_warning(self, name: str, test_func, *args, **kwargs):
        """Run a check that can produce warnings"""
        try:
            result = test_func(*args, **kwargs)
            if result:
                print_success(name)
                self.success_count += 1
                return True
            else:
                print_warning(name)
                self.warnings.append(name)
                return False
        except Exception as e:
            print_warning(f"{name}: {str(e)}")
            self.warnings.append(f"{name}: {str(e)}")
            return False


def check_environment_variables() -> bool:
    """Check critical environment variables"""
    print_header("Environment Variables Check")
    
    # Load environment from .env file
    try:
        from dotenv import load_dotenv
        env_path = backend_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass  # python-dotenv not installed, will use system env
    
    checker = SystemChecker()
    
    # Load settings to check actual values
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        # Required variables
        required_checks = [
            ("DATABASE_URL", "Database connection string", settings.database_url),
            ("THE_ODDS_API_KEY", "The Odds API key", settings.the_odds_api_key),
            ("OPENAI_API_KEY", "OpenAI API key", settings.openai_api_key),
        ]
        
        for var_name, description, value in required_checks:
            if value:
                # Mask sensitive values
                if "key" in var_name.lower() or "password" in var_name.lower() or "secret" in var_name.lower():
                    masked = value[:10] + "..." + value[-5:] if len(value) > 15 else "***"
                    checker.check(f"{description} ({var_name})", lambda: True)
                    print_info(f"  Value: {masked}")
                else:
                    # Mask database URL
                    if "@" in str(value):
                        masked = str(value).split("@")[0] + "@[HIDDEN]"
                    else:
                        masked = str(value)
                    checker.check(f"{description} ({var_name})", lambda: True)
                    print_info(f"  Value: {masked}")
            else:
                checker.check(f"{description} ({var_name})", lambda: False)
        
        # Optional but recommended
        optional_checks = [
            ("REDIS_URL", "Redis connection string", settings.redis_url),
            ("API_SPORTS_API_KEY", "API-Sports API key", settings.api_sports_api_key),
            ("RESEND_API_KEY", "Resend email API key (for verification/reset emails)", settings.resend_api_key),
        ]
        
        for var_name, description, value in optional_checks:
            if value:
                checker.check_warning(f"{description} ({var_name}) - Optional", lambda: True)
            else:
                checker.check_warning(f"{description} ({var_name}) - Not set (optional)", lambda: False)
                
    except Exception as e:
        checker.check("Settings loading", lambda: False)
        print_error(f"  Error loading settings: {str(e)}")
        return False
    
    return len(checker.errors) == 0


def check_python_dependencies() -> bool:
    """Check if all required Python packages are installed"""
    print_header("Python Dependencies Check")
    
    checker = SystemChecker()
    
    # Core dependencies
    core_deps = [
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("sqlalchemy", "SQL toolkit"),
        ("asyncpg", "PostgreSQL async driver"),
        ("pydantic", "Data validation"),
        ("pydantic_settings", "Settings management"),
        ("python-dotenv", "Environment variables"),
        ("httpx", "HTTP client"),
        ("openai", "OpenAI API client"),
        ("python-jose", "JWT handling"),
        ("passlib", "Password hashing"),
    ]
    
    # Map module names to their actual import names
    import_map = {
        "python-dotenv": "dotenv",
        "python-jose": "jose",
        "pydantic-settings": "pydantic_settings",
    }
    
    for module_name, description in core_deps:
        try:
            # Use mapped name if available, otherwise use module name with dashes replaced
            import_name = import_map.get(module_name, module_name.replace("-", "_"))
            importlib.import_module(import_name)
            checker.check(f"{description} ({module_name})", lambda: True)
        except ImportError:
            checker.check(f"{description} ({module_name})", lambda: False)
    
    # Optional dependencies
    optional_deps = [
        ("redis", "Redis client"),
        ("apscheduler", "Task scheduler"),
    ]
    
    for module_name, description in optional_deps:
        try:
            importlib.import_module(module_name.replace("-", "_"))
            checker.check_warning(f"{description} ({module_name}) - Optional", lambda: True)
        except ImportError:
            checker.check_warning(f"{description} ({module_name}) - Not installed (optional)", lambda: False)
    
    return len(checker.errors) == 0


def check_code_compilation() -> bool:
    """Check if code compiles and critical modules can be imported"""
    print_header("Code Compilation Check")
    
    checker = SystemChecker()
    
    # Critical modules to import
    critical_modules = [
        ("app.core.config", "Settings configuration"),
        ("app.database.session", "Database session"),
        ("app.main", "Main application"),
        ("app.api.routes.auth", "Auth routes"),
        ("app.services.auth_service", "Auth service"),
    ]
    
    for module_path, description in critical_modules:
        try:
            module = importlib.import_module(module_path)
            checker.check(f"{description} ({module_path})", lambda: True)
        except SyntaxError as e:
            checker.check(f"{description} ({module_path}) - Syntax Error", lambda: False)
            print_error(f"  Syntax error at line {e.lineno}: {e.msg}")
        except ImportError as e:
            checker.check(f"{description} ({module_path}) - Import Error", lambda: False)
            print_error(f"  Import error: {str(e)}")
        except Exception as e:
            checker.check(f"{description} ({module_path}) - Error", lambda: False)
            print_error(f"  Error: {str(e)}")
    
    # Try to compile main application
    try:
        from app.main import app
        checker.check("FastAPI app initialization", lambda: True)
        print_info(f"  App title: {app.title if hasattr(app, 'title') else 'N/A'}")
    except Exception as e:
        checker.check("FastAPI app initialization", lambda: False)
        print_error(f"  Error: {str(e)}")
        traceback.print_exc()
    
    return len(checker.errors) == 0


async def check_database_connection() -> bool:
    """Check database connectivity"""
    print_header("Database Connection Check")
    
    checker = SystemChecker()
    
    try:
        from app.database.session import engine, DATABASE_URL, is_sqlite
        from sqlalchemy import text
        
        # Check database type
        if is_sqlite:
            print_info("Database type: SQLite (local)")
        else:
            print_info("Database type: PostgreSQL")
        
        # Mask database URL
        if "@" in DATABASE_URL:
            masked_url = DATABASE_URL.split("@")[0] + "@[HIDDEN]"
        else:
            masked_url = DATABASE_URL
        print_info(f"Database URL: {masked_url}")
        
        # Test connection
        try:
            async with engine.begin() as conn:
                # SQLite doesn't have version(), use a simpler test
                if is_sqlite:
                    result = await conn.execute(text("SELECT 1"))
                    result.scalar()
                    checker.check("Database connection", lambda: True)
                    print_info("  SQLite database connected")
                    
                    # Check tables (SQLite syntax)
                    result = await conn.execute(text("""
                        SELECT COUNT(*) 
                        FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    """))
                    table_count = result.scalar()
                    checker.check_warning(f"Database tables ({table_count} found)", lambda: table_count > 0)
                else:
                    # PostgreSQL
                    result = await conn.execute(text("SELECT version()"))
                    version = result.scalar()
                    checker.check("Database connection", lambda: True)
                    print_info(f"  PostgreSQL version: {version[:60]}...")
                    
                    # Check tables
                    result = await conn.execute(text("""
                        SELECT COUNT(*) 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """))
                    table_count = result.scalar()
                    checker.check_warning(f"Database tables ({table_count} found)", lambda: table_count > 0)
                
        except Exception as e:
            checker.check("Database connection", lambda: False)
            print_error(f"  Connection error: {str(e)}")
            return False
            
    except Exception as e:
        checker.check("Database setup", lambda: False)
        print_error(f"  Setup error: {str(e)}")
        return False
    
    return len(checker.errors) == 0


async def check_external_apis() -> bool:
    """Check external API connectivity"""
    print_header("External API Check")
    
    checker = SystemChecker()
    
    # Check The Odds API
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        if settings.the_odds_api_key and len(settings.the_odds_api_key) > 10:
            checker.check("The Odds API key configured", lambda: True)
        else:
            checker.check("The Odds API key configured", lambda: False)
        
        if settings.openai_api_key and len(settings.openai_api_key) > 10:
            checker.check("OpenAI API key configured", lambda: True)
        else:
            checker.check("OpenAI API key configured", lambda: False)
        
        if settings.api_sports_api_key and len(settings.api_sports_api_key) > 10:
            checker.check_warning("API-Sports API key configured (optional)", lambda: True)
        else:
            checker.check_warning("API-Sports API key configured (optional)", lambda: False)
            
    except Exception as e:
        checker.check("API configuration", lambda: False)
        print_error(f"  Error: {str(e)}")
        return False
    
    return len(checker.errors) == 0


async def run_all_checks():
    """Run all system checks"""
    print_header("Parlay Gorilla System Check")
    print_info("Starting comprehensive system validation...\n")
    
    checker = SystemChecker()
    all_passed = True
    
    # Run checks
    checks = [
        ("Environment Variables", check_environment_variables, False),
        ("Python Dependencies", check_python_dependencies, False),
        ("Code Compilation", check_code_compilation, False),
        ("Database Connection", check_database_connection, True),
        ("External APIs", check_external_apis, True),
    ]
    
    for name, check_func, is_async in checks:
        try:
            if is_async:
                result = await check_func()
            else:
                result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print_error(f"{name} check failed with exception: {str(e)}")
            traceback.print_exc()
            all_passed = False
    
    # Summary
    print_header("System Check Summary")
    
    total_checks = sum(1 for _, _, _ in [
        ("Environment Variables", check_environment_variables, False),
        ("Python Dependencies", check_python_dependencies, False),
        ("Code Compilation", check_code_compilation, False),
        ("Database Connection", check_database_connection, True),
        ("External APIs", check_external_apis, True),
    ])
    
    print(f"{Colors.BOLD}Results:{Colors.END}")
    print(f"  {Colors.GREEN}✓ Checks completed{Colors.END}")
    print(f"  {Colors.YELLOW}⚠ Warnings: {len(checker.warnings)}{Colors.END}")
    print(f"  {Colors.RED}✗ Errors: {len(checker.errors)}{Colors.END}")
    
    if checker.warnings:
        print(f"\n{Colors.YELLOW}Warnings:{Colors.END}")
        for warning in checker.warnings:
            print(f"  ⚠ {warning}")
    
    if checker.errors:
        print(f"\n{Colors.RED}Errors:{Colors.END}")
        for error in checker.errors:
            print(f"  ✗ {error}")
    
    # Count actual errors from all checks
    total_errors = len(checker.errors)
    
    if total_errors == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All critical checks passed!{Colors.END}")
        print(f"{Colors.GREEN}System is ready to run.{Colors.END}\n")
        if checker.warnings:
            print(f"{Colors.YELLOW}Note: {len(checker.warnings)} optional items are not configured (this is OK).{Colors.END}\n")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ {total_errors} check(s) failed.{Colors.END}")
        print(f"{Colors.YELLOW}Please fix the errors above before running the application.{Colors.END}\n")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_checks())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSystem check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)

