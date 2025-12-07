# Database Migration Guide

## Quick Start with Docker PostgreSQL

### 1. Start PostgreSQL Container

```bash
docker-compose up -d postgres
```

This starts PostgreSQL on `localhost:5432` with:
- User: `devuser`
- Password: `devpass`
- Database: `parlaygorilla`

### 2. Update Environment

Edit `.env`:
```env
USE_SQLITE=false
DATABASE_URL=postgresql+asyncpg://devuser:devpass@localhost:5432/parlaygorilla
```

### 3. Run Migration

```bash
# Create initial migration
alembic revision --autogenerate -m "initial"

# Apply migration
alembic upgrade head
```

Or use the helper script:
```bash
python scripts/migrate_to_postgres.py
```

### 4. Populate with Data

```bash
python fetch_live_games.py
```

## Production Setup (Neon)

### 1. Create Neon Project

1. Go to https://neon.tech
2. Create new project
3. Copy connection string

### 2. Configure Production

Edit `.env`:
```env
ENVIRONMENT=production
NEON_DATABASE_URL=postgresql://user:pass@ep-xxxxx.us-east-2.aws.neon.tech/parlaygorilla?sslmode=require
```

### 3. Deploy Migrations

```bash
# Set production database URL
export DATABASE_URL=$NEON_DATABASE_URL

# Run migrations
alembic upgrade head
```

## Alembic Commands

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Folder Structure

```
backend/
├── alembic/              # Migration scripts
│   ├── versions/         # Migration files
│   └── env.py           # Alembic configuration
├── alembic.ini          # Alembic settings
├── app/
│   ├── models/         # SQLAlchemy models
│   ├── api/            # API routes
│   ├── services/       # Business logic
│   ├── workers/        # Background workers
│   └── database/       # Database session
└── docker-compose.yml  # Docker setup
```

