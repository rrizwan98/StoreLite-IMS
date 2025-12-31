"""
Agent Session Service - PostgreSQL-backed session storage for Schema Agent.

Uses OpenAI Agents SDK's SQLAlchemySession for persistent conversation history
across page reloads and browser sessions.
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from agents.extensions.memory import SQLAlchemySession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

logger = logging.getLogger(__name__)


# IMPORTANT:
# Do NOT cache SQLAlchemySession objects long-term.
# They hold DB connections/engines internally, which can become stale/closed
# (especially with reloads). Persistence is already provided by the DB tables.
_tables_created: bool = False


def _get_async_database_url() -> str:
    """
    Get async-compatible database URL from environment.

    Converts postgresql:// to postgresql+asyncpg:// and handles sslmode.
    Also converts Neon pooler URLs to direct connection URLs for session management.
    """
    database_url = os.getenv("DATABASE_URL", "")

    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    # Convert to async URL if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Convert Neon pooler URL to direct connection URL
    # The pooler doesn't work well with prepared statements after schema changes
    # Pooler: ep-xxx-pooler.region.aws.neon.tech
    # Direct: ep-xxx.region.aws.neon.tech
    if "-pooler." in database_url:
        database_url = database_url.replace("-pooler.", ".", 1)
        logger.info("[AgentSession] Using direct Neon connection (not pooler) for session management")

    # Handle sslmode for asyncpg - convert to ssl=require format
    if "sslmode=" in database_url:
        parsed = urlparse(database_url)
        query_params = parse_qs(parsed.query)

        # Remove sslmode and add ssl if sslmode was 'require'
        sslmode = query_params.pop("sslmode", ["disable"])[0]
        if sslmode == "require":
            query_params["ssl"] = ["require"]

        # Rebuild URL
        new_query = urlencode(query_params, doseq=True)
        database_url = urlunparse(parsed._replace(query=new_query))

    return database_url


def create_user_session(user_id: int, thread_id: Optional[str] = None) -> SQLAlchemySession:
    """
    Create or retrieve a session for a user using from_url method.

    Args:
        user_id: The user's ID
        thread_id: Optional thread ID for ChatKit (uses user_id if not provided)

    Returns:
        SQLAlchemySession instance backed by PostgreSQL
    """
    global _tables_created

    # Generate session ID from user_id and optional thread_id
    if thread_id:
        session_id = f"user-{user_id}-{thread_id[:20]}"  # Limit thread_id length
    else:
        session_id = f"user-{user_id}-default"

    try:
        database_url = _get_async_database_url()

        # Use from_url which handles table creation better
        # Only create tables on first session
        session = SQLAlchemySession.from_url(
            session_id,
            url=database_url,
            create_tables=not _tables_created,
        )

        _tables_created = True
        logger.info(f"[AgentSession] Created session (non-cached): {session_id}")
        return session

    except Exception as e:
        logger.error(f"[AgentSession] Failed to create session {session_id}: {e}")
        raise


def get_session_by_id(session_id: str) -> SQLAlchemySession:
    """
    Get a session by its ID.

    Args:
        session_id: The session ID (e.g., "user-123-thread-abc")

    Returns:
        SQLAlchemySession instance
    """
    global _tables_created

    database_url = _get_async_database_url()

    session = SQLAlchemySession.from_url(
        session_id,
        url=database_url,
        create_tables=not _tables_created,
    )

    _tables_created = True
    return session


async def delete_user_sessions(user_id: int) -> bool:
    """
    Delete all sessions for a user from cache.

    Args:
        user_id: The user's ID

    Returns:
        True if successful
    """
    try:
        # Sessions are no longer cached in-process; nothing to clear here.
        logger.info(f"[AgentSession] delete_user_sessions: sessions are non-cached; no action for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"[AgentSession] Failed to delete sessions for user {user_id}: {e}")
        return False


async def get_session_history(user_id: int, thread_id: Optional[str] = None, limit: int = 50) -> list:
    """
    Get conversation history for a user's session.

    Args:
        user_id: The user's ID
        thread_id: Optional thread ID
        limit: Maximum number of items to return

    Returns:
        List of conversation items
    """
    try:
        session = create_user_session(user_id, thread_id)
        items = await session.get_items(limit=limit)
        return items
    except Exception as e:
        logger.error(f"[AgentSession] Failed to get history for user {user_id}: {e}")
        return []


async def cleanup_session_engine():
    """
    Cleanup the session cache on shutdown.
    Call this when the application is shutting down.
    """
    global _tables_created
    _tables_created = False
    logger.info("[AgentSession] Session cache cleared")


class AgentSessionManager:
    """
    Manager class for handling agent sessions.

    Provides a convenient interface for creating and managing
    PostgreSQL-backed sessions for the Schema Query Agent.
    """

    def __init__(self, user_id: int):
        """
        Initialize session manager for a user.

        Args:
            user_id: The user's ID
        """
        self.user_id = user_id
        self._current_thread_id: Optional[str] = None

    def get_session(self, thread_id: Optional[str] = None) -> SQLAlchemySession:
        """
        Get or create a session for the current thread.

        Args:
            thread_id: Optional thread ID (from ChatKit)

        Returns:
            SQLAlchemySession instance
        """
        # Always return a fresh session object to avoid stale/closed connections.
        # The DB provides persistence, so this does not break history replay.
        self._current_thread_id = thread_id
        return create_user_session(self.user_id, thread_id)

    async def get_history(self, limit: int = 50) -> list:
        """
        Get conversation history for current session.

        Args:
            limit: Maximum items to return

        Returns:
            List of conversation items
        """
        return await get_session_history(self.user_id, self._current_thread_id, limit)

    async def clear_session(self):
        """
        Clear the current session.
        Creates a fresh session on next get_session call.
        """
        self._current_thread_id = None
        logger.info(f"[AgentSession] Cleared session for user {self.user_id}")


# Export for easy importing
__all__ = [
    "create_user_session",
    "get_session_by_id",
    "delete_user_sessions",
    "get_session_history",
    "cleanup_session_engine",
    "AgentSessionManager",
]
