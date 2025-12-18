#!/bin/bash

echo "========================================"
echo "Parlay Gorilla - Cloudflare Tunnel Setup"
echo "Share your app with remote users (FREE)"
echo "========================================"
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "ERROR: cloudflared is not installed"
    echo ""
    echo "Please install cloudflared:"
    echo "1. Download from: https://github.com/cloudflare/cloudflared/releases"
    echo "2. Extract and add to PATH"
    echo "   OR place it in this directory"
    echo "3. No account or authentication needed!"
    echo ""
    echo "Quick install options:"
    echo "  macOS:   brew install cloudflared"
    echo "  Linux:   Download from GitHub releases"
    echo "  Windows: Download .exe from GitHub releases"
    echo ""
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers and tunnels..."
    kill $BACKEND_PID $FRONTEND_PID $BACKEND_TUNNEL_PID $FRONTEND_TUNNEL_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

echo "Starting Backend Server..."
cd backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

echo "Starting Frontend Server..."
cd frontend
npm run dev:network &
FRONTEND_PID=$!
cd ..

# Wait a bit for frontend to start
sleep 5

echo ""
echo "========================================"
echo "Starting Cloudflare Tunnels..."
echo "========================================"
echo ""

echo "Starting Backend Tunnel (port 8000)..."
cloudflared tunnel --url http://localhost:8000 > /tmp/cloudflare-backend.log 2>&1 &
BACKEND_TUNNEL_PID=$!

sleep 2

echo "Starting Frontend Tunnel (port 3000)..."
cloudflared tunnel --url http://localhost:3000 > /tmp/cloudflare-frontend.log 2>&1 &
FRONTEND_TUNNEL_PID=$!

sleep 3

echo ""
echo "========================================"
echo "Tunnels are starting..."
echo ""
echo "IMPORTANT: Get your public URLs from the tunnel output above"
echo ""
echo "Each tunnel will show a URL like:"
echo "  https://xxxx-xxxx-xxxx.trycloudflare.com"
echo ""
echo "Backend tunnel URL:  Check the output above for port 8000"
echo "Frontend tunnel URL: Check the output above for port 3000"
echo ""
echo "You can also check the log files:"
echo "  Backend:  /tmp/cloudflare-backend.log"
echo "  Frontend: /tmp/cloudflare-frontend.log"
echo ""
echo "Share the FRONTEND URL with your testers!"
echo ""
echo "The frontend will automatically connect to the backend tunnel."
echo "========================================"
echo ""
echo "Press Ctrl+C to stop all servers and tunnels"

# Wait for processes
wait




