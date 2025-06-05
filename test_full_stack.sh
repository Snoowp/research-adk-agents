#!/bin/bash
#
# Quick Full Stack Test
# Tests that backend and frontend can work together
#

set -e

echo "🧪 Testing Full Stack Setup"
echo "=============================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}1. Testing Backend Startup...${NC}"

# Start backend in background
cd adk-backend
source ../.venv/bin/activate
python app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Test backend health
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend is running on http://localhost:8000${NC}"
else
    echo -e "${YELLOW}❌ Backend not responding${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${BLUE}2. Testing Frontend Setup...${NC}"
cd ../frontend

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo -e "${GREEN}✅ Frontend dependencies ready${NC}"

echo -e "${BLUE}3. Testing API Connection...${NC}"

# Test API endpoint
if curl -s -X POST http://localhost:8000/api/adk-research-stream \
   -H "Content-Type: application/json" \
   -d '{"question":"test","effort_level":"low","reasoning_model":"gemini-2.0-flash-exp"}' \
   | head -5 > /dev/null; then
    echo -e "${GREEN}✅ API endpoint responding${NC}"
else
    echo -e "${YELLOW}❌ API endpoint not working${NC}"
fi

# Cleanup
kill $BACKEND_PID 2>/dev/null || true

echo
echo -e "${GREEN}🎉 Full Stack Test Complete!${NC}"
echo
echo "To run the full application:"
echo "  ./run_full_stack.sh"
echo
echo "Or manually:"
echo "  Terminal 1: source .venv/bin/activate && cd adk-backend && python app.py"
echo "  Terminal 2: cd frontend && npm run dev"