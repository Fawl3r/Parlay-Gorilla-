@echo off
echo ========================================
echo  Fixing Tunnel 404 Issue
echo ========================================
echo.
echo This script will:
echo 1. Check if frontend is running
echo 2. Restart frontend if needed
echo 3. Provide correct tunnel setup
echo.
pause

echo.
echo [1] Checking frontend status...
netstat -ano | findstr :3000 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Frontend not running on port 3000
    echo Starting frontend...
    start "F3 Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev:network"
    echo Waiting for frontend to start...
    timeout /t 10 /nobreak >nul
) else (
    echo [OK] Frontend is running on port 3000
)

echo.
echo [2] Testing localhost connection...
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Frontend not responding on localhost
    echo Frontend may still be starting. Wait a moment and try again.
) else (
    echo [OK] Frontend responds on localhost
)

echo.
echo ========================================
echo  Tunnel Setup Instructions
echo ========================================
echo.
echo IMPORTANT: Make sure the frontend is FULLY started before
echo creating the tunnel. You should see "Ready" in the frontend window.
echo.
echo Steps:
echo 1. Check the "F3 Frontend" window - wait for "Ready" message
echo 2. The frontend tunnel should point to: http://localhost:3000
echo 3. Make sure you're using the FRONTEND tunnel URL (not backend)
echo 4. Try accessing: https://your-tunnel-url.trycloudflare.com
echo.
echo If you still get 404:
echo - Wait 30 seconds for Next.js to fully compile
echo - Try refreshing the page
echo - Check the frontend window for errors
echo - Make sure you're using the frontend tunnel URL
echo.
pause



