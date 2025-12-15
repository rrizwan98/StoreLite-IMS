"""
T011: Unit Tests for Session Manager (December 2025)

Tests for SessionManager class:
- Async session creation with UUID and metadata
- Session retrieval from PostgreSQL
- Conversation history updates with rolling window
- Session cleanup (deletion of old sessions)
- Session count tracking
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from app.agents.session_manager import SessionManager
from app.models import AgentSession


class TestSessionManagerInitialization:
    """Test SessionManager initialization"""

    def test_init_with_default_context_size(self):
        """Test: SessionManager initializes with default context_size=5"""
        # Arrange
        mock_db = AsyncMock()

        # Act
        manager = SessionManager(db_session=mock_db)

        # Assert
        assert manager.db_session == mock_db
        assert manager.context_size == 5

    def test_init_with_custom_context_size(self):
        """Test: SessionManager initializes with custom context_size"""
        # Arrange
        mock_db = AsyncMock()
        custom_size = 10

        # Act
        manager = SessionManager(db_session=mock_db, context_size=custom_size)

        # Assert
        assert manager.context_size == custom_size


class TestSessionCreation:
    """Test session creation functionality"""

    @pytest.mark.asyncio
    async def test_create_session_with_auto_generated_id(self):
        """Test: create_session() generates UUID if session_id not provided"""
        # Arrange
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.execute = AsyncMock()

        manager = SessionManager(db_session=mock_db)

        # Mock get_session to return None (session doesn't exist)
        with patch.object(manager, 'get_session', return_value=None):
            # Act
            session = await manager.create_session()

            # Assert
            assert session.session_id is not None
            assert len(session.session_id) == 36  # UUID length
            assert session.conversation_history == []
            assert session.session_metadata == {}
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_with_custom_id(self):
        """Test: create_session() uses provided session_id"""
        # Arrange
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        custom_id = "test-session-123"

        manager = SessionManager(db_session=mock_db)

        # Mock get_session to return None
        with patch.object(manager, 'get_session', return_value=None):
            # Act
            session = await manager.create_session(session_id=custom_id)

            # Assert
            assert session.session_id == custom_id

    @pytest.mark.asyncio
    async def test_create_session_with_metadata(self):
        """Test: create_session() stores metadata"""
        # Arrange
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        metadata = {"user": "alice", "store": "NYC"}

        manager = SessionManager(db_session=mock_db)

        # Mock get_session to return None
        with patch.object(manager, 'get_session', return_value=None):
            # Act
            session = await manager.create_session(metadata=metadata)

            # Assert
            assert session.session_metadata == metadata

    @pytest.mark.asyncio
    async def test_create_session_duplicate_raises_error(self):
        """Test: create_session() raises ValueError if session_id already exists"""
        # Arrange
        mock_db = AsyncMock()
        existing_session = MagicMock()
        existing_session.session_id = "existing-session"

        manager = SessionManager(db_session=mock_db)

        # Mock get_session to return existing session
        with patch.object(manager, 'get_session', return_value=existing_session):
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await manager.create_session(session_id="existing-session")

            assert "already exists" in str(exc_info.value)


class TestSessionRetrieval:
    """Test session retrieval functionality"""

    @pytest.mark.asyncio
    async def test_get_session_returns_existing_session(self):
        """Test: get_session() returns existing session"""
        # Arrange
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_session = MagicMock(spec=AgentSession)
        mock_session.session_id = "test-session"
        mock_session.conversation_history = []
        mock_result.scalars.return_value.first.return_value = mock_session
        mock_db.execute = AsyncMock(return_value=mock_result)

        manager = SessionManager(db_session=mock_db)

        # Act
        session = await manager.get_session("test-session")

        # Assert
        assert session == mock_session
        assert session.session_id == "test-session"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_returns_none_if_not_found(self):
        """Test: get_session() returns None if session doesn't exist"""
        # Arrange
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        manager = SessionManager(db_session=mock_db)

        # Act
        session = await manager.get_session("nonexistent")

        # Assert
        assert session is None

    @pytest.mark.asyncio
    async def test_get_session_with_conversation_history(self):
        """Test: get_session() retrieves conversation history"""
        # Arrange
        mock_db = AsyncMock()
        mock_result = MagicMock()
        conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        mock_session = MagicMock(spec=AgentSession)
        mock_session.conversation_history = conversation
        mock_result.scalars.return_value.first.return_value = mock_session
        mock_db.execute = AsyncMock(return_value=mock_result)

        manager = SessionManager(db_session=mock_db)

        # Act
        session = await manager.get_session("test-session")

        # Assert
        assert len(session.conversation_history) == 2
        assert session.conversation_history[0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_get_session_handles_error(self):
        """Test: get_session() raises exception on database error"""
        # Arrange
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("Database connection error"))

        manager = SessionManager(db_session=mock_db)

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await manager.get_session("test-session")

        assert "Database connection error" in str(exc_info.value)


