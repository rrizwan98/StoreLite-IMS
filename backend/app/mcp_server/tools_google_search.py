"""
Google Search Tool for Schema Agent.

This module provides a function tool that enables the Schema Agent to perform
web searches using Google Gemini's Search Grounding feature.

Features:
- Real-time web search for current information
- Automatic source attribution with markdown links
- Seamless integration with Schema Agent
- Two modes: User-forced (via prefix) and Agent-autonomous

Usage:
    # The tool is automatically added to Schema Agent's tools list
    # User can force search by selecting "Google Search" from Apps menu
    # Agent can also autonomously decide to use search based on query context
"""

import logging
from typing import Annotated

from agents import function_tool

from app.services.google_search import (
    GoogleSearchService,
    should_use_google_search,
    strip_tool_prefix,
)

logger = logging.getLogger(__name__)


@function_tool
async def google_search(
    query: Annotated[str, "The search query to perform on Google"]
) -> str:
    """
    Search the web using Google Search for real-time information.

    Use this tool when the user needs:
    - Current events, news, or today's information
    - Latest versions, updates, or recent releases
    - External documentation, tutorials, or how-to guides
    - Weather, stocks, or real-time data
    - Information about topics not in the database

    DO NOT use this tool for:
    - Queries about the user's database or inventory data
    - Counts, totals, or aggregations from the database
    - Internal business data stored in the database

    Args:
        query: The search query to perform

    Returns:
        Search results with sources formatted as markdown links.
        Format:
        [Response text with information]

        Sources:
        - [Source Title 1](https://example.com/1)
        - [Source Title 2](https://example.com/2)
    """
    logger.info(f"[Google Search Tool] Searching: {query[:100]}...")

    try:
        service = GoogleSearchService()
        result = await service.search(query)
        formatted = service.format_response_with_sources(result)

        if result.success:
            logger.info(f"[Google Search Tool] Success: {len(result.sources)} sources found")
        else:
            logger.warning(f"[Google Search Tool] Failed: {result.error}")

        return formatted

    except Exception as e:
        logger.error(f"[Google Search Tool] Error: {e}", exc_info=True)
        return f"Web search encountered an error: {str(e)}. Please try again."


# Export the tool for use in Schema Agent
GOOGLE_SEARCH_TOOLS = [google_search]

__all__ = [
    "google_search",
    "GOOGLE_SEARCH_TOOLS",
    "should_use_google_search",
    "strip_tool_prefix",
]
