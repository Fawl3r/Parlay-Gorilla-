@echo off
echo ========================================
echo  Backend Connection Diagnostic Test
echo ========================================
echo.

REM Get IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    set IP=!IP:~1!
    goto :found_ip
)
:found_ip

echo Testing backend connection...
echo.

echo [1] Checking if backend is running...
netstat -ano | findstr :8000 >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Backend is NOT running on port 8000
    echo Please start the backend server first
    pause
    exit /b 1
) else (
    echo [OK] Backend is running on port 8000
)

echo.
echo [2] Checking firewall rule...
netsh advfirewall firewall show rule name="Parlay Gorilla Backend (Port 8000)" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Firewall rule not found
    echo Run fix-firewall.bat as administrator
) else (
    echo [OK] Firewall rule exists
)

echo.
echo [3] Testing localhost connection...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Cannot connect to backend on localhost
    echo Backend may not be responding
) else (
    echo [OK] Backend responds on localhost
)

echo.
echo [4] Testing network IP connection...
if defined IP (
    echo Testing: http://%IP%:8000/health
    curl -s -m 5 http://%IP%:8000/health >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Cannot connect via network IP
        echo This might be normal if testing from this PC
    ) else (
        echo [OK] Backend responds on network IP
    )
) else (
    echo [SKIP] Could not determine IP address
)

echo.
echo ========================================
echo  Connection Test Summary
echo ========================================
echo.
echo Your Network IP: %IP%
echo.
echo Test URLs for mobile device:
echo   Backend:  http://%IP%:8000/health
echo   Frontend: http://%IP%:3000
echo.
echo If connection fails from mobile:
echo   1. Ensure both devices on same WiFi network
echo   2. Check router settings for "AP Isolation" (disable it)
echo   3. Try temporarily disabling Windows Firewall to test
echo   4. Check if mobile can ping this PC: ping %IP%
echo.
pause

