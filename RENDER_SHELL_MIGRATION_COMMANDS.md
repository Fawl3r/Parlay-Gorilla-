# Render Shell Migration Commands

If `alembic` command is not found, use Python module syntax:

## Option 1: Python Module Syntax (RECOMMENDED)

```bash
python -m alembic upgrade head
```

Or if Python 3 is required:

```bash
python3 -m alembic upgrade head
```

## Option 2: Check if Alembic is Installed

```bash
# Check if alembic is in requirements.txt
cat requirements.txt | grep alembic

# Check if it's installed
pip list | grep alembic

# If not installed, install it
pip install alembic
```

## Option 3: Use Full Path

If alembic is installed but not in PATH:

```bash
# Find where Python packages are installed
python -c "import alembic; print(alembic.__file__)"

# Or use pip to show location
pip show alembic
```

## Full Migration Command Sequence

```bash
# Navigate to backend directory (if not already there)
cd ~/project/src/backend

# Verify you're in the right place
ls -la alembic.ini

# Run migration using Python module
python -m alembic upgrade head

# Verify it worked - should see:
# INFO  [alembic.runtime.migration] Running upgrade ... -> 022_add_premium_usage_periods
```

## Troubleshooting

If `python -m alembic` also fails:

1. **Check Python version:**
   ```bash
   python --version
   python3 --version
   ```

2. **Check if requirements.txt includes alembic:**
   ```bash
   grep alembic requirements.txt
   ```
   
   If not, it should be added (we already added it in the fix).

3. **Install alembic manually:**
   ```bash
   pip install alembic psycopg2-binary
   ```

4. **Verify database connection:**
   ```bash
   python -c "from app.core.config import settings; print(settings.database_url[:50])"
   ```

## Expected Output

When migration runs successfully, you should see:

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 021_add_saved_parlay_results -> 022_add_premium_usage_periods, Add premium rolling-period usage counters to users
```

If you see "Target database is not up to date" or similar, the migration may have already run.



