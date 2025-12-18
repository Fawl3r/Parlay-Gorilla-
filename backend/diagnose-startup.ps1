# Diagnostic script to identify why backend might be crashing
# Usage: .\diagnose-startup.ps1

# Set error handling to prevent crashes
$ErrorActionPreference = "Continue"
$PSDefaultParameterValues['*:ErrorAction'] = 'SilentlyContinue'

# Trap all errors to prevent terminal crash
trap {
    Write-Host "  ⚠ Error during cleanup: $($_.Exception.Message)" -ForegroundColor Yellow
    continue
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend Startup Diagnostic" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 0: Clean up existing connections and processes
Write-Host "[0] Cleaning up existing localhost connections..." -ForegroundColor Yellow

function Stop-ListeningPort([int]$Port) {
  $killed = $false
  
  try {
    # Method 1: Use Get-NetTCPConnection (most reliable)
    try {
      $conns = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
      if ($conns) {
        foreach ($c in $conns) {
          try {
            if ($c.OwningProcess -and $c.OwningProcess -ne 0) {
              $process = $null
              try {
                $process = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
              } catch {
                # Process might not exist anymore
                continue
              }
              
              if ($process) {
                Write-Host "    Stopping $($process.ProcessName) (PID: $($process.Id)) on port $Port" -ForegroundColor Yellow
                try {
                  Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop
                  $killed = $true
                } catch {
                  Write-Host "      Trying taskkill as fallback..." -ForegroundColor DarkYellow
                  try {
                    $null = & taskkill /PID $c.OwningProcess /F /T 2>&1
                    if ($LASTEXITCODE -eq 0) {
                      $killed = $true
                    } else {
                      Write-Host "      (Could not stop process - may require admin)" -ForegroundColor DarkYellow
                    }
                  } catch {
                    Write-Host "      (Could not stop process - may require admin)" -ForegroundColor DarkYellow
                  }
                }
              }
            }
          } catch {
            # Skip this connection if there's an error
            continue
          }
        }
      }
    } catch {
      # Get-NetTCPConnection might not be available, use fallback
    }

    # Method 2: Use netstat (fallback for older PowerShell)
    try {
      $netstatOutput = netstat -ano 2>&1
      if ($LASTEXITCODE -eq 0) {
        $lines = $netstatOutput | Select-String -Pattern ":$Port\s" -ErrorAction SilentlyContinue
        foreach ($line in $lines) {
          try {
            $parts = ($line -split "\s+") | Where-Object { $_ -ne "" }
            $pid = $parts[-1]
            if ($pid -match "^\d+$") {
              $process = $null
              try {
                $process = Get-Process -Id ([int]$pid) -ErrorAction SilentlyContinue
              } catch {
                # Process doesn't exist
                continue
              }
              
              if ($process) {
                Write-Host "    Stopping $($process.ProcessName) (PID: $pid) on port $Port" -ForegroundColor Yellow
                try {
                  Stop-Process -Id ([int]$pid) -Force -ErrorAction Stop
                  $killed = $true
                } catch {
                  Write-Host "      Trying taskkill as fallback..." -ForegroundColor DarkYellow
                  try {
                    $null = & taskkill /PID ([int]$pid) /F /T 2>&1
                    if ($LASTEXITCODE -eq 0) {
                      $killed = $true
                    } else {
                      Write-Host "      (Could not stop process - may require admin)" -ForegroundColor DarkYellow
                    }
                  } catch {
                    Write-Host "      (Could not stop process - may require admin)" -ForegroundColor DarkYellow
                  }
                }
              }
            }
          } catch {
            # Skip this line if there's an error parsing
            continue
          }
        }
      }
    } catch {
      # netstat might have failed
    }
  } catch {
    # Overall function error - don't crash
    Write-Host "    Warning: Error checking port $Port" -ForegroundColor DarkYellow
  }
  
  # Wait a moment for processes to fully terminate
  if ($killed) {
    Start-Sleep -Milliseconds 500
  }
  
  return $killed
}

# Stop processes on common development ports
$portsToClean = @(8000, 3000, 3001, 3004, 8080)
Write-Host "  Cleaning ports: $($portsToClean -join ', ')" -ForegroundColor Yellow
foreach ($port in $portsToClean) {
  Stop-ListeningPort -Port $port | Out-Null
}

# Kill cloudflared processes
Write-Host "  Stopping cloudflared processes..." -ForegroundColor Yellow
try {
  $cloudflared = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
  if ($cloudflared) {
    foreach ($proc in $cloudflared) {
      try {
        Write-Host "    Stopping cloudflared (PID: $($proc.Id))" -ForegroundColor Yellow
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
      } catch {
        Write-Host "      (Could not stop cloudflared PID: $($proc.Id))" -ForegroundColor DarkYellow
      }
    }
  }
} catch {
  # Ignore errors
}

# Kill Python processes that might be running uvicorn
Write-Host "  Checking for Python backend processes..." -ForegroundColor Yellow
try {
  $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
  $killedCount = 0
  foreach ($proc in $pythonProcesses) {
    try {
      # Try to check command line, but don't fail if we can't
      $cmdLine = $null
      try {
        $procInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue
        if ($procInfo) {
          $cmdLine = $procInfo.CommandLine
        }
      } catch {
        # Can't get command line - that's okay, we'll skip this check
      }
      
      # If we got the command line and it matches, or if we can't check, be cautious
      if ($cmdLine -and ($cmdLine -match "uvicorn|app\.main")) {
        Write-Host "    Stopping backend Python process (PID: $($proc.Id))" -ForegroundColor Yellow
        try {
          Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
          $killedCount++
        } catch {
          Write-Host "      (Could not stop Python process PID: $($proc.Id))" -ForegroundColor DarkYellow
        }
      }
    } catch {
      # Skip this process if there's an error
      continue
    }
  }
  if ($killedCount -gt 0) {
    Write-Host "    Stopped $killedCount Python backend process(es)" -ForegroundColor Green
  }
} catch {
  Write-Host "    (Could not check Python processes)" -ForegroundColor DarkYellow
}

# Kill Node processes that might be running frontend
Write-Host "  Checking for Node.js frontend processes..." -ForegroundColor Yellow
try {
  $nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue
  $killedNodeCount = 0
  foreach ($proc in $nodeProcesses) {
    try {
      $cmdLine = $null
      try {
        $procInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue
        if ($procInfo) {
          $cmdLine = $procInfo.CommandLine
        }
      } catch {
        # Can't get command line
      }
      
      if ($cmdLine -and ($cmdLine -match "next|dev:network|dev")) {
        Write-Host "    Stopping frontend Node process (PID: $($proc.Id))" -ForegroundColor Yellow
        try {
          Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
          $killedNodeCount++
        } catch {
          Write-Host "      (Could not stop Node process PID: $($proc.Id))" -ForegroundColor DarkYellow
        }
      }
    } catch {
      # Skip this process
      continue
    }
  }
  if ($killedNodeCount -gt 0) {
    Write-Host "    Stopped $killedNodeCount Node frontend process(es)" -ForegroundColor Green
  }
} catch {
  Write-Host "    (Could not check Node processes)" -ForegroundColor DarkYellow
}

# Final verification - make sure ports are actually free
Write-Host "  Verifying ports are free..." -ForegroundColor Yellow
$portsStillInUse = @()
try {
  foreach ($port in $portsToClean) {
    Start-Sleep -Milliseconds 300
    $stillInUse = $false
    try {
      $conns = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
      if ($conns) { $stillInUse = $true }
    } catch {
      try {
        $netstatOutput = netstat -ano 2>&1
        if ($LASTEXITCODE -eq 0) {
          $netstat = $netstatOutput | Select-String -Pattern ":$port\s" -ErrorAction SilentlyContinue
          if ($netstat) { $stillInUse = $true }
        }
      } catch {
        # Can't check - assume it's free
      }
    }
    if ($stillInUse) {
      $portsStillInUse += $port
    }
  }

  if ($portsStillInUse.Count -gt 0) {
    Write-Host "  ⚠ Warning: Ports still in use after cleanup: $($portsStillInUse -join ', ')" -ForegroundColor Yellow
    Write-Host "    Attempting force cleanup..." -ForegroundColor Yellow
    foreach ($port in $portsStillInUse) {
      try {
        Stop-ListeningPort -Port $port | Out-Null
        Start-Sleep -Milliseconds 500
      } catch {
        # Ignore errors during force cleanup
      }
    }
  } else {
    Write-Host "  ✓ All ports are free" -ForegroundColor Green
  }
} catch {
  Write-Host "  ⚠ Could not verify port status" -ForegroundColor Yellow
}

Write-Host "  ✓ Cleanup complete" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 1

$errors = @()

# Check 1: Python installation
Write-Host "[1] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found in PATH" -ForegroundColor Red
    $errors += "Python not installed or not in PATH"
}

