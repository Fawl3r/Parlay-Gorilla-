# Sync User from Production to Local

This script allows you to copy your production user account to your local development database so you can login with the same credentials.

## Prerequisites

1. **Production Database URL**: Get this from your Render dashboard or production environment
   - Format: `postgresql://user:password@host:port/database`
   - Or: `postgresql+asyncpg://user:password@host:port/database`

2. **Local Database URL**: Your local PostgreSQL connection string
   - Format: `postgresql://devuser:devpass@localhost:5432/parlaygorilla`
   - Or check your `backend/.env` file for `DATABASE_URL`

3. **Your Email**: The email address of the user account you want to sync

## Usage

### Option 1: Command Line Arguments

```bash
cd backend
python scripts/sync_user_from_production.py \
  --email your@email.com \
  --prod-db-url "postgresql://user:pass@prod-host:5432/dbname" \
  --local-db-url "postgresql://devuser:devpass@localhost:5432/parlaygorilla" \
  --overwrite
```

### Option 2: Environment Variables

```bash
# Set environment variables
export PROD_DATABASE_URL="postgresql://user:pass@prod-host:5432/dbname"
export LOCAL_DATABASE_URL="postgresql://devuser:devpass@localhost:5432/parlaygorilla"
export USER_EMAIL="your@email.com"

# Run the script
cd backend
python scripts/sync_user_from_production.py --overwrite
```

### Option 3: Windows PowerShell

```powershell
$env:PROD_DATABASE_URL="postgresql://user:pass@prod-host:5432/dbname"
$env:LOCAL_DATABASE_URL="postgresql://devuser:devpass@localhost:5432/parlaygorilla"
$env:USER_EMAIL="your@email.com"

cd backend
python scripts/sync_user_from_production.py --overwrite
```

## What Gets Synced

The script copies all user data including:
- Email and username
- Password hash (so you can login with the same password)
- Account number
- Role and plan
- Subscription status
- Credit balance
- Free parlay usage
- Profile information (display name, avatar, bio, etc.)
- Preferences (favorite teams, sports, risk profile)
- Timestamps (created_at, updated_at, last_login)

## Flags

- `--overwrite`: If the user already exists in local database, replace it with production data
- Without `--overwrite`: Script will fail if user already exists (safety check)

## Example Output

```
🔄 Syncing user: your@email.com
   Production DB: prod-host:5432/dbname
   Local DB: localhost:5432/parlaygorilla
✅ Found user in production:
   ID: 123e4567-e89b-12d3-a456-426614174000
   Email: your@email.com
   Username: yourusername
   Role: user
   Plan: elite
   Has password: Yes
➕ Creating new user in local database...
✅ User created successfully!
```

## Troubleshooting

1. **"User not found in production database"**
   - Double-check your email address
   - Verify production database URL is correct
   - Ensure you have network access to production database

2. **"User already exists in local database"**
   - Use `--overwrite` flag to replace existing user
   - Or delete the user from local database first

3. **Connection errors**
   - Verify database URLs are correct
   - Check that local PostgreSQL is running
   - Ensure production database allows connections from your IP

4. **Account number conflicts**
   - The script uses the same account_number from production
   - If there's a conflict, the script will handle it automatically

## Security Note

This script copies the password hash, not the plain password. This means:
- ✅ You can login with your production password
- ✅ The password hash is secure (cannot be reversed)
- ⚠️ Make sure to keep your production database URL secure

