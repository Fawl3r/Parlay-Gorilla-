# Grant Lifetime Membership on Production

## Quick Method: Render Shell (Recommended)

1. **Go to Render Dashboard:**
   - Visit: https://dashboard.render.com
   - Login if needed

2. **Navigate to Backend Service:**
   - Click: **Services** → `parlay-gorilla-backend`

3. **Open Shell:**
   - Click: **Shell** tab (or "Open Shell" button)
   - This opens an interactive terminal with production environment

4. **Run the Script:**
   ```bash
   python scripts/grant_lifetime_membership.py Fawl3r85@gmail.com
   ```

5. **Verify Success:**
   - Should see: `✅ Successfully granted lifetime membership!`
   - Check: `User plan updated to: elite`
   - Check: `Is Lifetime: True`

## Alternative: Local with Production DATABASE_URL

If you prefer to run locally, you'll need the production DATABASE_URL:

1. **Get Production DATABASE_URL:**
   - Go to Render Dashboard
   - Navigate to: **Databases** → `parlay-gorilla-postgres`
   - Click: **Connections** tab
   - Copy the **Internal Database URL** (starts with `postgresql://`)

2. **Run Locally:**
   ```bash
   cd backend
   $env:DATABASE_URL="postgresql://user:pass@host/db"  # PowerShell
   # OR
   export DATABASE_URL="postgresql://user:pass@host/db"  # Bash
   
   python scripts/grant_lifetime_membership.py Fawl3r85@gmail.com
   ```

## What the Script Does

- Finds user by email (case-insensitive)
- Checks if user already has lifetime membership
- Creates a new lifetime subscription with:
  - `is_lifetime=True`
  - `current_period_end=None` (no expiration)
  - `plan="elite"`
  - `status="active"`
- Updates user record:
  - `plan="elite"`
  - `subscription_plan="elite"`
  - `subscription_status="active"`

## Verification

After running, verify the user has lifetime access:
- User should see "Lifetime" or "Elite" plan in their account
- No subscription expiration date
- Full premium features access

