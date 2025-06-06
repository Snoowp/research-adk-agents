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