#!/bin/bash

# Start all Consciousness OS services
# This script starts: LSL stream, Backend, and Frontend

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🧠 Starting Consciousness OS Services"
echo "======================================"
echo ""

# Check if processes are already running
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Kill existing processes on ports if needed
echo "Checking for existing processes..."
if check_port 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is in use. Killing existing process...${NC}"
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

if check_port 5173; then
    echo -e "${YELLOW}⚠️  Port 5173 is in use. Killing existing process...${NC}"
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Check for muselsl processes
if pgrep -f "muselsl stream" > /dev/null; then
    echo -e "${YELLOW}⚠️  muselsl stream is already running${NC}"
    echo "   Stopping existing muselsl stream..."
    pkill -f "muselsl stream" 2>/dev/null || true
    sleep 1
fi

echo ""
echo "Starting services..."
echo ""

# Activate backend venv
BACKEND_VENV="backend/venv"
if [ ! -d "$BACKEND_VENV" ]; then
    BACKEND_VENV="venv"
fi

if [ ! -d "$BACKEND_VENV" ]; then
    echo -e "${RED}❌ Python virtual environment not found${NC}"
    echo "   Please run: python3 -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt"
    exit 1
fi

# Start backend in background
echo -e "${GREEN}1. Starting Backend (FastAPI on port 8000)...${NC}"
cd "$(dirname "$0")"
source "$BACKEND_VENV/bin/activate" 2>/dev/null || source "venv/bin/activate"

# Start backend with output to log file (run from root, but set PYTHONPATH)
export PYTHONPATH="$(pwd):$PYTHONPATH"
cd backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
cd ..
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
echo "   Logs: backend/backend.log"
sleep 5  # Give backend time to fully start

# Check if backend started successfully
if check_port 8000; then
    echo -e "${GREEN}   ✅ Backend is running${NC}"
else
    echo -e "${YELLOW}   ⚠️  Backend may still be starting. Check backend/backend.log${NC}"
    echo "   Continuing anyway..."
fi

# Start frontend
echo ""
echo -e "${GREEN}2. Starting Frontend (Vite on port 5173)...${NC}"
cd consciousness-app

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}   Installing dependencies...${NC}"
    npm install
fi

# Start frontend in background
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"
echo "   Logs: frontend.log"
sleep 3

# Check if frontend started successfully
if check_port 5173; then
    echo -e "${GREEN}   ✅ Frontend is running${NC}"
else
    echo -e "${RED}   ❌ Frontend failed to start. Check frontend.log${NC}"
    exit 1
fi

cd ..

# Start Muse LSL stream with all sensors enabled (with retry loop)
echo ""
echo -e "${GREEN}3. Starting Muse LSL stream (with PPG, ACC, GYRO)...${NC}"
echo "   Will continuously search for Muse until you connect via web interface"
source "$BACKEND_VENV/bin/activate" 2>/dev/null || source "venv/bin/activate"
nohup bash muselsl_retry.sh > muselsl.log 2>&1 &
MUSE_PID=$!
echo "   Muse LSL PID: $MUSE_PID"
echo "   Logs: muselsl.log"
sleep 3

# Check if muselsl retry script started successfully
if pgrep -f "muselsl_retry.sh" > /dev/null || pgrep -f "muselsl stream" > /dev/null; then
    echo -e "${GREEN}   ✅ Muse LSL stream is running (searching for headband...)${NC}"
else
    echo -e "${YELLOW}   ⚠️  Muse LSL stream may still be starting${NC}"
    echo "   Check muselsl.log for connection status"
fi

echo ""
echo "======================================"
echo -e "${GREEN}✅ All services started!${NC}"
echo ""
echo "Services:"
echo "  • Backend:  http://localhost:8000"
echo "  • Frontend: http://localhost:5173"
echo "  • Muse LSL: Running (PPG, ACC, GYRO enabled)"
echo ""
echo "To stop all services:"
echo "  pkill -f 'uvicorn backend.main'"
echo "  pkill -f 'vite'"
echo "  pkill -f 'muselsl stream'"
echo ""
echo "Resource Usage:"
echo "  • Backend loads ML models on first request (throttled, ~2s delay between models)"
echo "  • Models stay in memory after first load (~2-4GB total)"
echo "  • M3 MacBook should handle this, but monitor Activity Monitor if issues occur"
echo ""

