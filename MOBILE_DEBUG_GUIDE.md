# Mobile Debugging Guide for iPhone

## The Problem
Chrome on iPhone is actually just a wrapper around Safari's WebKit engine (Apple's restriction), so you can't use Chrome DevTools directly on iPhone.

## Solution Options

### Option 1: Use Safari Web Inspector (Requires Mac)

**Steps:**
1. **On iPhone:**
   - Go to **Settings** → **Safari** → **Advanced**
   - Enable **Web Inspector**

2. **On Mac:**
   - Connect iPhone to Mac via USB
   - Open **Safari** on Mac
   - Go to **Develop** menu → Select your iPhone → Select the webpage
   - Safari DevTools will open (similar to Chrome DevTools)

**Note:** This only works with Safari browser on iPhone, not Chrome.

---

### Option 2: Use the Built-in Debug Panel (Easiest!)

I've added a mobile-friendly debug panel to your app! 

**To enable it:**

1. **In Development:** The panel shows automatically
2. **In Production:** Add `?debug=true` to your URL:
   - `http://10.0.0.76:3000/auth/login?debug=true`

**The debug panel shows:**
- ✅ Current API URL being used
- ✅ Network connection status
- ✅ Authentication token status
- ✅ Backend connection test button
- ✅ LocalStorage keys
- ✅ Recent errors
- ✅ Device information

**How to use:**
1. Open your app on iPhone
2. Add `?debug=true` to the URL if needed
3. Look for the **🐛 Debug Panel** button at the bottom of the screen
4. Tap it to expand and see all debug information
5. Use "Test Backend Connection" to verify backend is reachable

---

### Option 3: Use Remote Debugging Tools

#### A. Eruda (Mobile Console)
Add this to your app temporarily:

```html
<script src="https://cdn.jsdelivr.net/npm/eruda"></script>
<script>eruda.init();</script>
```

This creates a floating console button on your mobile screen.

#### B. vConsole (Alternative)
Similar to Eruda, provides a mobile-friendly console.

---

### Option 4: Use Desktop Browser with Mobile View

1. Open Chrome on your PC
2. Press `F12` to open DevTools
3. Click the device toggle icon (or press `Ctrl+Shift+M`)
4. Select "iPhone" from device list
5. Test your app at `http://10.0.0.76:3000`

**Limitation:** This won't catch network-specific issues, but good for UI debugging.

---

## Recommended Approach

**For your login issue, I recommend:**

1. **Use the Debug Panel** (Option 2) - It's already built into your app!
   - Add `?debug=true` to your login URL
   - Check if API URL is correct
   - Test backend connection
   - Check authentication status

2. **If you have a Mac**, use Safari Web Inspector (Option 1) for detailed console logs

3. **For quick testing**, use desktop Chrome with mobile view (Option 4)

---

## Quick Test Steps

1. **On iPhone, open:** `http://10.0.0.76:3000/auth/login?debug=true`
2. **Look for the debug panel** at the bottom
3. **Check the API URL** - should show `http://10.0.0.76:8000`
4. **Click "Test Backend Connection"** - should show success
5. **Try logging in** and watch the debug panel for errors

---

## Troubleshooting

**Debug panel not showing?**
- Make sure you're in development mode OR added `?debug=true` to URL
- Check browser console for errors (if accessible)

**Backend connection test fails?**
- Verify backend is running on port 8000
- Check Windows Firewall allows connections
- Ensure both devices on same network
- Try accessing `http://10.0.0.76:8000/health` directly in mobile browser

**Still can't see console?**
- Use the debug panel (it shows all the important info)
- Or use Safari Web Inspector if you have a Mac
- Or add Eruda script temporarily for a mobile console

---

## What the Debug Panel Shows

When you expand the debug panel, you'll see:

```
🐛 Debug Panel
├─ API Configuration
│  ├─ API URL: http://10.0.0.76:8000
│  ├─ Origin: http://10.0.0.76:3000
│  └─ Network: online
├─ Authentication
│  └─ ✓ Session token found (or ✗ No session token)
├─ Test Backend Connection [Button]
├─ LocalStorage (X keys)
├─ Recent Errors (if any)
└─ Device Info
```

This gives you all the information you need to debug the login issue without needing a console!



