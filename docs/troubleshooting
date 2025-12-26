# Cloudflare Tunnel Troubleshooting

## Issue: 404 Error When Accessing Frontend Through Tunnel

If you're seeing a 404 error when accessing the frontend through the Cloudflare tunnel, here are the steps to fix it:

### 1. Verify Frontend Server is Running

The frontend must be running with `npm run dev:network` (not just `npm run dev`) to bind to `0.0.0.0` and accept external connections.

**Check if it's running:**
```powershell
netstat -ano | Select-String ":3000"
```

You should see `0.0.0.0:3000` in the output.

### 2. Restart Frontend Server

If the frontend is running with `npm run dev` instead of `npm run dev:network`, restart it:

1. Stop the current frontend process
2. Run: `cd frontend && npm run dev:network`

### 3. Restart the Tunnel

After ensuring the frontend is running with `dev:network`, restart the Cloudflare tunnel:

1. Close the existing frontend tunnel window
2. Run: `.\start-cloudflare-tunnel.bat` again

### 4. Verify Tunnel URL

Check the "FRONTEND TUNNEL" window for the public URL. It should look like:
```
https://xxxx-xxxx-xxxx.trycloudflare.com
```

### 5. Test Locally First

Before using the tunnel, verify the frontend works locally:
- Open: `http://localhost:3000`
- If this works, the tunnel should work too

### 6. Common Issues

**Issue: "This page could not be found" (404)**
- **Cause**: Frontend server not running with `dev:network`
- **Fix**: Restart frontend with `npm run dev:network`

**Issue: Tunnel shows "Connection refused"**
- **Cause**: Frontend server not running or not bound to `0.0.0.0`
- **Fix**: Ensure `npm run dev:network` is running

**Issue: Backend API calls fail**
- **Cause**: Backend tunnel not running or API URL not configured
- **Fix**: 
  1. Check backend tunnel window for URL
  2. The frontend auto-detects tunnel domains and uses the same hostname for backend
  3. If needed, set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` to the backend tunnel URL

### 7. Quick Restart Script

To restart everything cleanly:

1. Close all tunnel windows
2. Stop frontend: `Get-Process | Where-Object {$_.ProcessName -eq "node"} | Stop-Process -Force`
3. Stop backend: Close the backend server window
4. Run: `.\start-cloudflare-tunnel.bat`

### 8. Verify Both Tunnels Are Running

You should have TWO tunnel windows:
- **Backend Tunnel**: Points to `http://localhost:8000`
- **Frontend Tunnel**: Points to `http://localhost:3000`

Both should show URLs like `https://xxxx-xxxx-xxxx.trycloudflare.com`

## Notes

- The frontend API client (`frontend/lib/api.ts`) automatically detects tunnel domains and uses the same hostname for backend API calls
- No manual configuration needed for tunnel domains
- Both servers must be running before starting tunnels
- Frontend must use `dev:network` to accept external connections




