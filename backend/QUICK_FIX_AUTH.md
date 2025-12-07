# Quick Fix for Registration 500 Error

## Problem
Getting 500 error when trying to register because:
1. Database table doesn't have `password_hash` column yet
2. OR `supabase_user_id` column is still NOT NULL

## Solution 1: Use SQLite (Quickest)

Edit `backend/.env`:
```env
USE_SQLITE=true
```

Then restart the backend. SQLite will recreate tables with the new schema automatically.

## Solution 2: Fix PostgreSQL Table

If using PostgreSQL, run this SQL:

```sql
-- Connect to your database
-- Then run:

-- Add password_hash column
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR;

-- Make supabase_user_id nullable
ALTER TABLE users ALTER COLUMN supabase_user_id DROP NOT NULL;
```

## Solution 3: Recreate Tables (Development Only)

If you don't have important data:

```sql
DROP TABLE IF EXISTS users CASCADE;
-- Then restart backend - tables will be recreated
```

## Solution 4: Run Migration Script

When PostgreSQL is running:
```bash
python scripts/fix_users_table.py
```

## Verify Fix

After fixing, try registering again. The backend will now:
- ✅ Accept users without Supabase
- ✅ Store password hashes
- ✅ Create JWT tokens

---

**Note**: The backend startup now automatically fixes the schema, but you need the database running first.

