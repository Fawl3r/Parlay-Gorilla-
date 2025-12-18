# Quick Fix for Tunnel Connection

## The Problem
Your debug panel shows:
- **Origin**: `https://ethics-viewer-vanilla-like.trycloudflare.com` ✅ (Frontend tunnel - correct!)
- **API URL**: `http://localhost:8000` ❌ (Should be backend tunnel URL!)

## Solution: Update Backend URL

You have 2 options:

### Option 1: Use Query Parameter (No Restart Needed!)

1. Get your **BACKEND tunnel URL** from the "Backend Tunnel" window
   - It should look like: `https://xxxx-xxxx-xxxx.trycloudflare.com`

2. Add it to your frontend URL like this:
   ```
   https://ethics-viewer-vanilla-like.trycloudflare.com?backend=https://YOUR-BACKEND-TUNNEL-URL
   ```

3. Replace `YOUR-BACKEND-TUNNEL-URL` with your actual backend tunnel URL

4. Open that full URL on your iPhone - it should work immediately!

### Option 2: Update Environment Variable (Requires Restart)

1. Get your **BACKEND tunnel URL** from the "Backend Tunnel" window

2. Edit `frontend/.env.local` and change:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
   To:
   ```
   NEXT_PUBLIC_API_URL=https://YOUR-BACKEND-TUNNEL-URL
   ```

3. Restart the frontend server:
   - Close the "F3 Frontend" window
   - Wait a moment
   - Run: `cd frontend && npm run dev:network`

4. Then access the frontend tunnel URL normally

## Quick Script

I've created `setup-tunnel-backend-url.bat` - run it and it will:
- Ask for your backend tunnel URL
- Update the `.env.local` file automatically
- Tell you to restart the frontend

## What's Your Backend Tunnel URL?

Check the "Backend Tunnel" window - what URL does it show?
Copy it here and I'll help you set it up!



