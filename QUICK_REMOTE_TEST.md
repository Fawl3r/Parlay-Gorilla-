# 🚀 Quick Remote Testing

## Setup (One Time)

1. **Install ngrok:**
   - Download: https://ngrok.com/download
   - Sign up: https://dashboard.ngrok.com/signup
   - Get token: https://dashboard.ngrok.com/get-started/your-authtoken
   - Authenticate: `ngrok authtoken YOUR_TOKEN`

## Start Everything

**Windows:**
```bash
start-tunnel.bat
```

**Mac/Linux:**
```bash
chmod +x start-tunnel.sh
./start-tunnel.sh
```

## Get Your URLs

Visit: **http://localhost:4040** (ngrok web interface)

Or check the terminal windows for:
```
Forwarding  https://xxxx-xx-xx-xx-xx.ngrok-free.app -> http://localhost:3000
```

## Share with Testers

**Share the FRONTEND URL:**
```
https://xxxx-xx-xx-xx-xx.ngrok-free.app
```

✅ Frontend automatically connects to backend  
✅ No configuration needed  
✅ Works from anywhere in the world  

## Manual Start

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

## Troubleshooting

**CORS errors?** - Backend is already configured for tunnels ✅

**Can't connect?** - Check both tunnels are running

**URLs keep changing?** - That's normal for ngrok free tier

**Need help?** - See `REMOTE_TESTING_GUIDE.md`




