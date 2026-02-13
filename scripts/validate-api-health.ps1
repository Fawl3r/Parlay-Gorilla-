# Validate api.parlaygorilla.com/health and /health/db from this machine.
# Usage: .\scripts\validate-api-health.ps1
# Optional: $env:API_BASE_URL = "https://api.parlaygorilla.com"
$BaseUrl = if ($env:API_BASE_URL) { $env:API_BASE_URL.TrimEnd('/') } else { "https://api.parlaygorilla.com" }

function Test-Endpoint {
    param([string]$Path, [string]$Label)
    $url = "$BaseUrl$Path"
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 15
        $code = $r.StatusCode
        $preview = "ok"
        try { $preview = ($r.Content | ConvertFrom-Json).status } catch { }
        Write-Host "$Label : HTTP $code ($preview)" -ForegroundColor Green
        return $code
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        if (-not $code) { $code = "error" }
        Write-Host "$Label : $code - $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

Write-Host "Validating $BaseUrl" -ForegroundColor Cyan
$healthCode = Test-Endpoint -Path "/health" -Label "/health"
$null = Test-Endpoint -Path "/health/db" -Label "/health/db"
if ($healthCode -eq 200) { exit 0 } else { exit 1 }
