# Restart all servers and tunnels, auto-configure frontend (Windows PowerShell 5.1 compatible)
# NOTE: Keep this file ASCII-only so it runs correctly in Windows PowerShell without a BOM.

function Write-Section([string]$Title) {
  Write-Host "========================================" -ForegroundColor Cyan
  Write-Host $Title -ForegroundColor Cyan
  Write-Host "========================================" -ForegroundColor Cyan
  Write-Host ""
}

function Ensure-Directory([string]$Path) {
  if (-not (Test-Path $Path)) {
    New-Item -ItemType Directory -Path $Path | Out-Null
  }
}

function Get-CloudflaredPath {
  $localExe = Join-Path $PSScriptRoot "cloudflared.exe"
  if (Test-Path $localExe) { return $localExe }

  $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }

  return $null
}

function Stop-ListeningPort([int]$Port) {
  try {
    $conns = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
      if ($c.OwningProcess -and $c.OwningProcess -ne 0) {
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
      }
    }
    return
  } catch {
    # Fallback below
  }

  # Fallback (no Get-NetTCPConnection): netstat parse
  $lines = netstat -ano | Select-String -Pattern (":$Port\s") -ErrorAction SilentlyContinue
  foreach ($line in $lines) {
    $parts = ($line -split "\s+") | Where-Object { $_ -ne "" }
    $pid = $parts[-1]
    if ($pid -match "^\d+$") {
      Stop-Process -Id ([int]$pid) -Force -ErrorAction SilentlyContinue
    }
  }
}

function Wait-ForPort([int]$Port, [int]$TimeoutSeconds = 45) {
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    try {
      if (Test-NetConnection -ComputerName "127.0.0.1" -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue) {
        return $true
      }
    } catch { }
    Start-Sleep -Seconds 1
  }
  return $false
}

function Find-TunnelUrl([string]$StdoutLog, [string]$StderrLog, [int]$TimeoutSeconds = 45) {
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  $pattern = "https://([a-z0-9-]+\.trycloudflare\.com)"

  while ((Get-Date) -lt $deadline) {
    foreach ($path in @($StdoutLog, $StderrLog)) {
      if (Test-Path $path) {
        $txt = Get-Content $path -Raw -ErrorAction SilentlyContinue
        if ($txt -match $pattern) {
          return ("https://{0}" -f $matches[1])
        }
      }
    }
    Start-Sleep -Seconds 2
  }

  return $null
}

function Update-FrontendEnv([string]$BackendUrl) {
  $frontendDir = Join-Path $PSScriptRoot "frontend"
  $envFile = Join-Path $frontendDir ".env.local"

  $lines = @()
  if (Test-Path $envFile) {
    $lines = Get-Content $envFile -ErrorAction SilentlyContinue
  }

  $filtered = $lines | Where-Object {
    ($_ -notmatch "^PG_BACKEND_URL=") -and
    ($_ -notmatch "^NEXT_PUBLIC_API_URL=") -and
    ($_ -notmatch "^# Backend API URL")
  }

  # Trim trailing empty lines
  while ($filtered.Count -gt 0 -and [string]::IsNullOrWhiteSpace($filtered[-1])) {
    $filtered = $filtered[0..($filtered.Count - 2)]
  }

  if ($filtered.Count -gt 0) { $filtered += "" }
  $filtered += "# Backend API URL (Tunnel - Auto-configured)"
  $filtered += ("PG_BACKEND_URL={0}" -f $BackendUrl)
  $filtered += ("NEXT_PUBLIC_API_URL={0}" -f $BackendUrl)

  # Use ASCII-safe content; encoding will be fine because content is ASCII.
  $filtered | Set-Content $envFile -Encoding UTF8
}

Write-Section "Restarting All Servers and Tunnels"

Write-Host "Stopping existing tunnels and servers..." -ForegroundColor Yellow
Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Stop-ListeningPort -Port 3000
Stop-ListeningPort -Port 8000
Start-Sleep -Seconds 2

