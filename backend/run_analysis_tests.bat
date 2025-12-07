@echo off
echo ============================================================
echo Parlay Gorilla Analysis System - Test Suite
echo ============================================================
echo.

cd /d "%~dp0"

echo Running Model Tests...
python test_analysis_models.py
if %errorlevel% neq 0 (
    echo Model tests failed!
    pause
    exit /b 1
)

echo.
echo Running Stats Scraper Tests...
python test_stats_scraper.py
if %errorlevel% neq 0 (
    echo Stats scraper tests failed!
    pause
    exit /b 1
)

echo.
echo Running Analysis Generator Tests...
python test_analysis_generator.py
if %errorlevel% neq 0 (
    echo Analysis generator tests failed!
    pause
    exit /b 1
)

echo.
echo Running API Route Tests...
python test_analysis_api.py
if %errorlevel% neq 0 (
    echo API route tests failed!
    pause
    exit /b 1
)

echo.
echo Running Frontend Component Verification...
python test_frontend_components.py
if %errorlevel% neq 0 (
    echo Frontend verification failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Running Comprehensive Test Suite...
echo ============================================================
python test_analysis_all.py

echo.
echo ============================================================
echo All Analysis System Tests Complete!
echo ============================================================
pause

