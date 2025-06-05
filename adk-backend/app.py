"""FastAPI application for ADK research agent with streaming support."""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

# Set up environment for ADK
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY', '')
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = os.getenv('GOOGLE_GENAI_USE_VERTEXAI', 'FALSE')

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from services.adk_runner import ADKRunner, ADKSessionManager
# from models.schemas import ResearchState  # Remove this import for now


# Request/Response models
class ResearchRequest(BaseModel):
    question: str
    effort_level: str = "medium"  # low, medium, high
    reasoning_model: str = "gemini-2.0-flash-thinking-exp"


class SessionResponse(BaseModel):
    session_id: str
    status: str


# Global session manager
session_manager = ADKSessionManager()
adk_runner = ADKRunner(session_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    print("ADK Research Agent starting up...")
    yield
    # Shutdown
    print("ADK Research Agent shutting down...")


# Create FastAPI app
app = FastAPI(
    title="ADK Research Agent API",
    description="Google ADK-powered research agent with streaming support",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_effort_config(effort_level: str) -> Dict[str, int]:
    """Get configuration based on effort level."""
    configs = {
        "low": {
            "initial_search_query_count": 1,
            "max_research_loops": 1
        },
        "medium": {
            "initial_search_query_count": 3,
            "max_research_loops": 3
        },
        "high": {
            "initial_search_query_count": 5,
            "max_research_loops": 10
        }
    }
    return configs.get(effort_level, configs["medium"])


@app.post("/api/adk-research-session", response_model=SessionResponse)
async def create_research_session(request: ResearchRequest):
    """Create a new research session."""
    try:
        # Get effort configuration
        config = get_effort_config(request.effort_level)
        config["reasoning_model"] = request.reasoning_model
        
        # Create session
        session_id = await session_manager.create_session(
            user_question=request.question,
            config=config
        )
        
        return SessionResponse(session_id=session_id, status="created")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/adk-research-stream/{session_id}")
async def stream_research_results(session_id: str):
    """Stream research agent results via Server-Sent Events."""
    
    async def event_generator():
        """Generate SSE events for the research process."""
        session = session_manager.get_session(session_id)
        if not session:
            yield f"data: {json.dumps({'event': 'error', 'data': {'error': 'Session not found'}})}\n\n"
            return
        
        # state = ResearchState.parse_obj(session['state'])  # Simplify for now
        user_question = session.get('user_question', 'Unknown question')
        
        try:
            async for event in adk_runner.run_research_agent_stream(session_id, user_question):
                # Format as SSE
                event_data = json.dumps(event)
                yield f"data: {event_data}\n\n"
                
                # Small delay to ensure proper streaming
                await asyncio.sleep(0.1)
                
        except Exception as e:
            error_event = {
                "event": "error",
                "data": {"error": str(e)}
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@app.post("/api/adk-research-stream")
async def stream_research_direct(request: ResearchRequest):
    """Stream research results directly (alternative endpoint)."""
    
    async def event_generator():
        """Generate SSE events for the research process."""
        try:
            # Get effort configuration
            config = get_effort_config(request.effort_level)
            config["reasoning_model"] = request.reasoning_model
            
            # Create session
            session_id = await session_manager.create_session(
                user_question=request.question,
                config=config
            )
            
            # Frontend already adds the user message, so don't send it again
            
            # Stream research process
            async for event in adk_runner.run_research_agent_stream(session_id, request.question):
                # Clean and validate event data
                try:
                    # Ensure event is properly formatted dict
                    if isinstance(event, dict):
                        # Clean any content that might have newlines
                        if 'data' in event and isinstance(event['data'], dict):
                            for key, value in event['data'].items():
                                if isinstance(value, str):
                                    event['data'][key] = value.replace('\n', ' ').replace('\r', ' ')
                        
                        # Format as clean SSE
                        event_json = json.dumps(event, ensure_ascii=False)
                        yield f"data: {event_json}\n\n"
                except Exception as json_error:
                    # Skip malformed events
                    print(f"Skipping malformed event: {json_error}")
                    continue
                
                # Small delay to ensure proper streaming
                await asyncio.sleep(0.1)
                
        except Exception as e:
            error_event = {
                "event": "error",
                "data": {"error": str(e)}
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@app.get("/api/adk-research-session/{session_id}")
async def get_research_session(session_id: str):
    """Get session information."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@app.delete("/api/adk-research-session/{session_id}")
async def delete_research_session(session_id: str):
    """Delete a research session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_manager.cleanup_session(session_id)
    return {"message": "Session deleted successfully"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ADK Research Agent"}


# Serve static files (frontend)
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    @app.get("/app/{path:path}")
    async def serve_frontend(path: str):
        """Serve frontend application."""
        file_path = os.path.join(frontend_path, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Fallback to index.html for SPA routing
        return FileResponse(os.path.join(frontend_path, "index.html"))
    
    @app.get("/app")
    async def serve_frontend_root():
        """Serve frontend root."""
        return FileResponse(os.path.join(frontend_path, "index.html"))


if __name__ == "__main__":
    # Configure logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run with uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )