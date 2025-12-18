# Troubleshooting 500 Error on /analysis

## Quick Fix Steps

1. **Clear Next.js cache**:
   ```powershell
   cd frontend
   Remove-Item -Recurse -Force .next
   ```

2. **Restart the dev server**:
   ```powershell
   npm run dev
   ```

   Or use the helper script (Windows/PowerShell):
   ```powershell
   cd frontend
   .\restart-dev.ps1
   ```

   For network testing (bind 0.0.0.0):
   ```powershell
   cd frontend
   .\restart-dev.ps1 -Network
   ```

3. **Check the terminal** for the actual error message - it will show what's causing the 500

4. **Check browser console** (F12) for any client-side errors

## Common Causes

### Backend Not Running
If the backend isn't running on port 8000, API calls will fail. Make sure:
```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Build Cache Issues
Sometimes Next.js cache gets corrupted. Clear it:
```powershell
cd frontend
Remove-Item -Recurse -Force .next
npm run dev
```

### Import/Export Issues
Make sure all imports are correct:
- `GameAnalysisHubClient` is exported as default
- All imports use correct paths
- No circular dependencies

## Debug Steps

1. **Check terminal output** when accessing `/analysis` - the error will be logged there
2. **Check browser Network tab** - see if any API calls are failing
3. **Check browser Console** - look for JavaScript errors
4. **Try a hard refresh** - Ctrl+Shift+R or Ctrl+F5

## If Error Persists

Share the exact error message from:
- Terminal output (when you access `/analysis`)
- Browser console (F12 → Console tab)
- Network tab (F12 → Network → look for failed requests)

