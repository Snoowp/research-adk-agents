"""Web Search Agent - Executes search queries and processes results."""

from typing import Dict, Any, List
from google.adk.agents import LlmAgent
from google.adk.tools import google_search

# Note: schemas not needed for inline agent creation


def create_web_search_agent(model_name: str = "gemini-2.0-flash-exp") -> LlmAgent:
    """Create a web search agent using ADK."""
    
    instruction = """You are a web research specialist. When given a search query, use the google_search tool 
to find relevant information and provide a comprehensive summary.

For each search:
1. Use the google_search tool with the provided query
2. Analyze the search results thoroughly
3. Summarize the key findings, important facts, and insights
4. Focus on information that would help answer research questions
5. Note any credible sources found

Provide detailed, informative summaries that capture the most relevant information from your search."""
    
    return LlmAgent(
        name="web_searcher",
        model=model_name,
        description="Performs web searches and summarizes findings",
        instruction=instruction,
        tools=[google_search],
        output_key="search_results"
    )