"""
ChatKit Store Service - PostgreSQL-backed storage for ChatKit threads and messages.

Enables persistent conversation history across server restarts and page reloads.
Users can continue conversations from where they left off.
"""

from __future__ import annotations

import logging
import json
from datetime import datetime
from typing import Optional, Any, List, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload

from chatkit.server import Store, ThreadMetadata, ThreadItem
from chatkit.types import Page, UserMessageItem, AssistantMessageItem

from app.models import ChatKitThread, ChatKitThreadItem

logger = logging.getLogger(__name__)


class PostgreSQLChatKitStore(Store):
    """
    PostgreSQL-backed store for ChatKit threads and messages.

    Provides persistent storage for conversation history, allowing users
    to continue conversations across page reloads and server restarts.
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
        self._attachments: dict[str, Any] = {}  # In-memory attachments (rarely used)
        logger.debug(f"[ChatKitStore] Initialized for user {user_id}")

    def generate_thread_id(self, context: Any) -> str:
        """Generate a unique thread ID."""
        import uuid
        thread_id = f"schema-thread-{uuid.uuid4().hex[:12]}"
        logger.debug(f"[ChatKitStore] Generated thread ID: {thread_id}")
        return thread_id

    def generate_item_id(self, item_type: str, thread: ThreadMetadata, context: Any) -> str:
        """Generate a unique item ID."""
        import uuid
        item_id = f"{item_type}-{uuid.uuid4().hex[:12]}"
        return item_id

    async def save_thread(self, thread: ThreadMetadata, context: Any) -> None:
        """Save or update a thread in the database."""
        try:
            # Check if thread exists
            result = await self.db.execute(
                select(ChatKitThread).where(ChatKitThread.id == thread.id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing thread
                existing.updated_at = datetime.utcnow()
                # Update title if provided
                if hasattr(thread, 'title') and thread.title:
                    existing.title = thread.title
                if hasattr(thread, 'metadata') and thread.metadata:
                    existing.thread_metadata = thread.metadata
            else:
                # Create new thread
                # Handle created_at which can be str, datetime, or None
                created_at_value = thread.created_at
                if created_at_value:
                    if isinstance(created_at_value, str):
                        created_at_value = datetime.fromisoformat(created_at_value)
                    elif isinstance(created_at_value, datetime):
                        pass  # Already datetime
                    else:
                        created_at_value = datetime.utcnow()
                else:
                    created_at_value = datetime.utcnow()

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

    async def load_thread(self, thread_id: str, context: Any) -> Optional[ThreadMetadata]:
        """Load a thread from the database, creating if it doesn't exist."""
        try:
            result = await self.db.execute(
                select(ChatKitThread).where(
                    ChatKitThread.id == thread_id,
                    ChatKitThread.user_id == self.user_id
                )
            )
            db_thread = result.scalar_one_or_none()

            if db_thread:
                logger.debug(f"[ChatKitStore] Loaded existing thread: {thread_id}")
                return ThreadMetadata(
                    id=db_thread.id,
                    title=db_thread.title,  # Include title for history display
                    created_at=db_thread.created_at.isoformat() if db_thread.created_at else None,
                )

            # Create new thread if not exists
            logger.debug(f"[ChatKitStore] Creating new thread: {thread_id}")
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
            # Return a basic thread metadata to avoid breaking the flow
            return ThreadMetadata(
                id=thread_id,
                created_at=datetime.utcnow().isoformat(),
            )

    async def delete_thread(self, thread_id: str, context: Any) -> None:
        """Delete a thread and all its items from the database."""
        try:
            await self.db.execute(
                delete(ChatKitThread).where(
                    ChatKitThread.id == thread_id,
                    ChatKitThread.user_id == self.user_id
                )
            )
            await self.db.commit()
            logger.info(f"[ChatKitStore] Deleted thread: {thread_id}")

        except Exception as e:
            logger.error(f"[ChatKitStore] Error deleting thread {thread_id}: {e}")
            await self.db.rollback()

    async def load_threads(self, limit: int, after: Optional[str], order: str, context: Any) -> Any:
        """Load all threads for the current user with pagination support."""
        try:
            logger.info(f"[ChatKitStore] load_threads called: user_id={self.user_id}, limit={limit}, after={after}, order={order}")

            # Build base query
            query = select(ChatKitThread).where(
                ChatKitThread.user_id == self.user_id
            )

            # Handle pagination with 'after' cursor
            if after:
                # Get the thread to use as cursor
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
                ChatKitThread.updated_at.desc() if order == "desc" else ChatKitThread.updated_at.asc()
            ).limit(limit + 1)  # Get one extra to check has_more

            result = await self.db.execute(query)
            db_threads = list(result.scalars().all())

            logger.info(f"[ChatKitStore] Found {len(db_threads)} threads in database for user {self.user_id}")

            has_more = len(db_threads) > limit
            threads_to_return = db_threads[:limit]

            threads = [
                ThreadMetadata(
                    id=t.id,
                    title=t.title,  # Include title for history display
                    created_at=t.created_at.isoformat() if t.created_at else None,
                )
                for t in threads_to_return
            ]

            # Calculate next cursor for pagination
            next_after = threads_to_return[-1].id if has_more and threads_to_return else None

            logger.info(f"[ChatKitStore] Returning {len(threads)} threads for user {self.user_id}, has_more={has_more}")
            return Page(data=threads, has_more=has_more, after=next_after)

        except Exception as e:
            logger.error(f"[ChatKitStore] Error loading threads: {e}", exc_info=True)
            return Page(data=[], has_more=False, after=None)

    async def add_thread_item(self, thread_id: str, item: ThreadItem, context: Any) -> None:
        """Add a new item (message) to a thread."""
        try:
            # Ensure thread exists
            await self.load_thread(thread_id, context)

            # Serialize item content
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
        after: Optional[str],
        limit: int,
        order: str,
        context: Any
    ) -> Any:
        """Load all items (messages) from a thread with pagination support."""
        try:
            # Build base query
            query = select(ChatKitThreadItem).where(
                ChatKitThreadItem.thread_id == thread_id
            )

            # Handle pagination with 'after' cursor
            if after:
                cursor_result = await self.db.execute(
                    select(ChatKitThreadItem).where(ChatKitThreadItem.id == after)
                )
                cursor_item = cursor_result.scalar_one_or_none()
                if cursor_item:
                    query = query.where(ChatKitThreadItem.created_at > cursor_item.created_at)

            # Apply ordering and limit
            query = query.order_by(
                ChatKitThreadItem.created_at.asc()  # Always chronological for chat
            ).limit(limit + 1)

            result = await self.db.execute(query)
            db_items = list(result.scalars().all())

            has_more = len(db_items) > limit
            items_to_return = db_items[:limit]

            items = []
            for db_item in items_to_return:
                item = self._deserialize_item(db_item)
                if item:
                    items.append(item)

            # Calculate next cursor for pagination
            next_after = items_to_return[-1].id if has_more and items_to_return else None

            logger.debug(f"[ChatKitStore] Loaded {len(items)} items from thread {thread_id}")
            return Page(data=items, has_more=has_more, after=next_after)

        except Exception as e:
            logger.error(f"[ChatKitStore] Error loading items from thread {thread_id}: {e}")
            return Page(data=[], has_more=False, after=None)

    async def load_item(self, thread_id: str, item_id: str, context: Any) -> Optional[ThreadItem]:
        """Load a specific item from a thread."""
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
        """Save or update an item in a thread."""
        try:
            item_id = getattr(item, 'id', None)
            if not item_id:
                # No ID, add as new item
                await self.add_thread_item(thread_id, item, context)
                return

            # Check if item exists
            result = await self.db.execute(
                select(ChatKitThreadItem).where(ChatKitThreadItem.id == item_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing item
                existing.content = self._serialize_item(item)
                existing.item_type = getattr(item, 'type', existing.item_type)
            else:
                # Create new item
                await self.add_thread_item(thread_id, item, context)

            await self.db.commit()

        except Exception as e:
            logger.error(f"[ChatKitStore] Error saving item: {e}")
            await self.db.rollback()

    async def delete_thread_item(self, thread_id: str, item_id: str, context: Any) -> None:
        """Delete an item from a thread."""
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

    async def save_attachment(self, attachment: Any, context: Any) -> None:
        """Save an attachment (in-memory cache)."""
        if hasattr(attachment, 'id'):
            self._attachments[attachment.id] = attachment
            logger.info(f"[ChatKitStore] Saved attachment to cache: {attachment.id}")

    async def load_attachment(self, attachment_id: str, context: Any) -> Any:
        """
        Load an attachment by ID.

        First checks in-memory cache, then falls back to database lookup
        for attachments uploaded via /api/files/chatkit-upload endpoint.
        """
        # Check in-memory cache first
        if attachment_id in self._attachments:
            logger.info(f"[ChatKitStore] Loaded attachment from cache: {attachment_id}")
            return self._attachments[attachment_id]

        # Fall back to database lookup for files uploaded via /api/files/chatkit-upload
        try:
            from app.models import UploadedFile
            from chatkit.types import FileAttachment, ImageAttachment
            import os

            def _base_url_from_context(ctx: Any) -> str:
                """
                Build an absolute base URL for preview_url.
                Prefer request headers from ChatKit context so the URL matches the host
                the browser is using (important when not localhost).
                """
                try:
                    headers = (ctx or {}).get("headers") or {}
                    host = headers.get("x-forwarded-host") or headers.get("host")
                    scheme = headers.get("x-forwarded-proto") or "http"
                    if host:
                        return f"{scheme}://{host}"
                except Exception:
                    pass
                return os.getenv("API_BASE_URL", "http://localhost:8000")

            result = await self.db.execute(
                select(UploadedFile).where(UploadedFile.file_id == attachment_id)
            )
            file_record = result.scalar_one_or_none()

            if file_record:
                logger.info(f"[ChatKitStore] Loaded attachment from database: {attachment_id} ({file_record.file_type})")

                # Create proper ChatKit attachment object
                if file_record.file_type == 'image':
                    # preview_url must be an absolute URL for Pydantic validation
                    base_url = _base_url_from_context(context)
                    attachment = ImageAttachment(
                        id=file_record.file_id,
                        name=file_record.file_name,
                        mime_type=file_record.mime_type or 'application/octet-stream',
                        preview_url=f"{base_url}/api/files/{file_record.file_id}/preview"
                    )
                else:
                    attachment = FileAttachment(
                        id=file_record.file_id,
                        name=file_record.file_name,
                        mime_type=file_record.mime_type or 'application/octet-stream'
                    )

                # Cache it for future lookups
                self._attachments[attachment_id] = attachment
                return attachment

        except Exception as e:
            logger.error(f"[ChatKitStore] Failed to load attachment from database: {e}")

        logger.warning(f"[ChatKitStore] Attachment not found: {attachment_id}")
        return None

    async def delete_attachment(self, attachment_id: str, context: Any) -> None:
        """Delete an attachment from cache."""
        if attachment_id in self._attachments:
            del self._attachments[attachment_id]
            logger.info(f"[ChatKitStore] Deleted attachment from cache: {attachment_id}")

    def _serialize_item(self, item: ThreadItem) -> str:
        """Serialize a ThreadItem to JSON string."""
        try:
            # Custom JSON encoder for datetime and Pydantic types
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                # Handle Pydantic URL types (AnyUrl, HttpUrl, etc.)
                if hasattr(obj, '__str__') and 'Url' in type(obj).__name__:
                    return str(obj)
                # Handle any Pydantic model
                if hasattr(obj, 'model_dump'):
                    return obj.model_dump()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            if hasattr(item, 'model_dump'):
                # Use mode='json' for proper serialization of Pydantic types
                data = item.model_dump(mode='json')
                return json.dumps(data, default=json_serializer)
            elif hasattr(item, 'dict'):
                data = item.dict()
                return json.dumps(data, default=json_serializer)
            else:
                # Fallback: serialize known attributes
                created_at = getattr(item, 'created_at', None)
                if isinstance(created_at, datetime):
                    created_at = created_at.isoformat()

                data = {
                    'id': getattr(item, 'id', None),
                    'type': getattr(item, 'type', None),
                    'thread_id': getattr(item, 'thread_id', None),
                    'created_at': created_at,
                }
                if hasattr(item, 'content'):
                    content = item.content
                    if isinstance(content, list):
                        data['content'] = [
                            c.model_dump() if hasattr(c, 'model_dump') else str(c)
                            for c in content
                        ]
                    else:
                        data['content'] = str(content)
                return json.dumps(data, default=json_serializer)
        except Exception as e:
            logger.error(f"[ChatKitStore] Error serializing item: {e}")
            return json.dumps({'error': str(e)})

    def _deserialize_item(self, db_item: ChatKitThreadItem) -> Optional[ThreadItem]:
        """Deserialize a database item to ThreadItem."""
        try:
            data = json.loads(db_item.content)
            item_type = db_item.item_type or data.get('type', 'unknown')

            # Return the raw data as a dict - ChatKit will handle it
            # We need to return proper ChatKit types
            if item_type == 'user_message':
                from chatkit.types import UserMessageItem as UMI, UserMessageTextContent, InferenceOptions
                from chatkit.types import ImageAttachment, FileAttachment
                content_list = data.get('content', [])
                attachments_list = data.get('attachments', [])

                # Get or create inference_options (required field)
                inference_opts = data.get('inference_options', {})
                if not inference_opts:
                    inference_opts = {}

                # Reconstruct attachments from stored data
                attachments = []
                for att_data in attachments_list:
                    try:
                        att_type = att_data.get('type', 'file')
                        if att_type == 'image':
                            attachments.append(ImageAttachment(**att_data))
                        else:
                            attachments.append(FileAttachment(**att_data))
                    except Exception as e:
                        logger.warning(f"[ChatKitStore] Could not deserialize attachment: {e}")

                return UMI(
                    id=data.get('id', db_item.id),
                    thread_id=data.get('thread_id', db_item.thread_id),
                    created_at=data.get('created_at', db_item.created_at.isoformat()),
                    type='user_message',
                    content=[
                        UserMessageTextContent(type='input_text', text=c.get('text', ''))
                        for c in content_list
                    ] if content_list else [],
                    attachments=attachments,
                    inference_options=InferenceOptions(**inference_opts),
                )
            elif item_type == 'assistant_message':
                from chatkit.types import AssistantMessageItem as AMI, AssistantMessageContent
                content_list = data.get('content', [])
                return AMI(
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
                # Return generic dict for unknown types
                return data

        except Exception as e:
            logger.error(f"[ChatKitStore] Error deserializing item {db_item.id}: {e}")
            return None


# Factory function for creating store instances
def create_chatkit_store(db: AsyncSession, user_id: int) -> PostgreSQLChatKitStore:
    """
    Create a PostgreSQL-backed ChatKit store for a user.

    Args:
        db: SQLAlchemy async session
        user_id: Current user's ID

    Returns:
        PostgreSQLChatKitStore instance
    """
    return PostgreSQLChatKitStore(db, user_id)