# Check 2: Backend directory structure
Write-Host "[2] Checking backend directory structure..." -ForegroundColor Yellow
$mainFile = "app\main.py"
if (Test-Path $mainFile) {
    Write-Host "  ✓ app\main.py found" -ForegroundColor Green
} else {
    Write-Host "  ✗ app\main.py not found" -ForegroundColor Red
    $errors += "Backend directory structure incorrect"
}

# Check 3: .env file
Write-Host "[3] Checking .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  ✓ .env file exists" -ForegroundColor Green
    
    # Check for critical variables
    $envContent = Get-Content ".env" -Raw
    $requiredVars = @("DATABASE_URL", "THE_ODDS_API_KEY")
    foreach ($var in $requiredVars) {
        if ($envContent -match "$var=") {
            $value = ($envContent | Select-String -Pattern "$var=(.+)" | ForEach-Object { $_.Matches.Groups[1].Value })
            if ([string]::IsNullOrWhiteSpace($value) -or $value -eq "your-value-here") {
                Write-Host "  ⚠ $var is set but appears to be a placeholder" -ForegroundColor Yellow
            } else {
                Write-Host "  ✓ $var is configured" -ForegroundColor Green
            }
        } else {
            Write-Host "  ✗ $var not found in .env" -ForegroundColor Red
            $errors += "$var missing from .env"
        }
    }
} else {
    Write-Host "  ✗ .env file not found" -ForegroundColor Red
    $errors += ".env file missing - copy .env.example to .env"
}

