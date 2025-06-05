"""Enhanced Research Orchestrator - Uses original LangGraph prompts with ADK patterns."""

import json
import asyncio
from typing import AsyncGenerator, Any, Dict, List
from datetime import datetime
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types

# Import schemas for structured output
from models.schemas import Reflection, SearchQuery, SearchQueryList


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
        query_writer_instructions = f"""Your goal is to generate sophisticated and diverse web search queries to research a topic.

Instructions:
- Each query should focus on one specific aspect of the original question.
- Don't produce more than {initial_queries} queries.
- Queries should be diverse, if the topic is broad, generate more than 1 query.
- Don't generate multiple similar queries, 1 is enough.
- The current date is {current_date}.

The research topic is provided in the user's message.

Format: 
- Format your response as a JSON object with this exact schema:
  {{
      "queries": [
          {{"query": "search query text", "rationale": "why this query is useful"}},
          ...
      ]
  }}

Example:
```json
{{
    "queries": [
        {{"query": "Apple total revenue growth fiscal year 2024", "rationale": "Targets specific financial data for Apple's revenue."}},
        {{"query": "iPhone unit sales growth fiscal year 2024", "rationale": "Targets product-specific sales metrics."}},
        {{"query": "Apple stock price growth fiscal year 2024", "rationale": "Targets stock performance for direct comparison."}}
    ]
}}
```

Based on the user's research topic, generate appropriate queries."""

        self._query_generator = LlmAgent(
            name="query_generator",
            model=query_model,
            description="Generates diverse search queries from user questions",
            instruction=query_writer_instructions,
            output_schema=SearchQueryList,
            output_key="search_queries",
            disallow_transfer_to_parent=True,
            disallow_transfer_to_peers=True
        )
        
        # Web searcher - enhanced prompt that reads from session state
        web_searcher_instructions = f"""You are an advanced research assistant. Conduct targeted Google Searches for a list of queries to gather the most recent, credible information and synthesize it into a single, cohesive summary.

Instructions:
- Query should ensure that the most current information is gathered. The current date is {current_date}.
- You will find a list of search queries in session state under the key 'queries_to_search'.
- For EACH query in the list, use the `google_search` tool to find relevant information.
- After completing all searches, consolidate all key findings into a single, well-written summary.
- The summary should be a comprehensive report based on all your search findings combined.
- Only include the information found in the search results, don't make up any information.

Read the list of search queries from session state, conduct a comprehensive search for each, and synthesize a unified summary."""

        from google.adk.tools import google_search
        
        self._web_searcher = LlmAgent(
            name="web_searcher",
            model=query_model,
            description="Performs web searches and summarizes findings",
            instruction=web_searcher_instructions,
            tools=[google_search],
            output_key="search_results"
        )
        
        # Reflection agent - enhanced prompt that reads from session state
        reflection_instructions = f"""You are an expert research assistant analyzing research summaries.

Instructions:
- Read the research topic from session state under the key 'research_topic'.
- Read the collected research summaries from the session state under the key 'research_summary'.
- Identify knowledge gaps or areas that need deeper exploration and generate follow-up queries.
- If provided summaries are sufficient to answer the user's question, don't generate follow-up queries.
- If there is a knowledge gap, generate follow-up queries that would help expand understanding.
- Focus on technical details, implementation specifics, or emerging trends that weren't fully covered.

Requirements:
- Ensure follow-up queries are self-contained and include necessary context for web search.

Output Format:
- Format your response as a JSON object with this exact schema:
    {{
        "is_sufficient": boolean,
        "reasoning": "Explanation of the assessment",
        "follow_up_queries": [
            {{"query": "additional query", "rationale": "why it is needed"}}
        ]
    }}
Example:
```json
{{
    "is_sufficient": true, // or false
    "reasoning": "The summary lacks information about performance metrics and benchmarks.",
    "follow_up_queries": [
        {{"query": "What are typical performance benchmarks for [technology]?", "rationale": "To gather quantitative data."}}
    ]
}}
```

Analyze the research summaries and determine if additional research is needed. Read the topic and summaries from session state."""

        self._reflection_agent = LlmAgent(
            name="reflection_analyst", 
            model=reasoning_model,
            description="Analyzes research quality and identifies gaps",
            instruction=reflection_instructions,
            output_schema=Reflection,
            output_key="reflection_analysis",
            disallow_transfer_to_parent=True,
            disallow_transfer_to_peers=True
        )
        
        # Answer synthesizer - enhanced prompt that reads from session state
        answer_instructions = f"""Generate a high-quality answer to the user's question based on the provided research summaries.

Instructions:
- The current date is {current_date}.
- Read the research topic from session state under the key 'research_topic'.
- Read the final, consolidated research summaries from session state under the key 'final_research_summary'.
- Generate a comprehensive, well-structured answer based on all the research findings.
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
            # Get the user's question from the invocation context
            if not ctx.user_content or not ctx.user_content.parts or not ctx.user_content.parts[0].text:
                yield Event(author=self.name, content=types.Content(parts=[types.Part(text="Error: No user question provided.")]))
                return
            user_question = ctx.user_content.parts[0].text
            
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
                         current_queries = [
                            SearchQuery(query=q, rationale="Follow-up research")
                            for q in current_queries
                        ]
                    # If queries are dicts, convert to SearchQuery objects
                    elif current_queries and isinstance(current_queries[0], dict):
                        current_queries = [SearchQuery(**q) for q in current_queries]
                    yield Event(
                        author=self.name,
                        content=types.Content(parts=[types.Part(text=f"Performing follow-up parallel research (iteration {research_loop_count}, {len(current_queries)} queries)...")]),
                        partial=True,  # Intermediate progress event
                        turn_complete=False  # Intermediate progress
                    )
                
                # Prepare for and execute web search
                ctx.session.state["queries_to_search"] = [q.get("query") if isinstance(q, dict) else q.query for q in current_queries]
                async for event in self._web_searcher.run_async(ctx):
                    yield event
                
                # Get synthesized search summary from session state
                search_summary = ctx.session.state.get("search_results", "")
                all_search_results.append(search_summary)
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
                        reasoning = reflection_data.get("reasoning", "Additional research needed")
                        follow_up_queries = reflection_data.get("follow_up_queries", [])
                        yield Event(
                            author=self.name,
                            content=types.Content(parts=[types.Part(text=f"Research quality analysis: {reasoning}. Generating {len(follow_up_queries)} follow-up queries...")]),
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


    def _get_queries_from_state(self, ctx: InvocationContext) -> List[Dict[str, Any]]:
        """Extract generated queries from state using the SearchQueryList schema."""
        queries_data = ctx.session.state.get("search_queries")
        if isinstance(queries_data, SearchQueryList):
            # Convert Pydantic models to dicts for downstream use
            return [q.model_dump() for q in queries_data.queries]
        if isinstance(queries_data, dict) and "queries" in queries_data:
            # Handle case where the state contains the dict representation
            return queries_data["queries"]
        return []

    def _get_reflection_analysis(self, ctx: InvocationContext) -> Dict[str, Any]:
        """Extract reflection analysis from state using the Reflection schema."""
        analysis_data = ctx.session.state.get("reflection_analysis")
        if isinstance(analysis_data, Reflection):
            # Convert Pydantic models to dicts for downstream use
            return analysis_data.model_dump()
        if isinstance(analysis_data, dict):
            return analysis_data
        return {}

    def _create_research_summary(self, search_summaries: List[str]) -> str:
        """Create a consolidated summary of all search iteration results."""
        if not search_summaries:
            return "No research results available."
        
        summary_parts = []
        for i, summary in enumerate(search_summaries, 1):
            summary_parts.append(f"## Research Iteration {i} Summary\n\n{summary}\n")
        
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