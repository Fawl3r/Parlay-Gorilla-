# Start tunnels and capture URLs automatically
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Tunnels and Capturing URLs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if cloudflared exists
$cloudflaredPath = "cloudflared.exe"
if (-not (Test-Path $cloudflaredPath)) {
    $cloudflaredPath = "cloudflared"
    $found = Get-Command cloudflared -ErrorAction SilentlyContinue
    if (-not $found) {
        Write-Host "ERROR: cloudflared not found!" -ForegroundColor Red
        Write-Host "Please ensure cloudflared.exe is in the project root or in PATH" -ForegroundColor Yellow
        exit 1
    }
}

# Check if servers are running
Write-Host "Checking if servers are running..." -ForegroundColor Yellow
$backendRunning = Test-NetConnection -ComputerName localhost -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue
$frontendRunning = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet -WarningAction SilentlyContinue

if (-not $backendRunning) {
    Write-Host "Starting backend server..." -ForegroundColor Yellow
    Start-Process -FilePath "cmd" -ArgumentList "/c", "cd /d `"$PWD\backend`" && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -WindowStyle Normal
    Start-Sleep -Seconds 5
}

if (-not $frontendRunning) {
    Write-Host "Starting frontend server..." -ForegroundColor Yellow
    Start-Process -FilePath "cmd" -ArgumentList "/c", "cd /d `"$PWD\frontend`" && npm run dev:network" -WindowStyle Normal
    Start-Sleep -Seconds 15
}

# Kill existing cloudflared processes
Write-Host "Stopping existing tunnels..." -ForegroundColor Yellow
Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Create temp directory for logs
$logDir = "tunnel-logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$backendLog = "$logDir\backend-tunnel.log"
$frontendLog = "$logDir\frontend-tunnel.log"

Write-Host ""
Write-Host "Starting backend tunnel..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath $cloudflaredPath -ArgumentList "tunnel", "--url", "http://localhost:8000" -RedirectStandardOutput $backendLog -RedirectStandardError "$logDir\backend-tunnel-err.log" -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 3

Write-Host "Starting frontend tunnel..." -ForegroundColor Green
$frontendProcess = Start-Process -FilePath $cloudflaredPath -ArgumentList "tunnel", "--url", "http://localhost:3000" -RedirectStandardOutput $frontendLog -RedirectStandardError "$logDir\frontend-tunnel-err.log" -PassThru -WindowStyle Hidden

Write-Host ""
Write-Host "Waiting for tunnels to establish (this may take 10-20 seconds)..." -ForegroundColor Yellow
Write-Host ""

# Wait and monitor for URLs
$maxWait = 30
$waited = 0
$backendUrl = $null
$frontendUrl = $null

while ($waited -lt $maxWait -and (-not $backendUrl -or -not $frontendUrl)) {
    Start-Sleep -Seconds 2
    $waited += 2
    
    # Try to read URLs from log files
    if (Test-Path $backendLog) {
        $backendContent = Get-Content $backendLog -ErrorAction SilentlyContinue -Raw
        if ($backendContent -match "https://([a-z0-9-]+\.trycloudflare\.com)") {
            $backendUrl = "https://$($matches[1])"
            Write-Host "✓ Backend tunnel URL found: $backendUrl" -ForegroundColor Green
        }
    }
    
    if (Test-Path $frontendLog) {
        $frontendContent = Get-Content $frontendLog -ErrorAction SilentlyContinue -Raw
        if ($frontendContent -match "https://([a-z0-9-]+\.trycloudflare\.com)") {
            $frontendUrl = "https://$($matches[1])"
            Write-Host "✓ Frontend tunnel URL found: $frontendUrl" -ForegroundColor Green
        }
    }
    
    Write-Host "." -NoNewline -ForegroundColor Gray
}

Write-Host ""
Write-Host ""

if (-not $backendUrl) {
    Write-Host "WARNING: Could not automatically detect backend URL from logs" -ForegroundColor Yellow
    Write-Host "Checking log file: $backendLog" -ForegroundColor Yellow
    
    if (Test-Path $backendLog) {
        Write-Host "Last 20 lines of backend log:" -ForegroundColor Cyan
        Get-Content $backendLog -Tail 20 | Write-Host
    }
    
    # Try to extract manually
    Write-Host ""
    Write-Host "Please check the tunnel output manually or provide the backend URL:" -ForegroundColor Yellow
    $backendUrl = Read-Host "Backend Tunnel URL"
}

if ($backendUrl) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Configuring Frontend" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Update .env.local
    $envFile = "frontend\.env.local"
    $content = @()
    
    if (Test-Path $envFile) {
        $content = Get-Content $envFile
    }
    
    # Remove old backend URL entries
    $content = $content | Where-Object {
        $_ -notmatch "^PG_BACKEND_URL=" -and
        $_ -notmatch "^NEXT_PUBLIC_API_URL=" -and
        $_ -notmatch "^# Backend API URL"
    }
    
    # Remove trailing empty lines
    while ($content.Count -gt 0 -and [string]::IsNullOrWhiteSpace($content[-1])) {
        $content = $content[0..($content.Count - 2)]
    }
    
    # Add new configuration
    if ($content.Count -gt 0 -and -not [string]::IsNullOrWhiteSpace($content[-1])) {
        $content += ""
    }
    $content += "# Backend API URL (Tunnel - Auto-configured)"
    $content += "PG_BACKEND_URL=$backendUrl"
    $content += "NEXT_PUBLIC_API_URL=$backendUrl"
    
    # Write to file
    $content | Set-Content $envFile -Encoding UTF8
    
    Write-Host "✓ Frontend configured with backend URL: $backendUrl" -ForegroundColor Green
    Write-Host ""
    Write-Host "Tunnel URLs:" -ForegroundColor Cyan
    Write-Host "  Backend:  $backendUrl" -ForegroundColor White
    if ($frontendUrl) {
        Write-Host "  Frontend: $frontendUrl" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "IMPORTANT: Restart the frontend server for changes to take effect!" -ForegroundColor Yellow
    Write-Host "  Close the 'F3 Frontend' window and restart it" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "ERROR: Could not configure frontend - no backend URL provided" -ForegroundColor Red
}

Write-Host ""
Write-Host "Tunnel processes are running. Logs are in: $logDir" -ForegroundColor Gray
Write-Host "To stop tunnels, run: Get-Process cloudflared | Stop-Process" -ForegroundColor Gray
Write-Host ""



