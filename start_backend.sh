#!/bin/bash

echo "🚀 Starting ADK Research Agent Backend"
echo "====================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create one based on .env.example"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies if needed
if [ ! -f "adk-backend/requirements.txt" ]; then
    echo "❌ Requirements file not found"
    exit 1
fi

echo "📥 Checking dependencies..."
pip install -r adk-backend/requirements.txt > /dev/null 2>&1

# Start the backend
echo "🔧 Starting backend server..."
cd adk-backend
python app.py