@echo off
echo ========================================
echo  Setup Backend Tunnel URL
echo ========================================
echo.
echo This script will help you configure the backend tunnel URL
echo so the frontend can connect to it.
echo.
echo First, get your BACKEND tunnel URL from the "Backend Tunnel" window.
echo It should look like: https://xxxx-xxxx-xxxx.trycloudflare.com
echo.
pause

set /p BACKEND_URL="Enter your BACKEND tunnel URL (https://...): "

if "%BACKEND_URL%"=="" (
    echo ERROR: No URL entered
    pause
    exit /b 1
)

echo.
echo Setting NEXT_PUBLIC_API_URL=%BACKEND_URL%
echo.

REM Create or update .env.local
if exist "frontend\.env.local" (
    echo Updating existing .env.local...
    REM Remove old NEXT_PUBLIC_API_URL line if exists
    findstr /v "NEXT_PUBLIC_API_URL" frontend\.env.local > frontend\.env.local.tmp 2>nul
    move /y frontend\.env.local.tmp frontend\.env.local >nul 2>&1
) else (
    echo Creating new .env.local...
)

REM Add the new API URL
echo NEXT_PUBLIC_API_URL=%BACKEND_URL% >> frontend\.env.local

echo.
echo ========================================
echo  Configuration Complete!
echo ========================================
echo.
echo Backend URL set to: %BACKEND_URL%
echo.
echo IMPORTANT: You need to restart the frontend server:
echo 1. Close the "F3 Frontend" window
echo 2. Wait a moment
echo 3. Open a new terminal and run:
echo    cd frontend
echo    npm run dev:network
echo.
echo OR restart the entire tunnel setup.
echo.
echo After restarting, the frontend will use the backend tunnel URL.
echo.
pause



