@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Parlay Gorilla - LocalTunnel Setup
echo Share your app with remote users (FREE)
echo ========================================
echo.

REM Check if npm is installed
where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm is not installed
    echo.
    echo Please install Node.js from: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo npm found. Checking for localtunnel...

REM Check if localtunnel is installed globally
npm list -g localtunnel >nul 2>&1
if errorlevel 1 (
    echo LocalTunnel not found. Installing...
    call npm install -g localtunnel
    if errorlevel 1 (
        echo ERROR: Failed to install localtunnel
        echo.
        echo Try running manually: npm install -g localtunnel
        pause
        exit /b 1
    )
    echo LocalTunnel installed successfully!
) else (
    echo LocalTunnel is already installed.
)
echo.

echo Starting Backend Server...
start "F3 Backend" cmd /k "cd /d %~dp0\backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
start "F3 Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev:network"

REM Wait a bit for frontend to start
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Starting LocalTunnels...
echo ========================================
echo.

echo Starting Backend Tunnel (port 8000)...
echo Note: If LocalTunnel asks for a password, visitors need to enter their IP address
start "Backend Tunnel" cmd /k "npx -y localtunnel --port 8000 --subdomain parlay-backend 2>nul || npx -y localtunnel --port 8000"

timeout /t 2 /nobreak >nul

echo Starting Frontend Tunnel (port 3000)...
echo Note: If LocalTunnel asks for a password, visitors need to enter their IP address
start "Frontend Tunnel" cmd /k "npx -y localtunnel --port 3000 --subdomain parlay-frontend 2>nul || npx -y localtunnel --port 3000"

echo.
echo ========================================
echo Tunnels are starting...
echo.
echo IMPORTANT: Check the LocalTunnel windows for your public URLs
echo.
echo Each tunnel will show a URL like:
echo   https://xxxx.loca.lt
echo.
echo Backend tunnel URL:  Check the "Backend Tunnel" window
echo Frontend tunnel URL: Check the "Frontend Tunnel" window
echo.
echo Share the FRONTEND URL with your testers!
echo.
echo The frontend will automatically connect to the backend tunnel.
echo ========================================
echo.
echo Press any key to exit (tunnels will continue running)
pause >nul

