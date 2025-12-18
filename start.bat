@echo off
echo ========================================
echo Parlay Gorilla - Development Server
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo Starting Backend Server...
start "F3 Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
start "F3 Frontend" cmd /k "cd frontend && npm run dev:network"

echo.
echo ========================================
echo Servers are starting...
echo.
echo LOCAL ACCESS:
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo NETWORK ACCESS:
echo Getting your IP address...
setlocal enabledelayedexpansion
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    set IP=!IP:~1!
    echo.
    echo Your IP Address: !IP!
    echo Backend:  http://!IP!:8000
    echo Frontend: http://!IP!:3000
    echo.
    echo Share these URLs with testers on your network
    goto :found
)
:found
echo ========================================
echo.
echo Press any key to exit (servers will continue running)
pause >nul

