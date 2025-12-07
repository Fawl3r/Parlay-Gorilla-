@echo off
REM Production setup script for Parlay Gorilla (Windows)

echo ==========================================
echo Parlay Gorilla - Production Setup
echo ==========================================

REM Check if Neon URL is set
if "%NEON_DATABASE_URL%"=="" (
    echo Error: NEON_DATABASE_URL environment variable not set
    echo Please set it to your Neon connection string
    exit /b 1
)

REM Set production environment
set ENVIRONMENT=production
set DATABASE_URL=%NEON_DATABASE_URL%

echo.
echo 1. Running database migrations...
alembic upgrade head

echo.
echo 2. Fetching live games...
python fetch_live_games.py

echo.
echo ==========================================
echo Production setup complete!
echo ==========================================

