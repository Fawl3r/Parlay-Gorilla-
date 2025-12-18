# Backend Crash Troubleshooting Guide

## Quick Fixes

### 1. Check the Backend Window
When `restart-all.bat` runs, a window titled **"F3 Backend"** should open. **Don't close it!** This window shows error messages if the backend crashes.

### 2. Run Diagnostics
```powershell
cd backend
.\diagnose-startup.ps1
```

This will check:
- Python installation
- Required dependencies
- .env file configuration
- Port availability
- App import capability

### 3. Common Issues and Solutions

#### Issue: Backend window closes immediately
**Cause**: Usually a Python import error or missing dependency

**Solution**:
```powershell
cd backend
pip install -r requirements.txt
```

#### Issue: "Module not found" errors
**Cause**: Missing Python packages

**Solution**:
```powershell
cd backend
pip install uvicorn fastapi sqlalchemy pydantic
```

#### Issue: "Port 8000 already in use"
**Cause**: Another process is using port 8000

**Solution**:
```powershell
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

Or use the diagnostic script:
```powershell
cd backend
.\diagnose-startup.ps1
```

#### Issue: Database connection error
**Cause**: Missing or incorrect `DATABASE_URL` in `.env`

**Solution**:
1. Copy `.env.example` to `.env` if missing
2. Configure `DATABASE_URL` in `.env`
3. Ensure database is accessible

#### Issue: Missing .env file
**Cause**: No configuration file

**Solution**:
```powershell
cd backend
Copy-Item .env.example .env
# Then edit .env with your configuration
```

### 4. Manual Start (for debugging)

Start the backend manually to see full error messages:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

This will show you the exact error message if something fails.

### 5. Check Logs

If the backend starts but then crashes, check:
- The "F3 Backend" window for error messages
- Windows Event Viewer for system errors
- Python traceback in the backend window

### 6. Verify Backend is Running

After starting, test the backend:
```powershell
# In PowerShell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing

# Or open in browser
# http://127.0.0.1:8000/health
# http://127.0.0.1:8000/docs
```

### 7. Updated restart-all.ps1

The `restart-all.ps1` script has been updated with:
- ✅ Prerequisite checks before starting
- ✅ Better error messages
- ✅ Health check verification
- ✅ Clearer warnings if backend doesn't start

The script will now:
1. Check for Python and dependencies
2. Verify .env file exists
3. Start backend in a visible window
4. Wait and verify backend responds
5. Show clear error messages if it fails

### Still Having Issues?

1. **Run diagnostics**: `.\diagnose-startup.ps1`
2. **Start manually**: See error messages directly
3. **Check the window**: The "F3 Backend" window shows all errors
4. **Review .env**: Ensure all required variables are set



