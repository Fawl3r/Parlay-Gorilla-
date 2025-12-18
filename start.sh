#!/bin/bash

echo "========================================"
echo "Parlay Gorilla - Development Server"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed or not in PATH"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
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

# Get local IP address
get_local_ip() {
    # Try different methods to get local IP
    if command -v ip &> /dev/null; then
        # Linux
        ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' | head -1
    elif command -v ifconfig &> /dev/null; then
        # macOS/Linux fallback
        ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1
    else
        echo "Unable to detect IP"
    fi
}

LOCAL_IP=$(get_local_ip)

echo ""
echo "========================================"
echo "Servers are running..."
echo ""
echo "LOCAL ACCESS:"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
if [ ! -z "$LOCAL_IP" ]; then
    echo "NETWORK ACCESS:"
    echo "Share these URLs with testers:"
    echo "Backend:  http://$LOCAL_IP:8000"
    echo "Frontend: http://$LOCAL_IP:3000"
    echo ""
    echo "Your IP Address: $LOCAL_IP"
fi
echo "========================================"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for both processes
wait

