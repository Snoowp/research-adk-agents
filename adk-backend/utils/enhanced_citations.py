"""Enhanced citation utilities matching original LangGraph implementation patterns."""

import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse


def resolve_urls(urls_to_resolve: List[Any], id: int) -> Dict[str, str]:
    """Create a map of vertex AI search URLs to short URLs with unique ID.
    
    From original implementation - ensures each original URL gets a consistent 
    shortened form while maintaining uniqueness.
    """
    prefix = f"https://vertexaisearch.cloud.google.com/id/"
    urls = [site.web.uri for site in urls_to_resolve if hasattr(site, 'web') and hasattr(site.web, 'uri')]

    # Create a dictionary that maps each unique URL to its first occurrence index
    resolved_map = {}
    for idx, url in enumerate(urls):
        if url not in resolved_map:
            resolved_map[url] = f"{prefix}{id}-{idx}"

    return resolved_map


def insert_citation_markers(text, citations_list):
    """Insert citation markers into text based on start and end indices.
    
    From original implementation - inserts citation markers [1], [2], etc. 
    into text string based on grounding metadata positions.
    """
    # Sort citations by end_index in descending order.
    # If end_index is the same, secondary sort by start_index descending.
    # This ensures that insertions at the end of the string don't affect
    # the indices of earlier parts of the string that still need to be processed.
    sorted_citations = sorted(
        citations_list, key=lambda c: (c["end_index"], c["start_index"]), reverse=True
    )

    modified_text = text
    for citation_info in sorted_citations:
        # These indices refer to positions in the *original* text,
        # but since we iterate from the end, they remain valid for insertion
        # relative to the parts of the string already processed.
        end_idx = citation_info["end_index"]
        marker_to_insert = ""
        for segment in citation_info["segments"]:
            marker_to_insert += f" [{segment['label']}]({segment['short_url']})"
        # Insert the citation marker at the original end_idx position
        modified_text = (
            modified_text[:end_idx] + marker_to_insert + modified_text[end_idx:]
        )

    return modified_text


def get_citations(response, resolved_urls_map):
    """Extract and format citation information from Gemini model's response.
    
    From original implementation - processes grounding metadata to construct
    citation objects with start/end indices and formatted markdown links.
    """
    citations = []

    # Ensure response and necessary nested structures are present
    if not response or not response.candidates:
        return citations

    candidate = response.candidates[0]
    if (
        not hasattr(candidate, "grounding_metadata")
        or not candidate.grounding_metadata
        or not hasattr(candidate.grounding_metadata, "grounding_supports")
    ):
        return citations

    for support in candidate.grounding_metadata.grounding_supports:
        citation = {}

        # Ensure segment information is present
        if not hasattr(support, "segment") or support.segment is None:
            continue  # Skip this support if segment info is missing

        start_index = (
            support.segment.start_index
            if support.segment.start_index is not None
            else 0
        )

        # Ensure end_index is present to form a valid segment
        if support.segment.end_index is None:
            continue  # Skip if end_index is missing, as it's crucial

        # Add 1 to end_index to make it an exclusive end for slicing/range purposes
        # (assuming the API provides an inclusive end_index)
        citation["start_index"] = start_index
        citation["end_index"] = support.segment.end_index

        citation["segments"] = []
        if (
            hasattr(support, "grounding_chunk_indices")
            and support.grounding_chunk_indices
        ):
            for ind in support.grounding_chunk_indices:
                try:
                    chunk = candidate.grounding_metadata.grounding_chunks[ind]
                    resolved_url = resolved_urls_map.get(chunk.web.uri, None)
                    citation["segments"].append(
                        {
                            "label": chunk.web.title.split(".")[:-1][0],
                            "short_url": resolved_url,
                            "value": chunk.web.uri,
                        }
                    )
                except (IndexError, AttributeError, NameError):
                    # Handle cases where chunk, web, uri, or resolved_map might be problematic
                    # For simplicity, we'll just skip adding this particular segment link
                    # In a production system, you might want to log this.
                    pass
        citations.append(citation)
    return citations


def process_search_response_with_grounding(response_text: str, grounding_metadata: Dict[str, Any], search_id: int) -> tuple:
    """Process search response with enhanced grounding metadata handling.
    
    Combines original citation processing with enhanced grounding metadata extraction.
    """
    if not grounding_metadata:
        return response_text, []
    
    # Create URL mapping using original pattern
    grounding_chunks = grounding_metadata.get('grounding_chunks', [])
    resolved_urls = resolve_urls(grounding_chunks, search_id)
    
    # Extract citations using original algorithm
    citations = get_citations_from_metadata(grounding_metadata, resolved_urls)
    
    # Insert citation markers into text
    cited_text = insert_citation_markers(response_text, citations)
    
    # Extract source list for final answer
    sources = extract_sources_from_citations(citations)
    
    return cited_text, sources


def get_citations_from_metadata(grounding_metadata: Dict[str, Any], resolved_urls: Dict[str, str]) -> List[Dict[str, Any]]:
    """Extract citations from grounding metadata dictionary format."""
    citations = []
    
    grounding_supports = grounding_metadata.get('grounding_supports', [])
    grounding_chunks = grounding_metadata.get('grounding_chunks', [])
    
    for support in grounding_supports:
        citation = {}
        
        # Extract segment information
        segment = support.get('segment', {})
        start_index = segment.get('start_index', 0)
        end_index = segment.get('end_index')
        
        if end_index is None:
            continue
            
        citation["start_index"] = start_index
        citation["end_index"] = end_index
        citation["segments"] = []
        
        # Process grounding chunk indices
        chunk_indices = support.get('grounding_chunk_indices', [])
        for chunk_idx in chunk_indices:
            if chunk_idx < len(grounding_chunks):
                try:
                    chunk = grounding_chunks[chunk_idx]
                    web_info = chunk.get('web', {})
                    uri = web_info.get('uri', '')
                    title = web_info.get('title', '')
                    
                    resolved_url = resolved_urls.get(uri, uri)
                    citation["segments"].append({
                        "label": title.split(".")[0] if title else "Source",
                        "short_url": resolved_url,
                        "value": uri,
                    })
                except (IndexError, KeyError, AttributeError):
                    continue
        
        if citation["segments"]:
            citations.append(citation)
    
    return citations


def extract_sources_from_citations(citations: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extract unique sources from citations for final bibliography."""
    sources = []
    seen_urls = set()
    
    for citation in citations:
        for segment in citation.get("segments", []):
            url = segment.get("value", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    "title": segment.get("label", "Unknown Source"),
                    "url": url,
                    "short_url": segment.get("short_url", url)
                })
    
    return sources


def format_sources_for_final_answer(sources: List[Dict[str, str]]) -> str:
    """Format sources section for final answer."""
    if not sources:
        return ""
    
    formatted_sources = ["## Sources"]
    for i, source in enumerate(sources, 1):
        title = source.get("title", "Unknown Source")
        url = source.get("url", "#")
        formatted_sources.append(f"[{i}] [{title}]({url})")
    
    return "\n".join(formatted_sources)


def enhance_web_search_with_citations(web_searcher_agent, use_grounding: bool = True):
    """Enhance web search agent with advanced citation processing."""
    if not use_grounding:
        return web_searcher_agent
    
    # This would be implemented to wrap the web_searcher_agent
    # with enhanced citation processing capabilities
    # For now, return the original agent
    return web_searcher_agent