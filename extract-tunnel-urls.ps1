# Extract tunnel URLs from running cloudflared processes
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Extracting Tunnel URLs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for cloudflared processes
$processes = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue

if (-not $processes) {
    Write-Host "No cloudflared processes found. Tunnels may not be running yet." -ForegroundColor Yellow
    Write-Host "Please wait a bit longer and try again, or check the tunnel windows manually." -ForegroundColor Yellow
    exit 1
}

Write-Host "Found $($processes.Count) cloudflared process(es)" -ForegroundColor Green
Write-Host ""

# Try to get URLs from process command lines or output
$backendUrl = $null
$frontendUrl = $null

foreach ($proc in $processes) {
    try {
        $procInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)"
        $cmdLine = $procInfo.CommandLine
        
        Write-Host "Process ID: $($proc.Id)" -ForegroundColor Gray
        Write-Host "Command: $($cmdLine.Substring(0, [Math]::Min(80, $cmdLine.Length)))..." -ForegroundColor Gray
        
        if ($cmdLine -match "localhost:8000") {
            Write-Host "  → This is the BACKEND tunnel" -ForegroundColor Green
        } elseif ($cmdLine -match "localhost:3000") {
            Write-Host "  → This is the FRONTEND tunnel" -ForegroundColor Green
        }
        Write-Host ""
    } catch {
        Write-Host "  Could not read process info" -ForegroundColor Yellow
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Tunnel URLs are displayed in console windows" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To find the URLs:" -ForegroundColor White
Write-Host "  1. Look for windows titled 'Backend Tunnel' and 'Frontend Tunnel'" -ForegroundColor White
Write-Host "  2. Or press Alt+Tab to cycle through open windows" -ForegroundColor White
Write-Host "  3. In each tunnel window, look for a line like:" -ForegroundColor White
Write-Host "     https://xxxx-xxxx-xxxx.trycloudflare.com" -ForegroundColor Cyan
Write-Host ""
Write-Host "Once you have the BACKEND URL, I can configure the frontend automatically." -ForegroundColor Yellow
Write-Host ""

# Try to read from any log files
$logDir = "tunnel-logs"
if (Test-Path $logDir) {
    Write-Host "Checking log files..." -ForegroundColor Cyan
    
    $backendLog = "$logDir\backend-tunnel.log"
    $frontendLog = "$logDir\frontend-tunnel.log"
    
    if (Test-Path $backendLog) {
        $backendContent = Get-Content $backendLog -ErrorAction SilentlyContinue -Raw
        if ($backendContent -match "https://([a-z0-9-]+\.trycloudflare\.com)") {
            $backendUrl = "https://$($matches[1])"
            Write-Host "✓ Found backend URL in log: $backendUrl" -ForegroundColor Green
        }
    }
    
    if (Test-Path $frontendLog) {
        $frontendContent = Get-Content $frontendLog -ErrorAction SilentlyContinue -Raw
        if ($frontendContent -match "https://([a-z0-9-]+\.trycloudflare\.com)") {
            $frontendUrl = "https://$($matches[1])"
            Write-Host "✓ Found frontend URL in log: $frontendUrl" -ForegroundColor Green
        }
    }
}

if ($backendUrl) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Auto-Configuring Frontend" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
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
    
    Write-Host ""
    Write-Host "✓ Frontend configured successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Tunnel URLs:" -ForegroundColor Cyan
    Write-Host "  Backend:  $backendUrl" -ForegroundColor White
    if ($frontendUrl) {
        Write-Host "  Frontend: $frontendUrl" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "IMPORTANT: Restart the frontend server for changes to take effect!" -ForegroundColor Yellow
    Write-Host "  The frontend window should be restarted to pick up the new configuration." -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Could not automatically extract backend URL." -ForegroundColor Yellow
    Write-Host "Please check the 'Backend Tunnel' window and provide the URL." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Then run: .\update-backend-url.ps1 -BackendUrl 'https://your-url.trycloudflare.com'" -ForegroundColor Cyan
    Write-Host ""
}



