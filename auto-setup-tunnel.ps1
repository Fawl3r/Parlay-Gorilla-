# Fully automated tunnel URL setup
# This script attempts to find and configure the backend tunnel URL

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Automated Tunnel Configuration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for cloudflared processes
$cloudflaredProcesses = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue

if ($cloudflaredProcesses) {
    Write-Host "Found cloudflared processes running" -ForegroundColor Green
    
    # Try to find backend tunnel URL from process output or logs
    # Note: This is challenging on Windows as cloudflared outputs to console windows
    # We'll provide instructions instead
    Write-Host ""
    Write-Host "To complete setup, we need the backend tunnel URL." -ForegroundColor Yellow
    Write-Host "Please check the 'Backend Tunnel' window for a URL like:" -ForegroundColor Yellow
    Write-Host "  https://xxxx-xxxx-xxxx.trycloudflare.com" -ForegroundColor Cyan
    Write-Host ""
    
    # Try to read from clipboard (user might have copied it)
    $clipboard = Get-Clipboard -ErrorAction SilentlyContinue
    if ($clipboard -and $clipboard -match "https://.*\.trycloudflare\.com") {
        Write-Host "Found URL in clipboard: $clipboard" -ForegroundColor Green
        $useClipboard = Read-Host "Use this URL? (y/n)"
        if ($useClipboard -eq "y" -or $useClipboard -eq "Y") {
            $backendUrl = $clipboard
        }
    }
    
    if (-not $backendUrl) {
        Write-Host ""
        Write-Host "Please enter the backend tunnel URL:" -ForegroundColor Yellow
        $backendUrl = Read-Host "Backend Tunnel URL"
    }
} else {
    Write-Host "No cloudflared processes found." -ForegroundColor Yellow
    Write-Host "Please start the tunnels first, then run this script again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To start tunnels, run: .\start-cloudflare-tunnel-fixed.bat" -ForegroundColor Cyan
    Read-Host "Press Enter to exit"
    exit 1
}

if ([string]::IsNullOrWhiteSpace($backendUrl)) {
    Write-Host ""
    Write-Host "No URL provided. Exiting." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Validate and clean URL
$backendUrl = $backendUrl.Trim()
if (-not $backendUrl.StartsWith("https://")) {
    if ($backendUrl -match "^[a-z0-9-]+\.trycloudflare\.com$") {
        $backendUrl = "https://" + $backendUrl
    } else {
        Write-Host ""
        Write-Host "WARNING: URL format may be incorrect" -ForegroundColor Yellow
        Write-Host "Expected format: https://xxxx-xxxx-xxxx.trycloudflare.com" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Configuring frontend with backend URL: $backendUrl" -ForegroundColor Green

# Update .env.local
$envFile = "frontend\.env.local"
$envContent = @()

if (Test-Path $envFile) {
    $envContent = Get-Content $envFile
}

# Remove old backend URL entries
$updatedContent = $envContent | Where-Object {
    $_ -notmatch "^PG_BACKEND_URL=" -and
    $_ -notmatch "^NEXT_PUBLIC_API_URL=" -and
    $_ -notmatch "^# Backend API URL"
}

# Remove trailing empty lines
while ($updatedContent.Count -gt 0 -and [string]::IsNullOrWhiteSpace($updatedContent[-1])) {
    $updatedContent = $updatedContent[0..($updatedContent.Count - 2)]
}

# Add new configuration
if ($updatedContent.Count -gt 0 -and -not [string]::IsNullOrWhiteSpace($updatedContent[-1])) {
    $updatedContent += ""
}
$updatedContent += "# Backend API URL (Tunnel - Auto-configured)"
$updatedContent += "PG_BACKEND_URL=$backendUrl"
$updatedContent += "NEXT_PUBLIC_API_URL=$backendUrl"

# Write to file
$updatedContent | Set-Content $envFile -Encoding UTF8

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Configuration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend URL configured: $backendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart the frontend server (close 'F3 Frontend' window)" -ForegroundColor White
Write-Host "  2. Restart it with: cd frontend && npm run dev:network" -ForegroundColor White
Write-Host ""
Write-Host "Or restart everything with: .\start-cloudflare-tunnel-fixed.bat" -ForegroundColor White
Write-Host ""

# Check if frontend is running
$nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*frontend*" -or $_.CommandLine -like "*next*"
}

if ($nodeProcesses) {
    Write-Host "Frontend server is running. You need to restart it for changes to take effect." -ForegroundColor Yellow
    Write-Host ""
    $restart = Read-Host "Would you like me to restart the frontend now? (y/n)"
    if ($restart -eq "y" -or $restart -eq "Y") {
        Write-Host "Stopping frontend processes..." -ForegroundColor Yellow
        # This is tricky - we'd need to find the right process
        # For now, just provide instructions
        Write-Host "Please manually restart the frontend window." -ForegroundColor Yellow
    }
}

Write-Host ""
Read-Host "Press Enter to exit"



