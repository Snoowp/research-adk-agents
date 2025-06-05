"""Custom Research Orchestrator using ADK Custom Agent pattern."""

import json
import asyncio
from typing import AsyncGenerator, Any, Dict, List
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.context import AgentContext
from google.adk.events import Event, MessageEvent
from google.adk.tools import google_search


class ResearchOrchestrator(BaseAgent):
    """Custom orchestrator that implements the research workflow explicitly."""
    
    def __init__(
        self,
        query_model: str = "gemini-2.0-flash-exp",
        reasoning_model: str = "gemini-2.0-flash-thinking-exp",
        max_loops: int = 3,
        initial_queries: int = 3
    ):
        super().__init__(
            name="research_orchestrator",
            description="Custom orchestrator for comprehensive research workflow"
        )
        
        self.max_loops = max_loops
        self.initial_queries = initial_queries
        
        # Create sub-agents
        self.query_generator = LlmAgent(
            name="query_generator",
            model=query_model,
            description="Generates diverse search queries from user questions",
            instruction=f"""Generate {initial_queries} diverse and effective search queries from the user's question.
            
            Return response as JSON:
            {{
                "queries": [
                    {{
                        "query": "search query text",
                        "rationale": "why this query is useful"
                    }}
                ]
            }}""",
            output_key="search_queries"
        )
        
        self.web_searcher = LlmAgent(
            name="web_searcher",
            model=query_model,
            description="Performs web searches and summarizes findings",
            instruction="""Use google_search tool to find information and provide comprehensive summary.
            
            For each search:
            1. Use the google_search tool with the provided query
            2. Analyze results and summarize key findings
            3. Focus on information that helps answer research questions
            4. Note credible sources found""",
            tools=[google_search],
            output_key="search_results"
        )
        
        self.reflection_agent = LlmAgent(
            name="reflection_analyst", 
            model=reasoning_model,
            description="Analyzes research quality and identifies gaps",
            instruction=f"""Analyze gathered research and determine if sufficient for comprehensive answer.
            
            Return analysis as JSON:
            {{
                "is_sufficient": true/false,
                "reasoning": "detailed explanation",
                "follow_up_queries": [
                    {{
                        "query": "additional search query if needed",
                        "rationale": "why this query would help"
                    }}
                ]
            }}
            
            If sufficient, set follow_up_queries to empty array.
            Maximum {max_loops} research iterations allowed.""",
            output_key="reflection_analysis"
        )
        
        self.answer_synthesizer = LlmAgent(
            name="answer_synthesizer",
            model=reasoning_model,
            description="Synthesizes research into comprehensive answers",
            instruction="""Create comprehensive answer based on gathered research.
            
            Guidelines:
            1. Directly address the user's question
            2. Organize information logically
            3. Include specific facts and examples
            4. Cite sources using [1], [2] format
            5. Present balanced viewpoints if applicable
            6. Include Sources section with numbered citations""",
            output_key="final_answer"
        )

    async def _run_async_impl(self, ctx: AgentContext) -> AsyncGenerator[Event, None]:
        """Execute the complete research workflow."""
        try:
            # Get the user's question from the latest message
            user_question = self._get_user_question(ctx)
            
            # Step 1: Generate search queries
            yield MessageEvent(
                author=self.name,
                content="Starting research workflow - generating search queries..."
            )
            
            async for event in self.query_generator.run_async(ctx):
                yield event
            
            # Get generated queries from state
            queries = self._get_queries_from_state(ctx)
            if not queries:
                yield MessageEvent(
                    author=self.name,
                    content="No search queries generated. Cannot proceed with research."
                )
                return
            
            # Step 2: Perform web searches for each query
            all_search_results = []
            for i, query_data in enumerate(queries):
                query = query_data.get("query", "")
                yield MessageEvent(
                    author=self.name,
                    content=f"Searching for: {query}"
                )
                
                # Create new context for this search
                search_ctx = ctx.create_child_context()
                search_ctx.add_user_message(f"Search for: {query}")
                
                async for event in self.web_searcher.run_async(search_ctx):
                    yield event
                
                # Collect search results
                search_result = search_ctx.get_session_state().get("search_results", "")
                if search_result:
                    all_search_results.append({
                        "query": query,
                        "result": search_result
                    })
            
            # Save all search results to main context state
            ctx.get_session_state()["all_search_results"] = all_search_results
            
            # Step 3: Reflection loop
            iteration_count = 0
            while iteration_count < self.max_loops:
                yield MessageEvent(
                    author=self.name,
                    content=f"Analyzing research quality (iteration {iteration_count + 1})"
                )
                
                # Create reflection context with research summary
                reflection_ctx = ctx.create_child_context()
                research_summary = self._create_research_summary(all_search_results)
                reflection_ctx.add_user_message(f"Original question: {user_question}\n\nGathered research:\n{research_summary}")
                
                async for event in self.reflection_agent.run_async(reflection_ctx):
                    yield event
                
                # Check reflection analysis
                reflection_data = self._get_reflection_analysis(reflection_ctx)
                if not reflection_data or reflection_data.get("is_sufficient", False):
                    break
                
                # Perform additional searches if needed
                follow_up_queries = reflection_data.get("follow_up_queries", [])
                if follow_up_queries:
                    for query_data in follow_up_queries:
                        query = query_data.get("query", "")
                        yield MessageEvent(
                            author=self.name,
                            content=f"Additional search: {query}"
                        )
                        
                        search_ctx = ctx.create_child_context()
                        search_ctx.add_user_message(f"Search for: {query}")
                        
                        async for event in self.web_searcher.run_async(search_ctx):
                            yield event
                        
                        search_result = search_ctx.get_session_state().get("search_results", "")
                        if search_result:
                            all_search_results.append({
                                "query": query,
                                "result": search_result
                            })
                
                iteration_count += 1
            
            # Step 4: Generate final answer
            yield MessageEvent(
                author=self.name,
                content="Synthesizing comprehensive answer..."
            )
            
            final_ctx = ctx.create_child_context()
            research_summary = self._create_research_summary(all_search_results)
            final_ctx.add_user_message(f"Create comprehensive answer for: {user_question}\n\nBased on research:\n{research_summary}")
            
            async for event in self.answer_synthesizer.run_async(final_ctx):
                yield event
            
            # Get and return final answer
            final_answer = final_ctx.get_session_state().get("final_answer", "")
            if final_answer:
                # Save to main context state
                ctx.get_session_state()["final_answer"] = final_answer
                yield MessageEvent(
                    author=self.name,
                    content=final_answer
                )
            else:
                yield MessageEvent(
                    author=self.name,
                    content="Unable to generate final answer from research."
                )
                
        except Exception as e:
            yield MessageEvent(
                author=self.name,
                content=f"Error in research workflow: {str(e)}"
            )

    def _get_user_question(self, ctx: AgentContext) -> str:
        """Extract user question from context."""
        messages = ctx.get_conversation_history()
        for message in reversed(messages):
            if message.role == "user":
                return str(message.parts[0].text) if message.parts else ""
        return ""

    def _get_queries_from_state(self, ctx: AgentContext) -> List[Dict[str, Any]]:
        """Extract generated queries from state."""
        queries_data = ctx.get_session_state().get("search_queries", "")
        if isinstance(queries_data, str):
            try:
                parsed = json.loads(queries_data)
                return parsed.get("queries", [])
            except json.JSONDecodeError:
                return []
        return []

    def _get_reflection_analysis(self, ctx: AgentContext) -> Dict[str, Any]:
        """Extract reflection analysis from state."""
        analysis_data = ctx.get_session_state().get("reflection_analysis", "")
        if isinstance(analysis_data, str):
            try:
                return json.loads(analysis_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def _create_research_summary(self, search_results: List[Dict[str, Any]]) -> str:
        """Create a summary of all search results."""
        if not search_results:
            return "No research results available."
        
        summary_parts = []
        for i, result in enumerate(search_results, 1):
            query = result.get("query", "")
            content = result.get("result", "")
            summary_parts.append(f"Search {i}: {query}\n{content}\n")
        
        return "\n".join(summary_parts)


def create_research_orchestrator(
    query_model: str = "gemini-2.0-flash-exp",
    reasoning_model: str = "gemini-2.0-flash-thinking-exp",
    max_loops: int = 3,
    initial_queries: int = 3
) -> ResearchOrchestrator:
    """Create custom research orchestrator."""
    return ResearchOrchestrator(
        query_model=query_model,
        reasoning_model=reasoning_model,
        max_loops=max_loops,
        initial_queries=initial_queries
    )