# Runs a bash snippet on the Oracle VM via SSH.
# Loads ORACLE_SSH_* from repo root `.env` (if present).
#
# Usage:
#   .\scripts\oracle-run-remote.ps1 -Bash 'echo hello'
#
param(
  [Parameter(Mandatory = $true)]
  [string]$Bash
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot ".env"

if (Test-Path -LiteralPath $EnvFile) {
  Get-Content -LiteralPath $EnvFile | ForEach-Object {
    if ($_ -match '^\s*(ORACLE_SSH_[A-Za-z0-9_]+)\s*=\s*(.*)$') {
      $name = $matches[1]
      $value = $matches[2].Trim()
      if ($value -match '^[\"''](.+)[\"'']$') { $value = $matches[1] }
      Set-Item -Path "Env:$name" -Value $value
    }
  }
}

$HostIP = if ($env:ORACLE_SSH_HOST) { $env:ORACLE_SSH_HOST } else { "147.224.172.113" }
$KeyPath = if ($env:ORACLE_SSH_KEY_PATH) { $env:ORACLE_SSH_KEY_PATH } else { "$env:USERPROFILE\.ssh\id_ed25519" }
$User = if ($env:ORACLE_SSH_USER) { $env:ORACLE_SSH_USER } else { "ubuntu" }

if (-not (Test-Path -LiteralPath $KeyPath)) {
  Write-Host "Key not found: $KeyPath" -ForegroundColor Red
  exit 1
}

$sshExe = $null
if (Get-Command ssh -ErrorAction SilentlyContinue) { $sshExe = "ssh" }
if (-not $sshExe) {
  foreach ($p in @("$env:ProgramFiles\OpenSSH\ssh.exe", "$env:SystemRoot\System32\OpenSSH\ssh.exe")) {
    if (Test-Path -LiteralPath $p) { $sshExe = $p; break }
  }
}
if (-not $sshExe) {
  Write-Host "ssh not found. Install OpenSSH or run this script from Git Bash." -ForegroundColor Red
  exit 1
}

$Remote = "${User}@${HostIP}"

# Avoid quote/newline issues by base64 encoding the bash snippet.
$encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Bash))
$remoteCmd = "echo $encoded | base64 -d | bash"

& $sshExe -i $KeyPath -o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new $Remote $remoteCmd

