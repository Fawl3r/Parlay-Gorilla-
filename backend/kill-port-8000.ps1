# Aggressive port 8000 cleanup script
# Usage: .\kill-port-8000.ps1

Write-Host "Finding processes using port 8000..." -ForegroundColor Yellow

# Method 1: Get-NetTCPConnection
$pids = @()
try {
    $conns = Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        if ($c.OwningProcess -and $c.OwningProcess -ne 0) {
            $pids += $c.OwningProcess
        }
    }
} catch {
    # Fallback to netstat
}

# Method 2: netstat fallback
if ($pids.Count -eq 0) {
    try {
        $netstatOutput = netstat -ano 2>&1
        $lines = $netstatOutput | Select-String -Pattern ":8000\s" -ErrorAction SilentlyContinue
        foreach ($line in $lines) {
            $parts = ($line -split "\s+") | Where-Object { $_ -ne "" }
            $targetPid = $parts[-1]
            if ($targetPid -match "^\d+$") {
                $pids += [int]$targetPid
            }
        }
    } catch {
        Write-Host "Could not check port 8000" -ForegroundColor Red
        exit 1
    }
}

if ($pids.Count -eq 0) {
    Write-Host "✓ Port 8000 is not in use" -ForegroundColor Green
    exit 0
}

Write-Host "Found $($pids.Count) process(es) using port 8000:" -ForegroundColor Yellow

foreach ($processId in $pids) {
    try {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  - $($process.ProcessName) (PID: $processId)" -ForegroundColor Cyan
            
            # Try to get command line
            try {
                $procInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction SilentlyContinue
                if ($procInfo -and $procInfo.CommandLine) {
                    $cmdLine = $procInfo.CommandLine
                    if ($cmdLine.Length -gt 100) {
                        $cmdLine = $cmdLine.Substring(0, 100) + "..."
                    }
                    Write-Host "    Command: $cmdLine" -ForegroundColor Gray
                }
            } catch {
                # Can't get command line
            }
            
            Write-Host "    Attempting to stop..." -ForegroundColor Yellow
            try {
                Stop-Process -Id $processId -Force -ErrorAction Stop
                Write-Host "    ✓ Stopped successfully" -ForegroundColor Green
            } catch {
                Write-Host "    ✗ Could not stop (may require admin rights)" -ForegroundColor Red
                Write-Host "    Try running as administrator or use: taskkill /PID $processId /F" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  - Process $processId (not found - may have already terminated)" -ForegroundColor DarkYellow
        }
    } catch {
        Write-Host "  - Process $processId (error accessing)" -ForegroundColor Red
    }
}

# Wait and verify
Start-Sleep -Seconds 1
Write-Host ""
Write-Host "Verifying port 8000 is now free..." -ForegroundColor Yellow

$stillInUse = $false
try {
    $conns = Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($conns) { $stillInUse = $true }
} catch {
    $netstat = netstat -ano | Select-String -Pattern ":8000\s"
    if ($netstat) { $stillInUse = $true }
}

if ($stillInUse) {
    Write-Host "✗ Port 8000 is still in use" -ForegroundColor Red
    Write-Host "You may need to:" -ForegroundColor Yellow
    Write-Host "  1. Run PowerShell as Administrator" -ForegroundColor Yellow
    Write-Host "  2. Manually kill the process: taskkill /PID <PID> /F" -ForegroundColor Yellow
    Write-Host "  3. Restart your computer if it's a system process" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✓ Port 8000 is now free!" -ForegroundColor Green
    exit 0
}

