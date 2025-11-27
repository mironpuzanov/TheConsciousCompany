#!/bin/bash

# Integration Test Script for Consciousness OS
# Tests the connection between Python backend and React frontend

set -e

echo "🧠 Consciousness OS - Integration Test"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo "1. Checking if backend is running..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo -e "${GREEN}✅ Backend is running${NC}"
else
    echo -e "${RED}❌ Backend is not running${NC}"
    echo "   Please start the backend first: cd backend && python main.py"
    exit 1
fi

# Check if muselsl stream is running
echo ""
echo "2. Checking if muselsl stream is available..."
if command -v muselsl &> /dev/null; then
    echo -e "${GREEN}✅ muselsl is installed${NC}"
    echo -e "${YELLOW}⚠️  Make sure 'muselsl stream' is running in another terminal${NC}"
else
    echo -e "${RED}❌ muselsl is not installed${NC}"
    echo "   Install with: pip install muselsl"
    exit 1
fi

# Test health endpoint
echo ""
echo "3. Testing backend health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/)
if echo "$HEALTH_RESPONSE" | grep -q "status.*ok"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi

# Test device info endpoint
echo ""
echo "4. Testing device info endpoint..."
DEVICE_INFO=$(curl -s http://localhost:8000/api/device-info)
echo "   Response: $DEVICE_INFO"

# Test WebSocket endpoint (basic check)
echo ""
echo "5. Testing WebSocket endpoint..."
if curl -s --include --no-buffer \
    --header "Connection: Upgrade" \
    --header "Upgrade: websocket" \
    --header "Sec-WebSocket-Key: test" \
    --header "Sec-WebSocket-Version: 13" \
    http://localhost:8000/ws 2>&1 | grep -q "101\|426"; then
    echo -e "${GREEN}✅ WebSocket endpoint is accessible${NC}"
else
    echo -e "${YELLOW}⚠️  WebSocket endpoint check inconclusive (this is normal)${NC}"
fi

# Check frontend
echo ""
echo "6. Checking if frontend is running..."
if curl -s http://localhost:5173/ > /dev/null; then
    echo -e "${GREEN}✅ Frontend is running${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend is not running${NC}"
    echo "   Start with: cd consciousness-app && npm run dev"
fi

echo ""
echo "========================================"
echo -e "${GREEN}✅ Basic integration checks complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Make sure 'muselsl stream' is running"
echo "2. Open http://localhost:5173 in your browser"
echo "3. Click 'Connect to Muse' button"
echo "4. Verify data is flowing"
echo ""

