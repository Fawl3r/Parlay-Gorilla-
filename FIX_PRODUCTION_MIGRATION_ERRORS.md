# Fix Production Migration Errors

## Issues Fixed

### 1. Missing `external_game_key` Column
**Error:** `column games.external_game_key does not exist`

**Root Cause:** Migration 037 (`037_add_live_scores_to_games.py`) hadn't run or failed silently.

**Fix Applied:**
- Updated migration 037 to use direct SQL queries for column existence checks
- Made migration fully idempotent - safe to run multiple times
- Added error handling for duplicate column errors

### 2. Missing `system_heartbeats` Table
**Error:** `relation "system_heartbeats" does not exist`

**Root Cause:** Migration 041 (`041_create_system_heartbeats.py`) hadn't run.

**Fix Applied:**
- Updated migration 041 to check table existence before creating
- Made migration fully idempotent
- Uses direct SQL queries for reliable table detection

## Next Steps

### Run Migrations in Render Shell

SSH into your Render service and run:

```bash
cd ~/project/src/backend
alembic upgrade head
```

This will:
1. Apply migration 037 (adds `external_game_key` column and other live score fields)
2. Apply migration 041 (creates `system_heartbeats` table)
3. Continue with any other pending migrations

### Expected Output

You should see:
```
INFO  [alembic.runtime.migration] Running upgrade ... -> 037_add_live_scores_to_games
INFO  [alembic.runtime.migration] Running upgrade 037_add_live_scores_to_games -> 038_create_parlay_legs_table
...
INFO  [alembic.runtime.migration] Running upgrade 040_create_parlay_feed_events -> 041_create_system_heartbeats
```

### Verification

After migrations complete, verify:

```sql
-- Check if external_game_key column exists
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'games' AND column_name = 'external_game_key';

-- Check if system_heartbeats table exists
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name = 'system_heartbeats';
```

## What Was Changed

### Migration 037 (`037_add_live_scores_to_games.py`)
- Now uses direct SQL queries (`information_schema.columns`) instead of SQLAlchemy inspector
- Checks column existence before adding
- Checks index existence before creating
- Handles duplicate errors gracefully

### Migration 041 (`041_create_system_heartbeats.py`)
- Now checks table existence using direct SQL query
- Handles duplicate table errors gracefully
- Fully idempotent

## Impact

After running migrations:
- ✅ `external_game_key` column will be added to `games` table
- ✅ `system_heartbeats` table will be created
- ✅ Settlement worker errors will be resolved
- ✅ Heartbeat worker errors will be resolved
- ✅ Score scraper service errors will be resolved

## Auto-Deploy

If Render auto-deploy is enabled, the code changes are already deployed. You just need to run the migrations manually in the Render shell.

If auto-deploy is disabled, trigger a manual deployment first, then run migrations.
