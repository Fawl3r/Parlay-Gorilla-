# Development Scripts Guide

This project includes convenient scripts to run both backend and frontend servers together.

## Available Scripts

### `run-dev.bat` (Windows Command Prompt)
- **Usage:** Double-click or run `run-dev.bat` from Command Prompt
- **Features:**
  - Checks for Python and Node.js
  - Installs frontend dependencies if needed
  - Checks if ports are in use
  - Starts both servers in separate windows
  - Displays local and network URLs

### `run-dev.ps1` (Windows PowerShell)
- **Usage:** Run `.\run-dev.ps1` from PowerShell
- **Features:** Same as `.bat` but with colored output and better PowerShell integration

### `run-dev.sh` (Mac/Linux)
- **Usage:** Run `./run-dev.sh` from terminal
- **Features:**
  - Checks for Python and Node.js
  - Installs frontend dependencies if needed
  - Checks if ports are in use
  - Starts both servers in background
  - Logs output to `backend.log` and `frontend.log`
  - Graceful shutdown on Ctrl+C
  - Displays local and network URLs

## Server URLs

Once the servers are running:

- **Backend API:** http://localhost:8000
- **Frontend App:** http://localhost:3000
- **API Documentation:** http://localhost:8000/docs
- **Network Access:** The scripts will display your local IP address for network access

## Stopping the Servers

### Windows (run-dev.bat / run-dev.ps1)
- Close the separate windows that opened for each server
- Or press Ctrl+C in each server window

### Mac/Linux (run-dev.sh)
- Press Ctrl+C in the terminal where you ran the script
- The script will automatically stop both servers

## Troubleshooting

### Port Already in Use
If you see a warning that port 8000 or 3000 is in use:
- **Windows:** Use `netstat -ano | findstr :8000` to find the process, then kill it
- **Mac/Linux:** Use `lsof -i :8000` to find the process, then kill it

### Dependencies Not Found
- Ensure Python 3.8+ is installed and in your PATH
- Ensure Node.js 18+ is installed and in your PATH
- Verify installations with `python --version` and `node --version`

### Frontend Dependencies
The scripts will automatically install frontend dependencies if `node_modules` is missing. If installation fails:
- Manually run `cd frontend && npm install`
- Check your internet connection
- Verify Node.js version is 18+

## Manual Server Startup

If you prefer to run servers manually:

**Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## Logs (Unix/Linux only)

When using `run-dev.sh`, logs are written to:
- `./backend.log` - Backend server logs
- `./frontend.log` - Frontend server logs

Monitor these files to see server output:
```bash
tail -f backend.log
tail -f frontend.log
```



