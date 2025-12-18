# Auto-configure Frontend to use Backend Tunnel URL
# This script extracts the backend tunnel URL and updates the frontend configuration

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Auto-Configuring Tunnel URLs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if cloudflared processes are running
$cloudflaredProcesses = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue

if (-not $cloudflaredProcesses) {
    Write-Host "ERROR: No cloudflared processes found!" -ForegroundColor Red
    Write-Host "Please start the tunnels first using start-cloudflare-tunnel-fixed.bat" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Found $($cloudflaredProcesses.Count) cloudflared process(es)" -ForegroundColor Green
Write-Host ""

# Try to find backend tunnel URL from process command line
$backendUrl = $null
$frontendUrl = $null

foreach ($proc in $cloudflaredProcesses) {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
        if ($cmdLine -match "localhost:8000") {
            Write-Host "Found backend tunnel process (PID: $($proc.Id))" -ForegroundColor Green
        }
        if ($cmdLine -match "localhost:3000") {
            Write-Host "Found frontend tunnel process (PID: $($proc.Id))" -ForegroundColor Green
        }
    } catch {
        # Can't read command line, continue
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Tunnel URL Detection" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Cloudflared outputs URLs to console windows." -ForegroundColor Yellow
Write-Host "Please check the 'Backend Tunnel' window for the URL." -ForegroundColor Yellow
Write-Host ""
Write-Host "The URL will look like: https://xxxx-xxxx-xxxx.trycloudflare.com" -ForegroundColor Cyan
Write-Host ""

$backendUrl = Read-Host "Enter the BACKEND tunnel URL (or press Enter to skip)"

if ([string]::IsNullOrWhiteSpace($backendUrl)) {
    Write-Host ""
    Write-Host "Skipping configuration. You can manually set:" -ForegroundColor Yellow
    Write-Host "  PG_BACKEND_URL=<backend-tunnel-url> in frontend/.env.local" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 0
}

# Validate URL format
if (-not ($backendUrl -match "^https://.*\.trycloudflare\.com$")) {
    Write-Host ""
    Write-Host "WARNING: URL doesn't match expected format (https://xxxx.trycloudflare.com)" -ForegroundColor Yellow
    $confirm = Read-Host "Continue anyway? (y/n)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        exit 0
    }
}

Write-Host ""
Write-Host "Configuring frontend to use backend tunnel URL..." -ForegroundColor Green

# Read existing .env.local
$envFile = "frontend\.env.local"
$envContent = @()

if (Test-Path $envFile) {
    $envContent = Get-Content $envFile
    Write-Host "Found existing .env.local, updating..." -ForegroundColor Green
} else {
    Write-Host "Creating new .env.local..." -ForegroundColor Green
}

# Remove old PG_BACKEND_URL and NEXT_PUBLIC_API_URL lines
$updatedContent = $envContent | Where-Object {
    $_ -notmatch "^PG_BACKEND_URL=" -and
    $_ -notmatch "^NEXT_PUBLIC_API_URL=" -and
    $_ -notmatch "^# Backend API URL"
}

# Add new configuration
$updatedContent += ""
$updatedContent += "# Backend API URL (Tunnel)"
$updatedContent += "PG_BACKEND_URL=$backendUrl"
$updatedContent += "NEXT_PUBLIC_API_URL=$backendUrl"

# Write updated content
$updatedContent | Set-Content $envFile -Encoding UTF8

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Configuration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend URL set to: $backendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Restart the frontend server for changes to take effect:" -ForegroundColor Yellow
Write-Host "  1. Close the 'F3 Frontend' window" -ForegroundColor Yellow
Write-Host "  2. Wait a moment" -ForegroundColor Yellow
Write-Host "  3. Restart it with: cd frontend && npm run dev:network" -ForegroundColor Yellow
Write-Host ""
Write-Host "Or restart the entire tunnel setup." -ForegroundColor Yellow
Write-Host ""

Read-Host "Press Enter to exit"



