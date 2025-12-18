#!/bin/bash

echo "========================================"
echo "Parlay Gorilla - Tunnel Setup"
echo "Share your app with remote users"
echo "========================================"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "ERROR: ngrok is not installed or not in PATH"
    echo ""
    echo "Please install ngrok:"
    echo "1. Download from: https://ngrok.com/download"
    echo "2. Extract and add to PATH"
    echo "3. Sign up at: https://dashboard.ngrok.com/signup"
    echo "4. Get your auth token and run: ngrok authtoken YOUR_TOKEN"
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
echo "Starting Tunnels..."
echo "========================================"
echo ""

echo "Starting Backend Tunnel (port 8000)..."
ngrok http 8000 > /tmp/ngrok-backend.log 2>&1 &
BACKEND_TUNNEL_PID=$!

sleep 2

echo "Starting Frontend Tunnel (port 3000)..."
ngrok http 3000 > /tmp/ngrok-frontend.log 2>&1 &
FRONTEND_TUNNEL_PID=$!

sleep 3

echo ""
echo "========================================"
echo "Tunnels are starting..."
echo ""
echo "IMPORTANT: Get your public URLs from ngrok:"
echo ""
echo "Option 1: Visit http://localhost:4040 in your browser"
echo "Option 2: Check the ngrok web interface"
echo ""
echo "Backend tunnel:  https://xxxx-xx-xx-xx-xx.ngrok-free.app (port 8000)"
echo "Frontend tunnel: https://xxxx-xx-xx-xx-xx.ngrok-free.app (port 3000)"
echo ""
echo "Share the FRONTEND URL with your testers!"
echo ""
echo "The frontend will automatically connect to the backend tunnel."
echo "========================================"
echo ""
echo "Press Ctrl+C to stop all servers and tunnels"

# Wait for processes
wait




