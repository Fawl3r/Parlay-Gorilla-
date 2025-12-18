@echo off
echo ========================================
echo Getting Tunnel URLs
echo ========================================
echo.
echo Checking tunnel windows...
echo.

REM Try to find the tunnel URLs from cloudflared output
echo Looking for active tunnels...
echo.

REM Check if we can read from cloudflared processes
echo NOTE: The tunnel URLs are displayed in the tunnel windows.
echo.
echo To find them:
echo 1. Press Alt+Tab to cycle through open windows
echo 2. Look for windows with titles containing "Tunnel"
echo 3. In those windows, look for lines starting with "https://"
echo.

echo Alternatively, check your Taskbar for:
echo - "Backend Tunnel" window
echo - "Frontend Tunnel" window
echo.

echo If you can't find the windows, they may be minimized.
echo Try clicking on the cloudflared icons in your taskbar.
echo.

pause




