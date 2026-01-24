# Fix Migration 028 - Arcade Points Tables

## Problem
Migration `028_add_arcade_points_tables` fails because `arcade_points_events` table already exists in the database, but Alembic is trying to create it again.

## Solution Applied
✅ Updated migration `028_add_arcade_points_tables.py` to:
- Use try-except blocks to catch `ProgrammingError` for duplicate table/index errors
- Gracefully skip table/index creation if they already exist
- Make the migration fully idempotent

## Option 1: Re-run Migration (Recommended)

Since you're already in the Render shell, just re-run:

```bash
cd ~/project/src/backend
alembic upgrade head
```

The fixed migration will now handle the existing table gracefully.

## Option 2: Manually Mark Migration as Applied (If Option 1 Still Fails)

If the migration still fails, you can manually mark it as applied in the Alembic version table:

### Step 1: Check Current Alembic Version
```bash
cd ~/project/src/backend
alembic current
```

### Step 2: Connect to Database via psql
Go to Render Dashboard → Your PostgreSQL Service → Connect → Connect via psql

Or use the connection string from your backend service environment variables.

### Step 3: Check if Migration is Already Recorded
```sql
SELECT * FROM alembic_version;
```

### Step 4: If Migration 028 is NOT in the version table, insert it:
```sql
-- Only run this if 028_add_arcade_points_tables is NOT in alembic_version
INSERT INTO alembic_version (version_num) 
VALUES ('028_add_arcade_points_tables')
ON CONFLICT DO NOTHING;
```

### Step 5: Verify Tables Exist
```sql
-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('arcade_points_events', 'arcade_points_totals');

-- Check if indexes exist
SELECT indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename = 'arcade_points_events';
```

### Step 6: Re-run Migration
```bash
cd ~/project/src/backend
alembic upgrade head
```

## Option 3: Use Fixed Code and Deploy

1. **Commit the fixed migration:**
   ```bash
   git add backend/alembic/versions/028_add_arcade_points_tables.py
   git commit -m "Fix: Make migration 028 idempotent for existing tables"
   git push
   ```

2. **Trigger deployment on Render:**
   - Go to Render Dashboard → Your Backend Service
   - Click "Manual Deploy" → "Deploy latest commit"
   - Migrations will run automatically via `start.sh`

## Verification

After migration completes successfully:

```bash
# Check current version
alembic current

# Should show the latest migration head
# Example: 029_merge_arcade_points_and_weekly_free_limits (head)
```

## Expected Output

When migration runs successfully, you should see:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 027_add_parlay_fingerprint_to_verification_records -> 028_add_arcade_points_tables, Add arcade_points_events and arcade_points_totals tables.
INFO  [alembic.runtime.migration] Running upgrade 028_add_arcade_points_tables -> 029_merge_arcade_points_and_weekly_free_limits, Merge Alembic heads: arcade points tables + weekly free limits.
```

If tables already exist, the migration will skip creation and only ensure indexes exist.