$cloudflaredPath = Get-CloudflaredPath
if (-not $cloudflaredPath) {
  Write-Host "ERROR: cloudflared not found (cloudflared.exe missing and not in PATH)." -ForegroundColor Red
  Write-Host "Put cloudflared.exe in the project root or install cloudflared into PATH." -ForegroundColor Yellow
  exit 1
}

$logsDir = Join-Path $PSScriptRoot "tunnel-logs"
Ensure-Directory $logsDir

$backendLog = Join-Path $logsDir "backend-tunnel.log"
$backendErr = Join-Path $logsDir "backend-tunnel-err.log"
$frontendLog = Join-Path $logsDir "frontend-tunnel.log"
$frontendErr = Join-Path $logsDir "frontend-tunnel-err.log"

Remove-Item -Force -ErrorAction SilentlyContinue $backendLog, $backendErr, $frontendLog, $frontendErr

# Check backend prerequisites before starting
$backendDir = Join-Path $PSScriptRoot "backend"
$backendEnvFile = Join-Path $backendDir ".env"
$backendMainFile = Join-Path $backendDir "app\main.py"

if (-not (Test-Path $backendMainFile)) {
  Write-Host "ERROR: Backend main.py not found at: $backendMainFile" -ForegroundColor Red
  exit 1
}

if (-not (Test-Path $backendEnvFile)) {
  Write-Host "WARNING: Backend .env file not found at: $backendEnvFile" -ForegroundColor Yellow
  Write-Host "The backend may fail to start without proper configuration." -ForegroundColor Yellow
  Write-Host "Copy backend\.env.example to backend\.env and configure it." -ForegroundColor Yellow
  Write-Host ""
  $continue = Read-Host "Continue anyway? (y/N)"
  if ($continue -ne "y" -and $continue -ne "Y") {
    exit 1
  }
}

# Check Python and uvicorn
try {
  $pythonVersion = python --version 2>&1
  Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
  Write-Host "ERROR: Python not found in PATH" -ForegroundColor Red
  exit 1
}

try {
  python -c "import uvicorn" 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: uvicorn not installed. Run: pip install -r backend\requirements.txt" -ForegroundColor Red
    exit 1
  }
} catch {
  Write-Host "ERROR: Failed to check uvicorn installation" -ForegroundColor Red
  exit 1
}

