@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Parlay Gorilla - Cloudflare Tunnel (Fixed)
echo Share your app with remote users (FREE)
echo ========================================
echo.

REM Check if cloudflared exists
if exist "cloudflared.exe" (
    set CLOUDFLARED_CMD=cloudflared.exe
    goto :found_cloudflared
)

where cloudflared >nul 2>&1
if not errorlevel 1 (
    set CLOUDFLARED_CMD=cloudflared
    goto :found_cloudflared
)

echo ERROR: cloudflared is not installed
echo Download from: https://github.com/cloudflare/cloudflared/releases
pause
exit /b 1

:found_cloudflared

echo [1] Starting Backend Server...
start "F3 Backend" cmd /k "cd /d %~dp0\backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo [2] Starting Frontend Server...
start "F3 Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev:network"

echo Waiting for frontend to start (this may take 30+ seconds)...
echo Please wait for "Ready" message in the frontend window...
timeout /t 15 /nobreak >nul

echo.
echo [3] Starting Backend Tunnel...
start "Backend Tunnel" cmd /k "cd /d %~dp0 && %CLOUDFLARED_CMD% tunnel --url http://localhost:8000"

timeout /t 3 /nobreak >nul

echo [4] Starting Frontend Tunnel...
start "Frontend Tunnel" cmd /k "cd /d %~dp0 && %CLOUDFLARED_CMD% tunnel --url http://localhost:3000"

echo.
echo ========================================
echo  IMPORTANT INSTRUCTIONS
echo ========================================
echo.
echo 1. Wait for BOTH tunnels to show URLs (may take 10-20 seconds)
echo.
echo 2. Check the tunnel windows for URLs:
echo    - "Backend Tunnel" window:  https://xxxx-xxxx-xxxx.trycloudflare.com
echo    - "Frontend Tunnel" window: https://xxxx-xxxx-xxxx.trycloudflare.com
echo.
echo 3. Copy BOTH URLs - you'll need them!
echo.
echo 4. IMPORTANT: The frontend needs to know the backend tunnel URL.
echo    After you get the URLs, you need to:
echo    a) Open the frontend tunnel URL in your browser
echo    b) Add ?backend=https://YOUR-BACKEND-TUNNEL-URL to the URL
echo    Example: https://frontend-url.trycloudflare.com?backend=https://backend-url.trycloudflare.com
echo.
echo 5. Or set environment variable in frontend/.env.local:
echo    NEXT_PUBLIC_API_URL=https://YOUR-BACKEND-TUNNEL-URL
echo    (Then restart frontend)
echo.
echo ========================================
echo.
echo Waiting 20 seconds for tunnels to establish...
timeout /t 20 /nobreak >nul

echo.
echo Tunnels should be ready now!
echo Check the tunnel windows for your URLs.
echo.
pause



