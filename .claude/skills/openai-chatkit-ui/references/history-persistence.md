# History Persistence Reference

> Complete guide for implementing PostgreSQL-backed thread and message persistence for ChatKit.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         ChatKit UI                               │
│  ┌──────────────┐   ┌──────────────────┐   ┌──────────────────┐ │
│  │ History Panel│   │ Thread Messages  │   │ New Message      │ │
│  │ (load_threads│   │ (load_thread_items│   │ (add_thread_item)│ │
│  └──────────────┘   └──────────────────┘   └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQLChatKitStore                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ User-scoped queries (all queries filter by user_id)      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PostgreSQL                               │
│  ┌────────────────────┐     ┌─────────────────────────────────┐ │
│  │ chatkit_threads    │     │ chatkit_thread_items            │ │
│  │ - id               │ ◄── │ - id                            │ │
│  │ - user_id          │     │ - thread_id (FK)                │ │
│  │ - title            │     │ - item_type                     │ │
│  │ - created_at       │     │ - content (JSON)                │ │
│  │ - updated_at       │     │ - created_at                    │ │
│  │ - thread_metadata  │     │                                 │ │
│  └────────────────────┘     └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Models

### ChatKitThread Model

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

class ChatKitThread(Base):
    """
    ChatKit thread for persistent conversation sessions.
    Each thread represents a chat conversation for a user.
    """
    __tablename__ = "chatkit_threads"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title = Column(String(255), nullable=True)  # Auto-generated from first message
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    thread_metadata = Column(JSONB, nullable=True, default={})

    __table_args__ = ({"extend_existing": True},)

    # Relationships
    user = relationship("User", backref="chatkit_threads")
    items = relationship(
        "ChatKitThreadItem",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ChatKitThreadItem.created_at"
    )

    def __repr__(self):
        return f"<ChatKitThread(id={self.id}, user_id={self.user_id}, title={self.title})>"
```

### ChatKitThreadItem Model

```python
class ChatKitThreadItem(Base):
    """
    ChatKit thread item (message) for persistent conversation history.
    Stores both user messages and assistant responses as JSON.
    """
    __tablename__ = "chatkit_thread_items"

    id = Column(String(100), primary_key=True, index=True)
    thread_id = Column(
        String(100),
        ForeignKey("chatkit_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    item_type = Column(String(50), nullable=False, index=True)  # "user_message", "assistant_message"
    content = Column(Text, nullable=False)  # JSON serialized ChatKit item
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = ({"extend_existing": True},)

    # Relationships
    thread = relationship("ChatKitThread", back_populates="items")

    def __repr__(self):
        return f"<ChatKitThreadItem(id={self.id}, thread_id={self.thread_id}, type={self.item_type})>"
```

---

## PostgreSQL Store Implementation

### Complete Store Class

```python
from chatkit.server import Store, ThreadMetadata, ThreadItem
from chatkit.types import (
    Page,
    UserMessageItem,
    AssistantMessageItem,
    UserMessageTextContent,
    AssistantMessageContent,
    InferenceOptions,
    ImageAttachment,
    FileAttachment,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class PostgreSQLChatKitStore(Store):
    """
    PostgreSQL-backed store for ChatKit threads and messages.

    Provides persistent storage for conversation history, allowing users
    to continue conversations across page reloads and server restarts.

    All queries are scoped to the current user_id for data isolation.
    """

    def __init__(self, db: AsyncSession, user_id: int):
        """
        Initialize the store with database session and user context.

        Args:
            db: SQLAlchemy async session
            user_id: Current user's ID for scoping threads
        """
        self.db = db
        self.user_id = user_id
        self._attachments: dict[str, Any] = {}
        logger.debug(f"[ChatKitStore] Initialized for user {user_id}")

    def generate_thread_id(self, context: Any) -> str:
        """Generate a unique thread ID."""
        import uuid
        return f"thread-{uuid.uuid4().hex[:12]}"

    def generate_item_id(self, item_type: str, thread: ThreadMetadata, context: Any) -> str:
        """Generate a unique item ID."""
        import uuid
        return f"{item_type}-{uuid.uuid4().hex[:12]}"

    # ========================================
    # Thread Operations
    # ========================================

    async def save_thread(self, thread: ThreadMetadata, context: Any) -> None:
        """Save or update a thread in the database."""
        try:
            result = await self.db.execute(
                select(ChatKitThread).where(ChatKitThread.id == thread.id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing thread
                existing.updated_at = datetime.utcnow()
                if hasattr(thread, 'title') and thread.title:
                    existing.title = thread.title
                if hasattr(thread, 'metadata') and thread.metadata:
                    existing.thread_metadata = thread.metadata
            else:
                # Create new thread
                created_at_value = self._parse_datetime(thread.created_at)

                db_thread = ChatKitThread(
                    id=thread.id,
                    user_id=self.user_id,
                    title=thread.title if hasattr(thread, 'title') else None,
                    created_at=created_at_value,
                    thread_metadata=thread.metadata if hasattr(thread, 'metadata') else {},
                )
                self.db.add(db_thread)

            await self.db.commit()
            logger.debug(f"[ChatKitStore] Saved thread: {thread.id}")

        except Exception as e:
            logger.error(f"[ChatKitStore] Error saving thread {thread.id}: {e}")
            await self.db.rollback()
            raise

    async def load_thread(self, thread_id: str, context: Any) -> ThreadMetadata | None:
        """Load a thread from the database, creating if it doesn't exist."""
        try:
            result = await self.db.execute(
                select(ChatKitThread).where(
                    ChatKitThread.id == thread_id,
                    ChatKitThread.user_id == self.user_id  # User isolation
                )
            )
            db_thread = result.scalar_one_or_none()

            if db_thread:
                return ThreadMetadata(
                    id=db_thread.id,
                    title=db_thread.title,
                    created_at=db_thread.created_at.isoformat() if db_thread.created_at else None,
                )

            # Create new thread if not exists
            new_thread = ChatKitThread(
                id=thread_id,
                user_id=self.user_id,
                created_at=datetime.utcnow(),
                thread_metadata={},
            )
            self.db.add(new_thread)
            await self.db.commit()

            return ThreadMetadata(
                id=thread_id,
                created_at=new_thread.created_at.isoformat(),
            )

        except Exception as e:
            logger.error(f"[ChatKitStore] Error loading thread {thread_id}: {e}")
            await self.db.rollback()
            return ThreadMetadata(id=thread_id, created_at=datetime.utcnow().isoformat())

    async def delete_thread(self, thread_id: str, context: Any) -> None:
        """Delete a thread and all its items (cascade) from the database."""
        try:
            await self.db.execute(
                delete(ChatKitThread).where(
                    ChatKitThread.id == thread_id,
                    ChatKitThread.user_id == self.user_id  # User isolation
                )
            )
            await self.db.commit()
            logger.info(f"[ChatKitStore] Deleted thread: {thread_id}")

        except Exception as e:
            logger.error(f"[ChatKitStore] Error deleting thread {thread_id}: {e}")
            await self.db.rollback()

    async def load_threads(
        self,
        limit: int,
        after: str | None,
        order: str,
        context: Any
    ) -> Page:
        """
        Load all threads for the current user with pagination support.

        Used by ChatKit history panel to show conversation list.
        """
        try:
            # Build base query - user scoped
            query = select(ChatKitThread).where(
                ChatKitThread.user_id == self.user_id
            )

            # Handle cursor-based pagination
            if after:
                cursor_result = await self.db.execute(
                    select(ChatKitThread).where(ChatKitThread.id == after)
                )
                cursor_thread = cursor_result.scalar_one_or_none()
                if cursor_thread:
                    if order == "desc":
                        query = query.where(ChatKitThread.updated_at < cursor_thread.updated_at)
                    else:
                        query = query.where(ChatKitThread.updated_at > cursor_thread.updated_at)

            # Apply ordering and limit
            query = query.order_by(
                ChatKitThread.updated_at.desc() if order == "desc"
                else ChatKitThread.updated_at.asc()
            ).limit(limit + 1)  # Get one extra to check has_more

            result = await self.db.execute(query)
            db_threads = list(result.scalars().all())

            has_more = len(db_threads) > limit
            threads_to_return = db_threads[:limit]

            threads = [
                ThreadMetadata(
                    id=t.id,
                    title=t.title,
                    created_at=t.created_at.isoformat() if t.created_at else None,
                )
                for t in threads_to_return
            ]

            next_after = threads_to_return[-1].id if has_more and threads_to_return else None

            return Page(data=threads, has_more=has_more, after=next_after)

        except Exception as e:
            logger.error(f"[ChatKitStore] Error loading threads: {e}")
            return Page(data=[], has_more=False, after=None)

    # ========================================
    # Thread Item (Message) Operations
    # ========================================

    async def add_thread_item(self, thread_id: str, item: ThreadItem, context: Any) -> None:
        """Add a new message to a thread."""
        try:
            # Ensure thread exists
            await self.load_thread(thread_id, context)

            # Serialize item
            item_content = self._serialize_item(item)
            item_type = getattr(item, 'type', 'unknown')
            item_id = getattr(item, 'id', self.generate_item_id(item_type, None, context))

            db_item = ChatKitThreadItem(
                id=item_id,
                thread_id=thread_id,
                item_type=item_type,
                content=item_content,
                created_at=datetime.utcnow(),
            )
            self.db.add(db_item)

            # Update thread's updated_at
            await self.db.execute(
                update(ChatKitThread)
                .where(ChatKitThread.id == thread_id)
                .values(updated_at=datetime.utcnow())
            )

            await self.db.commit()
            logger.debug(f"[ChatKitStore] Added item {item_id} to thread {thread_id}")

        except Exception as e:
            logger.error(f"[ChatKitStore] Error adding item to thread {thread_id}: {e}")
            await self.db.rollback()

    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: str,
        context: Any
    ) -> Page:
        """Load all messages from a thread with pagination."""
        try:
            query = select(ChatKitThreadItem).where(
                ChatKitThreadItem.thread_id == thread_id
            )

            if after:
                cursor_result = await self.db.execute(
                    select(ChatKitThreadItem).where(ChatKitThreadItem.id == after)
                )
                cursor_item = cursor_result.scalar_one_or_none()
                if cursor_item:
                    query = query.where(ChatKitThreadItem.created_at > cursor_item.created_at)

            # Always chronological for chat
            query = query.order_by(ChatKitThreadItem.created_at.asc()).limit(limit + 1)

            result = await self.db.execute(query)
            db_items = list(result.scalars().all())

            has_more = len(db_items) > limit
            items_to_return = db_items[:limit]

            items = []
            for db_item in items_to_return:
                item = self._deserialize_item(db_item)
                if item:
                    items.append(item)

            next_after = items_to_return[-1].id if has_more and items_to_return else None

            return Page(data=items, has_more=has_more, after=next_after)

        except Exception as e:
            logger.error(f"[ChatKitStore] Error loading items from thread {thread_id}: {e}")
            return Page(data=[], has_more=False, after=None)

    async def load_item(self, thread_id: str, item_id: str, context: Any) -> ThreadItem | None:
        """Load a specific message from a thread."""
        try:
            result = await self.db.execute(
                select(ChatKitThreadItem).where(
                    ChatKitThreadItem.id == item_id,
                    ChatKitThreadItem.thread_id == thread_id
                )
            )
            db_item = result.scalar_one_or_none()

            if db_item:
                return self._deserialize_item(db_item)
            return None

        except Exception as e:
            logger.error(f"[ChatKitStore] Error loading item {item_id}: {e}")
            return None

    async def save_item(self, thread_id: str, item: ThreadItem, context: Any) -> None:
        """Save or update a message in a thread."""
        try:
            item_id = getattr(item, 'id', None)
            if not item_id:
                await self.add_thread_item(thread_id, item, context)
                return

            result = await self.db.execute(
                select(ChatKitThreadItem).where(ChatKitThreadItem.id == item_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.content = self._serialize_item(item)
                existing.item_type = getattr(item, 'type', existing.item_type)
            else:
                await self.add_thread_item(thread_id, item, context)

            await self.db.commit()

        except Exception as e:
            logger.error(f"[ChatKitStore] Error saving item: {e}")
            await self.db.rollback()

    async def delete_thread_item(self, thread_id: str, item_id: str, context: Any) -> None:
        """Delete a message from a thread."""
        try:
            await self.db.execute(
                delete(ChatKitThreadItem).where(
                    ChatKitThreadItem.id == item_id,
                    ChatKitThreadItem.thread_id == thread_id
                )
            )
            await self.db.commit()
            logger.debug(f"[ChatKitStore] Deleted item {item_id} from thread {thread_id}")

        except Exception as e:
            logger.error(f"[ChatKitStore] Error deleting item {item_id}: {e}")
            await self.db.rollback()

    # ========================================
    # Attachment Operations
    # ========================================

    async def save_attachment(self, attachment: Any, context: Any) -> None:
        """Save attachment to in-memory cache."""
        if hasattr(attachment, 'id'):
            self._attachments[attachment.id] = attachment

    async def load_attachment(self, attachment_id: str, context: Any) -> Any:
        """Load attachment from cache or database."""
        # Check cache first
        if attachment_id in self._attachments:
            return self._attachments[attachment_id]

        # Fall back to database lookup (if using file upload table)
        # Implement based on your file storage strategy
        return None

    async def delete_attachment(self, attachment_id: str, context: Any) -> None:
        """Delete attachment from cache."""
        if attachment_id in self._attachments:
            del self._attachments[attachment_id]

    # ========================================
    # Serialization Helpers
    # ========================================

    def _parse_datetime(self, value: Any) -> datetime:
        """Parse datetime from various formats."""
        if value is None:
            return datetime.utcnow()
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return datetime.utcnow()

    def _serialize_item(self, item: ThreadItem) -> str:
        """Serialize a ThreadItem to JSON string."""
        try:
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                if hasattr(obj, '__str__') and 'Url' in type(obj).__name__:
                    return str(obj)
                if hasattr(obj, 'model_dump'):
                    return obj.model_dump()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            if hasattr(item, 'model_dump'):
                data = item.model_dump(mode='json')
                return json.dumps(data, default=json_serializer)
            elif hasattr(item, 'dict'):
                return json.dumps(item.dict(), default=json_serializer)
            else:
                return json.dumps({
                    'id': getattr(item, 'id', None),
                    'type': getattr(item, 'type', None),
                    'thread_id': getattr(item, 'thread_id', None),
                }, default=json_serializer)

        except Exception as e:
            logger.error(f"[ChatKitStore] Error serializing item: {e}")
            return json.dumps({'error': str(e)})

    def _deserialize_item(self, db_item: ChatKitThreadItem) -> ThreadItem | None:
        """Deserialize a database item to ThreadItem."""
        try:
            data = json.loads(db_item.content)
            item_type = db_item.item_type or data.get('type', 'unknown')

            if item_type == 'user_message':
                content_list = data.get('content', [])
                attachments_list = data.get('attachments', [])
                inference_opts = data.get('inference_options', {})

                # Reconstruct attachments
                attachments = []
                for att_data in attachments_list:
                    try:
                        att_type = att_data.get('type', 'file')
                        if att_type == 'image':
                            attachments.append(ImageAttachment(**att_data))
                        else:
                            attachments.append(FileAttachment(**att_data))
                    except Exception as e:
                        logger.warning(f"Could not deserialize attachment: {e}")

                return UserMessageItem(
                    id=data.get('id', db_item.id),
                    thread_id=data.get('thread_id', db_item.thread_id),
                    created_at=data.get('created_at', db_item.created_at.isoformat()),
                    type='user_message',
                    content=[
                        UserMessageTextContent(type='input_text', text=c.get('text', ''))
                        for c in content_list
                    ] if content_list else [],
                    attachments=attachments,
                    inference_options=InferenceOptions(**inference_opts) if inference_opts else InferenceOptions(),
                )

            elif item_type == 'assistant_message':
                content_list = data.get('content', [])
                return AssistantMessageItem(
                    id=data.get('id', db_item.id),
                    thread_id=data.get('thread_id', db_item.thread_id),
                    created_at=data.get('created_at', db_item.created_at.isoformat()),
                    type='assistant_message',
                    content=[
                        AssistantMessageContent(
                            type=c.get('type', 'output_text'),
                            text=c.get('text', ''),
                            annotations=c.get('annotations', [])
                        )
                        for c in content_list
                    ] if content_list else []
                )
            else:
                return data

        except Exception as e:
            logger.error(f"[ChatKitStore] Error deserializing item {db_item.id}: {e}")
            return None


# Factory function
def create_chatkit_store(db: AsyncSession, user_id: int) -> PostgreSQLChatKitStore:
    """Create a PostgreSQL-backed ChatKit store for a user."""
    return PostgreSQLChatKitStore(db, user_id)
```

---

## Auto-Generated Thread Titles

```python
async def respond(self, thread: ThreadMetadata, input_user_message, context):
    # Extract user message text
    user_message = ""
    if input_user_message and input_user_message.content:
        for content_item in input_user_message.content:
            if hasattr(content_item, 'text'):
                user_message += content_item.text

    # Auto-generate title for new threads (first message)
    if not thread.title and user_message:
        import re

        title_text = user_message.strip()

        # Remove tool prefixes like [TOOL:GMAIL]
        title_text = re.sub(r'\[TOOL:\w+\]\s*', '', title_text)

        # Remove file prefixes like [FILE:abc123]
        title_text = re.sub(r'\[FILE:[^\]]+\]\s*', '', title_text)

        # Truncate to 50 chars with ellipsis
        if len(title_text) > 50:
            thread.title = title_text[:47] + "..."
        else:
            thread.title = title_text if title_text else "New Conversation"

        # Save updated thread
        await self.store.save_thread(thread, context)
```

---

## Migration Script

```sql
-- ChatKit threads table
CREATE TABLE IF NOT EXISTS chatkit_threads (
    id VARCHAR(100) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    thread_metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT fk_chatkit_threads_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for user queries (history panel)
CREATE INDEX IF NOT EXISTS idx_chatkit_threads_user_id ON chatkit_threads(user_id);
CREATE INDEX IF NOT EXISTS idx_chatkit_threads_updated_at ON chatkit_threads(updated_at DESC);

-- ChatKit thread items (messages) table
CREATE TABLE IF NOT EXISTS chatkit_thread_items (
    id VARCHAR(100) PRIMARY KEY,
    thread_id VARCHAR(100) NOT NULL REFERENCES chatkit_threads(id) ON DELETE CASCADE,
    item_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_chatkit_thread_items_thread FOREIGN KEY (thread_id) REFERENCES chatkit_threads(id) ON DELETE CASCADE
);

-- Index for thread message queries
CREATE INDEX IF NOT EXISTS idx_chatkit_thread_items_thread_id ON chatkit_thread_items(thread_id);
CREATE INDEX IF NOT EXISTS idx_chatkit_thread_items_created_at ON chatkit_thread_items(created_at);
CREATE INDEX IF NOT EXISTS idx_chatkit_thread_items_type ON chatkit_thread_items(item_type);
```

---

## Best Practices

1. **Always filter by user_id** - Every query must include user isolation
2. **Use cascade delete** - When thread is deleted, items are automatically removed
3. **Update thread.updated_at** - Whenever a message is added
4. **Generate meaningful titles** - From first message, cleaned of prefixes
5. **Handle serialization errors** - Gracefully fallback for corrupt data
6. **Use cursor-based pagination** - For efficient history loading
7. **Index appropriately** - user_id, thread_id, updated_at, created_at
