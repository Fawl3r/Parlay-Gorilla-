# 🌐 Network Testing Guide

This guide explains how to allow others to test your app on your local network without deploying to Render.

## 🚀 Quick Start

### Option 1: Use the Start Scripts (Recommended)

**Windows:**
```bash
start.bat
```

**Mac/Linux:**
```bash
chmod +x start.sh
./start.sh
```

The scripts will automatically:
- Start both servers on network-accessible addresses
- Display your local IP address
- Show the URLs to share with testers

### Option 2: Manual Start

**Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev:network
```

## 📋 Prerequisites

1. **All devices must be on the same network** (same Wi-Fi/router)
2. **Firewall configuration** may be needed (see below)
3. **Backend CORS** is already configured to allow local network IPs

## 🔧 Finding Your IP Address

### Windows
```bash
ipconfig
# Look for "IPv4 Address" under your active network adapter
```

### Mac/Linux
```bash
ifconfig
# Look for "inet" address (not 127.0.0.1)
# Or use:
ip addr show
```

### Quick Command
- **Windows:** `ipconfig | findstr IPv4`
- **Mac/Linux:** `ifconfig | grep "inet " | grep -v 127.0.0.1`

## 🔥 Firewall Configuration

### Windows Firewall

1. Open **Windows Defender Firewall**
2. Click **"Allow an app or feature through Windows Firewall"**
3. Click **"Change Settings"** (if needed)
4. Click **"Allow another app..."**
5. Add:
   - **Python** (for backend on port 8000)
   - **Node.js** (for frontend on port 3000)
6. Or create rules:
   - **Inbound Rule** → **Port** → **TCP** → **8000** → **Allow**
   - **Inbound Rule** → **Port** → **TCP** → **3000** → **Allow**

### Mac Firewall

1. **System Preferences** → **Security & Privacy** → **Firewall**
2. Click **"Firewall Options"**
3. Ensure **"Block all incoming connections"** is **OFF**
4. Or add exceptions for Python and Node.js

### Linux (UFW)

```bash
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw status
```

## 📱 Sharing URLs with Testers

Once servers are running, share these URLs:

```
Backend API:  http://YOUR_IP:8000
Frontend App: http://YOUR_IP:3000
```

**Example:**
```
Backend API:  http://192.168.1.100:8000
Frontend App: http://192.168.1.100:3000
```

## ⚙️ Frontend API Configuration

The frontend automatically detects the API URL. If testers need to use a different backend:

1. Create `.env.local` in the `frontend` directory:
```env
NEXT_PUBLIC_API_URL=http://YOUR_IP:8000
```

2. Restart the frontend server

## 🔒 Security Notes

⚠️ **Important:** This setup is for **local network testing only**. 

- Only share with trusted testers on your network
- Don't expose these ports to the internet
- Use a VPN for remote testing (see below)
- For production, deploy via Render (see `QUICK_DEPLOY.md`)

## 🌍 Remote Testing (Outside Your Network)

If testers are not on your local network, you have two options:

### Option 1: VPN (Recommended)
- Set up a VPN server (WireGuard, OpenVPN, etc.)
- Testers connect to your VPN
- They can then access your local IP addresses

### Option 2: Tunneling Service (Quick but Limited)

**ngrok** (Free tier available):
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 3000  # For frontend
ngrok http 8000  # For backend (in another terminal)
```

**Cloudflare Tunnel** (Free):
```bash
# Install cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
cloudflared tunnel --url http://localhost:3000
```

⚠️ **Note:** Free tunneling services have limitations (rate limits, random URLs, etc.)

## 🐛 Troubleshooting

### "Connection Refused" Error

1. **Check servers are running:**
   ```bash
   # Backend
   curl http://localhost:8000/health
   
   # Frontend
   curl http://localhost:3000
   ```

2. **Check firewall rules** (see above)

3. **Verify IP address:**
   - Make sure you're using the correct IP
   - Try `localhost` first to confirm servers work

4. **Check network:**
   - Ensure all devices are on the same Wi-Fi/network
   - Some corporate networks block device-to-device communication

### CORS Errors

The backend is configured to allow local network IPs. If you see CORS errors:

1. Check the origin in browser console
2. Verify the IP matches the pattern: `192.168.x.x`, `10.x.x.x`, or `172.16-31.x.x`
3. Check `backend/app/main.py` CORS configuration

### Port Already in Use

If ports 3000 or 8000 are in use:

**Backend (different port):**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

**Frontend (different port):**
```bash
npm run dev:network -- -p 3001
```

Then update CORS in `backend/app/main.py` to include the new port.

## ✅ Testing Checklist

Before sharing with testers:

- [ ] Both servers start without errors
- [ ] You can access `http://localhost:3000` locally
- [ ] You can access `http://YOUR_IP:3000` from another device on your network
- [ ] Backend health check works: `http://YOUR_IP:8000/health`
- [ ] Firewall allows connections on ports 3000 and 8000
- [ ] Testers have the correct IP address and URLs

## 📞 Quick Reference

**Local URLs:**
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

**Network URLs (replace YOUR_IP):**
- Frontend: `http://YOUR_IP:3000`
- Backend: `http://YOUR_IP:8000`

**Health Check:**
- `http://YOUR_IP:8000/health`

---

**Need Help?** Check the troubleshooting section above or review the server logs for error messages.



