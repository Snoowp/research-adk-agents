"""Main Research Orchestrator - Coordinates the entire research workflow using ADK."""

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search


def create_research_orchestrator(
    query_model: str = "gemini-2.0-flash-exp",
    reasoning_model: str = "gemini-2.0-flash-thinking-exp",
    max_loops: int = 3,
    initial_queries: int = 3
) -> LlmAgent:
    """Create the main research orchestrator agent using ADK patterns."""
    
    # Create sub-agents inline to avoid import issues
    query_generator = LlmAgent(
        name="query_generator",
        model=query_model,
        description="Generates diverse search queries from user questions",
        instruction=f"""You are a search query generation expert. 
        Generate {initial_queries} diverse and effective search queries from the user's question.
        
        Guidelines:
        - Create queries that explore different aspects of the topic
        - Use a mix of general and specific queries
        - Consider current events if relevant
        - Include queries that might reveal contrasting viewpoints
        
        Return your response as JSON with this exact schema:
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
    
    web_searcher = LlmAgent(
        name="web_searcher",
        model=query_model,
        description="Performs web searches and summarizes findings",
        instruction="""You are a web research specialist. When given a search query, use the google_search tool 
        to find relevant information and provide a comprehensive summary.

        For each search:
        1. Use the google_search tool with the provided query
        2. Analyze the search results thoroughly
        3. Summarize the key findings, important facts, and insights
        4. Focus on information that would help answer research questions
        5. Note any credible sources found

        Provide detailed, informative summaries that capture the most relevant information from your search.""",
        tools=[google_search],
        output_key="search_results"
    )
    
    reflection_agent = LlmAgent(
        name="reflection_analyst",
        model=reasoning_model,
        description="Analyzes research quality and identifies information gaps",
        instruction=f"""You are a research quality analyst. Review gathered research information 
        and determine if it's sufficient to provide a comprehensive answer to the user's question.

        When analyzing research, consider:
        1. Completeness - Does it fully address the question?
        2. Depth - Is the information detailed enough?
        3. Reliability - Are the sources credible?
        4. Coverage - Are different perspectives represented?

        Always return your analysis as JSON with this exact schema:
        {{
            "is_sufficient": true/false,
            "reasoning": "detailed explanation of your assessment",
            "follow_up_queries": [
                {{
                    "query": "additional search query if needed",
                    "rationale": "why this query would help"
                }}
            ]
        }}

        If the research is sufficient, set follow_up_queries to an empty array.
        If more research is needed, provide 1-3 specific follow-up queries that would fill the gaps.
        Maximum {max_loops} research iterations allowed.""",
        output_key="reflection_analysis"
    )
    
    final_answer_agent = LlmAgent(
        name="answer_synthesizer",
        model=reasoning_model,
        description="Synthesizes research into comprehensive answers with citations",
        instruction="""You are an expert research synthesizer. Create comprehensive, well-structured answers 
        based on gathered research.

        Guidelines for creating answers:
        1. Provide a complete answer that directly addresses the user's question
        2. Organize information logically with clear sections if needed
        3. Include specific facts, data, and examples from the research
        4. Cite sources using [1], [2], etc. format inline when referencing information
        5. Be accurate and balanced in presenting information
        6. If there are conflicting viewpoints, present them fairly
        7. Conclude with a clear summary or key takeaways

        The answer should be informative, engaging, and easy to understand.
        When research includes sources, include a "Sources" section at the end with numbered citations.""",
        output_key="final_answer"
    )
    
    instruction = f"""You are a research orchestrator agent. Execute the complete research workflow by delegating to your sub-agents in sequence.

EXECUTE THIS COMPLETE WORKFLOW:

1. FIRST: Generate search queries by delegating to query_generator
2. THEN: For each query generated, delegate to web_searcher  
3. THEN: Analyze research quality by delegating to reflection_analyst
4. IF MORE RESEARCH NEEDED: Delegate additional searches to web_searcher and repeat reflection
5. FINALLY: Create final answer by delegating to answer_synthesizer

IMPORTANT: 
- Execute ALL steps in sequence, don't stop after the first delegation
- Use sub-agent names exactly: query_generator, web_searcher, reflection_analyst, answer_synthesizer
- When you delegate to web_searcher, include the specific search query
- Continue the full workflow until answer_synthesizer provides the final comprehensive answer
- The final answer from answer_synthesizer is what you should return to the user

Don't just delegate once - complete the entire research workflow!"""
    
    return LlmAgent(
        name="research_orchestrator",
        model=reasoning_model,
        description="Coordinates comprehensive research workflow with multiple specialized agents",
        instruction=instruction,
        sub_agents=[
            query_generator,
            web_searcher,
            reflection_agent,
            final_answer_agent
        ],
        output_key="final_answer"
    )