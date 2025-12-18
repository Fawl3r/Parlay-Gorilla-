@echo off
echo ========================================
echo Parlay Gorilla - Tunnel Setup
echo Share your app with remote users
echo ========================================
echo.

REM Check if ngrok is installed
where ngrok >nul 2>&1
if errorlevel 1 (
    echo ERROR: ngrok is not installed or not in PATH
    echo.
    echo Please install ngrok:
    echo 1. Download from: https://ngrok.com/download
    echo 2. Extract to a folder in your PATH
    echo 3. Sign up at: https://dashboard.ngrok.com/signup
    echo 4. Get your auth token and run: ngrok authtoken YOUR_TOKEN
    echo.
    pause
    exit /b 1
)

echo Starting Backend Server...
start "F3 Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
start "F3 Frontend" cmd /k "cd frontend && npm run dev:network"

REM Wait a bit for frontend to start
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Starting Tunnels...
echo ========================================
echo.

echo Starting Backend Tunnel (port 8000)...
start "Backend Tunnel" cmd /k "ngrok http 8000"

timeout /t 2 /nobreak >nul

echo Starting Frontend Tunnel (port 3000)...
start "Frontend Tunnel" cmd /k "ngrok http 3000"

echo.
echo ========================================
echo Tunnels are starting...
echo.
echo IMPORTANT: Check the ngrok windows for your public URLs
echo.
echo Backend tunnel will show:  https://xxxx-xx-xx-xx-xx.ngrok-free.app
echo Frontend tunnel will show: https://xxxx-xx-xx-xx-xx.ngrok-free.app
echo.
echo Share the FRONTEND URL with your testers!
echo.
echo The frontend will automatically connect to the backend tunnel.
echo ========================================
echo.
echo Press any key to exit (tunnels will continue running)
pause >nul




