# Running Database Migration - Quick Setup

## Option 1: Use SQLite (Easiest for Local Development)

1. **Create or update `.env` file in `backend/` directory:**

```bash
# Database Configuration
USE_SQLITE=true
DATABASE_URL=sqlite:///parlay_gorilla.db  # Not used when USE_SQLITE=true, but required

# Other required settings
ENVIRONMENT=development
DEBUG=true
THE_ODDS_API_KEY=your_key_here
OPENAI_ENABLED=false  # Set to false if you don't have OpenAI key for testing
```

2. **Run migration:**
```bash
cd backend
alembic upgrade head
```

## Option 2: Use PostgreSQL (Production-like)

### Start PostgreSQL Locally

**Windows:**
- Install PostgreSQL from https://www.postgresql.org/download/windows/
- Start PostgreSQL service
- Or use Docker: `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres`

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux:**
```bash
sudo systemctl start postgresql
```

### Configure Database

1. **Create database:**
```sql
CREATE DATABASE parlaygorilla;
```

2. **Update `.env` file:**
```bash
USE_SQLITE=false
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/parlaygorilla
```

3. **Run migration:**
```bash
cd backend
alembic upgrade head
```

## Option 3: Use Remote Database (Render/Production)

1. **Get connection string from Render Dashboard:**
   - Go to your PostgreSQL service
   - Copy "Internal Database URL"

2. **Update `.env` file:**
```bash
USE_SQLITE=false
DATABASE_URL=postgresql://user:password@dpg-xxx-a.oregon-postgres.render.com/parlaygorilla
```

3. **Run migration:**
```bash
cd backend
alembic upgrade head
```

## Troubleshooting

### "Connection refused" Error
- **SQLite:** Set `USE_SQLITE=true` in `.env`
- **PostgreSQL:** Ensure PostgreSQL is running (`pg_isready` or check service status)
- **Remote:** Verify connection string is correct

### "DATABASE_URL is required" Error
- Add `DATABASE_URL` to `.env` (even if using SQLite, it's required by config validation)

### Migration Fails
- Check database connection first
- Verify you have write permissions
- For SQLite, ensure directory is writable




