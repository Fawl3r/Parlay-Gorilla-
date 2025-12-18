# SportsRadar API Setup Guide

## Current Status - Trial Key Limitations

✅ **API Key Works** - The trial key is valid and functional

⚠️ **Limited Endpoints** - Trial version only provides access to:
- ✅ Schedule endpoints (`/games/{season}/{type}/schedule.json`)
- ✅ Week schedules (`/games/{season}/{type}/{week}/schedule.json`)
- ❌ Team profile endpoints (`/teams/{id}/profile.json`) - Returns 404
- ❌ Seasonal statistics (`/seasons/{season}/{type}/teams/{id}/statistics.json`) - Returns 404
- ❌ Game summaries/details - Returns 404

**Conclusion**: Trial keys provide schedule data only, not detailed team statistics.

## Current Implementation

- **Base URL**: Uses trial version (`/trial/v7/en` for NFL, `/trial/v8/en` for NBA, etc.)
- **Authentication**: API key passed as query parameter `api_key`
- **Working Endpoints** (Trial):
  - ✅ `/games/{season}/{type}/schedule.json` - Full season schedule
  - ✅ `/games/{season}/{type}/{week}/schedule.json` - Week schedule
- **Non-Working Endpoints** (Trial):
  - ❌ `/seasons/{season}/{season_type}/teams/{team_id}/statistics.json` - Returns 404
  - ❌ `/teams/{team_id}/profile.json` - Returns 404
  - ❌ `/games/{game_id}/summary.json` - Returns 404
- **Fallback Strategy**:
  1. Try SportsRadar seasonal statistics endpoint
  2. Try SportsRadar team profile endpoint
  3. Try SportsRadar schedule endpoint (for basic team info)
  4. Fall back to ESPN scraper (provides PPG/PAPG stats)

## ESPN Fallback Status

✅ **Working**: ESPN fallback is successfully providing:
- Team records (wins/losses)
- Points per game (PPG)
- Points allowed per game (PAPG)

Note: ESPN doesn't provide yards per game in their free team endpoint.

## To Get Full SportsRadar Functionality

**Current Situation**: Trial key works but only provides schedule data, not team statistics.

**To Get Team Statistics**:
1. **Upgrade to Paid Plan**: 
   - Trial keys don't provide access to team statistics endpoints
   - Paid plans unlock:
     - Team profiles
     - Seasonal statistics
     - Game summaries and play-by-play
     - Player statistics
   
2. **Contact SportsRadar**:
   - Visit https://developer.sportradar.com/
   - Check pricing for your use case
   - Trial keys are intentionally limited to schedule data only

3. **Current Workaround**:
   - System automatically falls back to ESPN for team statistics
   - ESPN provides PPG and PAPG (points stats)
   - Schedule data from SportsRadar can be used for game times and matchups

## Documentation References

- [NFL API Overview](https://developer.sportradar.com/football/reference/nfl-overview)
- [NBA API Overview](https://developer.sportradar.com/basketball/reference/nba-overview)
- [NHL API Overview](https://developer.sportradar.com/ice-hockey/reference/nhl-overview)
- [Soccer API Overview](https://developer.sportradar.com/soccer/reference/soccer-api-overview)

## Current Behavior

The system gracefully falls back to ESPN when SportsRadar fails, so the application continues to function. Stats are being fetched successfully from ESPN, though with limited detail (points stats only, no yards).

