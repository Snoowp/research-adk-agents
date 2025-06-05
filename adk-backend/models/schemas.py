"""Pydantic models for structured outputs in ADK agents."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """A single search query with explanation."""
    query: str = Field(description="The search query to execute")
    rationale: str = Field(description="Explanation of why this query is useful")


class SearchQueryList(BaseModel):
    """List of search queries generated for research."""
    queries: List[SearchQuery] = Field(
        description="List of search queries to execute",
        min_items=1,
        max_items=5
    )


class WebSearchResult(BaseModel):
    """Result from a single web search."""
    query: str = Field(description="The original search query")
    summary: str = Field(description="Summarized findings from the search")
    sources: List[dict] = Field(
        description="List of source citations with url and title",
        default_factory=list
    )


class Reflection(BaseModel):
    """Reflection on gathered research."""
    is_sufficient: bool = Field(
        description="Whether enough information has been gathered"
    )
    reasoning: str = Field(
        description="Explanation of the assessment"
    )
    follow_up_queries: Optional[List[SearchQuery]] = Field(
        description="Additional queries needed if information is insufficient",
        default=None
    )


class ResearchState(BaseModel):
    """Shared state for the research agent."""
    user_question: str = ""
    search_queries: List[SearchQuery] = Field(default_factory=list)
    web_research_results: List[WebSearchResult] = Field(default_factory=list)
    sources_gathered: List[dict] = Field(default_factory=list)
    research_loop_count: int = 0
    max_research_loops: int = 3
    initial_search_query_count: int = 3
    reasoning_model: str = "gemini-2.0-flash-thinking-exp"
    is_sufficient: bool = False
    final_answer: Optional[str] = None