$ErrorActionPreference = "Stop"

param(
  [switch]$Live
)

$scriptDir = Split-Path -Parent $PSCommandPath
$python = (Get-Command python -ErrorAction Stop).Source
$runner = Join-Path $scriptDir "full_app_test.py"

$argsList = @()
if ($Live) {
  $argsList += "--live"
}

Write-Host "Running full app test runner..." -ForegroundColor Cyan
Write-Host "Python: $python"
Write-Host "Runner: $runner"

& $python $runner @argsList
exit $LASTEXITCODE




