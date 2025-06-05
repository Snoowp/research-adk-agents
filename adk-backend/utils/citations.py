"""Utilities for handling citations and grounding metadata from Google Search."""

import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse


def extract_citations(grounding_metadata: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract citation information from grounding metadata."""
    citations = []
    
    if not grounding_metadata:
        return citations
    
    # Extract from grounding chunks
    grounding_chunks = grounding_metadata.get('grounding_chunks', [])
    
    for chunk in grounding_chunks:
        web_info = chunk.get('web', {})
        if web_info:
            citation = {
                'title': web_info.get('title', ''),
                'url': web_info.get('uri', ''),
                'snippet': chunk.get('content', '')
            }
            # Only add if we have both title and URL
            if citation['title'] and citation['url']:
                citations.append(citation)
    
    # Deduplicate by URL
    seen_urls = set()
    unique_citations = []
    for citation in citations:
        if citation['url'] not in seen_urls:
            seen_urls.add(citation['url'])
            unique_citations.append(citation)
    
    return unique_citations


def process_search_response(response_text: str, grounding_metadata: Dict[str, Any]) -> tuple:
    """Process search response to extract text with citations and source list."""
    # Extract citations
    sources = extract_citations(grounding_metadata)
    
    # Insert citation markers into text
    cited_text = insert_citation_markers(response_text, grounding_metadata, sources)
    
    return cited_text, sources


def insert_citation_markers(
    text: str, 
    grounding_metadata: Dict[str, Any], 
    sources: List[Dict[str, str]]
) -> str:
    """Insert citation markers [1], [2], etc. into text based on grounding metadata."""
    if not grounding_metadata or not sources:
        return text
    
    # Create URL to citation number mapping
    url_to_citation = {source['url']: idx + 1 for idx, source in enumerate(sources)}
    
    # Get grounding supports (which tell us where citations should go)
    grounding_supports = grounding_metadata.get('grounding_supports', [])
    
    # Sort by start index in reverse order to avoid shifting indices
    supports_with_indices = []
    for support in grounding_supports:
        for segment in support.get('segment', {}).get('part_index', []):
            start_idx = segment.get('start_index', 0)
            end_idx = segment.get('end_index', 0)
            
            # Find the corresponding URL
            for chunk_idx in support.get('grounding_chunk_indices', []):
                grounding_chunks = grounding_metadata.get('grounding_chunks', [])
                if chunk_idx < len(grounding_chunks):
                    chunk = grounding_chunks[chunk_idx]
                    web_info = chunk.get('web', {})
                    url = web_info.get('uri', '')
                    if url in url_to_citation:
                        supports_with_indices.append({
                            'start': start_idx,
                            'end': end_idx,
                            'citation_num': url_to_citation[url]
                        })
    
    # Sort by start index in reverse order
    supports_with_indices.sort(key=lambda x: x['start'], reverse=True)
    
    # Insert citation markers
    result_text = text
    for support in supports_with_indices:
        citation_marker = f"[{support['citation_num']}]"
        # Insert at the end of the segment
        insert_pos = support['end']
        if insert_pos <= len(result_text):
            result_text = (
                result_text[:insert_pos] + 
                citation_marker + 
                result_text[insert_pos:]
            )
    
    return result_text


def format_citations_markdown(sources: List[Dict[str, str]]) -> str:
    """Format sources as markdown citations."""
    if not sources:
        return ""
    
    citations = ["## Sources"]
    for i, source in enumerate(sources, 1):
        title = source.get('title', 'Untitled')
        url = source.get('url', '#')
        citations.append(f"[{i}] [{title}]({url})")
    
    return "\n".join(citations)


def resolve_short_urls(text: str, url_mapping: Dict[str, str]) -> str:
    """Replace short URLs with original URLs in text."""
    for short_url, original_url in url_mapping.items():
        text = text.replace(short_url, original_url)
    return text


def shorten_url(url: str, max_length: int = 50) -> str:
    """Create a shortened version of URL for token efficiency."""
    if len(url) <= max_length:
        return url
    
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path
    
    # Try to keep domain + shortened path
    if len(domain) < max_length - 10:
        remaining = max_length - len(domain) - 3  # 3 for "..."
        if remaining > 0:
            return f"{domain}...{path[-remaining:]}"
    
    # Just use domain if path is too long
    return domain if len(domain) <= max_length else domain[:max_length-3] + "..."


def create_url_mapping(sources: List[Dict[str, str]]) -> Dict[str, str]:
    """Create mapping from original URLs to shortened URLs."""
    mapping = {}
    for source in sources:
        original_url = source.get('url', '')
        if original_url:
            short_url = shorten_url(original_url)
            mapping[original_url] = short_url
    return mapping