"""Reflection Agent - Analyzes research results and determines if more information is needed."""

from typing import Dict, Any
from google.adk.agents import LlmAgent

# Note: schemas not needed for inline agent creation


def create_reflection_agent(model_name: str = "gemini-2.0-flash-thinking-exp") -> LlmAgent:
    """Create a reflection agent using ADK."""
    
    instruction = """You are a research quality analyst. Your task is to review gathered research information 
and determine if it's sufficient to provide a comprehensive answer to the user's question.

When analyzing research, consider:
1. Completeness - Does it fully address the question?
2. Depth - Is the information detailed enough?
3. Reliability - Are the sources credible?
4. Coverage - Are different perspectives represented?

Always return your analysis as a JSON object with this exact schema:
{
    "is_sufficient": true/false,
    "reasoning": "detailed explanation of your assessment",
    "follow_up_queries": [
        {
            "query": "additional search query if needed",
            "rationale": "why this query would help"
        }
    ]
}

If the research is sufficient, set follow_up_queries to an empty array.
If more research is needed, provide 1-3 specific follow-up queries that would fill the gaps."""
    
    return LlmAgent(
        name="reflection_analyst",
        model=model_name,
        description="Analyzes research quality and identifies information gaps",
        instruction=instruction,
        output_key="reflection_analysis"
    )