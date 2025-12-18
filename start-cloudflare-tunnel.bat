@echo off
echo ========================================
echo Parlay Gorilla - Cloudflare Tunnel Setup
echo Share your app with remote users (FREE)
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
echo.
echo Please install cloudflared:
echo 1. Download from: https://github.com/cloudflare/cloudflared/releases
echo 2. Extract cloudflared.exe to a folder in your PATH
echo    OR place it in this directory
echo 3. No account or authentication needed!
echo.
echo Quick install (if you have chocolatey):
echo   choco install cloudflared
echo.
pause
exit /b 1

:found_cloudflared

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
echo Starting Cloudflare Tunnels...
echo ========================================
echo.

echo Starting Backend Tunnel (port 8000)...
start "Backend Tunnel" cmd /k "cd /d %~dp0 && %CLOUDFLARED_CMD% tunnel --url http://localhost:8000"

timeout /t 2 /nobreak >nul

echo Starting Frontend Tunnel (port 3000)...
start "Frontend Tunnel" cmd /k "cd /d %~dp0 && %CLOUDFLARED_CMD% tunnel --url http://localhost:3000"

echo.
echo ========================================
echo Tunnels are starting...
echo.
echo IMPORTANT: Check the Cloudflare Tunnel windows for your public URLs
echo.
echo Each tunnel will show a URL like:
echo   https://xxxx-xxxx-xxxx.trycloudflare.com
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

