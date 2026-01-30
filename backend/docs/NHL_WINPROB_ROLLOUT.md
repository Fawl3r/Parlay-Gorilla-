# NHL Win Probability Rollout (Post-Deploy)

After deploying the API-Sports client and refresh-service fixes, run these steps so NHL analyses get real stats and win probabilities vary (no longer stuck at 51/49).

## 1. Trigger API-Sports refresh (admin)

As an admin, call once:

```http
POST /api/admin/apisports/refresh
Authorization: Bearer <admin_token>
```

This populates standings and team stats for active sports (including NHL). The scheduled job will then keep data fresh every 60 minutes.

## 2. Regenerate key NHL analyses

For a few upcoming NHL games, force-regenerate analyses so the new stats are used:

```http
POST /api/analysis/generate
Content-Type: application/json
Authorization: Bearer <token>

{
  "game_id": "<nhl_game_id>",
  "force_regenerate": true
}
```

Use game IDs from your games/analysis list for NHL matchups you care about.

## 3. Verify

- Hit several NHL analysis detail endpoints; confirm `model_win_probability.home_win_prob` (and away) **vary** by matchup (not all 0.5149 / 0.4851).
- Confirm `opening_summary` is no longer universally "51% vs 49%" for NHL.
