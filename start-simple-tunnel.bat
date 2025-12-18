@echo off
echo ========================================
echo Parlay Gorilla - Simple Tunnel (No Password Required)
echo Using serveo.net - SSH-based tunneling
echo ========================================
echo.

echo Starting Backend Server...
start "F3 Backend" cmd /k "cd /d %~dp0\backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
start "F3 Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev:network"

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Starting SSH Tunnels (No Password Required)...
echo ========================================
echo.

echo Starting Backend Tunnel (port 8000)...
echo This will show: ssh -R 80:localhost:8000 serveo.net
start "Backend Tunnel" cmd /k "ssh -R parlay-backend:80:localhost:8000 serveo.net"

timeout /t 2 /nobreak >nul

echo Starting Frontend Tunnel (port 3000)...
echo This will show: ssh -R 80:localhost:3000 serveo.net
start "Frontend Tunnel" cmd /k "ssh -R parlay-frontend:80:localhost:3000 serveo.net"

echo.
echo ========================================
echo Tunnels are starting...
echo.
echo IMPORTANT: Check the tunnel windows for your public URLs
echo.
echo Backend will be at:  https://parlay-backend.serveo.net
echo Frontend will be at: https://parlay-frontend.serveo.net
echo.
echo Share the FRONTEND URL with your testers!
echo.
echo NOTE: First-time setup may require accepting SSH host key
echo ========================================
echo.
echo Press any key to exit (tunnels will continue running)
pause >nul




