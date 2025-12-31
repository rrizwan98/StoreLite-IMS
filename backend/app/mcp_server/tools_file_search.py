"""
Gemini File Search Tool for Schema Agent.

This module provides a function tool that enables the Schema Agent to search
through user's uploaded files using Gemini's File Search API (semantic RAG).

Features:
- Semantic search across all user's uploaded files
- Automatic citations from source documents
- Integration with Gemini FileSearchStore
- Context-aware user file access (per-user isolation)

Usage:
    # The tool is automatically added to Schema Agent's tools list
    # User can trigger search by selecting "Use File Search" from Apps menu
    # Agent can also autonomously decide to use file search based on query context

Version: 1.0
Date: December 30, 2025
"""

import logging
from typing import Annotated, Optional

from agents import function_tool

logger = logging.getLogger(__name__)

# Thread-local context for user_id and db_session
# Set before agent runs and cleared after
_file_search_context = {
    "user_id": None,
    "db_session": None,
}


def set_file_search_context(user_id: int, db_session) -> None:
    """
    Set the file search context for the current request.

    Must be called before agent runs with user's file search query.

    Args:
        user_id: Current user's ID
        db_session: Database session for the request
    """
    _file_search_context["user_id"] = user_id
    _file_search_context["db_session"] = db_session
    logger.debug(f"[File Search Tool] Context set for user {user_id}")


def clear_file_search_context() -> None:
    """Clear the file search context after request completes."""
    _file_search_context["user_id"] = None
    _file_search_context["db_session"] = None
    logger.debug("[File Search Tool] Context cleared")


def get_file_search_context() -> tuple[Optional[int], Optional[object]]:
    """Get current file search context."""
    return _file_search_context["user_id"], _file_search_context["db_session"]


@function_tool
async def file_search(
    query: Annotated[str, "The search query to find information in user's uploaded files"]
) -> str:
    """
    Search through user's uploaded files to find relevant information.

    Use this tool when the user asks about:
    - Content in their uploaded documents, PDFs, or files
    - Information from files they've added through File Search feature
    - Specific data or facts from their personal documents
    - Summaries or analysis of their uploaded materials

    The search uses semantic understanding to find relevant content,
    not just keyword matching. Results include citations showing
    which files contained the information.

    DO NOT use this tool for:
    - Queries about the database or inventory data (use SQL tools instead)
    - General web searches (use google_search instead)
    - Creating or modifying files

    Args:
        query: The search query to find information in uploaded files

    Returns:
        Answer with citations from the user's files.
        Format:
        [Response text with information from files]

        Sources:
        1. **filename.pdf**: relevant excerpt...
        2. **document.docx**: relevant excerpt...
    """
    logger.info(f"[File Search Tool] Searching: {query[:100]}...")

    user_id, db_session = get_file_search_context()

    if not user_id:
        logger.warning("[File Search Tool] No user context set")
        return "Unable to search files: User context not available. Please try again."

    try:
        from app.services.gemini_file_search_service import gemini_file_search_service

        # Use the service to search
        if db_session:
            result = await gemini_file_search_service.search_files(user_id, query, db_session)
        else:
            # Fallback: create a new session
            from app.database import async_session
            async with async_session() as db:
                result = await gemini_file_search_service.search_files(user_id, query, db)

        # Check result status
        if not result.get("has_files", False):
            logger.info("[File Search Tool] No files uploaded by user")
            return result.get("answer", "You haven't uploaded any files yet. Please upload files first using the 'Use File Search' option in the + menu.")

        if result.get("processing", False):
            logger.info("[File Search Tool] Files still processing")
            return result.get("answer", "Your files are still processing. Please wait a moment and try again.")

        if result.get("error"):
            logger.warning(f"[File Search Tool] Search error: {result['error']}")
            return f"Search encountered an issue: {result['error']}"

        # Format response with citations
        answer = result.get("answer", "No relevant information found in your files.")
        citations = result.get("citations", [])

        if citations:
            formatted_response = answer + "\n\n**Sources:**\n"
            for i, cite in enumerate(citations, 1):
                source = cite.get("source", "Unknown")
                text = cite.get("text", "")
                formatted_response += f"{i}. **{source}**: {text}\n"

            logger.info(f"[File Search Tool] Success: {len(citations)} citations found")
            return formatted_response
        else:
            logger.info("[File Search Tool] Answer found but no citations")
            return answer

    except ImportError as e:
        logger.error(f"[File Search Tool] Import error: {e}")
        return "File search service not available. Please check your configuration."

    except Exception as e:
        logger.error(f"[File Search Tool] Error: {e}", exc_info=True)
        return f"File search encountered an error: {str(e)}. Please try again."


# Export the tool for use in Schema Agent
FILE_SEARCH_TOOLS = [file_search]

__all__ = [
    "file_search",
    "FILE_SEARCH_TOOLS",
    "set_file_search_context",
    "clear_file_search_context",
    "get_file_search_context",
]
