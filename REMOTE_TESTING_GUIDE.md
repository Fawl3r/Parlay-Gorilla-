# 🌍 Remote Testing Guide

This guide explains how to share your local app with users anywhere in the world using tunneling services.

## 🚀 Quick Start

### Option 1: Automated Script (Recommended)

**Windows:**
```bash
start-tunnel.bat
```

**Mac/Linux:**
```bash
chmod +x start-tunnel.sh
./start-tunnel.sh
```

The script will:
- Start your backend and frontend servers
- Create tunnels for both services
- Show you the public URLs to share

### Option 2: Manual Setup

#### Step 1: Install ngrok

1. **Download ngrok:**
   - Visit: https://ngrok.com/download
   - Download for your OS (Windows/Mac/Linux)

2. **Sign up for free account:**
   - Go to: https://dashboard.ngrok.com/signup
   - Create a free account

3. **Get your auth token:**
   - After signing up, go to: https://dashboard.ngrok.com/get-started/your-authtoken
   - Copy your authtoken

4. **Authenticate ngrok:**
   ```bash
   ngrok authtoken YOUR_AUTH_TOKEN
   ```

#### Step 2: Start Your Servers

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev:network
```

#### Step 3: Create Tunnels

**Terminal 3 - Backend Tunnel:**
```bash
ngrok http 8000
```

**Terminal 4 - Frontend Tunnel:**
```bash
ngrok http 3000
```

#### Step 4: Get Your URLs

Each ngrok terminal will show:
```
Forwarding  https://xxxx-xx-xx-xx-xx.ngrok-free.app -> http://localhost:8000
```

Or visit: **http://localhost:4040** to see the ngrok web interface with all your tunnels.

## 📋 What URLs to Share

**Share the FRONTEND tunnel URL with testers:**
```
https://xxxx-xx-xx-xx-xx.ngrok-free.app
```

The frontend automatically detects tunnel domains and connects to the backend tunnel.

## 🔧 Alternative Tunneling Services

### Cloudflare Tunnel (Free, No Signup Required)

**Install:**
```bash
# Windows: Download from https://github.com/cloudflare/cloudflared/releases
# Mac: brew install cloudflared
# Linux: Download from releases page
```

**Start Tunnels:**
```bash
# Backend
cloudflared tunnel --url http://localhost:8000

# Frontend  
cloudflared tunnel --url http://localhost:3000
```

**Pros:**
- No signup required
- Free unlimited use
- HTTPS by default

**Cons:**
- Random URLs each time
- URLs change on restart

### LocalTunnel (Free, No Signup)

**Install:**
```bash
npm install -g localtunnel
```

**Start Tunnels:**
```bash
# Backend
lt --port 8000

# Frontend
lt --port 3000
```

**Note:** Update CORS in `backend/app/main.py` to include `localtunnel.me` domains.

## ⚙️ Configuration

### Backend CORS

The backend is already configured to allow:
- ✅ ngrok domains (`*.ngrok.io`, `*.ngrok-free.app`)
- ✅ Cloudflare tunnels (`*.trycloudflare.com`)
- ✅ LocalTunnel (`*.localtunnel.me`)
- ✅ Other common tunneling services

### Frontend API Auto-Detection

The frontend automatically detects tunnel domains and connects to the backend on the same tunnel domain. No configuration needed!

### Manual API URL Override

If needed, create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=https://your-backend-tunnel-url.ngrok-free.app
```

## 🔒 Security Considerations

⚠️ **Important Security Notes:**

1. **Temporary Access Only:**
   - Only run tunnels when actively testing
   - Close tunnels when done
   - Don't leave tunnels running 24/7

2. **Free Tier Limitations:**
   - ngrok free: Random URLs, session limits
   - Cloudflare: Random URLs each restart
   - Consider paid plans for production-like testing

3. **Access Control:**
   - ngrok free: Anyone with the URL can access
   - Consider ngrok paid plans for password protection
   - Or use VPN for more control

4. **Data Privacy:**
   - Don't use with real production data
   - Use test accounts only
   - Be aware of what data is exposed

## 🐛 Troubleshooting

### "ngrok: command not found"

**Solution:**
1. Make sure ngrok is installed
2. Add ngrok to your PATH
3. Or use full path: `C:\path\to\ngrok.exe http 8000`

### CORS Errors

**Symptoms:** Browser console shows CORS errors

**Solution:**
1. Check that backend CORS includes your tunnel domain
2. Verify tunnel URL matches exactly (including https://)
3. Check browser console for exact error message

### Frontend Can't Connect to Backend

**Symptoms:** Frontend loads but API calls fail

**Solution:**
1. Check both tunnels are running
2. Verify frontend auto-detection is working
3. Manually set `NEXT_PUBLIC_API_URL` in `.env.local`
4. Check browser console for API errors

### ngrok Free Tier Limitations

**Symptoms:** 
- "Too many connections"
- "Session expired"
- Random disconnections

**Solutions:**
1. Use Cloudflare Tunnel (no limits)
2. Upgrade ngrok plan
3. Restart tunnels periodically

### Tunnel URLs Keep Changing

**ngrok Free:**
- URLs change on each restart
- Use ngrok paid for static domains

**Cloudflare:**
- URLs always change
- Use ngrok for static URLs

## 📊 Comparison of Tunneling Services

| Service | Free Tier | Static URLs | Signup Required | Best For |
|---------|-----------|-------------|-----------------|----------|
| **ngrok** | ✅ Limited | ❌ (paid) | ✅ Yes | Professional testing |
| **Cloudflare** | ✅ Unlimited | ❌ No | ❌ No | Quick testing |
| **LocalTunnel** | ✅ Unlimited | ❌ No | ❌ No | Simple testing |
| **Serveo** | ✅ Unlimited | ❌ No | ❌ No | SSH-based |

## ✅ Testing Checklist

Before sharing with remote testers:

- [ ] Both servers start without errors
- [ ] Both tunnels are active and showing URLs
- [ ] Frontend tunnel URL loads in your browser
- [ ] Backend health check works: `https://backend-tunnel-url/health`
- [ ] Frontend can make API calls (check browser console)
- [ ] Testers can access frontend URL
- [ ] No CORS errors in browser console

## 🎯 Quick Reference

**Start Everything:**
```bash
# Windows
start-tunnel.bat

# Mac/Linux
./start-tunnel.sh
```

**Manual Start:**
```bash
# Terminal 1: Backend
cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev:network

# Terminal 3: Backend Tunnel
ngrok http 8000

# Terminal 4: Frontend Tunnel
ngrok http 3000
```

**Get URLs:**
- Visit: http://localhost:4040 (ngrok web interface)
- Or check terminal output for tunnel URLs

**Share:**
- Share the **FRONTEND tunnel URL** with testers
- Frontend auto-connects to backend

---

**Need Help?** Check the troubleshooting section or review server/tunnel logs for errors.




