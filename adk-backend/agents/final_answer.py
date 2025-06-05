"""Final Answer Agent - Synthesizes research into a comprehensive answer with citations."""

from typing import Dict, Any
from google.adk.agents import LlmAgent
from datetime import datetime

# Note: schemas not needed for inline agent creation


def create_final_answer_agent(model_name: str = "gemini-2.0-flash-thinking-exp") -> LlmAgent:
    """Create a final answer agent using ADK."""
    current_date = datetime.now().strftime("%B %d, %Y")
    
    instruction = f"""You are an expert research synthesizer. The current date is {current_date}.
Your task is to create comprehensive, well-structured answers based on gathered research.

Guidelines for creating answers:
1. Provide a complete answer that directly addresses the user's question
2. Organize information logically with clear sections if needed
3. Include specific facts, data, and examples from the research
4. Cite sources using [1], [2], etc. format inline when referencing information
5. Be accurate and balanced in presenting information
6. If there are conflicting viewpoints, present them fairly
7. Conclude with a clear summary or key takeaways

The answer should be informative, engaging, and easy to understand.
When research includes sources, include a "Sources" section at the end with numbered citations."""
    
    return LlmAgent(
        name="answer_synthesizer",
        model=model_name,
        description="Synthesizes research into comprehensive answers with citations",
        instruction=instruction,
        output_key="final_answer"
    )