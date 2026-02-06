# Injury Reporting

## Overview

Game analysis pages show injury data for both teams. Injuries are sourced in order:

1. **API-Sports cache (DB)** – If we have a fresh cached injury payload for the team (by sport + team ID), we use it and convert to our canonical format.
2. **ESPN fallback** – If cache is missing or stale, we resolve the team by name via the ESPN teams API and fetch injuries by team ID or injuries URL. No team abbreviation mapping is required.

## Data flow

- **StatsScraperService.get_injury_report(team_name, league)**  
  - Checks in-memory cache (15 min TTL).  
  - Tries API-Sports DB (ApisportsInjuryRepository) by sport key + team ID from team_mapper.  
  - If missing: uses **EspnTeamResolver** to resolve `team_name` to a **ResolvedTeamRef** (team ID, injuries URL), then **EspnInjuriesClient** to fetch and parse injuries.  
  - Returns a canonical-style dict: `key_players_out`, `injury_summary`, `impact_assessment`, `injury_severity_score`, `total_injured`, `unit_counts`.

- **EspnTeamResolver**  
  - Fetches `{ESPN_BASE}/teams` for the sport, matches `team_name` against displayName/shortDisplayName/nickname (normalized + scored).  
  - Caches each resolved ref for **24 hours** (Redis if configured, else in-memory TTL).  
  - Logs success/failure; optionally emits Telegram alert `injuries.espn_resolve_failed` when resolution fails (if alerts enabled).

- **EspnInjuriesClient**  
  - Uses `ResolvedTeamRef.injuries_url` or `{base}/teams/{team_id}/injuries`.  
  - Parses response with the same logic as the legacy ESPN scraper (key players, severity, summary).

## Caching

- **Team ref cache**: Key `espn:teamref:{sport}:{normalized_team_name}`, TTL 24h. Reduces repeated calls to the ESPN teams list.
- **Injury report cache**: In-memory in StatsScraperService, key `injuries:{team_name}:{league}`, TTL 15 min.

## Supported sports / leagues

ESPN base URLs and team resolution are configured for:

- NFL, NBA, WNBA, NHL, MLB  
- Soccer: MLS, EPL, UCL, LaLiga, Serie A, Bundesliga  

Sport/league codes are mapped in `get_injury_report` (e.g. NHL, EPL, MLS). Missing leagues return a placeholder message and no crash.

## Known limitations

- ESPN API is undocumented and may change; team list and injuries endpoints are best-effort.
- Soccer injury coverage on ESPN varies by league.
- If ESPN resolution or fetch fails, the analysis still renders with an empty/placeholder injury section and a clear log (and optional Telegram alert).

## Debugging in production

- **Logs**: Look for `"ESPN injuries resolved"` (success, with `sport`, `team_name`, `match_method`, `confidence`) or `"ESPN team resolve failed"` / `"ESPN injuries fetch failed"` (failure).
- **Telegram**: If `TELEGRAM_ALERTS_ENABLED` is true, event `injuries.espn_resolve_failed` is emitted on resolve failure (payload: `sport`, `team_name`, `reason`).
- **Cache**: Redis keys `espn:teamref:*` hold resolved team refs for 24h. Clearing them forces fresh resolution on next request.
