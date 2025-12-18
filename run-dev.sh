#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "  F3 Parlay Gorilla - Development Mode"
echo "========================================"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}[INFO] Shutting down servers...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    echo -e "${GREEN}[SUCCESS] All servers stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}[ERROR] Python is not installed or not in PATH${NC}"
    echo "Please install Python 3.8+ and add it to your PATH"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js is not installed or not in PATH${NC}"
    echo "Please install Node.js 18+ and add it to your PATH"
    exit 1
fi

# Check if backend directory exists
if [ ! -f "backend/app/main.py" ]; then
    echo -e "${RED}[ERROR] Backend directory structure not found${NC}"
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}[WARNING] Frontend node_modules not found${NC}"
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to install frontend dependencies${NC}"
        exit 1
    fi
    cd ..
    echo -e "${GREEN}[SUCCESS] Frontend dependencies installed${NC}"
fi

# Check if ports are in use
check_port() {
    local port=$1
    if command -v lsof &> /dev/null; then
        lsof -i :$port > /dev/null 2>&1
        return $?
    elif command -v netstat &> /dev/null; then
        netstat -an | grep -q ":$port.*LISTEN"
        return $?
    elif command -v ss &> /dev/null; then
        ss -lnt | grep -q ":$port"
        return $?
    fi
    return 1
}

if check_port 8000; then
    echo -e "${YELLOW}[WARNING] Port 8000 is already in use${NC}"
    echo "Backend may fail to start. Please free the port or stop the existing process."
    sleep 2
fi

if check_port 3000; then
    echo -e "${YELLOW}[WARNING] Port 3000 is already in use${NC}"
    echo "Frontend may fail to start. Please free the port or stop the existing process."
    sleep 2
fi

# Start backend server
echo ""
echo -e "${BLUE}[INFO] Starting Backend Server (port 8000)...${NC}"
cd backend
$PYTHON_CMD -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to initialize
echo -e "${BLUE}[INFO] Waiting for backend to initialize...${NC}"
sleep 4

# Start frontend server
echo -e "${BLUE}[INFO] Starting Frontend Server (port 3000)...${NC}"
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Get local IP address
get_local_ip() {
    if command -v ip &> /dev/null; then
        # Linux
        ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' | head -1
    elif command -v ifconfig &> /dev/null; then
        # macOS/Linux fallback
        ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1
    else
        echo ""
    fi
}

LOCAL_IP=$(get_local_ip)

# Display server information
echo ""
echo "========================================"
echo "  Servers Running"
echo "========================================"
echo ""
echo -e "${GREEN}LOCAL ACCESS:${NC}"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo ""

if [ ! -z "$LOCAL_IP" ]; then
    echo -e "${GREEN}NETWORK ACCESS:${NC}"
    echo "  Backend:  http://$LOCAL_IP:8000"
    echo "  Frontend: http://$LOCAL_IP:3000"
    echo ""
    echo "Your IP Address: $LOCAL_IP"
    echo ""
fi

echo "========================================"
echo ""
echo -e "${BLUE}[INFO] Backend PID: $BACKEND_PID${NC}"
echo -e "${BLUE}[INFO] Frontend PID: $FRONTEND_PID${NC}"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo "  Backend:  ./backend.log"
echo "  Frontend: ./frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Wait for both processes
wait



