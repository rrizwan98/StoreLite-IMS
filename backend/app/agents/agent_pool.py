"""
Agent Pool Manager - Performance Optimization Module

This module provides caching and optimization for schema query agents
to reduce response times.

Key Optimizations:
1. Tiered Routing - Simple messages skip heavy MCP processing (~500ms vs 60s)
2. Tool Pre-loading - Cache function tools at module level

NOTE: MCP Server Pooling is NOT USED because postgres-mcp uses stdio transport
which creates a new subprocess for each connection. Stdio-based MCP servers
cannot be pooled as they are single-use processes.

IMPORTANT: This module does NOT change any agent logic, tool definitions,
or sub-agent behavior. It only optimizes the initialization layer.

Version: 1.1.0 - Removed MCP pooling (stdio incompatibility)
"""

import asyncio
import logging
import os
import re
from typing import Optional, List, Any, Dict

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration Constants
# ============================================================================

# Simple message detection patterns (for tiered routing)
SIMPLE_MESSAGE_PATTERNS = [
    r"^(hi|hello|hey|salam|assalam|asalam)[\s\!\.\?]*$",
    r"^(thanks|thank you|shukriya|thanks a lot)[\s\!\.\?]*$",
    r"^(bye|goodbye|ok|okay|alright)[\s\!\.\?]*$",
    r"^(yes|no|yeah|nope|han|nahi)[\s\!\.\?]*$",
    r"^(help|what can you do)[\s\?\!]*$",
]

# Pre-compiled patterns for performance
_SIMPLE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SIMPLE_MESSAGE_PATTERNS]


# ============================================================================
# Cached Function Tools (loaded once at module level)
# ============================================================================

_CACHED_FUNCTION_TOOLS: Optional[List[Any]] = None
_TOOLS_LOAD_LOCK = asyncio.Lock()


async def get_cached_function_tools() -> List[Any]:
    """
    Get function tools with module-level caching.
    Tools are loaded once and reused across all requests.

    Returns:
        List of function tools (Google Search, File Analysis, File Search, etc.)
    """
    global _CACHED_FUNCTION_TOOLS

    if _CACHED_FUNCTION_TOOLS is not None:
        return _CACHED_FUNCTION_TOOLS.copy()

    async with _TOOLS_LOAD_LOCK:
        # Double-check after acquiring lock
        if _CACHED_FUNCTION_TOOLS is not None:
            return _CACHED_FUNCTION_TOOLS.copy()

        tools = []

        # Load Google Search tool
        try:
            from app.mcp_server.tools_google_search import GOOGLE_SEARCH_TOOLS
            tools.extend(GOOGLE_SEARCH_TOOLS)
            logger.info("[AgentPool] Cached Google Search tools")
        except ImportError as e:
            logger.warning(f"[AgentPool] Google Search tools not available: {e}")

        # Load File Analysis tools
        try:
            from app.mcp_server.tools_file_analysis import FILE_ANALYSIS_TOOLS
            tools.extend(FILE_ANALYSIS_TOOLS)
            logger.info("[AgentPool] Cached File Analysis tools")
        except ImportError as e:
            logger.warning(f"[AgentPool] File Analysis tools not available: {e}")

        # Load File Search tools
        try:
            from app.mcp_server.tools_file_search import FILE_SEARCH_TOOLS
            tools.extend(FILE_SEARCH_TOOLS)
            logger.info("[AgentPool] Cached File Search tools")
        except ImportError as e:
            logger.warning(f"[AgentPool] File Search tools not available: {e}")

        _CACHED_FUNCTION_TOOLS = tools
        logger.info(f"[AgentPool] Cached {len(tools)} function tools at module level")

        return tools.copy()


def invalidate_function_tools_cache():
    """Invalidate the function tools cache (e.g., after adding new tools)."""
    global _CACHED_FUNCTION_TOOLS
    _CACHED_FUNCTION_TOOLS = None
    logger.info("[AgentPool] Function tools cache invalidated")


# ============================================================================
# Tiered Routing - Simple Message Detection
# ============================================================================

def is_simple_message(message: str) -> bool:
    """
    Check if a message is a simple greeting/acknowledgment
    that doesn't need full MCP database processing.

    Args:
        message: User's message text

    Returns:
        True if message is simple and can skip MCP processing
    """
    if not message:
        return False

    message_clean = message.strip()

    # Check against pre-compiled patterns
    for pattern in _SIMPLE_PATTERNS:
        if pattern.match(message_clean):
            logger.debug(f"[AgentPool] Simple message detected: '{message_clean[:30]}'")
            return True

    # Also check for very short messages (< 10 chars, no question mark)
    if len(message_clean) < 10 and "?" not in message_clean:
        # Additional check: no database-related keywords
        db_keywords = ["show", "get", "list", "find", "count", "how many", "what", "query", "select", "table"]
        if not any(kw in message_clean.lower() for kw in db_keywords):
            logger.debug(f"[AgentPool] Short simple message detected: '{message_clean}'")
            return True

    return False


# ============================================================================
# Simple Response Generator (for tiered routing)
# ============================================================================

