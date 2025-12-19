# Start LocalTunnel for Webhook Testing
# This exposes your local backend (port 8000) to the internet

Write-Host "🚀 Starting LocalTunnel for webhook testing..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Make sure your backend is running on port 8000!" -ForegroundColor Yellow
Write-Host ""

# Check if backend is running
$backendRunning = netstat -ano | findstr ":8000" | findstr "LISTENING"
if (-not $backendRunning) {
    Write-Host "⚠️  WARNING: Backend doesn't appear to be running on port 8000" -ForegroundColor Red
    Write-Host "   Start your backend first with: cd backend && python -m uvicorn app.main:app --reload --port 8000" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Starting tunnel... (Press Ctrl+C to stop)" -ForegroundColor Green
Write-Host ""

# Start localtunnel
# The URL will be printed when the tunnel is ready
lt --port 8000

