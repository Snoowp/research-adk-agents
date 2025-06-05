"""Sequential Research Orchestrator using ADK SequentialAgent pattern."""

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search


def create_sequential_research_orchestrator(
    query_model: str = "gemini-2.0-flash-exp",
    reasoning_model: str = "gemini-2.0-flash-thinking-exp",
    max_loops: int = 3,
    initial_queries: int = 3
) -> SequentialAgent:
    """Create a research orchestrator using SequentialAgent pattern."""
    
    # Step 1: Query Generation Agent
    query_generator = LlmAgent(
        name="query_generator",
        model=query_model,
        description="Generates diverse search queries from user questions",
        instruction=f"""Generate {initial_queries} diverse and effective search queries from the user's question.
        
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
    
    # Step 2: Web Search Agent  
    web_searcher = LlmAgent(
        name="web_searcher",
        model=query_model,
        description="Performs web searches and summarizes findings",
        instruction="""You are a web research specialist. Your task is to perform comprehensive web research based on the search queries generated in the previous step.

**Important**: The search queries are available in the session state under the key 'search_queries'. This contains a JSON object with a list of queries.

**Your process**:
1. First, acknowledge that you can see the search queries from the previous step
2. For EACH query in the search_queries list, use the google_search tool to find relevant information
3. Analyze all search results thoroughly
4. Summarize key findings, important facts, and insights from ALL searches combined
5. Focus on information that would help answer the original research question
6. Note credible sources found across all searches

**Output**: Provide a detailed, informative summary that captures the most relevant information from all your searches. Organize the findings clearly and mention which queries provided which information.""",
        tools=[google_search],
        output_key="search_results"
    )
    
    # Step 3: Answer Synthesizer (combines reflection and final answer)
    answer_synthesizer = LlmAgent(
        name="answer_synthesizer",
        model=reasoning_model,
        description="Synthesizes research into comprehensive answers with citations",
        instruction="""You are an expert research synthesizer. Your task is to create a comprehensive, well-structured answer based on the research conducted in previous steps.

**Important**: You have access to research data from previous agents:
- Search queries are in state['search_queries'] 
- Search results and findings are in state['search_results']
- The original user question is in the conversation history

**Your process**:
1. First, acknowledge the research that was conducted in previous steps
2. Analyze the research quality - determine if the gathered information is sufficient
3. Create a comprehensive final answer that synthesizes all research

**Guidelines for your answer**:
1. Directly address the user's original question
2. Organize information logically with clear sections if needed  
3. Include specific facts, data, and examples from the research
4. Cite sources using [1], [2], etc. format when referencing information
5. Be accurate and balanced in presenting information
6. If there are conflicting viewpoints, present them fairly
7. Conclude with a clear summary or key takeaways

The answer should be informative, engaging, and easy to understand.
If the research included sources, add a "Sources" section at the end with numbered citations.

**Note**: If the research seems insufficient, note what additional information would be helpful, but still provide the best answer possible with available information.""",
        output_key="final_answer"
    )
    
    # Create the sequential workflow
    research_workflow = SequentialAgent(
        name="research_orchestrator",
        description="Sequential research workflow using query generation, web search, and answer synthesis",
        sub_agents=[
            query_generator,
            web_searcher, 
            answer_synthesizer
        ]
    )
    
    return research_workflow