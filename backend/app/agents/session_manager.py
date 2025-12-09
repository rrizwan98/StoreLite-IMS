"""
Session Manager for persisting agent conversation history in PostgreSQL.

Handles:
- Session creation with unique session_id
- Conversation history retrieval (rolling window of last 5 messages)
- Session updates with new conversation history
- Session cleanup (deletion of old sessions)
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.sql import func

from app.models import AgentSession

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages agent sessions with PostgreSQL persistence."""

    def __init__(
        self,
        db_session: AsyncSession,
        context_size: int = 5,
    ):
        """
        Initialize SessionManager.

        Args:
            db_session: SQLAlchemy async session for database access
            context_size: Number of recent message pairs to retain
        """
        self.db_session = db_session
        self.context_size = context_size

    async def create_session(
        self,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentSession:
        """
        Create a new agent session.

        Args:
            session_id: Optional custom session ID; generates UUID if not provided
            metadata: Optional metadata dict (user context, store name, etc.)

        Returns:
            Created AgentSession object

        Raises:
            ValueError: If session_id already exists
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        # Check if session already exists
        existing = await self.get_session(session_id)
        if existing:
            raise ValueError(f"Session {session_id} already exists")

        # Create new session
        new_session = AgentSession(
            id=str(uuid.uuid4()),
            session_id=session_id,
            conversation_history=[],
            session_metadata=metadata or {},
        )

        self.db_session.add(new_session)
        await self.db_session.commit()
        await self.db_session.refresh(new_session)

        logger.info(f"Created new session: {session_id}")
        return new_session

    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        """
        Retrieve a session by session_id.

        Returns the session with its conversation history (last N messages).

        Args:
            session_id: Session ID to retrieve

        Returns:
            AgentSession if found, None otherwise
        """
        try:
            query = select(AgentSession).where(AgentSession.session_id == session_id)
            result = await self.db_session.execute(query)
            session = result.scalars().first()

            if session:
                logger.debug(f"Retrieved session {session_id} with {len(session.conversation_history)} messages")
            else:
                logger.debug(f"Session {session_id} not found")

            return session

        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            raise

    async def save_session(
        self,
        session_id: str,
        conversation_history: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentSession:
        """
        Update session with new conversation history.

        Automatically limits conversation history to the last N message pairs.

        Args:
            session_id: Session ID to update
            conversation_history: Complete conversation history list
            metadata: Optional metadata to update

        Returns:
            Updated AgentSession object

        Raises:
            ValueError: If session not found
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Limit to recent messages (context_size * 2 for user + assistant pairs)
        limited_history = conversation_history[-(self.context_size * 2) :]

        session.conversation_history = limited_history
        session.updated_at = datetime.utcnow()

        if metadata:
            session.session_metadata.update(metadata)

        await self.db_session.commit()
        await self.db_session.refresh(session)

        logger.debug(f"Updated session {session_id} with {len(limited_history)} messages")
        return session

    async def delete_old_sessions(self, days: int = 30) -> int:
        """
        Delete sessions older than N days.

        Used for cleanup of abandoned sessions.

        Args:
            days: Delete sessions created more than this many days ago

        Returns:
            Number of sessions deleted

        Raises:
            Exception: On database error
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Delete old sessions
            query = delete(AgentSession).where(
                AgentSession.created_at < cutoff_date
            )
            result = await self.db_session.execute(query)
            await self.db_session.commit()

            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} sessions older than {days} days")

            return deleted_count

        except Exception as e:
            logger.error(f"Error deleting old sessions: {e}")
            await self.db_session.rollback()
            raise

    async def get_session_count(self) -> int:
        """Get total number of active sessions."""
        try:
            query = select(func.count(AgentSession.id))
            result = await self.db_session.execute(query)
            count = result.scalar()
            return count or 0
        except Exception as e:
            logger.error(f"Error counting sessions: {e}")
            return 0
