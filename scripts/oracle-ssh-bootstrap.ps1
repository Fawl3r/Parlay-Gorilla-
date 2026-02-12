# Run Oracle VM bootstrap over SSH (clone, server_bootstrap.sh, chown).
# Optionally upload .env to the VM.
#
# Usage:
#   .\oracle-ssh-bootstrap.ps1 -OracleHost "129.146.x.x" -KeyPath "C:\Users\YOU\.ssh\your-key.pem"
#   # Or set env vars first:
#   $env:ORACLE_SSH_HOST = "129.146.x.x"
#   $env:ORACLE_SSH_KEY_PATH = "C:\Users\YOU\.oci\key.pem"
#   .\oracle-ssh-bootstrap.ps1
#
# Optional: upload .env from your machine to the VM
#   .\oracle-ssh-bootstrap.ps1 -OracleHost "..." -KeyPath "..." -EnvPath "C:\F3 Apps\F3 Parlay Gorilla\.env"

param(
    [string]$OracleHost = $env:ORACLE_SSH_HOST,
    [string]$KeyPath = $env:ORACLE_SSH_KEY_PATH,
    [string]$User = $env:ORACLE_SSH_USER,
    [string]$EnvPath = $null   # Local .env file to SCP to VM (optional)
)

if (-not $User) { $User = "ubuntu" }

if (-not $OracleHost) {
    Write-Host "Set ORACLE_SSH_HOST (VM public IP) and optionally ORACLE_SSH_KEY_PATH." -ForegroundColor Yellow
    Write-Host "Example: `$env:ORACLE_SSH_HOST = '129.146.x.x'; `$env:ORACLE_SSH_KEY_PATH = 'C:\Users\Fawl3\.oci\key.pem'" -ForegroundColor Gray
    Write-Host "Then run: .\scripts\oracle-ssh-bootstrap.ps1" -ForegroundColor Gray
    exit 1
}

$sshExe = (Get-Command ssh -ErrorAction SilentlyContinue).Source
if (-not $sshExe) { $sshExe = "C:\Windows\System32\OpenSSH\ssh.exe" }
if (-not (Test-Path $sshExe)) { Write-Host "SSH not found. Install OpenSSH Client (Settings > Apps > Optional features)." -ForegroundColor Red; exit 1 }

$sshArgs = @("-o", "StrictHostKeyChecking=accept-new")
if ($KeyPath -and (Test-Path $KeyPath)) { $sshArgs += @("-i", $KeyPath) }

$remoteCmd = "sudo apt-get update && sudo apt-get install -y git && sudo git clone https://github.com/Fawl3r/Parlay-Gorilla-.git /opt/parlaygorilla && sudo bash /opt/parlaygorilla/scripts/server_bootstrap.sh && sudo chown -R ${User}:${User} /opt/parlaygorilla"

Write-Host "Running bootstrap on ${User}@${OracleHost} (this may take 2-5 minutes) ..." -ForegroundColor Cyan
& $sshExe @sshArgs "${User}@${OracleHost}" $remoteCmd
if ($LASTEXITCODE -ne 0) {
    Write-Host "Bootstrap failed (exit $LASTEXITCODE). Check SSH key and VM reachability." -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "Bootstrap done." -ForegroundColor Green

# Optional: upload .env
$scpExe = (Get-Command scp -ErrorAction SilentlyContinue).Source
if (-not $scpExe) { $scpExe = "C:\Windows\System32\OpenSSH\scp.exe" }

if ($EnvPath -and (Test-Path $EnvPath)) {
    Write-Host "Uploading .env from $EnvPath to VM:/opt/parlaygorilla/.env ..." -ForegroundColor Cyan
    $scpArgs = @("-o", "StrictHostKeyChecking=accept-new")
    if ($KeyPath -and (Test-Path $KeyPath)) { $scpArgs += @("-i", $KeyPath) }
    & $scpExe @scpArgs $EnvPath "${User}@${OracleHost}:/opt/parlaygorilla/.env"
    if ($LASTEXITCODE -eq 0) {
        $checkCmd = "grep -q 'VERIFICATION_DELIVERY=db' /opt/parlaygorilla/.env || echo 'VERIFICATION_DELIVERY=db' >> /opt/parlaygorilla/.env"
        & $sshExe @sshArgs "${User}@${OracleHost}" $checkCmd
        Write-Host ".env uploaded and VERIFICATION_DELIVERY=db ensured." -ForegroundColor Green
    }
} else {
    Write-Host "No -EnvPath provided. Create .env on the VM: ssh ${User}@${OracleHost} 'nano /opt/parlaygorilla/.env'" -ForegroundColor Yellow
    Write-Host "Add VERIFICATION_DELIVERY=db for OCI verifier." -ForegroundColor Gray
}