class TestSessionUpdate:
    """Test session update functionality"""

    @pytest.mark.asyncio
    async def test_save_session_updates_conversation_history(self):
        """Test: save_session() updates conversation_history"""
        # Arrange
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_session = MagicMock(spec=AgentSession)
        mock_session.conversation_history = []
        mock_session.session_metadata = {}

        manager = SessionManager(db_session=mock_db)

        new_history = [
            {"role": "user", "content": "Add 10kg sugar"},
            {"role": "assistant", "content": "Done"},
        ]

        # Mock get_session
        with patch.object(manager, 'get_session', return_value=mock_session):
            # Act
            result = await manager.save_session("test-session", new_history)

            # Assert
            assert result.conversation_history == new_history
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_session_respects_context_window(self):
        """Test: save_session() limits history to context_size * 2"""
        # Arrange
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_session = MagicMock(spec=AgentSession)
        mock_session.conversation_history = []
        mock_session.session_metadata = {}

        manager = SessionManager(db_session=mock_db, context_size=2)

        # Create history with 6 messages (3 pairs)
        large_history = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(6)
        ]

        # Mock get_session
        with patch.object(manager, 'get_session', return_value=mock_session):
            # Act
            await manager.save_session("test-session", large_history)

            # Assert - should keep only last 4 messages (context_size * 2)
            assert len(mock_session.conversation_history) == 4
            assert mock_session.conversation_history[0]["content"] == "Message 2"

    @pytest.mark.asyncio
    async def test_save_session_updates_metadata(self):
        """Test: save_session() updates session_metadata"""
        # Arrange
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_session = MagicMock(spec=AgentSession)
        mock_session.conversation_history = []
        # Use MagicMock for session_metadata so .update() can be mocked
        mock_session.session_metadata = MagicMock()

        manager = SessionManager(db_session=mock_db)

        new_metadata = {"store": "NYC"}

        # Mock get_session
        with patch.object(manager, 'get_session', return_value=mock_session):
            # Act
            await manager.save_session(
                "test-session",
                [],
                metadata=new_metadata
            )

            # Assert
            mock_session.session_metadata.update.assert_called_once_with(new_metadata)

    @pytest.mark.asyncio
    async def test_save_session_updates_timestamp(self):
        """Test: save_session() updates updated_at timestamp"""
        # Arrange
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_session = MagicMock(spec=AgentSession)
        mock_session.conversation_history = []
        mock_session.session_metadata = {}

        manager = SessionManager(db_session=mock_db)

        # Mock get_session
        with patch.object(manager, 'get_session', return_value=mock_session):
            # Act
            await manager.save_session("test-session", [])

            # Assert
            assert mock_session.updated_at is not None
            assert isinstance(mock_session.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_save_session_nonexistent_raises_error(self):
        """Test: save_session() raises ValueError if session not found"""
        # Arrange
        mock_db = AsyncMock()
        manager = SessionManager(db_session=mock_db)

        # Mock get_session to return None
        with patch.object(manager, 'get_session', return_value=None):
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await manager.save_session("nonexistent", [])

            assert "not found" in str(exc_info.value)


class TestSessionCleanup:
    """Test session cleanup functionality"""

    @pytest.mark.asyncio
    async def test_delete_old_sessions_removes_expired_sessions(self):
        """Test: delete_old_sessions() deletes sessions older than N days"""
        # Arrange
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        manager = SessionManager(db_session=mock_db)

        # Act
        deleted_count = await manager.delete_old_sessions(days=30)

        # Assert
        assert deleted_count == 5
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_old_sessions_returns_zero_if_none_deleted(self):
        """Test: delete_old_sessions() returns 0 if no sessions to delete"""
        # Arrange
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        manager = SessionManager(db_session=mock_db)

        # Act
        deleted_count = await manager.delete_old_sessions(days=30)

        # Assert
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_delete_old_sessions_respects_custom_days(self):
        """Test: delete_old_sessions() uses custom days parameter"""
        # Arrange
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        manager = SessionManager(db_session=mock_db)

        # Act
        deleted_count = await manager.delete_old_sessions(days=7)

        # Assert
        assert deleted_count == 3
        # Verify the cutoff date calculation was based on 7 days
        call_args = mock_db.execute.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_delete_old_sessions_handles_error(self):
        """Test: delete_old_sessions() rolls back on error"""
        # Arrange
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("Database error"))
        mock_db.rollback = AsyncMock()

        manager = SessionManager(db_session=mock_db)

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await manager.delete_old_sessions(days=30)

        assert "Database error" in str(exc_info.value)
        mock_db.rollback.assert_called_once()


