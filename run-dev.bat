@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  F3 Parlay Gorilla - Development Mode
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if backend dependencies are installed
if not exist "backend\app\main.py" (
    echo [ERROR] Backend directory structure not found
    pause
    exit /b 1
)

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo [WARNING] Frontend node_modules not found
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo [SUCCESS] Frontend dependencies installed
)

REM Check if ports are in use
netstat -ano | findstr ":8000" >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Port 8000 is already in use
    echo Backend may fail to start. Please free the port or stop the existing process.
    timeout /t 2 /nobreak >nul
)

netstat -ano | findstr ":3000" >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Port 3000 is already in use
    echo Frontend may fail to start. Please free the port or stop the existing process.
    timeout /t 2 /nobreak >nul
)

echo.
echo [INFO] Starting Backend Server (port 8000)...
start "F3 Backend Server" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to initialize
echo [INFO] Waiting for backend to initialize...
timeout /t 4 /nobreak >nul

echo [INFO] Starting Frontend Server (port 3000)...
start "F3 Frontend Server" cmd /k "cd frontend && npm run dev"

REM Get local IP address for network access
echo.
echo ========================================
echo  Servers Starting...
echo ========================================
echo.
echo LOCAL ACCESS:
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo.

REM Try to get local IP
set IP_FOUND=0
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    set IP=!IP:~1!
    if !IP_FOUND!==0 (
        echo NETWORK ACCESS:
        echo   Backend:  http://!IP!:8000
        echo   Frontend: http://!IP!:3000
        echo.
        echo Your IP Address: !IP!
        set IP_FOUND=1
        goto :ip_found
    )
)

:ip_found
echo ========================================
echo.
echo [INFO] Both servers are starting in separate windows
echo [INFO] Close those windows or press Ctrl+C in them to stop
echo.
echo Press any key to exit this script (servers will continue running)...
pause >nul



