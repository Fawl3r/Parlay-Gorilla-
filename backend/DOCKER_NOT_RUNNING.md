# Docker Not Running - Using SQLite Instead

## ✅ Quick Fix Applied

Since Docker Desktop is not running, I've switched the backend to use **SQLite** for local development.

## What Changed

- `USE_SQLITE=true` in `backend/.env`
- Backend will now use SQLite database file: `backend/parlay_gorilla.db`
- No Docker required!

## Next Steps

1. **Restart the backend server**:
   ```bash
   # Stop current backend (Ctrl+C)
   # Then restart:
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Try registering again** - it should work now!

## When You Want PostgreSQL

1. **Start Docker Desktop**
2. **Edit `backend/.env`**:
   ```env
   USE_SQLITE=false
   ```
3. **Start PostgreSQL**:
   ```bash
   docker-compose up -d postgres
   ```
4. **Restart backend**

## SQLite vs PostgreSQL

- **SQLite**: Perfect for development, no setup needed
- **PostgreSQL**: Better for production, supports more features

Both work fine for this app! SQLite is actually faster for local development.

---

**Status**: ✅ Switched to SQLite - ready to test!

