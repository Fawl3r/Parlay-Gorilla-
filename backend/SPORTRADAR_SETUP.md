# Sports Data Source (SportsRadar Removed)

**SportsRadar has been removed** from Parlay Gorilla. The primary sports data source is now **API-Sports** (api-sports.io).

- **Primary:** API-Sports — schedules, stats, standings, results, form
- **Fallback:** ESPN — when API-Sports data is unavailable
- **Odds & scheduling:** The Odds API (primary for odds and game list)

See:
- [API_SPORTS_USAGE_GUIDE.md](docs/API_SPORTS_USAGE_GUIDE.md) for integration details
- [API_SPORTS_INTEGRATION_STATUS.md](API_SPORTS_INTEGRATION_STATUS.md) for status

Environment: set `API_SPORTS_API_KEY` for sports data; leave blank to rely on ESPN fallback.
