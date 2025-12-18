# Tunnel Options - No Password Required

LocalTunnel sometimes requires visitors to enter their IP address as a password, which can be annoying. Here are better alternatives:

## Option 1: Cloudflare Tunnel (Recommended - No Password)

**Best option** - No password required, very reliable.

### Setup:
1. Download cloudflared from: https://github.com/cloudflare/cloudflared/releases
2. Extract `cloudflared.exe` and place it in:
   - Your PATH (e.g., `C:\Windows\System32`), OR
   - The project root directory
3. Run: `start-cloudflare-frontend-only.bat` (recommended)

Why this is recommended:
- The app proxies `/api/*` and `/health` through the Next.js frontend (same-origin).
- This avoids CORS issues and “localhost on phone” problems.
- You only share ONE URL (the frontend tunnel URL).

**Pros:**
- ✅ No password required
- ✅ Very fast and reliable
- ✅ HTTPS by default
- ✅ Clean URLs: `https://xxxx-xxxx-xxxx.trycloudflare.com`

## Option 2: Serveo (SSH-based, No Password)

**Simple option** - Uses SSH, no installation needed (Windows 10+ has SSH built-in).

### Setup:
1. Just run: `start-simple-tunnel.bat`
2. First time: Accept the SSH host key when prompted

**Pros:**
- ✅ No password required
- ✅ No installation needed (SSH built into Windows 10+)
- ✅ Custom subdomains: `https://parlay-frontend.serveo.net`
- ✅ Free and simple

**Cons:**
- Requires SSH (built into Windows 10+, but may need to be enabled)

## Option 3: LocalTunnel with Subdomain (May Still Ask for Password)

If you want to stick with LocalTunnel, the updated script tries to use custom subdomains, but it may still ask for passwords.

### To bypass LocalTunnel password:
1. Visitors need to enter **their own IP address** (not yours)
2. They can find their IP at: https://whatismyipaddress.com/
3. Enter it in the password field on the LocalTunnel page

## Quick Comparison

| Feature | Cloudflare | Serveo | LocalTunnel |
|---------|-----------|--------|------------|
| Password Required | ❌ No | ❌ No | ⚠️ Sometimes |
| Installation | Download binary | None (SSH built-in) | npm install |
| Reliability | Excellent | Good | Good |
| Speed | Excellent | Good | Good |
| Custom Domain | No (random) | Yes (subdomain) | Maybe |

## Recommendation

**Use Cloudflare Tunnel** - It's the most reliable and doesn't require passwords. Just download the binary and run the script!

