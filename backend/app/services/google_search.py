"""
Google Search Service using Gemini's Search Grounding.

This service provides real-time web search capabilities using Google Gemini's
built-in google_search tool for grounding responses with current information.

Features:
- Real-time web search via Gemini API
- Source extraction from grounding metadata
- Markdown-formatted responses with clickable source links
- User-forced mode detection via [TOOL:GOOGLE_SEARCH] prefix
- Graceful error handling

Usage:
    service = GoogleSearchService(api_key=GEMINI_API_KEY)
    result = await service.search("What is the latest Python version?")
    formatted = service.format_response_with_sources(result)
"""

import logging
import os
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

# Tool prefix for user-forced mode
GOOGLE_SEARCH_PREFIX = "[TOOL:GOOGLE_SEARCH]"


@dataclass
class SearchSource:
    """A source from Google Search grounding."""
    title: str
    url: str


@dataclass
class GoogleSearchResult:
    """Result from Google Search with grounding."""
    text: str
    sources: List[SearchSource]
    search_queries: List[str]
    success: bool
    error: Optional[str] = None


def should_use_google_search(query: str) -> bool:
    """
    Check if query starts with Google Search tool prefix.

    Args:
        query: The user's query string

    Returns:
        True if query starts with [TOOL:GOOGLE_SEARCH], False otherwise
    """
    return query.strip().upper().startswith(GOOGLE_SEARCH_PREFIX)


def strip_tool_prefix(query: str) -> str:
    """
    Remove [TOOL:GOOGLE_SEARCH] prefix from query.

    Args:
        query: The user's query with potential prefix

    Returns:
        Clean query without the prefix
    """
    query = query.strip()
    # Case-insensitive prefix removal
    if query.upper().startswith(GOOGLE_SEARCH_PREFIX):
        return query[len(GOOGLE_SEARCH_PREFIX):].strip()
    return query


class GoogleSearchService:
    """
    Service for performing web searches using Google Gemini's
    google_search grounding tool.

    This service enables real-time web search capabilities by leveraging
    Gemini's built-in search grounding feature.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-robotics-er-1.5-preview"
    ):
        """
        Initialize Google Search Service.

        Args:
            api_key: Gemini API key. If not provided, uses GEMINI_API_KEY env var.
            model: Gemini model to use (default: gemini-2.5-flash)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self._client = None

        if not self.api_key:
            logger.warning("[Google Search] No GEMINI_API_KEY configured")

    def _get_client(self):
        """Get or create Gemini client."""
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"[Google Search] Initialized Gemini client (model: {self.model})")
            except ImportError:
                logger.error("[Google Search] google-genai package not installed")
                raise ImportError("google-genai package is required. Install with: pip install google-genai")
        return self._client

    async def search(self, query: str) -> GoogleSearchResult:
        """
        Perform a web search using Gemini's google_search tool.

        Args:
            query: The search query

        Returns:
            GoogleSearchResult with text, sources, and metadata
        """
        if not self.api_key:
            return GoogleSearchResult(
                text="",
                sources=[],
                search_queries=[],
                success=False,
                error="Google Search is not configured. Please set GEMINI_API_KEY."
            )

        try:
            from google.genai import types

            client = self._get_client()
            logger.info(f"[Google Search] Searching: {query[:100]}...")

            # Generate content with google_search grounding
            response = await client.aio.models.generate_content(
                model=self.model,
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(google_search=types.GoogleSearch())
                    ]
                ),
            )

            # Extract response text
            text = response.text if response.text else ""

            # Extract grounding metadata
            sources = []
            search_queries = []

            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                grounding = getattr(candidate, 'grounding_metadata', None)

                if grounding:
                    # Parse sources from grounding chunks
                    grounding_chunks = getattr(grounding, 'grounding_chunks', None)
                    if grounding_chunks:
                        for chunk in grounding_chunks:
                            web = getattr(chunk, 'web', None)
                            if web:
                                title = getattr(web, 'title', 'Unknown Source')
                                uri = getattr(web, 'uri', '')
                                if uri:
                                    sources.append(SearchSource(title=title, url=uri))

                    # Get search queries
                    web_search_queries = getattr(grounding, 'web_search_queries', None)
                    if web_search_queries:
                        search_queries = list(web_search_queries)

            logger.info(f"[Google Search] Found {len(sources)} sources, {len(search_queries)} queries")

            return GoogleSearchResult(
                text=text,
                sources=sources,
                search_queries=search_queries,
                success=True
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[Google Search] Error: {error_msg}", exc_info=True)

            # Provide user-friendly error messages
            if "timeout" in error_msg.lower():
                return GoogleSearchResult(
                    text="",
                    sources=[],
                    search_queries=[],
                    success=False,
                    error="Web search timed out. Please try again."
                )
            elif "quota" in error_msg.lower() or "rate" in error_msg.lower():
                return GoogleSearchResult(
                    text="",
                    sources=[],
                    search_queries=[],
                    success=False,
                    error="Search quota exceeded. Please try again later."
                )
            else:
                return GoogleSearchResult(
                    text="",
                    sources=[],
                    search_queries=[],
                    success=False,
                    error=f"Web search failed: {error_msg}"
                )

    def format_response_with_sources(self, result: GoogleSearchResult) -> str:
        """
        Format the search result with sources in markdown.

        Args:
            result: GoogleSearchResult from search()

        Returns:
            Markdown-formatted response with sources section
        """
        if not result.success:
            return f"Web search is temporarily unavailable: {result.error}"

        if not result.text:
            return "No results found for your search query. Please try a different query."

        # Build response with sources
        response = result.text

        if result.sources:
            response += "\n\nSources:\n"
            # Deduplicate sources by URL
            seen_urls = set()
            for source in result.sources:
                if source.url not in seen_urls:
                    seen_urls.add(source.url)
                    response += f"- [{source.title}]({source.url})\n"

        return response


# ============================================================================
# Function Tool for Agent Integration
# ============================================================================

async def perform_google_search(query: str) -> str:
    """
    Perform a Google Search and return formatted results.

    This is a convenience function for use as an agent tool.

    Args:
        query: The search query

    Returns:
        Formatted response with sources as markdown links
    """
    service = GoogleSearchService()
    result = await service.search(query)
    return service.format_response_with_sources(result)
