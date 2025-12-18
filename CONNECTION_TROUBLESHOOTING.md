# Connection Failed - Complete Troubleshooting Guide

## Quick Diagnosis

Run the diagnostic script:
```cmd
test-backend-connection.bat
```

This will check:
- ✅ Backend is running
- ✅ Firewall rule exists
- ✅ Localhost connection works
- ✅ Network IP connection works

## Common Issues & Solutions

### Issue 1: "Connection Failed" or "Load Failed"

**Symptoms:**
- Debug panel shows "Connection failed"
- Mobile browser can't reach backend
- Test button shows error

**Solutions (try in order):**

#### A. Verify Backend is Running
```cmd
netstat -ano | findstr :8000
```
Should show: `TCP    0.0.0.0:8000   LISTENING`

If not running, start it:
```cmd
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### B. Check Firewall Rule
```cmd
netsh advfirewall firewall show rule name="Parlay Gorilla Backend (Port 8000)"
```
Should show `Enabled: Yes`

If not, run `fix-firewall.bat` as administrator.

#### C. Test Direct Connection
On your mobile device, open browser and go to:
```
http://10.0.0.76:8000/health
```

**Expected:** JSON response like `{"status": "healthy", ...}`

**If this fails:**
- Backend not reachable from network
- Check firewall (see B above)
- Check network connectivity

**If this works but app fails:**
- CORS issue (see Issue 2)
- API URL detection issue
- Check browser console for specific errors

#### D. Check Network Isolation

**Router AP Isolation:**
Some routers have "AP Isolation" or "Client Isolation" enabled, which prevents devices from talking to each other.

**To fix:**
1. Log into your router admin panel (usually `192.168.1.1` or `10.0.0.1`)
2. Look for "AP Isolation", "Client Isolation", or "Wireless Isolation"
3. **Disable** it
4. Save and restart router if needed

**How to check:**
- Try pinging your PC from mobile (if possible)
- If ping fails, AP Isolation is likely enabled

#### E. Verify IP Address

Your PC might have multiple IP addresses. Use the correct one:

```cmd
ipconfig
```

Look for the IP under your active WiFi adapter (not virtual adapters).

Common patterns:
- `10.0.0.x` - Usually correct
- `192.168.x.x` - Usually correct
- `172.20.x.x` - Often a virtual adapter (ignore)
- `169.254.x.x` - Invalid (no DHCP)

#### F. Temporarily Disable Firewall (Test Only!)

**⚠️ WARNING: Only for testing! Re-enable after!**

1. Open Windows Defender Firewall
2. Turn off firewall temporarily
3. Test connection from mobile
4. **Re-enable firewall immediately**
5. If it works, the issue is firewall configuration

### Issue 2: CORS Errors

**Symptoms:**
- Connection reaches backend but fails with CORS error
- Browser console shows: `Access-Control-Allow-Origin` error
- Backend health check works, but API calls fail

**Solution:**
The backend CORS should already allow network IPs, but verify:

1. Check backend is running with `--host 0.0.0.0`
2. Check `backend/app/main.py` has the network regex pattern
3. Restart backend after any changes

### Issue 3: Wrong API URL

**Symptoms:**
- Debug panel shows wrong API URL
- Connection tries to wrong address

**Check:**
1. Open debug panel (`?debug=true`)
2. Verify API URL shows: `http://10.0.0.76:8000`
3. If it shows `localhost:8000`, the detection failed

**Fix:**
- Manually set `NEXT_PUBLIC_API_URL` in `.env.local`:
  ```
  NEXT_PUBLIC_API_URL=http://10.0.0.76:8000
  ```
- Restart frontend server

### Issue 4: Backend Only Listening on Localhost

**Symptoms:**
- `netstat` shows `127.0.0.1:8000` instead of `0.0.0.0:8000`
- Localhost works, network doesn't

**Fix:**
Backend must be started with `--host 0.0.0.0`:
```cmd
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Check `run-dev.bat` - it should already have this.

## Step-by-Step Debugging

### Step 1: Test from PC
```cmd
curl http://localhost:8000/health
```
Should return JSON. If not, backend isn't running correctly.

### Step 2: Test from Mobile Browser
Open on mobile: `http://10.0.0.76:8000/health`

**If this works:**
- Backend is reachable ✅
- Issue is in the app (CORS, API URL, etc.)

**If this fails:**
- Backend not reachable from network ❌
- Check firewall, network isolation, IP address

### Step 3: Check Debug Panel
1. Open app with `?debug=true`
2. Check API URL is correct
3. Click "Test Backend Connection"
4. Read the error message carefully

### Step 4: Check Browser Console
If you can access console (Safari Web Inspector on Mac):
- Look for CORS errors
- Look for network errors
- Check request URLs

## Network Configuration Checklist

- [ ] Backend running on `0.0.0.0:8000` (not `127.0.0.1`)
- [ ] Firewall rule exists and is enabled
- [ ] Both devices on same WiFi network
- [ ] Router AP Isolation is disabled
- [ ] Correct IP address (not virtual adapter)
- [ ] Backend responds to `http://10.0.0.76:8000/health` from mobile browser
- [ ] Frontend API URL detection works (check debug panel)
- [ ] CORS allows network IPs (backend config)

## Still Not Working?

1. **Try a different port:**
   - Change backend to port `8080`
   - Update firewall rule
   - Update frontend API URL

2. **Use a tunneling service:**
   - ngrok, cloudflare tunnel, etc.
   - Bypasses network issues entirely
   - See `TUNNEL_OPTIONS.md`

3. **Check router logs:**
   - Some routers log blocked connections
   - Look for port 8000 blocks

4. **Try from different device:**
   - Test from another PC on same network
   - If that works, issue is mobile-specific
   - If that fails, issue is network/firewall

## Quick Test Commands

```cmd
REM Check backend is running
netstat -ano | findstr :8000

REM Check firewall rule
netsh advfirewall firewall show rule name="Parlay Gorilla Backend (Port 8000)"

REM Test localhost
curl http://localhost:8000/health

REM Get your IP
ipconfig | findstr IPv4
```

## Need More Help?

1. Run `test-backend-connection.bat` and share output
2. Check debug panel error message
3. Try accessing `http://10.0.0.76:8000/health` directly from mobile browser
4. Check backend server window for error messages
5. Verify both devices are on the same WiFi network



