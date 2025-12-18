@echo off
REM Batch script to start the FastAPI backend server
REM Usage: start-server.bat

echo ========================================
echo Starting Parlay Gorilla Backend Server
echo ========================================
echo.

REM Check if we're in the backend directory
if not exist "app\main.py" (
    echo ERROR: app\main.py not found. Please run this script from the backend directory.
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check for .env file
if not exist ".env" (
    echo WARNING: .env file not found. Server may fail to start without proper configuration.
    echo Copy .env.example to .env and configure it.
    echo.
)

REM Check if port 8000 is already in use
echo Checking if port 8000 is available...
netstat -ano | findstr ":8000.*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo ERROR: Port 8000 is already in use.
    echo Run kill-port-8000.ps1 to free the port, or use a different port.
    pause
    exit /b 1
)
echo Port 8000 is available.
echo.

echo Starting uvicorn server...
echo Backend will be available at: http://127.0.0.1:8000
echo API docs will be available at: http://127.0.0.1:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
REM Note: Using 127.0.0.1 (localhost only) instead of 0.0.0.0 for better security
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

pause



