"""Simplified Research Agent - Uses LlmAgent pattern with step-by-step research."""

from google.adk.agents import LlmAgent
from google.adk.tools import google_search


def create_research_agent():
    """Create a research agent using LlmAgent pattern."""
    
    research_instructions = """You are an advanced research agent that conducts thorough research on user questions.

Your process:
1. GENERATE QUERIES: Create 2-3 diverse, specific search queries for the user's question
2. SEARCH: Use the google_search tool to find information for each query
3. ANALYZE: Review all search results and identify if more information is needed
4. SEARCH MORE: If gaps exist, generate additional targeted queries and search again
5. SYNTHESIZE: Combine all findings into a comprehensive, well-cited answer

Guidelines:
- Use diverse search queries to get comprehensive coverage
- Include citations for all factual claims
- If initial searches lack depth, conduct follow-up searches on specific aspects
- Provide a complete answer that addresses all parts of the user's question
- Always cite your sources with specific URLs where information was found

Current date: January 6, 2025"""

    return LlmAgent(
        name="research_agent",
        model="gemini-2.0-flash-exp",
        description="Conducts multi-step research with query generation, web search, and synthesis",
        instruction=research_instructions,
        tools=[google_search],
        output_key="research_result"
    )