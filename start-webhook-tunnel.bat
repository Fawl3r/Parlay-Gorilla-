@echo off
REM Start LocalTunnel for Webhook Testing
REM This exposes your local backend (port 8000) to the internet

echo.
echo 🚀 Starting LocalTunnel for webhook testing...
echo.
echo Make sure your backend is running on port 8000!
echo.

REM Check if backend is running
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo ⚠️  WARNING: Backend doesn't appear to be running on port 8000
    echo    Start your backend first with: cd backend ^&^& python -m uvicorn app.main:app --reload --port 8000
    echo.
)

echo Starting tunnel... (Press Ctrl+C to stop)
echo.

REM Start localtunnel
REM The URL will be printed when the tunnel is ready
lt --port 8000

