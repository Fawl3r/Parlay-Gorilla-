# LocalTunnel Setup Guide

This guide shows you how to expose your local development server to the internet using LocalTunnel - a simple npm-based alternative to ngrok.

## Why LocalTunnel?

- ✅ **100% Free** - No account required
- ✅ **Easy Setup** - Just one npm install
- ✅ **No Installation** - Uses npm (you already have it!)
- ✅ **Simple URLs** - Clean `xxxx.loca.lt` domains
- ✅ **HTTPS by Default** - Secure connections

## Installation

Since you already have npm installed, just run:

```bash
npm install -g localtunnel
```

Or on Windows:
```cmd
npm install -g localtunnel
```

## Usage

### Quick Start (Windows)

1. Run the tunnel script:
   ```cmd
   start-localtunnel.bat
   ```

2. The script will:
   - Install localtunnel if needed
   - Start your backend server (port 8000)
   - Start your frontend server (port 3000)
   - Create two LocalTunnel tunnels

3. Check the tunnel windows for your public URLs:
   - Each tunnel will display a URL like: `https://xxxx.loca.lt`
   - Backend URL: Use for API calls
   - Frontend URL: Share with testers

### Manual Usage

If you prefer to run tunnels manually:

#### Backend Tunnel
```bash
lt --port 8000
```

#### Frontend Tunnel
```bash
lt --port 3000
```

#### Custom Subdomain (if available)
```bash
lt --port 3000 --subdomain myapp
```

## Getting Your URLs

When you run a tunnel, you'll see output like:

```
your url is: https://random-name.loca.lt
```

Copy the URL and share it with your testers!

## Tips

1. **URLs Change Each Time**: LocalTunnel generates new URLs each time. Use `--subdomain` for a custom name (if available).

2. **Both Tunnels Needed**: You need both backend and frontend tunnels running.

3. **Check Tunnel Windows**: On Windows, the tunnel URLs will appear in the separate command windows.

4. **First Visit**: The first time someone visits your tunnel URL, they'll see a warning page. Click "Continue" to proceed.

## Troubleshooting

### "lt command not found"
- Make sure localtunnel is installed globally: `npm install -g localtunnel`
- Restart your terminal after installation

### Tunnel not connecting
- Make sure your local servers are running first
- Check that ports 8000 and 3000 are not blocked by firewall
- Wait a few seconds for tunnels to establish

### URLs not working
- Tunnels take a few seconds to become active
- Make sure both backend and frontend servers are running
- Check the tunnel output for any error messages
- First-time visitors need to click "Continue" on the warning page

## Comparison: LocalTunnel vs Cloudflare Tunnel

| Feature | LocalTunnel | Cloudflare Tunnel |
|---------|-------------|-------------------|
| Setup | npm install | Download binary |
| URLs | xxxx.loca.lt | xxxx.trycloudflare.com |
| Speed | Good | Excellent |
| Reliability | Good | Excellent |
| Custom Domain | Limited | Yes (with account) |

Both are great free options! Choose based on your preference.




