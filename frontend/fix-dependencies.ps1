# Fix Next.js Dependencies - Clean reinstall
# This script fixes React 19 compatibility issues with Next.js 16.1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fixing Next.js Dependencies" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$frontendDir = $PSScriptRoot
if (-not $frontendDir) {
    $frontendDir = Get-Location
}

Set-Location $frontendDir

Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  1. Remove node_modules" -ForegroundColor White
Write-Host "  2. Remove .next cache" -ForegroundColor White
Write-Host "  3. Clear npm cache" -ForegroundColor White
Write-Host "  4. Reinstall all dependencies" -ForegroundColor White
Write-Host ""

$continue = Read-Host "Continue? (Y/N)"
if ($continue -ne "Y" -and $continue -ne "y") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "[1/4] Removing node_modules..." -ForegroundColor Green
if (Test-Path "node_modules") {
    Remove-Item -Recurse -Force "node_modules" -ErrorAction SilentlyContinue
    Write-Host "  Done." -ForegroundColor Green
} else {
    Write-Host "  node_modules not found, skipping." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2/4] Removing .next cache..." -ForegroundColor Green
if (Test-Path ".next") {
    Remove-Item -Recurse -Force ".next" -ErrorAction SilentlyContinue
    Write-Host "  Done." -ForegroundColor Green
} else {
    Write-Host "  .next not found, skipping." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[3/4] Clearing npm cache..." -ForegroundColor Green
npm cache clean --force 2>&1 | Out-Null
Write-Host "  Done." -ForegroundColor Green

Write-Host ""
Write-Host "[4/4] Installing dependencies..." -ForegroundColor Green
$installResult = npm install 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: npm install failed!" -ForegroundColor Red
    Write-Host $installResult -ForegroundColor Red
    exit 1
}
Write-Host "  Done." -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Dependencies Fixed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run: npm run dev" -ForegroundColor White
Write-Host "  2. Or use: ..\restart-all.bat" -ForegroundColor White
Write-Host ""

