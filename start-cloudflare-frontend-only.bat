@echo off
echo ========================================
echo Parlay Gorilla - Cloudflare Tunnel (Frontend Only)
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
pause
exit /b 1

:found_cloudflared

echo Starting Backend Server (local only)...
start "F3 Backend" cmd /k "cd /d %~dp0\backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
start "F3 Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev:network"

REM Wait a bit for frontend to start
timeout /t 8 /nobreak >nul

echo.
echo ========================================
echo Starting Cloudflare Tunnel (Frontend)...
echo ========================================
echo.

echo Starting Frontend Tunnel (port 3000)...
start "Frontend Tunnel" cmd /k "cd /d %~dp0 && %CLOUDFLARED_CMD% tunnel --url http://localhost:3000"

echo.
echo ========================================
echo Share the FRONTEND URL from the tunnel window
echo ========================================
echo.
echo Notes:
echo - Only ONE tunnel is needed.
echo - The frontend proxies /api/* and /health to the backend via Next.js rewrites.
echo - This avoids CORS and fixes mobile/tunnel localhost issues.
echo.
echo Press any key to exit (servers/tunnel will continue running)
pause >nul




