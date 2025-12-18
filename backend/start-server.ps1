# PowerShell script to start the FastAPI backend server
# Usage: .\start-server.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Parlay Gorilla Backend Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the backend directory
if (-not (Test-Path "app\main.py")) {
    Write-Host "ERROR: app\main.py not found. Please run this script from the backend directory." -ForegroundColor Red
    exit 1
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if uvicorn is installed
try {
    python -c "import uvicorn" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: uvicorn is not installed. Run: pip install -r requirements.txt" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR: Failed to check uvicorn installation" -ForegroundColor Red
    exit 1
}

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found. Server may fail to start without proper configuration." -ForegroundColor Yellow
    Write-Host "Copy .env.example to .env and configure it." -ForegroundColor Yellow
    Write-Host ""
}

# Check if port 8000 is already in use
Write-Host "Checking if port 8000 is available..." -ForegroundColor Yellow
$portInUse = $false
try {
    $conns = Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($conns) {
        $portInUse = $true
        $pid = $conns[0].OwningProcess
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "ERROR: Port 8000 is already in use by process: $($process.ProcessName) (PID: $pid)" -ForegroundColor Red
            Write-Host "Run .\kill-port-8000.ps1 to free the port, or use a different port." -ForegroundColor Yellow
            exit 1
        }
    }
} catch {
    # Fallback to netstat
    $netstat = netstat -ano | Select-String -Pattern ":8000\s.*LISTENING"
    if ($netstat) {
        $portInUse = $true
        Write-Host "ERROR: Port 8000 appears to be in use." -ForegroundColor Red
        Write-Host "Run .\kill-port-8000.ps1 to free the port, or use a different port." -ForegroundColor Yellow
        exit 1
    }
}

if (-not $portInUse) {
    Write-Host "✓ Port 8000 is available" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting uvicorn server..." -ForegroundColor Green
Write-Host "Backend will be available at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "API docs will be available at: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
# Note: Using 127.0.0.1 (localhost only) instead of 0.0.0.0 for better security and fewer permission issues
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000



