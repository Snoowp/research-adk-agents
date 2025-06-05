"""Query Generator Agent - Converts user questions into optimized search queries."""

from typing import Dict, Any
from google.adk.agents import LlmAgent
import json
from datetime import datetime

# Note: schemas not needed for inline agent creation


def create_query_generator_agent(model_name: str = "gemini-2.0-flash-exp") -> LlmAgent:
    """Create a query generator agent using ADK."""
    current_date = datetime.now().strftime("%B %d, %Y")
    
    instruction = f"""You are a search query generation expert. The current date is {current_date}.
Your task is to generate diverse and effective search queries that will help gather comprehensive 
information to answer the user's question.

Guidelines:
- Create queries that explore different aspects of the topic
- Use a mix of general and specific queries
- Consider current events if relevant to the question
- Include queries that might reveal contrasting viewpoints

Always return your response as a JSON object with this exact schema:
{{
    "queries": [
        {{
            "query": "search query text",
            "rationale": "why this query is useful"
        }}
    ]
}}

Generate 3-5 diverse search queries for the user's question."""
    
    return LlmAgent(
        name="query_generator",
        model=model_name,
        description="Generates diverse search queries from user questions",
        instruction=instruction,
        output_key="search_queries"
    )