SIMPLE_RESPONSES = {
    "greeting": [
        "Hello! How can I help you with your database today?",
        "Hi there! I'm ready to help you query your data. What would you like to know?",
        "Hey! Ask me anything about your database.",
    ],
    "thanks": [
        "You're welcome! Let me know if you need anything else.",
        "Happy to help! Feel free to ask more questions.",
        "No problem! Is there anything else you'd like to know?",
    ],
    "bye": [
        "Goodbye! Come back anytime you need help with your data.",
        "See you later! Your data will be here when you return.",
        "Take care! Feel free to ask more questions anytime.",
    ],
    "yes_no": [
        "Got it! What would you like to do next?",
        "Understood. How can I help you further?",
    ],
    "help": [
        "I can help you query your database using natural language! Try asking:\n"
        "- 'How many records are in the database?'\n"
        "- 'Show me the top 10 items'\n"
        "- 'What's the total value?'\n"
        "- 'Find records where status is active'\n\n"
        "Just ask your question and I'll translate it to SQL!",
    ],
}


def get_simple_response(message: str) -> str:
    """
    Get a response for simple messages without hitting the LLM.

    Args:
        message: User's simple message

    Returns:
        Appropriate response string
    """
    import random

    message_lower = message.lower().strip()

    # Determine category
    if any(w in message_lower for w in ["hi", "hello", "hey", "salam", "assalam"]):
        responses = SIMPLE_RESPONSES["greeting"]
    elif any(w in message_lower for w in ["thanks", "thank", "shukriya"]):
        responses = SIMPLE_RESPONSES["thanks"]
    elif any(w in message_lower for w in ["bye", "goodbye", "ok", "okay", "alright"]):
        responses = SIMPLE_RESPONSES["bye"]
    elif any(w in message_lower for w in ["yes", "no", "yeah", "nope", "han", "nahi"]):
        responses = SIMPLE_RESPONSES["yes_no"]
    elif any(w in message_lower for w in ["help", "what can you do"]):
        responses = SIMPLE_RESPONSES["help"]
    else:
        responses = SIMPLE_RESPONSES["greeting"]  # Default

    return random.choice(responses)


# ============================================================================
# MCP Pool Stub (No-op for compatibility)
# ============================================================================
# NOTE: MCP pooling is disabled because postgres-mcp uses stdio transport
# which cannot be reused. These are stub functions for API compatibility.

class MCPPoolEntry:
    """Stub class for compatibility - MCP pooling is disabled."""
    pass


class MCPServerPool:
    """
    Stub MCP Server Pool - pooling is disabled for stdio-based servers.

    postgres-mcp uses stdio transport which spawns a subprocess.
    These subprocesses cannot be reused after completion, so pooling
    is not possible. Each query gets a fresh MCP connection.
    """

    def __init__(self):
        logger.info("[MCPServerPool] Initialized (pooling disabled - stdio incompatible)")

    async def acquire(self, user_id: int, database_uri: str, access_mode: str = "restricted"):
        """Stub - always returns None to signal fresh connection needed."""
        return None

    async def release(self, user_id: int, entry):
        """Stub - no-op since we don't pool."""
        pass

    async def clear_user_pool(self, user_id: int):
        """Stub - no-op since we don't pool."""
        logger.debug(f"[MCPServerPool] clear_user_pool called for user {user_id} (no-op)")

    async def clear_all_pools(self):
        """Stub - no-op since we don't pool."""
        logger.debug("[MCPServerPool] clear_all_pools called (no-op)")

    def get_pool_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Return stats indicating pooling is disabled."""
        return {
            "pooling_enabled": False,
            "reason": "stdio-based MCP servers cannot be pooled",
            "optimization_active": ["tiered_routing", "tool_caching"],
        }


# Global pool instance (stub)
_mcp_pool: Optional[MCPServerPool] = None


def get_mcp_pool() -> MCPServerPool:
    """Get the global MCP server pool instance (stub)."""
    global _mcp_pool
    if _mcp_pool is None:
        _mcp_pool = MCPServerPool()
    return _mcp_pool


async def shutdown_mcp_pool():
    """Shutdown the global MCP pool (no-op for stub)."""
    global _mcp_pool
    _mcp_pool = None
    logger.info("[AgentPool] MCP pool shutdown (no-op - pooling disabled)")


# ============================================================================
# Pre-warm Helper Functions (No-op for stdio MCP)
# ============================================================================

async def pre_warm_user_agent(
    user_id: int,
    database_uri: str,
    schema_metadata: dict,
    access_mode: str = "restricted"
):
    """
    Pre-warm function (currently no-op for stdio MCP).

    NOTE: Cannot pre-warm stdio-based MCP servers as they are single-use.
    This function exists for API compatibility and future HTTP-based MCP support.
    """
    # Pre-load function tools (this still works!)
    await get_cached_function_tools()
    logger.info(f"[AgentPool] Pre-loaded function tools for user {user_id}")


# ============================================================================
# Statistics
# ============================================================================

def get_optimization_stats() -> Dict[str, Any]:
    """Get statistics about the optimization layer."""
    return {
        "mcp_pooling": {
            "enabled": False,
            "reason": "stdio-based MCP servers cannot be pooled"
        },
        "tiered_routing": {
            "enabled": True,
            "patterns_count": len(_SIMPLE_PATTERNS),
        },
        "tool_caching": {
            "enabled": True,
            "cached": _CACHED_FUNCTION_TOOLS is not None,
            "tools_count": len(_CACHED_FUNCTION_TOOLS) if _CACHED_FUNCTION_TOOLS else 0,
        },
        "active_optimizations": [
            "tiered_routing - simple messages skip MCP (~500ms)",
            "tool_caching - function tools loaded once",
        ],
    }