# 1) Start backend first
Write-Host "Starting backend server (http://localhost:8000)..." -ForegroundColor Green
# NOTE:
# - We intentionally do NOT use `--reload` by default when running tunnels.
#   Uvicorn reload can restart the server when `__pycache__` files are created,
#   which causes intermittent "socket hang up" / connection resets for users.
# - To enable reload explicitly, set: $env:PG_BACKEND_RELOAD = "1"
$reloadFlag = ""
if ($env:PG_BACKEND_RELOAD -eq "1") { $reloadFlag = "--reload" }
$backendCmd = "cd /d `"$backendDir`" && python -m uvicorn app.main:app $reloadFlag --host 0.0.0.0 --port 8000"

# Start backend in a visible window so errors can be seen
$backendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $backendCmd -WindowStyle Normal -PassThru

if (-not $backendProcess) {
  Write-Host "ERROR: Failed to start backend process" -ForegroundColor Red
  exit 1
}

Write-Host "Backend process started (PID: $($backendProcess.Id))" -ForegroundColor Green
Write-Host "Waiting for backend port 8000..." -ForegroundColor Yellow

# Wait longer and verify with HTTP request
$backendReady = $false
for ($i = 0; $i -lt 60; $i++) {
  if (Wait-ForPort -Port 8000 -TimeoutSeconds 1) {
    # Double-check with HTTP request
    try {
      $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
      if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Backend is responding on port 8000" -ForegroundColor Green
        $backendReady = $true
        break
      }
    } catch {
      # Still starting, continue waiting
    }
  }
  Start-Sleep -Seconds 1
  if ($i % 5 -eq 0) {
    Write-Host "." -NoNewline -ForegroundColor Yellow
  }
}

Write-Host ""

if (-not $backendReady) {
  Write-Host "WARNING: Backend not responding on port 8000 after 60 seconds." -ForegroundColor Yellow
  Write-Host "Check the 'F3 Backend' window for error messages." -ForegroundColor Yellow
  Write-Host "Common issues:" -ForegroundColor Yellow
  Write-Host "  - Missing .env file or configuration" -ForegroundColor Yellow
  Write-Host "  - Database connection error" -ForegroundColor Yellow
  Write-Host "  - Missing Python dependencies" -ForegroundColor Yellow
  Write-Host "  - Port 8000 already in use" -ForegroundColor Yellow
  Write-Host ""
  $continue = Read-Host "Continue anyway? (y/N)"
  if ($continue -ne "y" -and $continue -ne "Y") {
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
  }
}

# 2) Start backend tunnel and capture URL
Write-Host "Starting backend tunnel..." -ForegroundColor Green
Start-Process -FilePath $cloudflaredPath -ArgumentList @("tunnel", "--url", "http://localhost:8000") -RedirectStandardOutput $backendLog -RedirectStandardError $backendErr -WindowStyle Hidden | Out-Null

Write-Host "Waiting for backend tunnel URL..." -ForegroundColor Yellow
$backendUrl = Find-TunnelUrl -StdoutLog $backendLog -StderrLog $backendErr -TimeoutSeconds 60
if ($backendUrl) {
  Write-Host ("[OK] Backend tunnel URL: {0}" -f $backendUrl) -ForegroundColor Green
  Write-Host "Updating frontend/.env.local with backend tunnel URL..." -ForegroundColor Green
  Update-FrontendEnv -BackendUrl $backendUrl
} else {
  Write-Host "[WARN] Could not detect backend tunnel URL from logs." -ForegroundColor Yellow
  Write-Host ("Check: {0}" -f $backendLog) -ForegroundColor Yellow
}

# 3) Start frontend (after env is updated)
$frontendDir = Join-Path $PSScriptRoot "frontend"
Write-Host "Starting frontend server (http://localhost:3000)..." -ForegroundColor Green
$frontendCmd = ("cd /d `"{0}`" && npm run dev:network" -f $frontendDir)
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $frontendCmd -WindowStyle Normal | Out-Null

Write-Host "Waiting for frontend port 3000..." -ForegroundColor Yellow
if (-not (Wait-ForPort -Port 3000 -TimeoutSeconds 90)) {
  Write-Host "WARNING: frontend not reachable on port 3000 yet. Continuing anyway..." -ForegroundColor Yellow
}

# 4) Start frontend tunnel and capture URL
Write-Host "Starting frontend tunnel..." -ForegroundColor Green
Start-Process -FilePath $cloudflaredPath -ArgumentList @("tunnel", "--url", "http://localhost:3000") -RedirectStandardOutput $frontendLog -RedirectStandardError $frontendErr -WindowStyle Hidden | Out-Null

Write-Host "Waiting for frontend tunnel URL..." -ForegroundColor Yellow
$frontendUrl = Find-TunnelUrl -StdoutLog $frontendLog -StderrLog $frontendErr -TimeoutSeconds 60
if ($frontendUrl) {
  Write-Host ("[OK] Frontend tunnel URL: {0}" -f $frontendUrl) -ForegroundColor Green
} else {
  Write-Host "[WARN] Could not detect frontend tunnel URL from logs." -ForegroundColor Yellow
  Write-Host ("Check: {0}" -f $frontendLog) -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "All Services Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Tunnel URLs:" -ForegroundColor Cyan
if ($backendUrl) { Write-Host ("  Backend:  {0}" -f $backendUrl) -ForegroundColor White }
if ($frontendUrl) { Write-Host ("  Frontend: {0}" -f $frontendUrl) -ForegroundColor White }
Write-Host ""
if (-not $backendReady) {
  Write-Host "IMPORTANT: Backend may not be running properly!" -ForegroundColor Red
  Write-Host "Check the 'F3 Backend' window for error messages." -ForegroundColor Yellow
  Write-Host ""
}
Write-Host "Open the FRONTEND tunnel URL in your browser to test remote access." -ForegroundColor Cyan

