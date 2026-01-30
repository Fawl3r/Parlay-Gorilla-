# Full-Article Analysis: Roster Policy

## Only current matchup-team players

Full-game analysis articles may mention **only players who are currently on the rosters of the two teams in the matchup** (home + away) for the game's season.

- **Why:** Mentioning players who have moved (e.g. a former Seahawk in a Seahawks preview) is inaccurate and confuses users.
- **How:** The allowlist is built from cached API-Sports rosters for the game's home and away teams and the **game's season** (date-aware). Before building the allowlist, rosters for those two teams are refreshed so the cache reflects current rosters (post-trades, moves).
- **Where:** `RosterContextBuilder` builds the allowlist; `FullArticleJobRunner` calls `ensure_rosters_for_game()` then `get_allowed_player_names()`. The LLM is given the allowlist in the system prompt; `AllowedPlayerNameEnforcer` redacts any other player names in the generated text.

If rosters are missing or teams cannot be mapped to API-Sports IDs, the allowlist is empty and **no** specific player names are allowed (all player-name patterns are redacted).

## Key Players: roster mismatch protection

The **Key Players** block (UGIE v2) fails closed when roster binding is incomplete or inconsistent. If the allowlist is non-empty but per-team lists do not match the game's home/away (e.g. cached rosters for different team IDs), the block returns `status="unavailable"` with `reason="roster_team_mismatch"` and **zero** players. This prevents wrong-team names from appearing in the UI.

## Debugging

When `ensure_rosters_for_game()` runs, one log line reports **home_roster_age_seconds** and **away_roster_age_seconds** (seconds since roster was last fetched; `None` if missing). Correlate with **redaction_count** (in article metadata / `article_redaction_applied` log):

- **High redaction_count + fresh rosters** → model overreaching (mentioning players not on allowlist).
- **High redaction_count + stale rosters** → refresh cadence or quota issue; rosters not updating.
