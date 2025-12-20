# 🌐 Domain Setup Guide - api.parlaygorilla.com

Complete guide to setting up your custom domain and subdomain on Render.

## 📋 What You Have

- ✅ Domain: `www.parlaygorilla.com` (already purchased)
- 🎯 Goal: Set up `api.parlaygorilla.com` as a subdomain for your backend

---

## 🚀 Step-by-Step Setup

### Step 1: Get Your Render Service URLs

First, you need your Render service URLs:

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Find your services**:
   - `parlay-gorilla-frontend` → Copy the URL (e.g., `https://parlay-gorilla-frontend.onrender.com`)
   - `parlay-gorilla-backend` → Copy the URL (e.g., `https://parlay-gorilla-backend.onrender.com`)

**You'll need these URLs for DNS configuration.**

---

### Step 2: Configure DNS Records

You need to add DNS records at your domain provider (where you bought the domain). Common providers:
- Cloudflare
- Namecheap
- GoDaddy
- Google Domains
- Route 53 (AWS)

#### Option A: Using Cloudflare (Recommended)

1. **Add your domain to Cloudflare**:
   - Sign up at https://cloudflare.com (free)
   - Add your domain `parlaygorilla.com`
   - Update your domain's nameservers to Cloudflare's (they'll provide instructions)

2. **Add DNS Records**:
   - Go to **DNS** → **Records**
   - Add these records:

   **For www.parlaygorilla.com (Frontend):**
   ```
   Type: CNAME
   Name: www
   Target: parlay-gorilla-frontend.onrender.com
   Proxy status: Proxied (orange cloud) ✅
   TTL: Auto
   ```

   **For api.parlaygorilla.com (Backend):**
   ```
   Type: CNAME
   Name: api
   Target: parlay-gorilla-backend.onrender.com
   Proxy status: Proxied (orange cloud) ✅
   TTL: Auto
   ```

   **For root domain (parlaygorilla.com) - Optional:**
   ```
   Type: CNAME
   Name: @
   Target: parlay-gorilla-frontend.onrender.com
   Proxy status: Proxied (orange cloud) ✅
   TTL: Auto
   ```

3. **Save the records** - DNS propagation takes 5-30 minutes

#### Option B: Using Other DNS Providers

The process is similar, but the interface varies:

1. **Log into your domain provider**
2. **Go to DNS Management** (or DNS Settings)
3. **Add CNAME records**:

   **For www subdomain:**
   - **Type**: CNAME
   - **Host/Name**: `www`
   - **Value/Target**: `parlay-gorilla-frontend.onrender.com`
   - **TTL**: 3600 (or Auto)

   **For api subdomain:**
   - **Type**: CNAME
   - **Host/Name**: `api`
   - **Value/Target**: `parlay-gorilla-backend.onrender.com`
   - **TTL**: 3600 (or Auto)

4. **Save the records**

**⚠️ Important Notes:**
- Use **CNAME** records, not A records (Render uses dynamic IPs)
- Don't include the `https://` in the target - just the domain
- DNS changes can take 5-30 minutes to propagate

---

### Step 3: Add Custom Domains in Render

After DNS is configured, add the domains in Render:

#### Add Frontend Domain (www.parlaygorilla.com)

1. **Go to Render Dashboard** → `parlay-gorilla-frontend` service
2. **Click "Settings"** tab
3. **Scroll to "Custom Domains"** section
4. **Click "Add Custom Domain"**
5. **Enter**: `www.parlaygorilla.com`
6. **Click "Add"**
7. **Render will verify DNS** - wait for it to show "Valid" (green checkmark)

#### Add Backend Domain (api.parlaygorilla.com)

1. **Go to Render Dashboard** → `parlay-gorilla-backend` service
2. **Click "Settings"** tab
3. **Scroll to "Custom Domains"** section
4. **Click "Add Custom Domain"**
5. **Enter**: `api.parlaygorilla.com`
6. **Click "Add"**
7. **Render will verify DNS** - wait for it to show "Valid" (green checkmark)

**⏱️ DNS Verification:**
- Render will check if DNS is configured correctly
- This can take 5-30 minutes after you add DNS records
- You'll see "Pending" until DNS propagates, then "Valid"

---

### Step 4: Update Environment Variables

After domains are verified, update your environment variables:

#### Backend Environment Variables

1. **Go to `parlay-gorilla-backend`** → **Environment** tab
2. **Update these variables**:

   ```
   FRONTEND_URL=https://www.parlaygorilla.com
   BACKEND_URL=https://api.parlaygorilla.com
   APP_URL=https://www.parlaygorilla.com
   ```

3. **Click "Save Changes"** - Render will auto-redeploy

#### Frontend Environment Variables

1. **Go to `parlay-gorilla-frontend`** → **Environment** tab
2. **Update these variables**:

   ```
   NEXT_PUBLIC_SITE_URL=https://www.parlaygorilla.com
   NEXT_PUBLIC_API_URL=https://api.parlaygorilla.com
   ```

3. **Click "Save Changes"** - Render will auto-redeploy

---

### Step 5: Update render.yaml (Optional)

If you want to update the default domains in `render.yaml` for future deployments:

```yaml
  - type: web
    name: parlay-gorilla-frontend
    domains:
      - www.parlaygorilla.com  # Update this
    envVars:
      - key: NEXT_PUBLIC_SITE_URL
        value: https://www.parlaygorilla.com  # Update this
      - key: NEXT_PUBLIC_API_URL
        value: https://api.parlaygorilla.com  # Update this

  - type: web
    name: parlay-gorilla-backend
    domains:
      - api.parlaygorilla.com  # Update this
    envVars:
      - key: FRONTEND_URL
        value: https://www.parlaygorilla.com  # Update this
      - key: BACKEND_URL
        value: https://api.parlaygorilla.com  # Update this
      - key: APP_URL
        value: https://www.parlaygorilla.com  # Update this
```

---

## 🔍 Verify Everything Works

### 1. Check DNS Propagation

Use these tools to verify DNS is working:
- https://dnschecker.org - Check DNS propagation globally
- https://www.whatsmydns.net - Check DNS records
- Command line: `nslookup api.parlaygorilla.com`

### 2. Test Your Domains

After DNS propagates and Render verifies:

- **Frontend**: Visit `https://www.parlaygorilla.com`
- **Backend Health**: Visit `https://api.parlaygorilla.com/health`
- **Backend API**: Visit `https://api.parlaygorilla.com/api/metrics` (if public)

### 3. Check SSL Certificates

Render automatically provisions SSL certificates via Let's Encrypt:
- Certificates are auto-generated when domains are verified
- Takes 5-10 minutes after domain verification
- Your sites will automatically use HTTPS

---

## 🐛 Troubleshooting

### DNS Not Propagating?

1. **Wait longer**: DNS can take up to 48 hours (usually 5-30 minutes)
2. **Check DNS records**: Verify they're correct in your DNS provider
3. **Clear DNS cache**: 
   - Windows: `ipconfig /flushdns`
   - Mac/Linux: `sudo dscacheutil -flushcache`
4. **Check TTL**: Lower TTL values (300 seconds) help with faster updates

### Render Says "Invalid DNS"?

1. **Verify CNAME records**: Make sure they point to the correct Render URLs
2. **Check for typos**: Ensure no extra spaces or `https://` in targets
3. **Wait for propagation**: DNS changes need time to propagate
4. **Check with DNS checker**: Use dnschecker.org to verify records globally

### Domain Not Loading?

1. **Check SSL certificate**: Wait 5-10 minutes after domain verification
2. **Check service status**: Ensure services are "Live" in Render
3. **Check environment variables**: Ensure URLs are updated correctly
4. **Check browser console**: Look for CORS or connection errors

### CORS Errors?

If you see CORS errors after switching domains:

1. **Update backend CORS settings**: Ensure `FRONTEND_URL` is set correctly
2. **Check allowed origins**: Backend should allow `https://www.parlaygorilla.com`
3. **Restart services**: Sometimes services need a restart after env var changes

---

## 📝 DNS Record Summary

Here's what you need to add at your DNS provider:

| Type | Name | Target | Purpose |
|------|------|--------|---------|
| CNAME | `www` | `parlay-gorilla-frontend.onrender.com` | Frontend website |
| CNAME | `api` | `parlay-gorilla-backend.onrender.com` | Backend API |
| CNAME | `@` | `parlay-gorilla-frontend.onrender.com` | Root domain (optional) |

**Note:** The `@` record is for the root domain (`parlaygorilla.com` without www). This is optional but recommended.

---

## ✅ Setup Checklist

- [ ] DNS records added at domain provider
- [ ] DNS records verified (using dnschecker.org)
- [ ] Custom domain added in Render frontend service
- [ ] Custom domain added in Render backend service
- [ ] Domains show "Valid" in Render dashboard
- [ ] SSL certificates provisioned (automatic)
- [ ] Backend environment variables updated
- [ ] Frontend environment variables updated
- [ ] Services redeployed
- [ ] Frontend accessible at `https://www.parlaygorilla.com`
- [ ] Backend accessible at `https://api.parlaygorilla.com/health`
- [ ] No CORS errors in browser console

---

## 🔗 Quick Links

- [Render Dashboard](https://dashboard.render.com)
- [Cloudflare DNS](https://dash.cloudflare.com)
- [DNS Checker](https://dnschecker.org)
- [Render Custom Domains Docs](https://render.com/docs/custom-domains)

---

## 💡 Pro Tips

1. **Use Cloudflare**: Free SSL, CDN, and DNS management
2. **Enable Proxy**: In Cloudflare, keep the orange cloud (proxy) enabled for DDoS protection
3. **Monitor DNS**: Use DNS checker tools to verify propagation
4. **Test Gradually**: Test with one domain first, then add the other
5. **Keep Render URLs**: Don't delete the `.onrender.com` URLs - they still work as backups

---

**Once setup is complete, you'll have:**
- ✅ `https://www.parlaygorilla.com` - Your frontend
- ✅ `https://api.parlaygorilla.com` - Your backend API
- ✅ Automatic HTTPS via Let's Encrypt
- ✅ Professional domain setup

🎉 **You're all set!**

