$ErrorActionPreference = "Stop"

param(
  [switch]$Network
)

function Stop-ListeningPort([int]$Port) {
  try {
    $conns = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
      if ($c.OwningProcess -and $c.OwningProcess -ne 0) {
        try {
          # Kill the whole process tree (important for Next.js which spawns workers).
          taskkill /PID $c.OwningProcess /T /F | Out-Null
          Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        } catch { }
      }
    }
  } catch {
    # Fallback: netstat parse
    $lines = netstat -ano | Select-String -Pattern (":$Port\s") -ErrorAction SilentlyContinue
    foreach ($line in $lines) {
      $parts = ($line -split "\s+") | Where-Object { $_ -ne "" }
      $pid = $parts[-1]
      if ($pid -match "^\d+$") {
        try {
          taskkill /PID ([int]$pid) /T /F | Out-Null
          Stop-Process -Id ([int]$pid) -Force -ErrorAction SilentlyContinue
        } catch { }
      }
    }
  }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Restarting Frontend Dev Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Stopping anything listening on 3000/3004..." -ForegroundColor Yellow
Stop-ListeningPort -Port 3000
Stop-ListeningPort -Port 3004
Start-Sleep -Seconds 1

Write-Host "Clearing Next.js caches (.next, .turbo)..." -ForegroundColor Yellow
if (Test-Path ".next") { Remove-Item -Recurse -Force ".next" -ErrorAction SilentlyContinue }
if (Test-Path ".turbo") { Remove-Item -Recurse -Force ".turbo" -ErrorAction SilentlyContinue }

Write-Host "" 
Write-Host "Starting Next dev..." -ForegroundColor Green
Write-Host ""

if ($Network) {
  npm run dev:network
} else {
  npm run dev
}