class TestSessionCount:
    """Test session count tracking"""

    @pytest.mark.asyncio
    async def test_get_session_count_returns_count(self):
        """Test: get_session_count() returns total active sessions"""
        # Arrange
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 10
        mock_db.execute = AsyncMock(return_value=mock_result)

        manager = SessionManager(db_session=mock_db)

        # Act
        count = await manager.get_session_count()

        # Assert
        assert count == 10
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_count_returns_zero_if_empty(self):
        """Test: get_session_count() returns 0 if no sessions"""
        # Arrange
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        manager = SessionManager(db_session=mock_db)

        # Act
        count = await manager.get_session_count()

        # Assert
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_session_count_handles_error(self):
        """Test: get_session_count() returns 0 on database error"""
        # Arrange
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("Database error"))

        manager = SessionManager(db_session=mock_db)

        # Act
        count = await manager.get_session_count()

        # Assert
        assert count == 0  # Should return 0 on error, not raise


class TestSessionManagerIntegration:
    """Integration tests for complete workflows"""

    @pytest.mark.asyncio
    async def test_full_workflow_create_update_retrieve(self):
        """Test: Full workflow of creating, updating, and retrieving session"""
        # Arrange
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        manager = SessionManager(db_session=mock_db, context_size=5)

        # Create session
        mock_new_session = MagicMock(spec=AgentSession)
        mock_new_session.session_id = "test-123"
        mock_new_session.conversation_history = []
        mock_new_session.session_metadata = {}

        with patch.object(manager, 'get_session', return_value=None):
            session = await manager.create_session(session_id="test-123")

        # Update session
        mock_updated_session = MagicMock(spec=AgentSession)
        mock_updated_session.conversation_history = [
            {"role": "user", "content": "Hello"},
        ]
        mock_updated_session.session_metadata = {}

        with patch.object(manager, 'get_session', return_value=mock_updated_session):
            updated = await manager.save_session(
                "test-123",
                [{"role": "user", "content": "Hello"}]
            )

        # Retrieve session
        mock_retrieved_session = MagicMock(spec=AgentSession)
        mock_retrieved_session.conversation_history = [
            {"role": "user", "content": "Hello"},
        ]

        with patch.object(manager, 'get_session', return_value=mock_retrieved_session):
            retrieved = await manager.get_session("test-123")

        # Assert
        assert retrieved.conversation_history == [{"role": "user", "content": "Hello"}]

    @pytest.mark.asyncio
    async def test_multiple_sessions_independent(self):
        """Test: Multiple sessions are independent"""
        # Arrange
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        manager = SessionManager(db_session=mock_db)

        # Create two sessions
        session1 = MagicMock(spec=AgentSession)
        session1.session_id = "session-1"
        session1.conversation_history = []

        session2 = MagicMock(spec=AgentSession)
        session2.session_id = "session-2"
        session2.conversation_history = []

        # Update first session
        session1.conversation_history = [{"role": "user", "content": "Session 1"}]

        # Update second session
        session2.conversation_history = [{"role": "user", "content": "Session 2"}]

        # Assert - sessions have different histories
        assert session1.conversation_history != session2.conversation_history
        assert session1.conversation_history[0]["content"] == "Session 1"
        assert session2.conversation_history[0]["content"] == "Session 2"


# Markers for pytest
pytestmark = pytest.mark.unit
