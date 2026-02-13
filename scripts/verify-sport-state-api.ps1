# Verify /api/sports and /api/sports/{sport}/games response shape (sport_state, status_label, etc.)
$BaseUrl = if ($env:API_BASE_URL) { $env:API_BASE_URL.TrimEnd('/') } else { "https://api.parlaygorilla.com" }
Write-Host "Using $BaseUrl" -ForegroundColor Cyan

Write-Host "`n--- GET /api/sports ---" -ForegroundColor Yellow
$sports = Invoke-RestMethod -Uri "$BaseUrl/api/sports" -TimeoutSec 15
$first = $sports[0]
Write-Host "First sport keys: $($first.PSObject.Properties.Name -join ', ')"
Write-Host "Sample: slug=$($first.slug) sport_state=$($first.sport_state) status_label=$($first.status_label) is_enabled=$($first.is_enabled)"
if ($first.PSObject.Properties['policy_mode']) { Write-Host "policy_mode=$($first.policy_mode)" }

Write-Host "`n--- GET /api/sports/nfl/games (listMeta) ---" -ForegroundColor Yellow
$gamesResp = Invoke-RestMethod -Uri "$BaseUrl/api/sports/nfl/games" -TimeoutSec 15
Write-Host "sport_state=$($gamesResp.sport_state) status_label=$($gamesResp.status_label) games_count=$($gamesResp.games.Count)"
if ($gamesResp.PSObject.Properties['preseason_enable_days']) { Write-Host "preseason_enable_days=$($gamesResp.preseason_enable_days)" }
Write-Host "`nDone."
