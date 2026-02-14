# One-off: build .env.prod from repo .env and SCP to Oracle VM.
# Uses ORACLE_SSH_* from .env (or defaults: host 147.224.172.113, key ~/.ssh/id_ed25519).
# Run from repo root: .\scripts\oracle-upload-env-prod.ps1
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$EnvFile = Join-Path $RepoRoot ".env"

if (-not (Test-Path -LiteralPath $EnvFile)) {
  Write-Host "Missing .env at $EnvFile" -ForegroundColor Red
  exit 1
}

# Load ORACLE_SSH_* from .env
Get-Content -LiteralPath $EnvFile | ForEach-Object {
  if ($_ -match '^\s*(ORACLE_SSH_[A-Za-z0-9_]+)\s*=\s*(.*)$') {
    $name = $matches[1]
    $value = $matches[2].Trim() -replace '^["'']|["'']$'
    Set-Item -Path "Env:$name" -Value $value -ErrorAction SilentlyContinue
  }
}

$HostIP = if ($env:ORACLE_SSH_HOST) { $env:ORACLE_SSH_HOST } else { "147.224.172.113" }
$KeyPath = if ($env:ORACLE_SSH_KEY_PATH) { $env:ORACLE_SSH_KEY_PATH } else { "$env:USERPROFILE\.ssh\id_ed25519" }
$User = if ($env:ORACLE_SSH_USER) { $env:ORACLE_SSH_USER } else { "ubuntu" }

if (-not (Test-Path -LiteralPath $KeyPath)) {
  Write-Host "Key not found: $KeyPath" -ForegroundColor Red
  exit 1
}

# Parse .env for required keys (first occurrence, skip comments)
$vars = @{}
Get-Content -LiteralPath $EnvFile | ForEach-Object {
  if ($_ -match '^\s*([A-Za-z0-9_]+)\s*=\s*(.*)$' -and $matches[1] -notmatch '^#') {
    $k = $matches[1]
    $v = $matches[2].Trim() -replace '^["'']|["'']$'
    if (-not $vars.ContainsKey($k)) { $vars[$k] = $v }
  }
}

$required = @(
  "DATABASE_URL", "REDIS_URL", "TELEGRAM_BOT_TOKEN", "JWT_SECRET", "THE_ODDS_API_KEY", "OPENAI_API_KEY"
)
$alertId = if ($vars["TELEGRAM_ALERT_CHAT_ID"]) { $vars["TELEGRAM_ALERT_CHAT_ID"] } else { $vars["TELEGRAM_CHAT_ID"] }

$lines = @()
$lines += "ENVIRONMENT=production"
$lines += "SCHEDULER_STANDALONE=true"
foreach ($k in $required) {
  if ($vars[$k]) { $lines += "$k=$($vars[$k])" }
}
if ($alertId) { $lines += "TELEGRAM_ALERT_CHAT_ID=$alertId" }

$content = $lines -join "`n"
$tmp = [System.IO.Path]::GetTempFileName()
try {
  [System.IO.File]::WriteAllText($tmp, $content)
  $sshExe = Get-Command ssh -ErrorAction SilentlyContinue
  if (-not $sshExe) { $sshExe = Get-Command "$env:SystemRoot\System32\OpenSSH\ssh.exe" -ErrorAction SilentlyContinue }
  if (-not $sshExe) { Write-Host "ssh not found." -ForegroundColor Red; exit 1 }
  $scpExe = "scp"
  if (Test-Path "$env:SystemRoot\System32\OpenSSH\scp.exe") { $scpExe = "$env:SystemRoot\System32\OpenSSH\scp.exe" }
  & $scpExe -i $KeyPath -o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new $tmp "${User}@${HostIP}:/opt/parlaygorilla/.env.prod"
  Write-Host "Uploaded .env.prod to ${User}@${HostIP}:/opt/parlaygorilla/.env.prod" -ForegroundColor Green
} finally {
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
