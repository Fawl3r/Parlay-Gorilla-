@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Parlay Gorilla - Auto Tunnel Setup
echo Automatically downloads and uses Cloudflare Tunnel
echo ========================================
echo.

REM Check if cloudflared exists in current directory
if exist "cloudflared.exe" (
    echo cloudflared.exe found in current directory.
    set CLOUDFLARED_CMD=cloudflared.exe
    goto :start_servers
)

REM Check if cloudflared is in PATH
where cloudflared >nul 2>&1
if not errorlevel 1 (
    echo cloudflared found in PATH.
    set CLOUDFLARED_CMD=cloudflared
    goto :start_servers
)

REM Download cloudflared if not found
echo cloudflared not found. Downloading...
echo.

REM Get the latest release URL
for /f "tokens=*" %%i in ('powershell -Command "(Invoke-RestMethod -Uri 'https://api.github.com/repos/cloudflare/cloudflared/releases/latest').assets ^| Where-Object { $_.name -like '*windows-amd64.exe' } ^| Select-Object -First 1 -ExpandProperty browser_download_url"') do set DOWNLOAD_URL=%%i

if "%DOWNLOAD_URL%"=="" (
    echo ERROR: Could not get download URL
    echo.
    echo Please manually download cloudflared:
    echo 1. Visit: https://github.com/cloudflare/cloudflared/releases/latest
    echo 2. Download: cloudflared-windows-amd64.exe
    echo 3. Rename to: cloudflared.exe
    echo 4. Place in this directory
    echo.
    pause
    exit /b 1
)

echo Downloading from: %DOWNLOAD_URL%
echo.

powershell -Command "Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile 'cloudflared.exe'"

if not exist "cloudflared.exe" (
    echo ERROR: Failed to download cloudflared
    echo.
    echo Please manually download from:
    echo https://github.com/cloudflare/cloudflared/releases/latest
    echo.
    pause
    exit /b 1
)

echo cloudflared downloaded successfully!
set CLOUDFLARED_CMD=cloudflared.exe

:start_servers
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

echo Starting Backend Tunnel (port 8000)...
start "Backend Tunnel" cmd /k "%CLOUDFLARED_CMD% tunnel --url http://localhost:8000"

timeout /t 2 /nobreak >nul

echo Starting Frontend Tunnel (port 3000)...
start "Frontend Tunnel" cmd /k "%CLOUDFLARED_CMD% tunnel --url http://localhost:3000"

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




