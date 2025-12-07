# Starting Docker Desktop for PostgreSQL

## Step 1: Start Docker Desktop

1. **Open Docker Desktop** from your Start menu or desktop
2. **Wait for it to fully start** (you'll see "Docker Desktop is running" in the system tray)
3. This may take 1-2 minutes on first start

## Step 2: Verify Docker is Running

```bash
docker ps
```

You should see an empty list (no error). If you get an error, Docker isn't ready yet.

## Step 3: Start PostgreSQL

```bash
cd backend
docker-compose up -d postgres
```

This will:
- Download PostgreSQL image (first time only)
- Start PostgreSQL container
- Create database `parlaygorilla`
- Expose on port 5432

## Step 4: Verify PostgreSQL is Running

```bash
docker ps
```

You should see a container named `parlaygorilla-db` or similar.

## Step 5: Restart Backend

Restart your backend server - it will now connect to PostgreSQL and automatically fix the users table schema.

## Troubleshooting

### "Docker Desktop is not running"
- Make sure Docker Desktop is actually started (check system tray)
- Wait a few more seconds for it to fully initialize

### "Cannot connect to Docker daemon"
- Docker Desktop is still starting up
- Wait 30-60 seconds and try again

### Port 5432 already in use
- Another PostgreSQL instance is running
- Stop it or change the port in `docker-compose.yml`

### Container won't start
```bash
# Check logs
docker-compose logs postgres

# Remove and recreate
docker-compose down
docker-compose up -d postgres
```

---

**Once Docker is running, PostgreSQL will start automatically and the registration will work!**

