# Upload backend/.env to Oracle VM so the backend has the same env as local (e.g. Stripe test API).
# Usage (PowerShell, from repo root or backend/scripts):
#   .\backend\scripts\upload_env_to_oracle.ps1 -OracleHost "your-oracle-vm.example.com"
#   .\backend\scripts\upload_env_to_oracle.ps1 -OracleHost "your-oracle-vm.example.com" -KeyPath "$env:USERPROFILE\.ssh\oracle_deploy"
#
# Env vars (optional): $env:ORACLE_HOST, $env:ORACLE_USER, $env:ORACLE_SSH_KEY_PATH
#
# After upload you must SSH to the VM and apply the file (see printed instructions).
# WARNING: If your local .env has different DATABASE_URL or REDIS_URL, replacing
# /etc/parlaygorilla/backend.env will point production at the wrong services.
# Use only if local .env already uses production DB/Redis, or merge vars manually.

param(
    [Parameter(Mandatory = $false)]
    [string]$OracleHost = $env:ORACLE_HOST,
    [string]$User = $env:ORACLE_USER,
    [string]$KeyPath = $env:ORACLE_SSH_KEY_PATH
)

if (-not $User) { $User = "ubuntu" }
$HostTarget = $OracleHost

# Resolve backend/.env from script location (backend/scripts -> backend/.env)
$scriptsDir = $PSScriptRoot
$backendDir = Split-Path $scriptsDir -Parent
$envPath = Join-Path $backendDir ".env"

if (-not (Test-Path $envPath)) {
    Write-Error "backend/.env not found at: $envPath"
    exit 1
}

if (-not $HostTarget) {
    Write-Error "Provide -OracleHost or set env ORACLE_HOST (e.g. your VM hostname or IP)."
    exit 1
}

$dest = "${User}@${HostTarget}:/tmp/backend.env.uploaded"
Write-Host "Uploading $envPath to $dest ..."

if ($KeyPath -and (Test-Path $KeyPath)) {
    scp -o StrictHostKeyChecking=accept-new -i $KeyPath $envPath $dest
} else {
    scp -o StrictHostKeyChecking=accept-new $envPath $dest
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "scp failed."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Upload done. Run the next steps ON THE ORACLE VM (SSH in first):"
Write-Host "  ssh $User@$HostTarget   (add -i <key> if needed)"
Write-Host ""
Write-Host "Then on the VM run:"
Write-Host "  sudo cp /etc/parlaygorilla/backend.env /etc/parlaygorilla/backend.env.bak"
Write-Host "  sudo cp /tmp/backend.env.uploaded /etc/parlaygorilla/backend.env"
Write-Host "  sudo systemctl restart parlaygorilla-backend   # or parlaygorilla-api if that is what you have"
Write-Host "  # If 'Unit not found': install the systemd unit (see docs/deploy/VM_OPS_VERIFY_RUNBOOK.md, section 0)"
Write-Host ""
Write-Host "If your local .env has different DATABASE_URL or REDIS_URL, do NOT replace;"
Write-Host "instead merge only needed vars (e.g. STRIPE_*) into /etc/parlaygorilla/backend.env"
