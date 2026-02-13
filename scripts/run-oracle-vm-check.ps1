# Load ORACLE_SSH_* from repo root .env (if present) then run oracle-server-check.ps1.
# Run from repo root: .\scripts\run-oracle-vm-check.ps1
$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot ".env"
if (Test-Path -LiteralPath $EnvFile) {
    Get-Content -LiteralPath $EnvFile | ForEach-Object {
        if ($_ -match '^\s*(ORACLE_SSH_[A-Za-z0-9_]+)\s*=\s*(.*)$') {
            $name = $matches[1]
            $value = $matches[2].Trim()
            if ($value -match '^["''](.+)["'']$') { $value = $matches[1] }
            Set-Item -Path "Env:$name" -Value $value
        }
    }
}
& (Join-Path $RepoRoot "scripts\oracle-server-check.ps1")
