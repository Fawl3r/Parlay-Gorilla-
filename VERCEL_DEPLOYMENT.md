# Vercel Deployment Guide

## Quick Fix for 404 Error

If you're getting a 404 error on Vercel, you need to configure Vercel to use the `frontend` directory as the root.

### Option 1: Vercel Dashboard (Recommended - Easiest)

1. Go to your Vercel project: https://vercel.com/dashboard
2. Click on your project
3. Go to **Settings** → **General**
4. Scroll down to **Root Directory**
5. Click **Edit** and set it to: `frontend`
6. Click **Save**
7. Go to **Deployments** tab and click **Redeploy** on the latest deployment

### Option 2: Use vercel.json (Already Created)

The `vercel.json` file in the root directory is already configured. After pushing to GitHub:
1. Vercel should auto-detect the configuration
2. If not, manually trigger a redeploy

### Option 3: Import with Correct Settings

If importing fresh:
1. When importing the project, Vercel will ask for settings
2. Set **Root Directory** to: `frontend`
3. Set **Framework Preset** to: `Next.js`
4. Vercel will auto-detect the rest

### Required Environment Variables

Make sure to add these in Vercel dashboard under **Settings** → **Environment Variables**:

- `NEXT_PUBLIC_API_URL` - Your backend API URL (e.g., `https://your-backend.vercel.app` or your backend server URL)
- `NEXT_PUBLIC_SITE_URL` - Your frontend URL (e.g., `https://parlay-gorilla.vercel.app`)
- `NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION` - (Optional) Google Search Console verification
- `NEXT_PUBLIC_ADSENSE_CLIENT_ID` - (Optional) Google AdSense client ID

### After Configuration

1. Push the `vercel.json` file to your repository (already done)
2. Vercel will automatically detect the changes on next push
3. Or manually trigger a redeploy in Vercel dashboard

### Troubleshooting

If you still get 404:
1. Check Vercel build logs for errors
2. Verify the root directory is set to `frontend` in dashboard
3. Make sure `frontend/package.json` exists
4. Check that `frontend/app/page.tsx` exists (the root route)
5. Check build logs for any TypeScript or build errors
