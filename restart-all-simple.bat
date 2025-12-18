@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Restarting All Servers and Tunnels
echo ========================================
echo.

REM Stop existing processes
echo Stopping existing processes...
taskkill /F /IM cloudflared.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr /C:"PID:"') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM Create logs directory
if not exist "tunnel-logs" mkdir tunnel-logs

REM Check for cloudflared
if exist "cloudflared.exe" (
    set CLOUDFLARED_CMD=cloudflared.exe
    goto :found_cloudflared
)

where cloudflared >nul 2>&1
if not errorlevel 1 (
    set CLOUDFLARED_CMD=cloudflared
    goto :found_cloudflared
)

echo ERROR: cloudflared not found!
pause
exit /b 1

:found_cloudflared

echo Starting backend server...
start "F3 Backend" cmd /k "cd /d %~dp0\backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 5 /nobreak >nul

echo Starting frontend server...
start "F3 Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev:network"

timeout /t 15 /nobreak >nul

echo Starting backend tunnel...
start "Backend Tunnel" cmd /k "cd /d %~dp0 && %CLOUDFLARED_CMD% tunnel --url http://localhost:8000 > tunnel-logs\backend-tunnel.log 2>&1 & type tunnel-logs\backend-tunnel.log"

timeout /t 3 /nobreak >nul

echo Starting frontend tunnel...
start "Frontend Tunnel" cmd /k "cd /d %~dp0 && %CLOUDFLARED_CMD% tunnel --url http://localhost:3000 > tunnel-logs\frontend-tunnel.log 2>&1 & type tunnel-logs\frontend-tunnel.log"

echo.
echo ========================================
echo Waiting for tunnels to establish...
echo ========================================
echo.
timeout /t 20 /nobreak >nul

echo.
echo ========================================
echo Tunnels Started!
echo ========================================
echo.
echo Check the tunnel windows for URLs:
echo   - Backend Tunnel window
echo   - Frontend Tunnel window
echo.
echo URLs look like: https://xxxx-xxxx-xxxx.trycloudflare.com
echo.
echo To auto-configure frontend, run:
echo   .\extract-tunnel-urls.ps1
echo.
echo Or manually update frontend\.env.local with the backend URL.
echo.
pause



