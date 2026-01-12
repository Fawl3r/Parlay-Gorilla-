# Quick Start: Sync Your Production User to Local

## Step 1: Get Your Production Database URL

1. Go to **Render Dashboard**: https://dashboard.render.com
2. Click on **PostgreSQL** service (usually named `parlay-gorilla-postgres`)
3. Find **"Internal Database URL"** in the Connections section
4. Copy the URL (looks like: `postgresql://user:password@dpg-xxxx-a.oregon-postgres.render.com/parlaygorilla`)

## Step 2: Run the Sync Script

Open PowerShell in the `backend` directory and run:

```powershell
# Set your production database URL (replace with your actual URL)
$env:PROD_DATABASE_URL="postgresql://user:password@dpg-xxxx-a.oregon-postgres.render.com/parlaygorilla"

# Set your email
$env:USER_EMAIL="your@email.com"

# Local database is already configured (postgresql://devuser:devpass@localhost:5432/parlaygorilla)
# So you don't need to set LOCAL_DATABASE_URL unless you want to override it

# Run the sync script
python scripts/sync_user_from_production.py --overwrite
```

## Step 3: Verify

Try logging in at http://localhost:3000 with your production email and password!

## Troubleshooting

**"User not found in production database"**
- Double-check your email address
- Verify the production database URL is correct
- Make sure you're using the "Internal Database URL" (not External)

**"Connection refused"**
- Make sure your local PostgreSQL is running: `docker ps | findstr postgres`
- If not running: `docker-compose -f backend/docker-compose.yml up -d postgres`

**"User already exists"**
- Use `--overwrite` flag to replace the existing user
- Or manually delete the user from local database first


