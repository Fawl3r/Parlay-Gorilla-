# Cloudflare Tunnel Setup Guide

This guide shows you how to expose your local development server to the internet using Cloudflare Tunnel (cloudflared) - a free alternative to ngrok.

## Why Cloudflare Tunnel?

- ✅ **100% Free** - No account required for basic usage
- ✅ **No Rate Limits** - Unlike ngrok free tier
- ✅ **HTTPS by Default** - Secure connections out of the box
- ✅ **Easy Setup** - Single command to get started
- ✅ **Reliable** - Powered by Cloudflare's global network

## Installation

### Windows

1. **Download cloudflared:**
   - Visit: https://github.com/cloudflare/cloudflared/releases
   - Download `cloudflared-windows-amd64.exe`
   - Rename to `cloudflared.exe`
   - Place in a folder in your PATH (e.g., `C:\Windows\System32`) OR in the project root

2. **Or use Chocolatey (if installed):**
   ```powershell
   choco install cloudflared
   ```

### macOS

```bash
brew install cloudflared
```

### Linux

1. Download from: https://github.com/cloudflare/cloudflared/releases
2. Extract and add to PATH:
   ```bash
   sudo mv cloudflared /usr/local/bin/
   sudo chmod +x /usr/local/bin/cloudflared
   ```

## Usage

### Quick Start (Windows)

1. Run the tunnel script:
   ```cmd
   start-cloudflare-tunnel.bat
   ```

2. The script will:
   - Start your backend server (port 8000)
   - Start your frontend server (port 3000)
   - Create two Cloudflare tunnels

3. Check the tunnel windows for your public URLs:
   - Each tunnel will display a URL like: `https://xxxx-xxxx-xxxx.trycloudflare.com`
   - Backend URL: Use for API calls
   - Frontend URL: Share with testers

### Quick Start (macOS/Linux)

1. Make the script executable:
   ```bash
   chmod +x start-cloudflare-tunnel.sh
   ```

2. Run the tunnel script:
   ```bash
   ./start-cloudflare-tunnel.sh
   ```

3. Check the output for your public URLs

## Manual Usage

If you prefer to run tunnels manually:

### Backend Tunnel
```bash
cloudflared tunnel --url http://localhost:8000
```

### Frontend Tunnel
```bash
cloudflared tunnel --url http://localhost:3000
```

## Getting Your URLs

When you run a tunnel, you'll see output like:

```
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
|  https://example-1234.trycloudflare.com                                                    |
+--------------------------------------------------------------------------------------------+
```

Copy the URL and share it with your testers!

## Tips

1. **URLs Change Each Time**: Cloudflare Tunnel generates new URLs each time you start it. If you need a persistent URL, you'll need to set up a named tunnel (requires Cloudflare account).

2. **Both Tunnels Needed**: You need both backend and frontend tunnels running for the app to work properly.

3. **Check Tunnel Windows**: On Windows, the tunnel URLs will appear in the separate command windows that open.

4. **Log Files**: On Linux/macOS, check `/tmp/cloudflare-backend.log` and `/tmp/cloudflare-frontend.log` for tunnel URLs.

## Troubleshooting

### "cloudflared not found"
- Make sure cloudflared is in your PATH
- Or place `cloudflared.exe` (Windows) or `cloudflared` (macOS/Linux) in the project root

### Tunnel not connecting
- Make sure your local servers are running first
- Check that ports 8000 and 3000 are not blocked by firewall
- Wait a few seconds for tunnels to establish

### URLs not working
- Tunnels take a few seconds to become active
- Make sure both backend and frontend servers are running
- Check the tunnel output for any error messages

## Advanced: Named Tunnels (Persistent URLs)

If you want the same URL every time, you can set up a named tunnel:

1. Sign up for a free Cloudflare account: https://dash.cloudflare.com/sign-up
2. Create a named tunnel:
   ```bash
   cloudflared tunnel create my-tunnel
   ```
3. Configure routes:
   ```bash
   cloudflared tunnel route dns my-tunnel example.com
   ```

For most development purposes, the quick tunnels (no account needed) work perfectly!




