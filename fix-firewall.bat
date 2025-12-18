@echo off
echo ========================================
echo  Fixing Windows Firewall for Backend
echo ========================================
echo.
echo This script will add a firewall rule to allow
echo incoming connections on port 8000 for the backend server.
echo.
pause

echo.
echo Adding firewall rule for port 8000...
netsh advfirewall firewall add rule name="Parlay Gorilla Backend (Port 8000)" dir=in action=allow protocol=TCP localport=8000

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to add firewall rule
    echo You may need to run this script as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Firewall rule added successfully!
echo.
echo Testing connection...
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo  Firewall Configuration Complete
echo ========================================
echo.
echo The backend server should now be accessible from:
echo   - Local PC: http://localhost:8000
echo   - Network:  http://10.0.0.76:8000
echo.
echo Try the connection test again on your mobile device.
echo.
pause



