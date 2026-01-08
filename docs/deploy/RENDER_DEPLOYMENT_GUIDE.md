# 🚀 Render Deployment Guide

This guide ensures your data is stored remotely and ready for Render deployment.

**Note:** This project is designed to run **fully on Render**:
- **Frontend (Next.js)**: Render Web Service (Node)
- **Backend (FastAPI)**: Render Web Service (Python)
- **Database (PostgreSQL)**: Render PostgreSQL
- **Redis**: Render Key Value

## 📊 Current Database Status

Run this to check your database configuration:

```bash
python scripts/verify_remote_database.py
```

## ✅ Step 1: Create Render Services (Recommended)

Use the repo’s root `render.yaml` Blueprint. It will create:
- Render PostgreSQL (`parlay-gorilla-postgres`)
- Render Key Value (`parlay-gorilla-redis`)
- Backend web service (`parlay-gorilla-backend`)
- Frontend web service (`parlay-gorilla-frontend`)

## ✅ Step 2: Update Local .env File

Edit `backend/.env` (local dev only):

```env
# Disable SQLite
USE_SQLITE=false

# Use a database (local dev example shown)
DATABASE_URL=postgresql+asyncpg://devuser:devpass@localhost:5432/parlaygorilla

# Set environment
ENVIRONMENT=development
```

**Important:**
- Add `+asyncpg` after `postgresql` for async support
- For remote Render databases, use SSL if required by your connection string.
- Never commit `.env` file to git

## ✅ Step 3: Run Migrations on Remote Database

```bash
cd backend

# This will create all tables on your remote database
alembic upgrade head
```

## ✅ Step 4: Backfill Data to Remote Database

```bash
# This will populate 2024 and 2025 data for all sports
python scripts/backfill_all_sports_data.py
```

Or use the API endpoint:

```bash
curl -X POST "http://localhost:8000/api/games/backfill-all-sports"
```

## ✅ Step 5: Verify Remote Database

```bash
python scripts/verify_remote_database.py
```

You should see:
- ✓ REMOTE DATABASE CONFIRMED
- Server Address: (remote IP, not localhost)
- Database contains records

## ✅ Step 6: Configure Render Environment Variables

In Render dashboard, add these environment variables:

### Required:

```
ENVIRONMENT=production
THE_ODDS_API_KEY=your_key
OPENAI_API_KEY=your_key
FRONTEND_URL=https://your-frontend.onrender.com
APP_URL=https://your-frontend.onrender.com
BACKEND_URL=https://your-backend.onrender.com
JWT_SECRET=your-super-secret-key-change-in-production
```

**Notes:**
- If you deploy using the repo's root `render.yaml` Blueprint, **`DATABASE_URL` and `REDIS_URL` are wired automatically** from Render PostgreSQL + Render Key Value.
- `REDIS_URL` is required in production to enable the distributed Odds API cache and scheduler leader election.

### Optional (but recommended):

```
OPENAI_ENABLED=true
SPORTSRADAR_API_KEY=your_key
RESEND_API_KEY=your_key  # enables verification + password reset emails
```

## ✅ Step 7: Deploy to Render

1. **Connect your GitHub repository** to Render
2. **Create a new Web Service**
3. **Configure:**
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Add Environment Variables** (from Step 6)
5. **Deploy**

**Note:** If you deploy using the repo’s root `render.yaml` Blueprint, the backend start command already runs migrations for you.

## 🔍 Verification After Deployment

Once deployed, verify your remote database is being used:

```bash
# Check health endpoint
curl https://your-app.onrender.com/health

# Check if data is accessible
curl https://your-app.onrender.com/api/sports/nfl/games
```

## 📝 Important Notes

1. **Data Persistence**: All your sports data (games, stats, results, analyses) is stored in PostgreSQL, which persists across deployments.

2. **Local vs Remote**:
   - Local development: Can use local PostgreSQL or SQLite
   - Production (Render): MUST use remote PostgreSQL

3. **Database Migrations**: `alembic upgrade head` is used for supplemental schema changes. The app also runs `create_all` on startup in dev/test.

4. **Backfill Once**: After setting up remote database, run backfill once to populate historical data. Future fetches will only get new data.

## 🆘 Troubleshooting

### "Connection refused" or "Database not found"
- Verify DATABASE_URL is correct
- Check if database allows connections from Render's IPs
- Ensure SSL mode is set: `?sslmode=require`

### "Table does not exist"
- Run migrations: `alembic upgrade head`
- Check if migrations ran successfully

### "No data showing"
- Run backfill script to populate data
- Check if backfill completed successfully
- Verify data exists in remote database using `verify_remote_database.py`

### "SQLite detected"
- Set `USE_SQLITE=false` in .env
- Ensure DATABASE_URL points to PostgreSQL (not SQLite file)

## ✅ Checklist Before Deploying

- [ ] Render PostgreSQL database created (or created via `render.yaml`)
- [ ] USE_SQLITE=false in .env
- [ ] Migrations run on remote database (`alembic upgrade head`)
- [ ] Backfill completed (`python scripts/backfill_all_sports_data.py`)
- [ ] Verified remote database connection (`python scripts/verify_remote_database.py`)
- [ ] All environment variables set in Render dashboard
- [ ] JWT_SECRET changed from default value
- [ ] Tested locally with remote database connection

Once all checkboxes are complete, you're ready to deploy to Render! 🚀


