# Launch Frontend & Backend

Run from the project root (`C:\F3 Apps\F3 Money Parlays`) to start both services in separate PowerShell windows:

```powershell
Start-Process powershell -ArgumentList "cd 'backend'; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

Start-Process powershell -ArgumentList "cd 'frontend'; npm run dev"
```

