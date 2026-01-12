# How to Get Your Production Database URL

## From Render Dashboard

1. **Log in to Render**: https://dashboard.render.com

2. **Navigate to your PostgreSQL service**:
   - Click on "PostgreSQL" in the left sidebar
   - Or find it in your services list (usually named something like `parlay-gorilla-postgres`)

3. **Get the Internal Database URL**:
   - In the PostgreSQL service dashboard, look for "Connections" section
   - Find "Internal Database URL" (this is the one you want for server-to-server connections)
   - It will look like: `postgresql://user:password@dpg-xxxx-a.oregon-postgres.render.com/parlaygorilla`

4. **Copy the URL**:
   - Click the copy button next to "Internal Database URL"
   - This is your `PROD_DATABASE_URL` for the sync script

## Alternative: From Environment Variables

If you have access to your Render backend service:

1. Go to your **Backend Web Service** in Render
2. Click on "Environment" tab
3. Look for `DATABASE_URL` variable
4. Copy that value

## Security Note

⚠️ **Important**: The production database URL contains sensitive credentials. Keep it secure:
- Don't commit it to git
- Don't share it publicly
- Use environment variables when possible
- Only use it for legitimate development/testing purposes

## Format

The URL should look like one of these formats:
```
postgresql://user:password@dpg-xxxx-a.oregon-postgres.render.com/parlaygorilla
postgres://user:password@dpg-xxxx-a.oregon-postgres.render.com/parlaygorilla
```

Both formats work - the sync script will automatically convert them to the correct async format.


