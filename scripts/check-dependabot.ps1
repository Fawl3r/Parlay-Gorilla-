# Dependabot Alert and PR Checker Script
# Requires GitHub CLI (gh) to be installed and authenticated

param(
    [string]$Token = $env:GITHUB_TOKEN,
    [string]$Repo = "Fawl3r/Parlay-Gorilla-"
)

Write-Host "=== Dependabot Status Check ===" -ForegroundColor Cyan
Write-Host ""

# Check if GitHub CLI is installed
$ghInstalled = Get-Command gh -ErrorAction SilentlyContinue

if (-not $ghInstalled) {
    Write-Host "GitHub CLI (gh) is not installed." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Install it from: https://cli.github.com/" -ForegroundColor Yellow
    Write-Host "Or use: winget install --id GitHub.cli" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After installation, run: gh auth login" -ForegroundColor Yellow
    exit 1
}

# Check authentication
Write-Host "Checking GitHub authentication..." -ForegroundColor Cyan
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not authenticated. Run: gh auth login" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Authenticated" -ForegroundColor Green
Write-Host ""

# Get Dependabot alerts
Write-Host "=== Dependabot Alerts ===" -ForegroundColor Cyan
$alerts = gh api "repos/$Repo/dependabot/alerts" --jq '.[] | {
    number: .number,
    state: .state,
    severity: .security_vulnerability.severity,
    package: .dependency.package.name,
    manifest: .dependency.manifest_path,
    created: .created_at
}'

if ($alerts) {
    $alerts | ConvertFrom-Json | Format-Table -AutoSize
} else {
    Write-Host "No open alerts found" -ForegroundColor Green
}

Write-Host ""

# Get Dependabot PRs
Write-Host "=== Dependabot Pull Requests ===" -ForegroundColor Cyan
$prs = gh pr list --repo $Repo --author "app/dependabot" --json number,title,state,headRefName,url,labels

if ($prs) {
    $prs | ConvertFrom-Json | ForEach-Object {
        Write-Host "PR #$($_.number): $($_.title)" -ForegroundColor Yellow
        Write-Host "  State: $($_.state)" -ForegroundColor $(if ($_.state -eq 'OPEN') { 'Green' } else { 'Gray' })
        Write-Host "  URL: $($_.url)" -ForegroundColor Cyan
        Write-Host ""
    }
} else {
    Write-Host "No Dependabot PRs found" -ForegroundColor Green
}

Write-Host ""

# Summary
Write-Host "=== Summary ===" -ForegroundColor Cyan
$openAlerts = if ($alerts) { ($alerts | ConvertFrom-Json | Where-Object { $_.state -eq 'open' }).Count } else { 0 }
$openPRs = if ($prs) { ($prs | ConvertFrom-Json | Where-Object { $_.state -eq 'OPEN' }).Count } else { 0 }

Write-Host "Open alerts: $openAlerts" -ForegroundColor $(if ($openAlerts -gt 0) { 'Yellow' } else { 'Green' })
Write-Host "Open PRs: $openPRs" -ForegroundColor $(if ($openPRs -gt 0) { 'Yellow' } else { 'Green' })

if ($openPRs -gt 0) {
    Write-Host ""
    Write-Host "To review and merge a PR:" -ForegroundColor Cyan
    Write-Host "  gh pr view <number>" -ForegroundColor White
    Write-Host "  gh pr merge <number> --squash" -ForegroundColor White
}

