# Backend Connection Fix Guide

## Problem
The backend connection test is failing from your mobile device, even though the backend is running.

## Quick Fix

### Option 1: Run the Firewall Fix Script (Easiest)

1. **Right-click** on `fix-firewall.bat`
2. Select **"Run as administrator"**
3. Follow the prompts

This will automatically add a Windows Firewall rule to allow connections on port 8000.

### Option 2: Manual Firewall Configuration

1. **Open Windows Defender Firewall:**
   - Press `Win + R`
   - Type `wf.msc` and press Enter

2. **Create Inbound Rule:**
   - Click **"Inbound Rules"** in the left panel
   - Click **"New Rule..."** in the right panel
   - Select **"Port"** → Next
   - Select **"TCP"** and enter port **8000** → Next
   - Select **"Allow the connection"** → Next
   - Check all profiles (Domain, Private, Public) → Next
   - Name it: **"Parlay Gorilla Backend (Port 8000)"** → Finish

3. **Verify the rule exists:**
   - Look for the rule in the Inbound Rules list
   - Make sure it's **Enabled** (green checkmark)

### Option 3: PowerShell Command (Quick)

Open PowerShell as Administrator and run:

```powershell
New-NetFirewallRule -DisplayName "Parlay Gorilla Backend (Port 8000)" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

## Verify Backend is Running

Check if the backend is listening on the correct interface:

```cmd
netstat -ano | findstr :8000
```

You should see:
```
TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING
```

If you see `127.0.0.1:8000` instead, the backend is only listening on localhost and won't accept network connections.

## Test Connection

### From Your PC:
1. Open browser: `http://localhost:8000/health`
2. Should return: `{"status": "healthy", ...}`

### From Mobile Device:
1. Open browser: `http://10.0.0.76:8000/health`
2. Should return: `{"status": "healthy", ...}`

If this works, the backend is reachable!

## Troubleshooting

### Still Can't Connect?

1. **Check Windows Firewall:**
   ```cmd
   netsh advfirewall firewall show rule name="Parlay Gorilla Backend (Port 8000)"
   ```
   Should show the rule exists and is enabled.

2. **Check Network Connection:**
   - Ensure both devices are on the same WiFi network
   - Try pinging your PC from mobile (if possible)
   - Verify the IP address: `10.0.0.76` (check with `ipconfig`)

3. **Check Backend Server:**
   - Make sure backend is running
   - Check the backend window for errors
   - Verify it says: `Uvicorn running on http://0.0.0.0:8000`

4. **Try Different Port:**
   - If port 8000 is blocked by your network/router
   - Change backend to port 8080 or 3001
   - Update firewall rule accordingly

5. **Router/Network Issues:**
   - Some routers block device-to-device communication
   - Check router settings for "AP Isolation" or "Client Isolation"
   - Disable it if enabled

## Common Issues

### "Connection Refused"
- Backend not running
- Firewall blocking connection
- Backend only listening on localhost

### "Connection Timeout"
- Firewall blocking
- Network connectivity issue
- Wrong IP address

### "Network Error"
- Devices not on same network
- Router blocking communication
- Mobile data instead of WiFi

## After Fixing

1. **Restart the backend server** (if it was running)
2. **Test from mobile:** `http://10.0.0.76:8000/health`
3. **Use the debug panel** in the app to test connection
4. **Try logging in** again

## Still Having Issues?

If the connection test still fails after fixing the firewall:

1. Check the exact error message in the debug panel
2. Try accessing `http://10.0.0.76:8000/health` directly in mobile browser
3. Check backend logs for connection attempts
4. Verify both devices are on the same network
5. Try temporarily disabling Windows Firewall to test (then re-enable!)



