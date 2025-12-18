@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Parlay Gorilla - Cloudflare Tunnel (Single Window)
echo All output in one window for easy viewing
echo ========================================
echo.

REM Check if cloudflared exists in current directory first
if exist "cloudflared.exe" (
    set CLOUDFLARED_CMD=cloudflared.exe
    echo Found cloudflared.exe in current directory.
    goto :found_cloudflared
)

REM Check if cloudflared is in PATH
where cloudflared >nul 2>&1
if not errorlevel 1 (
    set CLOUDFLARED_CMD=cloudflared
    echo Found cloudflared in PATH.
    goto :found_cloudflared
)

echo ERROR: cloudflared is not installed
echo Please place cloudflared.exe in this directory
pause
exit /b 1

:found_cloudflared

echo.
echo Starting Backend Server...
start "F3 Backend" cmd /k "cd /d %~dp0\backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
start "F3 Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev:network"

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Starting Cloudflare Tunnels...
echo ========================================
echo.

REM Start both tunnels in a single visible window
start "Tunnel URLs - CHECK HERE FOR YOUR URLS" cmd /k "cd /d %~dp0 && echo ======================================== && echo BACKEND TUNNEL (Port 8000) && echo ======================================== && %CLOUDFLARED_CMD% tunnel --url http://localhost:8000 && echo. && echo ======================================== && echo FRONTEND TUNNEL (Port 3000) && echo ======================================== && %CLOUDFLARED_CMD% tunnel --url http://localhost:3000"

echo.
echo ========================================
echo IMPORTANT: A window titled "Tunnel URLs" will open
echo Check that window for your public URLs!
echo.
echo The URLs will look like:
echo   https://xxxx-xxxx-xxxx.trycloudflare.com
echo.
echo Share the FRONTEND URL with your testers!
echo ========================================
echo.
echo Press any key to exit (tunnels will continue running)
pause >nul




