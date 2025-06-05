"""Enhanced Research Orchestrator - Uses original LangGraph prompts with ADK patterns."""

import json
import asyncio
from typing import AsyncGenerator, Any, Dict, List
from datetime import datetime
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.tools import google_search
from google.genai import types
from typing import AsyncGenerator
from utils.enhanced_citations import (
    process_search_response_with_grounding,
    format_sources_for_final_answer,
    enhance_web_search_with_citations
)


def get_current_date():
    """Get current date in readable format - from original implementation."""
    return datetime.now().strftime("%B %d, %Y")


class EnhancedResearchOrchestrator(BaseAgent):
    """Enhanced orchestrator that implements the full LangGraph research workflow."""
    
    def __init__(
        self,
        query_model: str = "gemini-2.0-flash-exp",
        reasoning_model: str = "gemini-2.0-flash-thinking-exp",
        max_loops: int = 3,
        initial_queries: int = 3
    ):
        # Store configuration as private attributes to avoid field validation
        self._max_loops = max_loops
        self._initial_queries = initial_queries
        
        # Create sub-agents using original LangGraph prompts
        current_date = get_current_date()
        
        # Initialize the base class with required fields
        super().__init__(
            name="enhanced_research_orchestrator",
            description="Enhanced orchestrator with reflection loops and parallel processing"
        )
        
        # Query generator - enhanced prompt that reads from session state
        query_writer_instructions = f"""Your goal is to generate sophisticated and diverse web search queries. These queries are intended for an advanced automated web research tool capable of analyzing complex results, following links, and synthesizing information.

Instructions:
- Always prefer a single search query, only add another query if the original question requests multiple aspects or elements and one query is not enough.
- Each query should focus on one specific aspect of the original question.
- Don't produce more than {initial_queries} queries.
- Queries should be diverse, if the topic is broad, generate more than 1 query.
- Don't generate multiple similar queries, 1 is enough.
- Query should ensure that the most current information is gathered. The current date is {current_date}.

You will find the research topic in the session state under the key 'research_topic'. Use this topic to generate your queries.

Format: 
- Format your response as a JSON object with ALL three of these exact keys:
   - "rationale": Brief explanation of why these queries are relevant
   - "query": A list of search queries

Example:

Topic: What revenue grew more last year apple stock or the number of people buying an iphone
```json
{{
    "rationale": "To answer this comparative growth question accurately, we need specific data points on Apple's stock performance and iPhone sales metrics. These queries target the precise financial information needed: company revenue trends, product-specific unit sales figures, and stock price movement over the same fiscal period for direct comparison.",
    "query": ["Apple total revenue growth fiscal year 2024", "iPhone unit sales growth fiscal year 2024", "Apple stock price growth fiscal year 2024"],
}}
```

Read the research topic from session state and generate appropriate queries for that topic."""

        self._query_generator = LlmAgent(
            name="query_generator",
            model=query_model,
            description="Generates diverse search queries from user questions",
            instruction=query_writer_instructions,
            output_key="search_queries"
        )
        
        # Web searcher - enhanced prompt that reads from session state
        web_searcher_instructions = f"""Conduct targeted Google Searches to gather the most recent, credible information and synthesize it into a verifiable text artifact.

Instructions:
- Query should ensure that the most current information is gathered. The current date is {current_date}.
- Use the search query from session state under the key 'current_search_query'.
- Consolidate key findings while meticulously tracking the source(s) for each specific piece of information.
- The output should be a well-written summary or report based on your search findings. 
- Only include the information found in the search results, don't make up any information.

Read the current search query from session state and conduct a comprehensive search on that topic."""

        self._web_searcher = LlmAgent(
            name="web_searcher",
            model=query_model,
            description="Performs web searches and summarizes findings",
            instruction=web_searcher_instructions,
            tools=[google_search],
            output_key="search_results"
        )
        
        # Enhance web searcher with advanced citation processing
        self._web_searcher = enhance_web_search_with_citations(self._web_searcher, use_grounding=True)
        
        # Reflection agent - enhanced prompt that reads from session state
        reflection_instructions = f"""You are an expert research assistant analyzing research summaries.

Instructions:
- Read the research topic from session state under the key 'research_topic'.
- Read the research summaries from the provided formatted_reflection_prompt in session state.
- Identify knowledge gaps or areas that need deeper exploration and generate follow-up queries.
- If provided summaries are sufficient to answer the user's question, don't generate follow-up queries.
- If there is a knowledge gap, generate follow-up queries that would help expand understanding.
- Focus on technical details, implementation specifics, or emerging trends that weren't fully covered.

Requirements:
- Ensure follow-up queries are self-contained and include necessary context for web search.

Output Format:
- Format your response as a JSON object with these exact keys:
   - "is_sufficient": true or false
   - "knowledge_gap": Describe what information is missing or needs clarification
   - "follow_up_queries": Write specific questions to address the gaps

Example:
```json
{{
    "is_sufficient": true, // or false
    "knowledge_gap": "The summary lacks information about performance metrics and benchmarks", // "" if is_sufficient is true
    "follow_up_queries": ["What are typical performance benchmarks and metrics used to evaluate [specific technology]?"] // [] if is_sufficient is true
}}
```

Analyze the research summaries and determine if additional research is needed. Read the research topic and summaries from session state."""

        self._reflection_agent = LlmAgent(
            name="reflection_analyst", 
            model=reasoning_model,
            description="Analyzes research quality and identifies gaps",
            instruction=reflection_instructions,
            output_key="reflection_analysis"
        )
        
        # Answer synthesizer - enhanced prompt that reads from session state
        answer_instructions = f"""Generate a high-quality answer to the user's question based on the provided research summaries.

Instructions:
- The current date is {current_date}.
- Read the research topic from session state under the key 'research_topic'.
- Read the research summaries from the provided formatted_answer_prompt in session state.
- Generate a high-quality answer based on the research findings.
- Include all citations from the summaries in the answer correctly.
- Provide a comprehensive, well-structured response that addresses the user's question.

Read the research topic and summaries from session state and synthesize a complete answer."""

        self._answer_synthesizer = LlmAgent(
            name="answer_synthesizer",
            model=reasoning_model,
            description="Synthesizes research into comprehensive answers",
            instruction=answer_instructions,
            output_key="final_answer"
        )

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Execute the enhanced research workflow with reflection loops."""
        try:
            # Get the user's question from the latest message
            user_question = self._get_user_question(ctx)
            
            # Step 1: Generate search queries using real LLM agent
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text="Starting enhanced research workflow - generating diverse search queries...")]),
                partial=True,  # This is a streaming intermediate event
                turn_complete=False  # Explicitly mark as not final
            )
            
            # Store research topic in session state for query generator to read
            ctx.session.state["research_topic"] = user_question
            
            # Run query generator with same context (CORRECT ADK PATTERN)
            async for event in self._query_generator.run_async(ctx):
                yield event
            
            # Get generated queries from session state using output_key
            queries = self._get_queries_from_state(ctx)
            if not queries:
                yield Event(
                    author=self.name,
                    content=types.Content(parts=[types.Part(text="No search queries generated. Cannot proceed with research.")]),
                    partial=False,  # This is a complete error message
                    turn_complete=True  # This is a final error event
                )
                return
            
            # Initialize research loop
            all_search_results = []
            research_loop_count = 0
            
            # Main research loop with reflection
            max_loops = getattr(self, '_max_loops', 3)  # Default to 3 if not found
            while research_loop_count < max_loops:
                research_loop_count += 1
                ctx.session.state["research_loop_count"] = research_loop_count
                
                # Step 2: Perform web searches (parallel processing for current queries)
                if research_loop_count == 1:
                    # Initial queries
                    current_queries = queries
                    yield Event(
                        author=self.name,
                        content=types.Content(parts=[types.Part(text=f"Performing initial parallel web research ({len(current_queries)} queries)...")]),
                        partial=True,  # Intermediate progress event
                        turn_complete=False  # Intermediate progress
                    )
                else:
                    # Follow-up queries from reflection
                    reflection_data = self._get_reflection_analysis(ctx)
                    current_queries = reflection_data.get("follow_up_queries", [])
                    if not current_queries:
                        break
                    # Convert string queries to proper format
                    if current_queries and isinstance(current_queries[0], str):
                        current_queries = [{"query": q, "rationale": "Follow-up research"} for q in current_queries]
                    yield Event(
                        author=self.name,
                        content=types.Content(parts=[types.Part(text=f"Performing follow-up parallel research (iteration {research_loop_count}, {len(current_queries)} queries)...")]),
                        partial=True,  # Intermediate progress event
                        turn_complete=False  # Intermediate progress
                    )
                
                # Execute real parallel web searches using proper ADK pattern
                async for event in self._execute_parallel_searches(ctx, current_queries):
                    yield event
                
                # Get search results from session state
                iteration_results = ctx.session.state.get("parallel_search_results", [])
                all_search_results.extend(iteration_results)
                ctx.session.state["all_search_results"] = all_search_results
                
                # Step 3: Real reflection and quality analysis
                if research_loop_count < max_loops:  # Don't reflect on final iteration
                    yield Event(
                        author=self.name,
                        content=types.Content(parts=[types.Part(text="Analyzing research quality and identifying knowledge gaps...")]),
                        partial=True,  # Intermediate progress event
                        turn_complete=False  # Intermediate progress
                    )
                    
                    # Prepare research summary for reflection
                    research_summary = self._create_research_summary(all_search_results)
                    
                    # Store reflection data in session state
                    ctx.session.state["research_summary"] = research_summary
                    
                    # Run reflection agent with same context (CORRECT ADK PATTERN)
                    async for event in self._reflection_agent.run_async(ctx):
                        yield event
                    
                    # Get reflection analysis from session state
                    reflection_data = self._get_reflection_analysis(ctx)
                    
                    # Make continuation decision based on real reflection analysis
                    if reflection_data and reflection_data.get("is_sufficient", False):
                        yield Event(
                            author=self.name,
                            content=types.Content(parts=[types.Part(text="Research quality analysis: Sufficient information gathered. Proceeding to answer synthesis.")]),
                            partial=True,  # Intermediate progress event
                            turn_complete=False  # Intermediate progress
                        )
                        break  # Exit the research loop
                    else:
                        knowledge_gap = reflection_data.get("knowledge_gap", "Additional research needed")
                        follow_up_queries = reflection_data.get("follow_up_queries", [])
                        yield Event(
                            author=self.name,
                            content=types.Content(parts=[types.Part(text=f"Research quality analysis: {knowledge_gap}. Generating {len(follow_up_queries)} follow-up queries...")]),
                            partial=True,  # Intermediate progress event
                            turn_complete=False  # Intermediate progress
                        )
                        # Continue to next iteration with follow-up queries
            
            # Step 4: Generate final answer
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text="Synthesizing comprehensive answer from all research...")]),
                partial=True,  # Intermediate progress event
                turn_complete=False  # Intermediate progress
            )
            
            # Prepare research summary for answer synthesis
            research_summary = self._create_research_summary(all_search_results)
            
            # Store answer synthesis data in session state
            ctx.session.state["final_research_summary"] = research_summary
            
            # Run answer synthesizer with same context (CORRECT ADK PATTERN)
            async for event in self._answer_synthesizer.run_async(ctx):
                yield event
            
            # Get final answer from session state using output_key
            final_answer = ctx.session.state.get("final_answer", "")
            if not final_answer:
                yield Event(
                    author=self.name,
                    content=types.Content(parts=[types.Part(text="Unable to generate final answer from research.")]),
                    partial=False,  # This is a complete error message
                    turn_complete=True  # This is a final error event
                )
                
        except Exception as e:
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text=f"Error in enhanced research workflow: {str(e)})")]),
                partial=False,  # This is a complete error message
                turn_complete=True  # This is a final error event
            )

    async def _execute_parallel_searches(self, ctx: InvocationContext, queries: List[Dict[str, Any]]) -> AsyncGenerator[Event, None]:
        """Execute multiple web searches using proper ADK parallel execution pattern."""
        search_results = []
        
        # Store all search queries in session state for the web searcher to process
        query_list = []
        for i, query_data in enumerate(queries):
            query = query_data.get("query", "")
            query_list.append({
                "query": query,
                "index": i,
                "research_topic": query
            })
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text=f"Preparing parallel search: {query}")]),
                partial=True,  # Intermediate progress event
                turn_complete=False  # Intermediate progress
            )
        
        # Store query information in session state
        ctx.session.state["parallel_search_queries"] = query_list
        
        # Execute searches using enhanced web searcher
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=f"Executing {len(queries)} searches in parallel...")]),
            partial=True,  # Intermediate progress event
            turn_complete=False  # Intermediate progress
        )
        
        # For parallel execution, we'll run each search sequentially but with enhanced processing
        # In a real ADK implementation, you would use ParallelAgent for true parallelism
        iteration_results = []
        for query_data in query_list:
            query = query_data["query"]
            index = query_data["index"]
            
            # Store search context in session state
            ctx.session.state[f"search_instruction_{index}"] = f"Search for: {query}"
            
            # Store current search context
            ctx.session.state["current_search_query"] = query
            ctx.session.state["current_search_index"] = index
            
            # Run web searcher for this specific query
            async for event in self._web_searcher.run_async(ctx):
                # Modify event to include search context
                if event.content and event.content.parts:
                    original_text = event.content.parts[0].text
                    modified_text = f"[Search {index+1}] {original_text}"
                    event.content.parts[0].text = modified_text
                yield event
            
            # Get search result from session state
            search_result = ctx.session.state.get("search_results", "")
            if search_result:
                result_entry = {
                    "query": query,
                    "result": search_result,
                    "iteration": ctx.session.state.get("research_loop_count", 1),
                    "index": index
                }
                iteration_results.append(result_entry)
                
                yield Event(
                    author=self.name,
                    content=types.Content(parts=[types.Part(text=f"Completed parallel search {index+1}: {query}")]),
                    partial=True,  # Intermediate progress event
                    turn_complete=False  # Intermediate progress
                )
        
        # Store all results in session state for the orchestrator to access
        ctx.session.state["parallel_search_results"] = iteration_results
        
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=f"Completed {len(iteration_results)} parallel searches")]),
            partial=True,  # Intermediate progress event
            turn_complete=False  # Intermediate progress
        )

    def _get_user_question(self, ctx: InvocationContext) -> str:
        """Extract user question from context."""
        # Access conversation history through session
        messages = getattr(ctx.session, 'events', [])
        for event in reversed(messages):
            if hasattr(event, 'content') and event.content and event.content.parts:
                # Look for user message content
                if hasattr(event, 'role') and event.role == 'user':
                    return str(event.content.parts[0].text)
                # Look for content that looks like a user question
                content_text = str(event.content.parts[0].text)
                if '?' in content_text or len(content_text) > 10:  # Heuristic for user question
                    return content_text
        return "What are the latest developments in AI?"  # Default fallback

    def _get_queries_from_state(self, ctx: InvocationContext) -> List[Dict[str, Any]]:
        """Extract generated queries from state - handle original format and markdown JSON."""
        queries_data = ctx.session.state.get("search_queries", "")
        if isinstance(queries_data, str):
            try:
                # Handle markdown-wrapped JSON (```json ... ```)
                if queries_data.strip().startswith("```json"):
                    # Extract JSON from markdown code block
                    lines = queries_data.strip().split('\n')
                    json_lines = []
                    in_json = False
                    for line in lines:
                        if line.strip() == "```json":
                            in_json = True
                            continue
                        elif line.strip() == "```":
                            break
                        elif in_json:
                            json_lines.append(line)
                    queries_data = '\n'.join(json_lines)
                
                parsed = json.loads(queries_data)
                # Handle original format: {"query": ["query1", "query2"], "rationale": "..."}
                if "query" in parsed and isinstance(parsed["query"], list):
                    return [{"query": q, "rationale": parsed.get("rationale", "")} for q in parsed["query"]]
                # Handle new format: {"queries": [{"query": "...", "rationale": "..."}]}
                elif "queries" in parsed:
                    return parsed["queries"]
                return []
            except json.JSONDecodeError:
                return []
        return []

    def _get_reflection_analysis(self, ctx: InvocationContext) -> Dict[str, Any]:
        """Extract reflection analysis from state - handle markdown JSON."""
        analysis_data = ctx.session.state.get("reflection_analysis", "")
        if isinstance(analysis_data, str):
            try:
                # Handle markdown-wrapped JSON (```json ... ```)
                if analysis_data.strip().startswith("```json"):
                    # Extract JSON from markdown code block
                    lines = analysis_data.strip().split('\n')
                    json_lines = []
                    in_json = False
                    for line in lines:
                        if line.strip() == "```json":
                            in_json = True
                            continue
                        elif line.strip() == "```":
                            break
                        elif in_json:
                            json_lines.append(line)
                    analysis_data = '\n'.join(json_lines)
                
                return json.loads(analysis_data)
            except json.JSONDecodeError:
                return {}
        elif isinstance(analysis_data, dict):
            return analysis_data
        return {}

    def _create_research_summary(self, search_results: List[Dict[str, Any]]) -> str:
        """Create a summary of all search results."""
        if not search_results:
            return "No research results available."
        
        summary_parts = []
        for i, result in enumerate(search_results, 1):
            query = result.get("query", "")
            content = result.get("result", "")
            iteration = result.get("iteration", 1)
            summary_parts.append(f"Search {i} (Iteration {iteration}): {query}\n{content}\n")
        
        return "\n".join(summary_parts)


def create_enhanced_research_orchestrator(
    query_model: str = "gemini-2.0-flash-exp",
    reasoning_model: str = "gemini-2.0-flash-thinking-exp",
    max_loops: int = 3,
    initial_queries: int = 3
) -> EnhancedResearchOrchestrator:
    """Create enhanced research orchestrator with reflection loops."""
    return EnhancedResearchOrchestrator(
        query_model=query_model,
        reasoning_model=reasoning_model,
        max_loops=max_loops,
        initial_queries=initial_queries
    )