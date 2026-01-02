# Running Database Migration on Render

## Method 1: Using Render Shell (Recommended)

1. **Go to Render Dashboard:**
   - Navigate to https://dashboard.render.com
   - Select your backend service (e.g., `parlay-gorilla-backend`)

2. **Open Shell:**
   - Click on "Shell" tab in the left sidebar
   - Or use the "Connect" button → "Open Shell"

3. **Run Migration:**
   ```bash
   cd backend  # If your backend code is in a subdirectory
   alembic upgrade head
   ```

4. **Verify:**
   ```bash
   alembic current
   ```
   Should show: `299b00a5cc58 (head)`

## Method 2: Using Render CLI

1. **Install Render CLI:**
   ```bash
   npm install -g render
   ```

2. **Login:**
   ```bash
   render login
   ```

3. **Run Migration via SSH:**
   ```bash
   render ssh <service-name>
   cd backend
   alembic upgrade head
   ```

## Method 3: Automatic Migration on Deploy

You can configure Render to automatically run migrations on deploy by adding a build command:

1. **Go to Render Dashboard → Your Backend Service → Settings**

2. **Update Build Command:**
   ```bash
   pip install -r requirements.txt && alembic upgrade head
   ```

3. **Or add to your `render.yaml`:**
   ```yaml
   services:
     - type: web
       name: parlay-gorilla-backend
       buildCommand: pip install -r requirements.txt && alembic upgrade head
       startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

## Method 4: Manual SQL (If Migration Fails)

If the migration fails, you can run the SQL manually:

1. **Go to Render Dashboard → PostgreSQL Service**

2. **Click "Connect" → "Connect via psql"**

3. **Run SQL:**
   ```sql
   -- Add Stripe columns to users table
   ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
   ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);
   
   -- Create indexes
   CREATE INDEX IF NOT EXISTS ix_users_stripe_customer_id ON users(stripe_customer_id);
   CREATE INDEX IF NOT EXISTS ix_users_stripe_subscription_id ON users(stripe_subscription_id);
   
   -- Update subscription_plans provider (optional - only if migrating from LemonSqueezy)
   UPDATE subscription_plans SET provider = 'stripe' WHERE provider = 'lemonsqueezy';
   
   -- Update subscriptions provider (optional - only if migrating from LemonSqueezy)
   UPDATE subscriptions SET provider = 'stripe' WHERE provider = 'lemonsqueezy';
   
   -- Update alembic version
   UPDATE alembic_version SET version_num = '299b00a5cc58';
   ```

## Verification

After migration, verify:

1. **Check columns exist:**
   ```sql
   SELECT column_name 
   FROM information_schema.columns 
   WHERE table_name = 'users' 
   AND column_name IN ('stripe_customer_id', 'stripe_subscription_id');
   ```

2. **Check indexes:**
   ```sql
   SELECT indexname 
   FROM pg_indexes 
   WHERE tablename = 'users' 
   AND indexname LIKE '%stripe%';
   ```

3. **Check migration version:**
   ```bash
   alembic current
   ```

## Troubleshooting

### "Connection refused" Error
- Ensure your Render PostgreSQL service is running
- Check `DATABASE_URL` environment variable is set correctly
- Verify you're using the Internal Database URL (not External)

### "Table already exists" Error
- The migration may have partially run
- Check current migration state: `alembic current`
- If needed, stamp to the correct version: `alembic stamp <revision>`

### "Permission denied" Error
- Ensure you have database admin permissions
- Check that the database user has ALTER TABLE permissions

### Migration Hangs
- Check Render service logs
- Verify database connection is stable
- Consider running during low-traffic period

## Pre-Migration Checklist

- [ ] Backup database (Render provides automatic backups)
- [ ] Verify `DATABASE_URL` is set correctly
- [ ] Check current migration state: `alembic current`
- [ ] Ensure no other migrations are running
- [ ] Review migration SQL in `299b00a5cc58_migrate_to_stripe_add_fields.py`

## Post-Migration Checklist

- [ ] Verify migration completed: `alembic current` shows `299b00a5cc58`
- [ ] Check columns exist in `users` table
- [ ] Verify indexes were created
- [ ] Test application startup
- [ ] Monitor logs for any errors

