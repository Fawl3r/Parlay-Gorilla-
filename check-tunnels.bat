@echo off
echo ========================================
echo Checking Tunnel Status
echo ========================================
echo.

echo Checking if servers are running...
netstat -an | findstr ":3000 :8000" >nul
if errorlevel 1 (
    echo ERROR: Servers are not running on ports 3000 or 8000
) else (
    echo Servers are running on ports 3000 and 8000
)

echo.
echo Checking for cloudflared processes...
tasklist | findstr "cloudflared" >nul
if errorlevel 1 (
    echo No cloudflared processes found
) else (
    echo Cloudflared processes found:
    tasklist | findstr "cloudflared"
)

echo.
echo ========================================
echo To see tunnel URLs:
echo 1. Look for windows titled "Backend Tunnel" and "Frontend Tunnel"
echo 2. The URLs will be shown in those windows
echo 3. They look like: https://xxxx-xxxx-xxxx.trycloudflare.com
echo ========================================
echo.
pause




