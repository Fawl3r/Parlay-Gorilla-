# Simple script to update backend tunnel URL
param(
    [Parameter(Mandatory=$true)]
    [string]$BackendUrl
)

$envFile = "frontend\.env.local"

Write-Host "Updating backend URL to: $BackendUrl" -ForegroundColor Green

# Read existing content
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
$content += "# Backend API URL (Tunnel)"
$content += "PG_BACKEND_URL=$BackendUrl"
$content += "NEXT_PUBLIC_API_URL=$BackendUrl"

# Write to file
$content | Set-Content $envFile -Encoding UTF8

Write-Host "Configuration updated successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Restart the frontend server for changes to take effect." -ForegroundColor Yellow



