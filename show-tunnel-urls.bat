@echo off
echo ========================================
echo Cloudflare Tunnel URLs
echo ========================================
echo.
echo The tunnel windows should be open. Look for:
echo.
echo 1. A window showing: "cloudflared.exe tunnel --url http://localhost:3000"
echo    This is your FRONTEND tunnel - look for the URL in that window
echo.
echo 2. A window showing: "cloudflared.exe tunnel --url http://localhost:8000"
echo    This is your BACKEND tunnel - look for the URL in that window
echo.
echo The URLs will appear as:
echo   https://xxxx-xxxx-xxxx.trycloudflare.com
echo.
echo ========================================
echo.
echo Press Alt+Tab to cycle through windows and find the tunnel windows
echo.
echo If you can't find them, I'll restart them in clearly labeled windows...
echo.
pause

echo.
echo Restarting tunnels with clear window titles...
echo.

REM Kill existing cloudflared processes
taskkill /F /IM cloudflared.exe >nul 2>&1

timeout /t 2 /nobreak >nul

REM Start with clear titles
start "=== FRONTEND TUNNEL - CHECK HERE FOR URL ===" cmd /k "cd /d %~dp0 && cloudflared.exe tunnel --url http://localhost:3000"

timeout /t 2 /nobreak >nul

start "=== BACKEND TUNNEL - CHECK HERE FOR URL ===" cmd /k "cd /d %~dp0 && cloudflared.exe tunnel --url http://localhost:8000"

echo.
echo ========================================
echo Tunnels restarted!
echo.
echo Look for windows with these titles:
echo   "=== FRONTEND TUNNEL - CHECK HERE FOR URL ==="
echo   "=== BACKEND TUNNEL - CHECK HERE FOR URL ==="
echo.
echo The URLs will appear in those windows.
echo ========================================
echo.
pause




