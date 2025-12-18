# Backend Server Startup Guide

## Quick Start

### Option 1: Use the PowerShell Script (Recommended for PowerShell)
```powershell
cd backend
.\start-server.ps1
```

### Option 2: Use the Batch Script (Works in CMD or PowerShell)
```cmd
cd backend
.\start-server.bat
```

**Note for PowerShell users**: You must use `.\` prefix when running batch files:
```powershell
.\start-server.bat
```

### Option 3: Direct Command (PowerShell)
```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Option 4: Direct Command (CMD)
```cmd
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Why Your Command Didn't Work

In PowerShell, you cannot run batch files directly by name. You must use:
- `.\start-server.bat` (relative path with `.\` prefix)
- Or `cmd /c start-server.bat` (run via CMD)

## Verification

Once the server starts, you should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Test the Server

Open in browser or use curl:
- **API Docs**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health
- **Alternative API**: http://127.0.0.1:8000/api/health (if mounted)

## Troubleshooting

### Server Won't Start

1. **Check Python is installed**:
   ```powershell
   python --version
   ```

2. **Check dependencies are installed**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Check .env file exists**:
   ```powershell
   # Copy example if missing
   Copy-Item .env.example .env
   # Then edit .env with your configuration
   ```

4. **Check for port conflicts**:
   ```powershell
   netstat -ano | findstr :8000
   ```

5. **Run diagnostics**:
   ```powershell
   .\diagnose-startup.ps1
   ```

### Import Errors

If you see import errors, make sure you're in the `backend` directory:
```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Environment Variables

The server requires a `.env` file with at minimum:
- `DATABASE_URL` (PostgreSQL connection string)
- `THE_ODDS_API_KEY` (for odds data)
- Other optional keys (see `.env.example`)

## Background Process

To run in background (PowerShell):
```powershell
Start-Process python -ArgumentList "-m","uvicorn","app.main:app","--reload","--host","127.0.0.1","--port","8000" -NoNewWindow
```

Or use the provided `start.bat` in the root directory to start both frontend and backend.

## PowerShell vs CMD

**PowerShell**:
- Use `.\` prefix for batch files: `.\start-server.bat`
- Use `.\` prefix for PowerShell scripts: `.\start-server.ps1`
- Can run Python directly: `python -m uvicorn ...`

**CMD**:
- Can run batch files directly: `start-server.bat`
- Can run Python directly: `python -m uvicorn ...`
