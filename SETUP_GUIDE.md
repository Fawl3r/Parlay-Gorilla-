# Quick Setup Guide

## ✅ Completed Steps

1. ✅ Environment files created (`backend/.env` and `frontend/.env.local`)
2. ✅ Backend dependencies installed
3. ✅ Frontend dependencies installed

## 🔑 Next Steps: Add Your API Keys

### 1. The Odds API (FREE Tier Available)

**Yes, The Odds API has a free tier!**

- **Free Tier:** 500 requests/month
- **Sign up:** https://the-odds-api.com
- **Get your API key:** After signing up, go to your dashboard
- **Update:** Edit `backend/.env` and replace `your_odds_api_key_here` with your actual key

**Note:** The app caches odds for 24 hours, so 500 requests/month should be plenty for development and early users.

### 2. OpenAI API Key

- **Sign up:** https://platform.openai.com
- **Add payment method:** Required for API access (pay-as-you-go)
- **Get your API key:** Go to API Keys section in your dashboard
- **Update:** Edit `backend/.env` and replace `your_openai_api_key_here` with your actual key

**Cost:** Uses `gpt-4o-mini` by default (very affordable, ~$0.15 per 1M input tokens)

### 3. Supabase Database (FREE Tier Available)

**Free tier includes:**
- 500MB database storage
- 2GB bandwidth
- Unlimited API requests

**Setup steps:**

1. **Create account:** https://supabase.com
2. **Create new project:**
   - Click "New Project"
   - Choose organization
   - Enter project name (e.g., "f3-parlay-ai")
   - Set database password (save this!)
   - Choose region closest to you
   - Click "Create new project"

3. **Install Supabase CLI:**
   ```bash
   # Using npm (recommended)
   npm install -g supabase
   
   # Or using Scoop (Windows)
   scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
   scoop install supabase
   ```

4. **Login to Supabase CLI:**
   ```bash
   supabase login
   ```
   - This will open your browser to authenticate
   - After login, return to terminal

5. **Link your project:**
   ```bash
   # Navigate to your project directory
   cd backend
   
   # Link to your Supabase project
   supabase link --project-ref your-project-ref
   ```
   - Find your project ref in Supabase dashboard (Settings → General → Reference ID)

6. **Get connection string using CLI:**
   ```bash
   supabase status
   ```
   - This will show your database connection details
   - Look for the "DB URL" or use:
   ```bash
   supabase db remote get
   ```

7. **Alternative: Get connection string from dashboard:**
   - Go to Settings → Database
   - Scroll to "Connection string"
   - Select "URI" tab
   - Copy the connection string
   - Replace `[YOUR-PASSWORD]` with your database password
   - **Important:** Add `+asyncpg` after `postgresql` (e.g., `postgresql+asyncpg://...`)

8. **Update:** Edit `backend/.env` and replace the `DATABASE_URL` with your connection string

**Example format:**
```
DATABASE_URL=postgresql+asyncpg://postgres.xxxxxxxxxxxxx:your_password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Note:** The `+asyncpg` part is required for async SQLAlchemy to work properly.

## 🚀 Running the Application

### Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

**Test it:** Visit http://localhost:8000/health

### Start Frontend Server

In a **new terminal window:**

```bash
cd frontend
npm run dev
```

The frontend will be available at: http://localhost:3000

## 📝 Environment Variables Summary

### `backend/.env`
```
DATABASE_URL=postgresql+asyncpg://... (from Supabase)
THE_ODDS_API_KEY=your_actual_key_here
OPENAI_API_KEY=your_actual_key_here
BACKEND_URL=http://localhost:8000
```

### `frontend/.env.local`
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🧪 Testing

1. **Backend health check:**
   - Visit: http://localhost:8000/health
   - Should return: `{"status":"healthy",...}`

2. **Fetch NFL games:**
   - Visit: http://localhost:8000/api/sports/nfl/games
   - First request will fetch from The Odds API and cache in database
   - Subsequent requests (within 24 hours) will use cached data

3. **Frontend:**
   - Visit: http://localhost:3000
   - Should display NFL games with odds (if games are available)

## 💰 Cost Summary

**Free Tier Services:**
- ✅ Supabase: Free (500MB database)
- ✅ The Odds API: Free (500 requests/month)
- ✅ Vercel: Free (for frontend hosting)
- ✅ Render/Railway: Free (for backend hosting, with limitations)

**Paid Services:**
- 💵 OpenAI: Pay-as-you-go (very cheap with gpt-4o-mini)

**Total estimated cost for MVP:** ~$0-5/month (only OpenAI usage)

## 🐛 Troubleshooting

### Backend won't start
- Check that all environment variables are set in `backend/.env`
- Verify Supabase connection string is correct
- Make sure port 8000 is not in use

### Frontend can't connect to backend
- Verify backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local`
- Check browser console for CORS errors

### No games showing
- Verify The Odds API key is correct
- Check backend logs for API errors
- NFL season may be off-season (try different sport later)

