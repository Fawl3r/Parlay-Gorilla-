# Project Status

## Current state
SHIP

## Active feature
`/app` (Dashboard → Games / "Intelligence Overview") matchup list quality:
- No duplicate matchups rendered
- Prefer the odds-backed row when multiple sources exist (so Win Prob renders)

## Today's focus
Fix duplicate matchup rows caused by cross-provider start-time drift (schedule vs odds) so the UI keeps only the best (odds-backed) entry per matchup.

## Done condition
- `/app` Games table shows **one row per matchup**
- For duplicates, the remaining row is the one with **odds + Win Prob**
