#!/bin/bash
#
# Full Stack Development Runner
# Starts both the ADK backend and React frontend
#

set -e

echo "🚀 Starting ADK Research Agent Full Stack"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i:"$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ Node.js/npm is required but not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo

# Check environment variables
echo -e "${BLUE}Checking environment configuration...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "   Please create .env file based on .env.example"
    exit 1
fi

echo -e "${GREEN}✅ Environment configuration found${NC}"

# Check if ports are available
if port_in_use 8000; then
    echo -e "${RED}❌ Port 8000 is already in use (needed for backend)${NC}"
    exit 1
fi

if port_in_use 5173; then
    echo -e "${YELLOW}⚠️  Port 5173 is already in use (frontend will try another port)${NC}"
fi

# Install backend dependencies
echo -e "${BLUE}Installing backend dependencies...${NC}"
cd adk-backend
if [ ! -d "../.venv" ]; then
    echo "Creating Python virtual environment..."
    cd ..
    python3 -m venv .venv
    cd adk-backend
fi

source ../.venv/bin/activate
pip install -r requirements.txt
echo -e "${GREEN}✅ Backend dependencies installed${NC}"
echo

# Install frontend dependencies
echo -e "${BLUE}Installing frontend dependencies...${NC}"
cd ../frontend
npm install
echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
echo

# Create log directory
mkdir -p ../logs

# Start backend in background
echo -e "${BLUE}Starting ADK backend server...${NC}"
cd ../adk-backend
source ../.venv/bin/activate

# Start backend server
nohup python app.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
echo "   Backend logs: tail -f logs/backend.log"

# Wait a moment for backend to start
sleep 3

# Check if backend is running
if ! port_in_use 8000; then
    echo -e "${RED}❌ Backend failed to start on port 8000${NC}"
    echo "Check logs/backend.log for details"
    exit 1
fi

# Start frontend
echo -e "${BLUE}Starting React frontend...${NC}"
cd ../frontend

# Start frontend (this will block)
npm run dev &
FRONTEND_PID=$!

echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
echo

echo "🎉 Full stack is running!"
echo "================================"
echo -e "${GREEN}Backend:${NC}  http://localhost:8000"
echo -e "${GREEN}Frontend:${NC} http://localhost:5173"
echo -e "${GREEN}Health:${NC}   http://localhost:8000/health"
echo
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    fi
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Backend stopped${NC}"
    fi
    
    echo -e "${GREEN}🏁 All services stopped${NC}"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Wait for frontend process
wait $FRONTEND_PID