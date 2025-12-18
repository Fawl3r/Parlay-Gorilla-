@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Parlay Gorilla - Cloudflare Tunnel (With Log Capture)
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
pause
exit /b 1

:found_cloudflared

REM Create logs directory
if not exist "tunnel-logs" mkdir tunnel-logs

echo [1] Starting Backend Server...
start "F3 Backend" cmd /k "cd /d %~dp0\backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo [2] Starting Frontend Server...
start "F3 Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev:network"

echo Waiting for frontend to start...
timeout /t 15 /nobreak >nul

echo.
echo [3] Starting Backend Tunnel (with log capture)...
start "Backend Tunnel" cmd /k "cd /d %~dp0 && %CLOUDFLARED_CMD% tunnel --url http://localhost:8000 > tunnel-logs\backend-tunnel.log 2>&1 & type tunnel-logs\backend-tunnel.log"

timeout /t 3 /nobreak >nul

echo [4] Starting Frontend Tunnel (with log capture)...
start "Frontend Tunnel" cmd /k "cd /d %~dp0 && %CLOUDFLARED_CMD% tunnel --url http://localhost:3000 > tunnel-logs\frontend-tunnel.log 2>&1 & type tunnel-logs\frontend-tunnel.log"

echo.
echo ========================================
echo Tunnels started! Logs are being captured.
echo ========================================
echo.
echo Waiting 20 seconds for tunnels to establish and capture URLs...
timeout /t 20 /nobreak >nul

echo.
echo Now running PowerShell script to extract URLs and configure frontend...
powershell -ExecutionPolicy Bypass -File ".\extract-tunnel-urls.ps1"

pause



