"""ADK Runner service for managing agent execution and session state."""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, AsyncGenerator
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import enhanced orchestrator only
from agents.enhanced_orchestrator import create_enhanced_research_orchestrator


class ADKSessionManager:
    """Manages ADK agent sessions using proper ADK patterns."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_service = InMemorySessionService()
        self.runners: Dict[str, Runner] = {}
    
    async def create_session(self, user_question: str, config: Dict[str, Any] = None) -> str:
        """Create a new ADK session for a research task."""
        session_id = str(uuid.uuid4())
        app_name = f"research_agent_{session_id}"
        user_id = "research_user"
        
        # Create ADK session
        adk_session = await self.session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        # Store session data
        self.sessions[session_id] = {
            'user_question': user_question,
            'config': config or {},
            'status': 'created',
            'app_name': app_name,
            'user_id': user_id,
            'adk_session': adk_session
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        return self.sessions.get(session_id)
    
    def create_runner(self, session_id: str) -> Runner:
        """Create an ADK runner for the session."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        config = session['config']
        
        # Create enhanced research orchestrator with reflection loops
        from google.adk.agents import LlmAgent
        from google.adk.tools import google_search
        
        # Use the selected model from frontend for all agents (query_model and reasoning_model)
        selected_model = config.get('reasoning_model', 'gemini-2.0-flash-exp')
        
        research_agent = create_enhanced_research_orchestrator(
            query_model=selected_model,  # Use selected model for query generation
            reasoning_model=selected_model,  # Use selected model for reasoning/reflection
            max_loops=config.get('max_research_loops', 3),
            initial_queries=config.get('initial_search_query_count', 3)
        )
        
        # Create ADK runner
        runner = Runner(
            agent=research_agent,
            app_name=session['app_name'],
            session_service=self.session_service
        )
        
        self.runners[session_id] = runner
        return runner
    
    def get_runner(self, session_id: str) -> Optional[Runner]:
        """Get active runner for session."""
        return self.runners.get(session_id)
    
    def cleanup_session(self, session_id: str):
        """Clean up session resources."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.runners:
            del self.runners[session_id]
    


class ADKRunner:
    """Runs ADK agents using proper ADK patterns."""
    
    def __init__(self, session_manager: ADKSessionManager):
        self.session_manager = session_manager
    
    async def run_research_agent_stream(
        self,
        session_id: str,
        user_question: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Run the research agent using ADK and yield streaming events."""
        
        try:
            # Get or create runner
            runner = self.session_manager.get_runner(session_id)
            if not runner:
                runner = self.session_manager.create_runner(session_id)
            
            # Get session data
            session = self.session_manager.get_session(session_id)
            if not session:
                yield {"event": "error", "data": {"error": "Session not found"}}
                return
            
            # Update session status
            session['status'] = 'running'
            
            # Yield start event
            yield {
                "event": "start",
                "data": {"message": "Starting research agent", "session_id": session_id}
            }
            
            # Frontend already adds the user message, no need to echo it back
            
            # Create user message for ADK
            user_content = types.Content(
                role='user', 
                parts=[types.Part(text=user_question)]
            )
            
            # Track current step for progress reporting
            current_step = ""
            reflection_count = 0
            web_search_count = 0
            
            # Run the ADK agent and stream events
            async for event in runner.run_async(
                user_id=session['user_id'],
                session_id=session_id,
                new_message=user_content
            ):
                # Debug: Log all events
                content_preview = "No content"
                if event.content and event.content.parts and event.content.parts[0].text:
                    content_preview = event.content.parts[0].text[:50]
                print(f"🔍 EVENT: Author={event.author}, IsFinal={event.is_final_response()}, Content={content_preview}...")
                print(f"   Event type: {type(event).__name__}, Has actions: {bool(event.actions)}")
                if hasattr(event, 'turn_complete'):
                    print(f"   Turn complete: {event.turn_complete}")
                else:
                    print("   Turn complete: Not set")
                    
                # Additional debugging for Event attributes
                print(f"   Event dir: {[attr for attr in dir(event) if not attr.startswith('_') and 'turn' in attr.lower()]}")
                
                # Map ADK events to our streaming format - enhanced orchestrator detection
                if hasattr(event, 'author') and event.author:
                    # Detect different phases based on which agent is currently active
                    if event.author == "query_generator":
                        if current_step != "generate_query":
                            current_step = "generate_query"
                            yield {"event": "generate_query", "data": {"status": "running"}}
                    
                    elif event.author == "web_searcher":
                        # Track web search iterations
                        web_search_count += 1
                        
                        # Extract source information from grounding metadata
                        sources_gathered = []
                        
                        # Debug logging
                        print(f"\n🔍 Web Search Event #{web_search_count}:")
                        print(f"   Has grounding_metadata: {hasattr(event, 'grounding_metadata')}")
                        if hasattr(event, 'grounding_metadata'):
                            print(f"   grounding_metadata is None: {event.grounding_metadata is None}")
                            if event.grounding_metadata:
                                print(f"   grounding_chunks: {hasattr(event.grounding_metadata, 'grounding_chunks')}")
                        
                        # Try multiple ways to extract sources
                        # Method 1: Direct grounding metadata
                        if hasattr(event, 'grounding_metadata') and event.grounding_metadata:
                            grounding_chunks = event.grounding_metadata.grounding_chunks or []
                            print(f"   Number of grounding chunks: {len(grounding_chunks)}")
                            for chunk in grounding_chunks:
                                if hasattr(chunk, 'web') and chunk.web:
                                    source = {
                                        "label": chunk.web.title or "Unknown Source",
                                        "url": chunk.web.uri or ""
                                    }
                                    if source["url"]:
                                        sources_gathered.append(source)
                        
                        # Method 2: Check session state for search results with URLs
                        if not sources_gathered:
                            try:
                                # Get the ADK session from the session manager
                                adk_session = self.session_manager.get_session(session_id)
                                if adk_session and 'adk_session' in adk_session:
                                    # Get the search results from ADK session state
                                    search_results = adk_session['adk_session'].state.get("search_results", "")
                                if search_results and isinstance(search_results, str):
                                    # Extract URLs from the search results text
                                    import re
                                    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:\.[^\s<>"{}|\\^`\[\]]+)+'
                                    urls = re.findall(url_pattern, search_results)
                                    
                                    # Extract domain names as labels
                                    for url in urls[:5]:  # Limit to first 5 URLs
                                        domain = url.split('/')[2] if '/' in url else url
                                        sources_gathered.append({
                                            "label": domain,
                                            "url": url
                                        })
                            except Exception as e:
                                print(f"Error extracting sources from session: {e}")
                        
                        iteration_msg = f" (Iteration {web_search_count})" if web_search_count > 1 else ""
                        yield {
                            "event": "web_research", 
                            "data": {
                                "status": "running",
                                "sources_gathered": sources_gathered,
                                "message": f"Web Research{iteration_msg}",
                                "iteration": web_search_count
                            }
                        }
                        current_step = "web_research"
                    
                    elif event.author == "reflection_analyst":
                        # Track reflection iterations
                        reflection_count += 1
                        iteration_msg = f" (Iteration {reflection_count})" if reflection_count > 1 else ""
                        
                        # Try to extract reflection analysis from the event content
                        reflection_data = {"is_sufficient": False, "follow_up_queries": []}
                        if event.content and event.content.parts and event.content.parts[0].text:
                            content_text = event.content.parts[0].text
                            # Try to parse JSON from the reflection response
                            import json
                            import re
                            try:
                                # Extract JSON from markdown code blocks if present
                                json_match = re.search(r'```json\s*(.*?)\s*```', content_text, re.DOTALL)
                                if json_match:
                                    json_str = json_match.group(1)
                                    reflection_data = json.loads(json_str)
                                else:
                                    # Try direct JSON parse
                                    reflection_data = json.loads(content_text)
                            except:
                                # Fallback: look for keywords
                                if "sufficient" in content_text.lower() and "true" in content_text.lower():
                                    reflection_data["is_sufficient"] = True
                        
                        yield {
                            "event": "reflection", 
                            "data": {
                                "status": "running",
                                "message": f"Reflection{iteration_msg}",
                                "iteration": reflection_count,
                                "is_sufficient": reflection_data.get("is_sufficient", False),
                                "follow_up_queries": reflection_data.get("follow_up_queries", [])
                            }
                        }
                        current_step = "reflection"
                    
                    elif event.author == "answer_synthesizer":
                        if current_step != "finalize_answer":
                            current_step = "finalize_answer"
                            yield {"event": "finalize_answer", "data": {"status": "running"}}
                    
                    elif event.author == "enhanced_research_orchestrator":
                        # Handle orchestrator progress messages - but don't duplicate events
                        if event.content and event.content.parts:
                            content = event.content.parts[0].text
                            # Only send orchestrator status updates, not duplicate phase events
                            if "analyzing research quality" in content.lower():
                                # Don't send duplicate reflection event, just log progress
                                print(f"📊 Orchestrator: {content}")
                            elif "follow-up" in content.lower() and "queries" in content.lower():
                                # Don't send duplicate web_research event
                                print(f"🔄 Orchestrator: {content}")
                            elif "synthesizing comprehensive answer" in content.lower():
                                # Don't send duplicate finalize_answer event
                                print(f"✍️ Orchestrator: {content}")
                
                # Check if this is the final response from the answer_synthesizer or orchestrator
                if event.is_final_response() and (event.author == "answer_synthesizer" or event.author == "enhanced_research_orchestrator"):
                    if event.content and event.content.parts:
                        final_answer = event.content.parts[0].text
                        
                        # Mark final step as complete
                        yield {
                            "event": "finalize_answer",
                            "data": {
                                "status": "complete",
                                "answer": final_answer
                            }
                        }
                        
                        # Send final chat message
                        yield {
                            "event": "messages",
                            "data": {
                                "type": "ai",
                                "content": final_answer,
                                "id": str(uuid.uuid4())
                            }
                        }
                        
                        # End event
                        yield {"event": "__end__", "data": {}}
                        break
                
                # Also check for final response from the orchestrator itself (backup)
                elif event.is_final_response() and event.author == "research_orchestrator":
                    if event.content and event.content.parts:
                        final_answer = event.content.parts[0].text
                        yield {
                            "event": "finalize_answer",
                            "data": {"status": "complete", "answer": final_answer}
                        }
                        yield {
                            "event": "messages",
                            "data": {"type": "ai", "content": final_answer, "id": str(uuid.uuid4())}
                        }
                        yield {"event": "__end__", "data": {}}
                        break
                
                # For debugging: log all final responses
                elif event.is_final_response():
                    print(f"🔍 DEBUG: Final response from {event.author} - checking if this should end workflow...")
                    # Continue processing other sub-agent completions
                
                # Small delay for smooth streaming
                await asyncio.sleep(0.1)
            
        except Exception as e:
            yield {
                "event": "error",
                "data": {"error": str(e)}
            }
        finally:
            # Update session status
            if session_id in self.session_manager.sessions:
                self.session_manager.sessions[session_id]['status'] = 'completed'