# Check 4: Python dependencies
Write-Host "[4] Checking Python dependencies..." -ForegroundColor Yellow
$requiredModules = @("uvicorn", "fastapi", "sqlalchemy", "pydantic")
foreach ($module in $requiredModules) {
    try {
        python -c "import $module" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ $module installed" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $module not installed" -ForegroundColor Red
            $errors += "$module not installed - run: pip install -r requirements.txt"
        }
    } catch {
        Write-Host "  ✗ $module not installed" -ForegroundColor Red
        $errors += "$module not installed"
    }
}

# Check 5: Port availability (should be free after cleanup)
Write-Host "[5] Verifying port 8000 is available..." -ForegroundColor Yellow
try {
    $conns = Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($conns) {
        Write-Host "  ⚠ Port 8000 is still in use after cleanup" -ForegroundColor Yellow
        foreach ($conn in $conns) {
            $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "    Process: $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor Yellow
                Write-Host "    Attempting to force stop..." -ForegroundColor Yellow
                Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            }
        }
        Start-Sleep -Seconds 1
        # Check again
        $conns2 = Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue
        if ($conns2) {
            Write-Host "  ✗ Port 8000 still in use - may require manual intervention" -ForegroundColor Red
            $errors += "Port 8000 is in use - try: netstat -ano | findstr :8000 then taskkill /PID <PID> /F"
        } else {
            Write-Host "  ✓ Port 8000 is now available" -ForegroundColor Green
        }
    } else {
        Write-Host "  ✓ Port 8000 is available" -ForegroundColor Green
    }
} catch {
    # Fallback: use netstat
    $netstat = netstat -ano | Select-String -Pattern ":8000\s"
    if ($netstat) {
        Write-Host "  ⚠ Port 8000 may be in use (check manually with: netstat -ano | findstr :8000)" -ForegroundColor Yellow
        $errors += "Port 8000 may be in use - verify manually"
    } else {
        Write-Host "  ✓ Port 8000 appears available" -ForegroundColor Green
    }
}

# Check 6: Try importing the app
Write-Host "[6] Testing app import..." -ForegroundColor Yellow
try {
    $importTest = python -c "import sys; sys.path.insert(0, '.'); from app.main import app; print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ App imports successfully" -ForegroundColor Green
    } else {
        Write-Host "  ✗ App import failed" -ForegroundColor Red
        Write-Host "    Error: $importTest" -ForegroundColor Red
        $errors += "App import failed - check error above"
    }
} catch {
    Write-Host "  ✗ Failed to test import" -ForegroundColor Red
    $errors += "Could not test app import"
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Diagnostic Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($errors.Count -eq 0) {
    Write-Host "✓ All checks passed! Backend should start successfully." -ForegroundColor Green
    Write-Host ""
    Write-Host "If the backend still crashes, check the error window for:" -ForegroundColor Yellow
    Write-Host "  - Database connection errors" -ForegroundColor Yellow
    Write-Host "  - Missing environment variables" -ForegroundColor Yellow
    Write-Host "  - Import errors in Python modules" -ForegroundColor Yellow
} else {
    Write-Host "✗ Found $($errors.Count) issue(s):" -ForegroundColor Red
    Write-Host ""
    foreach ($error in $errors) {
        Write-Host "  - $error" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Fix these issues before starting the backend." -ForegroundColor Yellow
}

Write-Host ""

