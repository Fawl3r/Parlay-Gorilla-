# Backfill Scripts and Scheduling

## Scripts
- `scripts/sequential_backfill.py`  
  Runs backfill sequentially (one sport at a time) to avoid SQLite locks. It checks progress, skips completed seasons, and processes only what’s missing.

- `scripts/check_backfill_progress.py`  
  Shows games processed per sport/season and ATS/O/U coverage.

## How to run manually
```bash
cd backend
PYTHONPATH=. python scripts/sequential_backfill.py
```

## Scheduling (run once every 24h after quotas reset)

### Windows Task Scheduler
1. Task -> Create Basic Task
2. Trigger: Daily (e.g., 2 AM)
3. Action: Start a program  
   - Program: `powershell.exe`  
   - Args: `-NoProfile -ExecutionPolicy Bypass -Command "cd C:\F3 Apps\F3 Parlay Gorilla\backend; $env:PYTHONPATH='.'; python scripts\sequential_backfill.py"`

### Linux cron
```
0 2 * * * cd /path/to/backend && PYTHONPATH=. /usr/bin/python scripts/sequential_backfill.py >> /var/log/backfill.log 2>&1
```

### Notes
- Runs sports sequentially; safe for SQLite.
- Skips seasons that already meet the completion threshold (~80% of expected games).
- If you move to Postgres, you can still use the same script; locking issues will be reduced.

### Troubleshooting
- If you see `database is locked`, rerun once at a time (the script already retries commits/flushes).  
- Check progress: `PYTHONPATH=. python scripts/check_backfill_progress.py`  
- Check backend logs for `[SEQ]` and `[ATS/OU]` messages.




