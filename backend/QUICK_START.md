# 🚀 Quick Start Guide

## Local Development (5 minutes)

### 1. Start PostgreSQL
```bash
cd backend
docker-compose up -d postgres
```

### 2. Configure Environment
Edit `backend/.env`:
```env
USE_SQLITE=false
DATABASE_URL=postgresql+asyncpg://devuser:devpass@localhost:5432/parlaygorilla
THE_ODDS_API_KEY=your_key
OPENAI_API_KEY=your_key
```

### 3. Run Migrations
```bash
cd backend
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### 4. Populate Database
```bash
python fetch_live_games.py
```

### 5. Start Backend
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 6. Start Frontend
```bash
cd frontend
npm run dev
```

## Production (Neon)

### 1. Get Neon Connection String
- Go to https://neon.tech
- Create project
- Copy connection string

### 2. Set Environment
```bash
export NEON_DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/parlaygorilla?sslmode=require"
export ENVIRONMENT=production
```

### 3. Deploy
```bash
alembic upgrade head
python fetch_live_games.py
```

## Common Commands

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Check status
alembic current

# View history
alembic history
```

## API Testing

```bash
# Health check
curl http://localhost:8000/health

# Generate parlay
curl -X POST http://localhost:8000/api/parlay/suggest \
  -H "Content-Type: application/json" \
  -d '{"num_legs": 5, "risk_profile": "balanced", "sport": "NFL"}'

# Get team stats
curl http://localhost:8000/api/team-stats/nfl/Kansas%20City%20Chiefs

# Trigger scraper
curl -X POST http://localhost:8000/api/scraper/update
```

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs parlaygorilla-db

# Restart container
docker-compose restart postgres
```

### Migration Issues
```bash
# Reset database (WARNING: deletes all data)
alembic downgrade base
alembic upgrade head
```

### Background Jobs Not Running
- Check `ENABLE_BACKGROUND_JOBS=true` in `.env`
- Check scheduler logs in console output
- Verify database connection

## File Locations

- **Migrations**: `backend/alembic/versions/`
- **Models**: `backend/app/models/`
- **API Routes**: `backend/app/api/routes/`
- **Workers**: `backend/app/workers/`
- **Config**: `backend/app/core/config.py`
- **Docker**: `backend/docker-compose.yml`

## Next Steps

1. ✅ Database setup complete
2. ✅ API routes ready
3. ✅ Background workers configured
4. 🔄 Test all endpoints
5. 🔄 Add SEO features
6. 🔄 Deploy to production

---

**Need Help?** Check:
- `BUILD_SYSTEM.md` - Full architecture guide
- `MIGRATION_GUIDE.md` - Database migration details
- `IMPLEMENTATION_SUMMARY.md` - Complete feature list

