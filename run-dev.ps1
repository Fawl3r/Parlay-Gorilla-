# F3 Parlay Gorilla - Development Mode (PowerShell)
# Run both backend and frontend servers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  F3 Parlay Gorilla - Development Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[INFO] Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and add it to your PATH" -ForegroundColor Yellow
    exit 1
}

# Check if Node.js is available
try {
    $nodeVersion = node --version 2>&1
    Write-Host "[INFO] Found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Node.js 18+ and add it to your PATH" -ForegroundColor Yellow
    exit 1
}

# Check if backend directory exists
if (-not (Test-Path "backend\app\main.py")) {
    Write-Host "[ERROR] Backend directory structure not found" -ForegroundColor Red
    exit 1
}

# Check if frontend dependencies are installed
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "[WARNING] Frontend node_modules not found" -ForegroundColor Yellow
    Write-Host "Installing frontend dependencies..." -ForegroundColor Blue
    Set-Location frontend
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install frontend dependencies" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
    Set-Location ..
    Write-Host "[SUCCESS] Frontend dependencies installed" -ForegroundColor Green
}

# Check if ports are in use
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    Write-Host "[WARNING] Port 8000 is already in use" -ForegroundColor Yellow
    Write-Host "Backend may fail to start. Please free the port or stop the existing process." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}

$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000) {
    Write-Host "[WARNING] Port 3000 is already in use" -ForegroundColor Yellow
    Write-Host "Frontend may fail to start. Please free the port or stop the existing process." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "[INFO] Starting Backend Server (port 8000)..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -WindowStyle Normal

# Wait for backend to initialize
Write-Host "[INFO] Waiting for backend to initialize..." -ForegroundColor Blue
Start-Sleep -Seconds 4

Write-Host "[INFO] Starting Frontend Server (port 3000)..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev" -WindowStyle Normal

# Get local IP address
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } | Select-Object -First 1).IPAddress

# Display server information
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Servers Starting" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "LOCAL ACCESS:" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  Frontend: http://localhost:3000"
Write-Host "  API Docs: http://localhost:8000/docs"
Write-Host ""

if ($localIP) {
    Write-Host "NETWORK ACCESS:" -ForegroundColor Green
    Write-Host "  Backend:  http://$localIP:8000"
    Write-Host "  Frontend: http://$localIP:3000"
    Write-Host ""
    Write-Host "Your IP Address: $localIP"
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Both servers are starting in separate windows" -ForegroundColor Blue
Write-Host "[INFO] Close those windows or press Ctrl+C in them to stop" -ForegroundColor Blue
Write-Host ""
Write-Host "Press any key to exit this script (servers will continue running)..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")



