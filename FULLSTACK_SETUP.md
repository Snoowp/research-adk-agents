# 🚀 Full Stack Setup Guide

## Quick Start (Recommended)

Run the automated setup script:

```bash
./run_full_stack.sh
```

This will start both the backend and frontend automatically.

## Manual Setup

### Terminal 1 - Backend Server

```bash
# Set your Google API key
export GOOGLE_API_KEY=your_api_key_here
export GOOGLE_GENAI_USE_VERTEXAI=FALSE

# Activate virtual environment and start backend
source .venv/bin/activate
cd adk-backend
python app.py
```

Backend will start on: `http://localhost:8000`

### Terminal 2 - Frontend Development Server

```bash
# Install dependencies (first time only)
cd frontend
npm install

# Start development server
npm run dev
```

Frontend will start on: `http://localhost:5173`

## 🔗 How It Works

### Frontend → Backend Connection

1. **Vite Proxy**: Frontend dev server proxies `/api/*` requests to `http://localhost:8000`
2. **SSE Streaming**: React app connects to `/api/adk-research-stream`
3. **Enhanced Orchestrator**: Backend runs our 5-feature enhanced research workflow
4. **Real-time Updates**: Events stream to frontend for live progress tracking

### API Flow

```
User Input → React Frontend → Vite Proxy → ADK Backend → Enhanced Orchestrator
     ↓
Question Processing → Query Generation → Web Search → Reflection → Answer Synthesis
     ↓
SSE Events ← Timeline Updates ← Real-time Progress ← Frontend
```

### Supported Models

The frontend includes model selectors for:
- **Gemini 2.0 Flash** (fast, efficient)
- **Gemini 2.5 Flash** (latest, improved)  
- **Gemini 2.5 Pro** (highest quality)

### Effort Levels

- **Low**: 1 query, 1 research loop
- **Medium**: 3 queries, 3 research loops  
- **High**: 5 queries, 10 research loops

## 🧪 Testing

Test the full stack setup:

```bash
./test_full_stack.sh
```

## 🔧 Development

### Backend Development

The backend uses our enhanced orchestrator with:
- ✅ Real LLM query generation
- ✅ Real web searches with google_search
- ✅ Real reflection/quality analysis  
- ✅ Real answer synthesis
- ✅ Iterative research loops

### Frontend Development

The frontend features:
- Modern React with TypeScript
- Real-time SSE streaming
- Activity timeline with live updates
- Model and effort level selection
- Responsive chat interface
- Markdown rendering with citations

## 📡 API Endpoints

- **POST** `/api/adk-research-stream` - Main research endpoint with SSE streaming
- **GET** `/health` - Backend health check
- **POST** `/api/adk-research-session` - Create session (alternative)

## 🎯 What You'll See

1. **Welcome Screen**: Clean interface with model/effort selectors
2. **Live Research Progress**: Real-time timeline showing:
   - Query generation phase
   - Web research phase with source gathering
   - Reflection phase with sufficiency analysis
   - Answer synthesis phase
3. **Final Results**: Comprehensive answers with proper citations
4. **Chat History**: Full conversation with copy functionality

## 🔍 Troubleshooting

### Backend Issues
- Check API key is set: `echo $GOOGLE_API_KEY`
- Check virtual environment: `source .venv/bin/activate`
- Check port 8000 is free: `lsof -i:8000`

### Frontend Issues  
- Check Node.js version: `node --version` (needs 16+)
- Check dependencies: `cd frontend && npm install`
- Check port 5173 is free: `lsof -i:5173`

### Connection Issues
- Backend health: `curl http://localhost:8000/health`
- API test: `curl -X POST http://localhost:8000/api/adk-research-stream -H "Content-Type: application/json" -d '{"question":"test","effort_level":"low","reasoning_model":"gemini-2.0-flash-exp"}'`

## 🎉 Success!

When working correctly, you'll see:
- Backend: `✅ ADK Research Agent starting up...`  
- Frontend: `Local: http://localhost:5173/`
- Proxy: API calls automatically forwarded to backend
- Real-time research workflow with all 5 enhanced features!