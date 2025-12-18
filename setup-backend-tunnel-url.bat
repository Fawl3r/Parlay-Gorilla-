@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  Auto-Configure Backend Tunnel URL
echo ========================================
echo.
echo This will configure the frontend to use your backend tunnel URL.
echo.
echo STEP 1: Get your BACKEND tunnel URL
echo.
echo Look for the "Backend Tunnel" window (check your taskbar or Alt+Tab).
echo The URL will look like: https://xxxx-xxxx-xxxx.trycloudflare.com
echo.
echo It should be in a window showing: cloudflared tunnel --url http://localhost:8000
echo.
pause

set /p BACKEND_URL="Enter your BACKEND tunnel URL (https://...): "

if "%BACKEND_URL%"=="" (
    echo.
    echo ERROR: No URL entered
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Updating Configuration
echo ========================================
echo.

REM Read existing .env.local and update it
set ENV_FILE=frontend\.env.local
set TEMP_FILE=frontend\.env.local.tmp

if exist "%ENV_FILE%" (
    echo Found existing .env.local, updating...
    
    REM Remove old backend URL lines
    findstr /v "^PG_BACKEND_URL=" "%ENV_FILE%" | findstr /v "^NEXT_PUBLIC_API_URL=" | findstr /v "^# Backend API URL" > "%TEMP_FILE%" 2>nul
    
    REM Add new configuration
    echo. >> "%TEMP_FILE%"
    echo # Backend API URL (Tunnel) >> "%TEMP_FILE%"
    echo PG_BACKEND_URL=%BACKEND_URL% >> "%TEMP_FILE%"
    echo NEXT_PUBLIC_API_URL=%BACKEND_URL% >> "%TEMP_FILE%"
    
    move /y "%TEMP_FILE%" "%ENV_FILE%" >nul 2>&1
) else (
    echo Creating new .env.local...
    echo # Backend API URL (Tunnel) > "%ENV_FILE%"
    echo PG_BACKEND_URL=%BACKEND_URL% >> "%ENV_FILE%"
    echo NEXT_PUBLIC_API_URL=%BACKEND_URL% >> "%ENV_FILE%"
    echo. >> "%ENV_FILE%"
)

echo.
echo ========================================
echo  Configuration Complete!
echo ========================================
echo.
echo Backend URL set to: %BACKEND_URL%
echo.
echo IMPORTANT: Restart the frontend server:
echo.
echo Option 1 - Restart just the frontend:
echo   1. Close the "F3 Frontend" window
echo   2. Open a new terminal and run:
echo      cd frontend
echo      npm run dev:network
echo.
echo Option 2 - Restart everything:
echo   Run start-cloudflare-tunnel-fixed.bat again
echo.
echo After restarting, the frontend will connect to the backend via tunnel!
echo.
pause



