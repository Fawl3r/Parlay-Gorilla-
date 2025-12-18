# 🚀 Quick Network Testing

## Start Servers (Network Mode)

**Windows:**
```bash
start.bat
```

**Mac/Linux:**
```bash
./start.sh
```

## Share These URLs

After starting, the script will show your IP. Share:

```
Frontend: http://YOUR_IP:3000
Backend:  http://YOUR_IP:8000
```

## Important Notes

✅ **All devices must be on the same Wi-Fi/network**

✅ **Firewall:** Allow ports 3000 and 8000 (see NETWORK_TESTING_GUIDE.md)

✅ **Auto-detection:** Frontend automatically connects to backend on same IP

## Troubleshooting

**Can't connect?**
1. Check firewall settings
2. Verify same network
3. Try `http://localhost:3000` on your machine first

**CORS errors?**
- Backend is already configured for network IPs
- Check browser console for specific error

**Need help?**
- See `NETWORK_TESTING_GUIDE.md` for detailed instructions




