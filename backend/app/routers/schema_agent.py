"""
Schema Agent Router (Phase 9)

API endpoints for Schema Query Agent - enables AI-powered natural language
queries against user's existing PostgreSQL database without creating any tables.

Supports both:
- Custom /chat endpoint for direct API calls
- /chatkit endpoint for OpenAI ChatKit UI integration
"""

import logging
import json
import uuid
import asyncio
import re
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncIterator
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

# ChatKit imports
from chatkit.server import (
    ChatKitServer,
    Store,
    ThreadMetadata,
    ThreadItem,
    UserMessageItem,
    ThreadStreamEvent,
)
from chatkit.store import AttachmentStore
from chatkit.types import (
    ThreadItemDoneEvent,
    ThreadItemAddedEvent,
    ThreadItemUpdatedEvent,
    AssistantMessageItem,
    AssistantMessageContent,
    ProgressUpdateEvent,
    ErrorEvent,
    ErrorCode,
    Page,
    ImageAttachment,
    FileAttachment,
    # WorkflowItem types for collapsible streaming progress display
    WorkflowItem,
    Workflow,
    CustomTask,
    SearchTask,
    ThoughtTask,
    URLSource,
    CustomSummary,
    DurationSummary,
    # Workflow update event types
    WorkflowTaskAdded,
    WorkflowTaskUpdated,
    # Annotation types for inline citations (like ChatGPT sources)
    Annotation,
)
from chatkit.agents import ThreadItemConverter
from openai.types.responses import ResponseInputImageParam, ResponseInputTextParam, ResponseInputFileParam

from app.database import get_db
from app.models import User, UserConnection
from app.models import UserSettings, UploadedFile
from app.routers.auth import get_current_user
from app.services.schema_discovery import (
    test_connection,
    discover_schema,
    format_schema_for_prompt,
    SchemaDiscoveryError,
    TooManyTablesError,
    MAX_TABLES_LIMIT
)
from app.mcp_server.tools_schema_query import (
    schema_list_tables,
    schema_describe_table,
    schema_execute_query,
    schema_get_sample_data,
    schema_get_table_stats
)
from app.agents.schema_query_agent import SchemaQueryAgent, create_schema_query_agent
from app.services.chatkit_store_service import PostgreSQLChatKitStore, create_chatkit_store
from app.connector_agents import get_connector_agent_tools

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schema-agent", tags=["schema-agent"])


# ============================================================================
# Custom ThreadItemConverter for File Attachments
# ============================================================================

class SchemaAgentThreadItemConverter(ThreadItemConverter):
    """
    Custom ThreadItemConverter that properly converts file attachments to model input.

    This is required because:
    1. ChatKit's default converter doesn't know how to read our file storage
    2. Images need to be converted to base64 data URLs for the model to see them
    3. PDFs need to be converted to base64 file params

    This class reads file bytes from our storage and converts them to the proper
    OpenAI ResponseInput format.
    """

    def __init__(self, db_session=None):
        """Initialize with optional database session for file lookups."""
        super().__init__()
        self.db_session = db_session

    async def attachment_to_message_content(self, attachment):
        """
        Convert attachment to model input content.

        For images: Returns ResponseInputImageParam with base64 data URL
        For PDFs: Returns ResponseInputFileParam with base64 file data
        For other files: Returns ResponseInputTextParam with file info
        """
        import base64
        import aiofiles
        from pathlib import Path

        attachment_id = getattr(attachment, 'id', None)
        if not attachment_id:
            logger.warning("[ThreadItemConverter] Attachment has no ID")
            return None

        logger.info(f"[ThreadItemConverter] Converting attachment: {attachment_id}")

        # Read file bytes from storage
        file_bytes = await self._read_file_bytes(attachment_id)

        if file_bytes is None:
            logger.warning(f"[ThreadItemConverter] Could not read file bytes for: {attachment_id}")
            # Return text description as fallback
            return ResponseInputTextParam(
                type="input_text",
                text=f"[Attached file: {getattr(attachment, 'name', 'unknown')} (could not read content)]"
            )

        mime_type = getattr(attachment, 'mime_type', 'application/octet-stream')
        file_name = getattr(attachment, 'name', 'unknown')

        # Check if it's an image attachment
        if isinstance(attachment, ImageAttachment) or mime_type.startswith('image/'):
            # Convert to base64 data URL for images
            b64_content = base64.b64encode(file_bytes).decode('utf-8')
            data_url = f"data:{mime_type};base64,{b64_content}"

            logger.info(f"[ThreadItemConverter] Converted image to data URL ({len(file_bytes)} bytes)")

            return ResponseInputImageParam(
                type="input_image",
                detail="auto",
                image_url=data_url,
            )

        # Check if it's a PDF
        elif mime_type == 'application/pdf':
            b64_content = base64.b64encode(file_bytes).decode('utf-8')
            data_url = f"data:{mime_type};base64,{b64_content}"

            logger.info(f"[ThreadItemConverter] Converted PDF to file param ({len(file_bytes)} bytes)")

            return ResponseInputFileParam(
                type="input_file",
                file_data=data_url,
                filename=file_name,
            )

        # For other file types, return text description with content
        else:
            # For CSV/Excel, the processed_data already contains the content
            # Just return a text description
            logger.info(f"[ThreadItemConverter] File type {mime_type} - returning text description")

            return ResponseInputTextParam(
                type="input_text",
                text=f"[Attached file: {file_name} ({mime_type})]"
            )

    async def _read_file_bytes(self, file_id: str) -> bytes | None:
        """Read file bytes from storage using file ID."""
        import aiofiles
        from pathlib import Path

        try:
            # Look up file record from database
            from app.database import async_session
            from app.models import UploadedFile

            # Use provided session or create new one
            if self.db_session:
                result = await self.db_session.execute(
                    select(UploadedFile).where(UploadedFile.file_id == file_id)
                )
                file_record = result.scalar_one_or_none()
            else:
                async with async_session() as db:
                    result = await db.execute(
                        select(UploadedFile).where(UploadedFile.file_id == file_id)
                    )
                    file_record = result.scalar_one_or_none()

            if not file_record:
                logger.warning(f"[ThreadItemConverter] File not found in database: {file_id}")
                return None

            storage_path = Path(file_record.storage_path)
            if not storage_path.exists():
                logger.warning(f"[ThreadItemConverter] File not found on disk: {storage_path}")
                return None

            # Read file bytes
            async with aiofiles.open(storage_path, 'rb') as f:
                file_bytes = await f.read()

            logger.info(f"[ThreadItemConverter] Read {len(file_bytes)} bytes from {storage_path}")
            return file_bytes

        except Exception as e:
            logger.error(f"[ThreadItemConverter] Error reading file {file_id}: {e}")
            return None

security = HTTPBearer(auto_error=False)


# ============================================================================
# Request/Response Models
# ============================================================================

class SchemaConnectRequest(BaseModel):
    """Request to connect database in schema-query mode"""
    database_uri: str = Field(..., description="PostgreSQL connection URI")
    allowed_schemas: Optional[List[str]] = Field(
        default=["public"],
        description="List of schemas to query (default: ['public'])"
    )
    auto_discover_schema: bool = Field(
        default=True,
        description="Automatically discover schema on connect"
    )


class SchemaConnectResponse(BaseModel):
    """Response from schema connection"""
    status: str
    message: str
    tables_found: Optional[int] = None
    schema_summary: Optional[dict] = None
    mcp_session_id: Optional[str] = None


class SchemaMetadataResponse(BaseModel):
    """Response with schema metadata"""
    success: bool
    schema_metadata: Optional[dict] = None
    schema_prompt: Optional[str] = None
    error: Optional[str] = None


class QueryRequest(BaseModel):
    """Natural language or SQL query request"""
    query: str = Field(..., description="Natural language query or SQL SELECT statement")
    include_sql: bool = Field(default=True, description="Include generated SQL in response")
    max_rows: int = Field(default=100, ge=1, le=10000, description="Maximum rows to return")


class QueryResponse(BaseModel):
    """Query execution response"""
    success: bool
    natural_response: Optional[str] = None
    sql_executed: Optional[str] = None
    data: Optional[list] = None
    columns: Optional[list] = None
    row_count: Optional[int] = None
    error: Optional[str] = None
    visualization: Optional[dict] = None


class TableListResponse(BaseModel):
    """Response with list of tables"""
    success: bool
    schema_name: str
    table_count: int
    tables: list


class TableDescribeResponse(BaseModel):
    """Response with table structure"""
    success: bool
    table_name: str
    schema_name: str
    estimated_rows: int
    columns: list
    error: Optional[str] = None


class ConnectionStatusResponse(BaseModel):
    """Connection status response"""
    connected: bool
    connection_mode: Optional[str] = None
    mcp_status: Optional[str] = None
    database_uri_set: bool
    schema_cached: bool
    schema_last_updated: Optional[datetime] = None
    table_count: Optional[int] = None


# ============================================================================
# Helper Functions
# ============================================================================

async def get_user_connection(user: User, db: AsyncSession) -> Optional[UserConnection]:
    """Get user's connection record"""
    result = await db.execute(
        select(UserConnection).where(UserConnection.user_id == user.id)
    )
    return result.scalar_one_or_none()


async def require_schema_mode_connection(user: User, db: AsyncSession) -> UserConnection:
    """Require user to have schema_query_only connection"""
    connection = await get_user_connection(user, db)

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No connection configured. Please connect your database first."
        )

    if connection.connection_type != "schema_query_only":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only available for Schema Query Mode connections."
        )

    if not connection.database_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database URI not configured."
        )

    return connection


# ============================================================================
# ChatKit Store for Schema Agent
# ============================================================================

class SchemaAgentStore(Store):
    """In-memory store for Schema Agent ChatKit threads and messages."""

    def __init__(self):
        self._threads: dict[str, ThreadMetadata] = {}
        self._items: dict[str, list[ThreadItem]] = {}
        self._attachments: dict[str, Any] = {}

    def generate_thread_id(self, context: Any) -> str:
        return f"schema-thread-{uuid.uuid4().hex[:12]}"

    def generate_item_id(self, item_type: str, thread: ThreadMetadata, context: Any) -> str:
        return f"{item_type}-{uuid.uuid4().hex[:12]}"

    async def save_thread(self, thread: ThreadMetadata, context: Any) -> None:
        self._threads[thread.id] = thread
        if thread.id not in self._items:
            self._items[thread.id] = []

    async def load_thread(self, thread_id: str, context: Any) -> ThreadMetadata | None:
        if thread_id not in self._threads:
            new_thread = ThreadMetadata(
                id=thread_id,
                created_at=datetime.now().isoformat(),
            )
            self._threads[thread_id] = new_thread
            self._items[thread_id] = []
        return self._threads.get(thread_id)

    async def delete_thread(self, thread_id: str, context: Any) -> None:
        if thread_id in self._threads:
            del self._threads[thread_id]
        if thread_id in self._items:
            del self._items[thread_id]

    async def load_threads(self, limit: int, after: str | None, order: str, context: Any) -> Any:
        threads = list(self._threads.values())
        # Sort by created_at if available
        threads_sorted = sorted(
            threads,
            key=lambda t: getattr(t, 'created_at', '') or '',
            reverse=(order == "desc")
        )
        threads_to_return = threads_sorted[:limit]
        has_more = len(threads_sorted) > limit
        next_after = threads_to_return[-1].id if has_more and threads_to_return else None
        return Page(data=threads_to_return, has_more=has_more, after=next_after)

    async def add_thread_item(self, thread_id: str, item: ThreadItem, context: Any) -> None:
        if thread_id not in self._items:
            self._items[thread_id] = []
        self._items[thread_id].append(item)

    async def load_thread_items(self, thread_id: str, after: str | None, limit: int, order: str, context: Any) -> Any:
        items = self._items.get(thread_id, [])
        items_to_return = items[:limit]
        has_more = len(items) > limit
        next_after = items_to_return[-1].id if has_more and items_to_return and hasattr(items_to_return[-1], 'id') else None
        return Page(data=items_to_return, has_more=has_more, after=next_after)

    async def load_item(self, thread_id: str, item_id: str, context: Any) -> ThreadItem | None:
        items = self._items.get(thread_id, [])
        for item in items:
            if hasattr(item, 'id') and item.id == item_id:
                return item
        return None

    async def save_item(self, thread_id: str, item: ThreadItem, context: Any) -> None:
        if thread_id not in self._items:
            self._items[thread_id] = []
        items = self._items[thread_id]
        for i, existing in enumerate(items):
            if hasattr(existing, 'id') and hasattr(item, 'id') and existing.id == item.id:
                items[i] = item
                return
        items.append(item)

    async def delete_thread_item(self, thread_id: str, item_id: str, context: Any) -> None:
        if thread_id in self._items:
            self._items[thread_id] = [
                item for item in self._items[thread_id]
                if not (hasattr(item, 'id') and item.id == item_id)
            ]

    async def save_attachment(self, attachment: Any, context: Any) -> None:
        if hasattr(attachment, 'id'):
            self._attachments[attachment.id] = attachment
            logger.info(f"[Store] Saved attachment: {attachment.id}")

    async def load_attachment(self, attachment_id: str, context: Any) -> Any:
        """
        Load attachment by ID.

        First checks in-memory cache, then falls back to database lookup
        for attachments uploaded via /api/files/chatkit-upload endpoint.
        """
        # Check in-memory cache first
        if attachment_id in self._attachments:
            logger.info(f"[Store] Loaded attachment from cache: {attachment_id}")
            return self._attachments[attachment_id]

        # Fall back to database lookup for files uploaded via /api/files/chatkit-upload
        try:
            from app.database import async_session
            from app.models import UploadedFile
            from sqlalchemy import select
            from chatkit.types import FileAttachment, ImageAttachment
            import os

            def _base_url_from_context(ctx: Any) -> str:
                try:
                    headers = (ctx or {}).get("headers") or {}
                    host = headers.get("x-forwarded-host") or headers.get("host")
                    scheme = headers.get("x-forwarded-proto") or "http"
                    if host:
                        return f"{scheme}://{host}"
                except Exception:
                    pass
                return os.getenv("API_BASE_URL", "http://localhost:8000")

            async with async_session() as db:
                result = await db.execute(
                    select(UploadedFile).where(UploadedFile.file_id == attachment_id)
                )
                file_record = result.scalar_one_or_none()

                if file_record:
                    logger.info(f"[Store] Loaded attachment from database: {attachment_id} ({file_record.file_type})")

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
            logger.error(f"[Store] Failed to load attachment from database: {e}")

        logger.warning(f"[Store] Attachment not found: {attachment_id}")
        return None

    async def delete_attachment(self, attachment_id: str, context: Any) -> None:
        if attachment_id in self._attachments:
            del self._attachments[attachment_id]
            logger.info(f"[Store] Deleted attachment from cache: {attachment_id}")


# ============================================================================
# ChatKit Server for Schema Agent
# ============================================================================

class SchemaNoopAttachmentStore(AttachmentStore):
    """
    ChatKit may call attachments.delete as part of its UI lifecycle (e.g. clearing composer state).
    We already handle actual uploads via /api/files/chatkit-upload (direct upload strategy),
    so we just need to *not crash* here. No-op keeps uploaded files available for analysis.
    """

    async def delete_attachment(self, attachment_id: str, context: Any) -> None:
        logger.info(f"[Schema ChatKit] Attachment delete requested (noop): {attachment_id}")
        return


class SchemaChatKitServer(ChatKitServer):
    """
    Schema Agent ChatKit Server implementation.

    Uses Schema Query Agent to process natural language queries
    against user's database.
    """

    def __init__(self, store: Store, attachment_store: AttachmentStore | None = None):
        super().__init__(store, attachment_store=attachment_store)

    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Process user message using Schema Query Agent with streaming progress.

        Yields detailed ProgressUpdateEvent for each step:
        - Tool calls with names and arguments
        - Tool outputs with previews
        - Agent thinking/reasoning steps
        - Final response

        For image attachments, converts them to base64 data URLs and passes
        them as multi-modal input to the agent.
        """
        import time

        try:
            if input_user_message is None:
                return

            # ============================================================================
            # Extract user message text from content AND attachments from attachments field
            # UserMessageItem structure:
            # - content: list[UserMessageTextContent | UserMessageTagContent] - text/tags
            # - attachments: list[Attachment] - FileAttachment or ImageAttachment objects
            # ============================================================================
            user_message = ""
            attachments_list = []  # List of actual Attachment objects

            # Extract text from content array
            if hasattr(input_user_message, 'content') and input_user_message.content:
                logger.info(f"[Schema ChatKit] Content has {len(input_user_message.content)} items")
                for idx, content_item in enumerate(input_user_message.content):
                    content_type = getattr(content_item, 'type', None)
                    # Extract text content
                    if content_type == 'input_text' or hasattr(content_item, 'text'):
                        text = getattr(content_item, 'text', '')
                        if text:
                            user_message += text
                            logger.info(f"[Schema ChatKit] Extracted text: {text[:50]}...")

            # Extract attachments from the dedicated attachments field (NOT content)
            if hasattr(input_user_message, 'attachments') and input_user_message.attachments:
                logger.info(f"[Schema ChatKit] Found {len(input_user_message.attachments)} attachment(s) in message!")
                for idx, att in enumerate(input_user_message.attachments):
                    att_id = getattr(att, 'id', None)
                    att_name = getattr(att, 'name', 'unknown')
                    att_type = getattr(att, 'type', 'file')
                    att_mime = getattr(att, 'mime_type', 'application/octet-stream')
                    logger.info(f"[Schema ChatKit] Attachment[{idx}]: id={att_id}, name={att_name}, type={att_type}, mime={att_mime}")
                    if att_id:
                        attachments_list.append(att)
            else:
                logger.info(f"[Schema ChatKit] No attachments field or empty attachments")

            logger.info(f"[Schema ChatKit] Raw user message: {user_message[:100] if user_message else '(empty)'}...")
            logger.info(f"[Schema ChatKit] Found {len(attachments_list)} attachment(s) in message")

            # Auto-generate title for new threads (first message)
            # This enables the history panel to show meaningful conversation titles
            if not thread.title and user_message:
                # Generate title from first 50 chars of user message
                title_text = user_message.strip()
                # Remove any tool prefixes like [TOOL:GMAIL]
                title_text = re.sub(r'\[TOOL:\w+\]\s*', '', title_text)
                title_text = re.sub(r'\[FILE:[^\]]+\]\s*', '', title_text)
                # Truncate to 50 chars with ellipsis if needed
                if len(title_text) > 50:
                    thread.title = title_text[:47] + "..."
                else:
                    thread.title = title_text if title_text else "New Conversation"
                # Save the updated thread with title
                await self.store.save_thread(thread, context)
                logger.info(f"[Schema ChatKit] Auto-generated thread title: {thread.title}")

            # Check if tool prefix is present
            if '[TOOL:' in user_message:
                logger.info(f"[Schema ChatKit] Tool prefix detected in message!")

            # Get selected tool from context
            selected_tool = context.get("selected_tool")
            if selected_tool:
                logger.info(f"[Schema ChatKit] Tool from context: {selected_tool}")
                if f'[TOOL:{selected_tool.upper()}]' not in user_message:
                    user_message = f"[TOOL:{selected_tool.upper()}] {user_message}"
                    logger.info(f"[Schema ChatKit] Prepended tool prefix to message")

            # Get attached file IDs from context AND from message attachments
            # Merge both sources to ensure we capture all attachments
            attachment_ids_from_message = [getattr(att, 'id', None) for att in attachments_list if getattr(att, 'id', None)]
            attached_file_ids = list(set(
                context.get("attached_file_ids", []) + attachment_ids_from_message
            ))

            if attached_file_ids:
                logger.info(f"[Schema ChatKit] Total attached files: {len(attached_file_ids)} - {attached_file_ids}")
                # Add file prefix for text-based agent processing (fallback)
                file_prefix = " ".join([f"[FILE:{fid}]" for fid in attached_file_ids])
                if not any(f"[FILE:" in user_message for _ in [1]):
                    user_message = f"{file_prefix} {user_message}"
                    logger.info(f"[Schema ChatKit] Prepended {len(attached_file_ids)} file reference(s) to message")

            # Get user_id and connection info from context
            user_id = context.get("user_id")
            database_uri = context.get("database_uri")
            schema_metadata = context.get("schema_metadata")

            if not user_id or not database_uri:
                error_msg = "No database connection found. Please connect your database first."
                yield ErrorEvent(
                    type="error",
                    code=ErrorCode.INVALID_REQUEST,
                    message=error_msg,
                    allow_retry=False
                )
                return

            if not schema_metadata:
                error_msg = "Schema not discovered yet. Please wait while I analyze your database structure."
                yield ErrorEvent(
                    type="error",
                    code=ErrorCode.INVALID_REQUEST,
                    message=error_msg,
                    allow_retry=True
                )
                return

            logger.info(f"[Schema ChatKit] Processing message for user {user_id}: {user_message[:50]}...")

            start_time = time.time()
            thread_id = thread.id if thread else None
            logger.info(f"[Schema ChatKit] Thread ID for session: {thread_id}")

            # Load connector sub-agents as tools
            connector_tools = []
            db_session = context.get("db_session")

            if db_session:
                try:
                    logger.info(f"[Schema ChatKit] Loading connector sub-agents for user {user_id}")
                    connector_tools = await get_connector_agent_tools(
                        db_session,
                        user_id,
                    )
                    if connector_tools:
                        tool_names = [getattr(t, 'name', str(t)) for t in connector_tools]
                        logger.info(f"[Schema ChatKit] Loaded {len(connector_tools)} connector tools: {tool_names}")
                except Exception as e:
                    logger.warning(f"[Schema ChatKit] Failed to load connector sub-agents: {e}")

            # Create cache key
            connector_count = len(connector_tools)
            cache_key = f"{user_id}:connectors_{connector_count}"

            # Get or create agent
            if cache_key not in _agent_cache:
                try:
                    yield ProgressUpdateEvent(
                        type="progress_update",
                        text="Initializing AI agent with your database schema..."
                    )
                    agent = await create_schema_query_agent(
                        database_uri=database_uri,
                        schema_metadata=schema_metadata,
                        auto_initialize=True,
                        user_id=user_id,
                        thread_id=thread_id,
                        connector_tools=connector_tools,
                    )
                    _agent_cache[cache_key] = agent
                    logger.info(f"Created Schema Query Agent for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to create agent for user {user_id}: {e}")
                    yield ErrorEvent(
                        type="error",
                        code=ErrorCode.STREAM_ERROR,
                        message=f"Failed to initialize agent: {str(e)}",
                        allow_retry=True
                    )
                    return
            else:
                agent = _agent_cache[cache_key]

            # Use streaming query for detailed progress updates
            logger.info(f"[Schema ChatKit] Starting streamed agent query...")

            # Set file analysis context for file tools (required for analyze_uploaded_file)
            if attached_file_ids and db_session:
                try:
                    from app.mcp_server.tools_file_analysis import set_file_analysis_context, clear_file_analysis_context
                    set_file_analysis_context(user_id, db_session)
                    logger.info(f"[Schema ChatKit] File analysis context set for {len(attached_file_ids)} file(s)")
                except ImportError as e:
                    logger.warning(f"[Schema ChatKit] Could not set file analysis context: {e}")

            # Set Gemini file search context (always set for file_search tool - Feature 013)
            if db_session:
                try:
                    from app.mcp_server.tools_file_search import set_file_search_context
                    set_file_search_context(user_id, db_session)
                    logger.info(f"[Schema ChatKit] Gemini file search context set for user {user_id}")
                except ImportError as e:
                    logger.warning(f"[Schema ChatKit] Could not set Gemini file search context: {e}")

            # ============================================================================
            # Convert attachments to multi-modal input for the agent
            # We use the attachments_list directly from UserMessageItem.attachments
            # which contains the actual Attachment objects (ImageAttachment/FileAttachment)
            # ============================================================================
            multimodal_content = []

            # Add text content
            if user_message:
                multimodal_content.append({
                    "type": "input_text",
                    "text": user_message
                })

            # Convert attachments (images, PDFs) to base64 for multi-modal input
            # First try to use attachments from the message directly
            # Fall back to looking up by file IDs from context if needed
            attachments_to_convert = attachments_list.copy()  # Actual Attachment objects from message

            # If we have file IDs from context but no attachments from message,
            # try to load them from the store
            if not attachments_to_convert and attached_file_ids:
                logger.info(f"[Schema ChatKit] No attachments in message, loading {len(attached_file_ids)} from store...")
                for file_id in attached_file_ids:
                    try:
                        attachment = await self.store.load_attachment(file_id, context)
                        if attachment:
                            attachments_to_convert.append(attachment)
                    except Exception as e:
                        logger.warning(f"[Schema ChatKit] Could not load attachment {file_id}: {e}")

            if attachments_to_convert:
                yield ProgressUpdateEvent(
                    type="progress_update",
                    text=f"Processing {len(attachments_to_convert)} attached file(s)..."
                )

                converter = SchemaAgentThreadItemConverter(db_session=db_session)

                for attachment in attachments_to_convert:
                    try:
                        att_id = getattr(attachment, 'id', 'unknown')
                        att_type = getattr(attachment, 'type', 'file')
                        logger.info(f"[Schema ChatKit] Converting attachment: {att_id} (type: {att_type})")

                        # Convert attachment to model input
                        content_param = await converter.attachment_to_message_content(attachment)

                        if content_param:
                            # Convert Pydantic model to dict for agent input
                            if hasattr(content_param, 'model_dump'):
                                content_dict = content_param.model_dump()
                            elif hasattr(content_param, 'dict'):
                                content_dict = content_param.dict()
                            else:
                                content_dict = dict(content_param)

                            multimodal_content.append(content_dict)
                            logger.info(f"[Schema ChatKit] Added {content_dict.get('type', 'unknown')} content for {att_id}")

                            # Show progress for image processing
                            if content_dict.get('type') == 'input_image':
                                yield ProgressUpdateEvent(
                                    type="progress_update",
                                    text="Image loaded and ready for analysis..."
                                )
                        else:
                            logger.warning(f"[Schema ChatKit] Converter returned None for attachment: {att_id}")

                    except Exception as e:
                        att_id = getattr(attachment, 'id', 'unknown')
                        logger.error(f"[Schema ChatKit] Error converting attachment {att_id}: {e}")

            # Prepare agent input - either string or multi-modal list
            if len(multimodal_content) > 1:
                # Multi-modal input with images/files
                agent_input = [{
                    "role": "user",
                    "content": multimodal_content
                }]
                logger.info(f"[Schema ChatKit] Using multi-modal input with {len(multimodal_content)} content items")
            else:
                # Simple text input
                agent_input = user_message
                logger.info(f"[Schema ChatKit] Using simple text input")

            # ============================================================================
            # WorkflowItem-based streaming with collapsible dropdown
            # Shows real-time progress that user can expand/collapse after completion
            # ============================================================================
            response_text = ""
            tools_used = []
            workflow_tasks = []  # Track all tasks for the workflow
            task_index = 0  # Current task index
            workflow_id = f"workflow-{uuid.uuid4().hex[:12]}"
            search_sources = []  # Track URLs from web search as dicts {url, title}
            thoughts_content = []  # Track reasoning/thoughts

            # Helper to get icon for tool type (using valid ChatKit icons)
            # Valid icons: agent, analytics, atom, batch, bolt, book-open, book-closed, book-clock,
            # bug, calendar, chart, check, check-circle, check-circle-filled, chevron-left, chevron-right,
            # circle-question, compass, confetti, cube, desktop, document, dot, dots-horizontal, dots-vertical,
            # empty-circle, external-link, globe, keys, lab, images, info, lifesaver, lightbulb, mail,
            # map-pin, maps, mobile, name, notebook, notebook-pencil, page-blank, phone, play, plus,
            # profile, profile-card, reload, star, star-filled, search, sparkle, sparkle-double,
            # square-code, square-image, square-text, suitcase, settings-slider, user, wreath, write, write-alt, write-alt2
            def get_tool_icon(tool_name: str) -> str:
                if "execute_sql" in tool_name or "query" in tool_name.lower():
                    return "analytics"
                elif "notion" in tool_name.lower():
                    return "notebook"
                elif "gmail" in tool_name.lower():
                    return "mail"
                elif "google_search" in tool_name.lower():
                    return "search"
                elif "file" in tool_name.lower() or "upload" in tool_name.lower():
                    return "document"
                elif "list_tables" in tool_name or "list_objects" in tool_name:
                    return "chart"
                else:
                    return "sparkle"

            # Helper to get display title for tool
            def get_tool_title(tool_name: str) -> str:
                if "execute_sql" in tool_name:
                    return "Executing SQL Query"
                elif tool_name == "notion_connector":
                    return "Connecting to Notion"
                elif "notion" in tool_name.lower():
                    notion_tool = tool_name.replace("notion-", "").replace("notion_", "")
                    if "search" in notion_tool:
                        return "Searching Notion"
                    elif "create" in notion_tool and "page" in notion_tool:
                        return "Creating Notion Page"
                    elif "create" in notion_tool and "database" in notion_tool:
                        return "Creating Notion Database"
                    elif "update" in notion_tool:
                        return "Updating Notion"
                    elif "query" in notion_tool:
                        return "Querying Notion Database"
                    return f"Notion: {notion_tool}"
                elif "gmail" in tool_name.lower() or "gmail_connector" in tool_name:
                    return "Processing Email"
                elif "google_search" in tool_name.lower():
                    return "Searching the Web"
                elif "file_search" in tool_name.lower():
                    return "Searching Files"
                elif "analyze_uploaded_file" in tool_name.lower():
                    return "Analyzing File"
                elif "get_uploaded_file_info" in tool_name.lower():
                    return "Getting File Info"
                elif "list_tables" in tool_name or "list_objects" in tool_name:
                    return "Listing Tables"
                elif "get_object_details" in tool_name:
                    return "Getting Table Details"
                else:
                    return f"Using {tool_name}"

            def format_response_with_sources(
                response_text: str,
                collected_urls: List[dict]
            ) -> str:
                """
                Format response text with inline citations and a sources section.

                Since ChatKit annotations may not work with custom API setup,
                this formats sources directly in markdown for better display:
                - Replaces domain mentions with clickable markdown links
                - Adds a clean "📚 Sources" section at the end with all links

                Example:
                    Input: "Buy from Naheed.pk"
                    Output: "Buy from [Naheed.pk](https://www.naheed.pk)"

                Args:
                    response_text: The full response text
                    collected_urls: List of dicts with 'url' and 'title' from web search

                Returns:
                    Formatted response text with markdown links
                """
                import re as fmt_re
                from urllib.parse import urlparse

                seen_urls = set()
                source_map = {}  # domain -> {url, title}
                all_sources = []

                # Extract existing markdown links from response: [Title](URL)
                markdown_links = fmt_re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', response_text)
                for title, url in markdown_links:
                    if url not in seen_urls:
                        seen_urls.add(url)
                        try:
                            domain = urlparse(url).netloc.replace('www.', '')
                        except:
                            domain = title[:30]
                        all_sources.append({'url': url, 'title': title, 'domain': domain})
                        source_map[domain.lower()] = {'url': url, 'title': title, 'domain': domain}
                        short_domain = domain.split('.')[0].lower()
                        if short_domain not in source_map:
                            source_map[short_domain] = {'url': url, 'title': title, 'domain': domain}

                # Extract plain text format: "- Daraz Pakistan: https://www.daraz.pk"
                plain_links = fmt_re.findall(r'[-\*]\s*([^:\n]+):\s*(https?://[^\s\n]+)', response_text)
                for title, url in plain_links:
                    title = title.strip()
                    url = url.strip()
                    if url not in seen_urls:
                        seen_urls.add(url)
                        try:
                            domain = urlparse(url).netloc.replace('www.', '')
                        except:
                            domain = title[:30]
                        all_sources.append({'url': url, 'title': title, 'domain': domain})
                        source_map[domain.lower()] = {'url': url, 'title': title, 'domain': domain}
                        short_domain = domain.split('.')[0].lower()
                        if short_domain not in source_map:
                            source_map[short_domain] = {'url': url, 'title': title, 'domain': domain}
                        # Map title words
                        for word in title.lower().split():
                            if len(word) > 3 and word not in source_map:
                                source_map[word] = {'url': url, 'title': title, 'domain': domain}

                # Add collected URLs from search tasks
                for source in collected_urls:
                    url = source.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        title = source.get('title', '')
                        try:
                            domain = urlparse(url).netloc.replace('www.', '')
                        except:
                            domain = 'source'
                        if not title:
                            title = domain
                        all_sources.append({'url': url, 'title': title, 'domain': domain})
                        source_map[domain.lower()] = {'url': url, 'title': title, 'domain': domain}
                        short_domain = domain.split('.')[0].lower()
                        if short_domain not in source_map:
                            source_map[short_domain] = {'url': url, 'title': title, 'domain': domain}

                # Remove existing Sources section
                clean_text = response_text
                sources_patterns = [
                    r'\n\n(Sources?\s*\([^)]*\)\s*:?\s*\n[-\*].*?)$',
                    r'\n\n(Sources?:?\s*\n[-\*].*?)$',
                    r'\n\n(References?:?\s*\n[-\*].*?)$',
                ]
                for pattern in sources_patterns:
                    match = fmt_re.search(pattern, response_text, fmt_re.DOTALL | fmt_re.IGNORECASE)
                    if match:
                        clean_text = response_text[:match.start()]
                        break

                # Remove standalone source URLs
                clean_text = fmt_re.sub(
                    r'\n[-\*]\s*[^:\n]+:\s*https?://[^\s\n]+',
                    '',
                    clean_text,
                    flags=fmt_re.MULTILINE
                )

                # Don't add inline links (ChatKit doesn't render markdown links)
                # Just keep domain mentions as-is in the text

                # Add formatted sources section at the end if we have sources
                # Use bare URLs which ChatKit may auto-link
                if all_sources:
                    clean_text = clean_text.strip()
                    clean_text += "\n\n---\n\n**Sources:**\n"
                    seen_in_footer = set()
                    for i, source in enumerate(all_sources[:8], 1):  # Limit to 8 sources
                        if source['url'] not in seen_in_footer:
                            seen_in_footer.add(source['url'])
                            title = source['title'][:40]
                            # Format: [1] Title - URL (bare URL for auto-linking)
                            clean_text += f"[{i}] {title}\n{source['url']}\n\n"

                return clean_text.strip()

            # Create initial workflow with first task (analyzing)
            initial_task = CustomTask(
                type="custom",
                title="Analyzing Request",
                content="Understanding your question and planning the approach...",
                status_indicator="loading",
                icon="search"
            )
            workflow_tasks.append(initial_task)

            # Create workflow item (expanded while processing)
            workflow = Workflow(
                type="custom",
                tasks=workflow_tasks.copy(),
                expanded=True,
                summary=None
            )

            workflow_item = WorkflowItem(
                id=workflow_id,
                thread_id=thread.id,
                created_at=datetime.now(),
                type="workflow",
                workflow=workflow
            )

            # Emit workflow started
            yield ThreadItemAddedEvent(type="thread.item.added", item=workflow_item)

            async for event in agent.query_streamed(agent_input, thread_id=thread_id):
                event_type = event.get("type", "unknown")

                if event_type == "progress":
                    # Update first task content
                    progress_text = event.get("text", "Processing...")
                    if workflow_tasks and workflow_tasks[0].status_indicator == "loading":
                        workflow_tasks[0].content = progress_text
                        yield ThreadItemUpdatedEvent(
                            type="thread.item.updated",
                            item_id=workflow_id,
                            update=WorkflowTaskUpdated(
                                type="workflow.task.updated",
                                task_index=0,
                                task=workflow_tasks[0]
                            )
                        )

                elif event_type == "tool_call":
                    # Tool is being called - add a new task with loading state
                    tool_name = event.get("tool_name", "tool")
                    args = event.get("arguments", "")
                    tools_used.append(tool_name)

                    # Mark previous task as complete if it was loading
                    for t in workflow_tasks:
                        if t.status_indicator == "loading":
                            t.status_indicator = "complete"

                    # Determine if this is a web search (use SearchTask)
                    if "google_search" in tool_name.lower():
                        # Extract search query from args (may be JSON)
                        search_query = "searching..."
                        if args:
                            try:
                                import json as json_parse
                                args_dict = json_parse.loads(args) if isinstance(args, str) else args
                                if isinstance(args_dict, dict):
                                    search_query = args_dict.get("query", args_dict.get("q", str(args_dict)[:100]))
                                else:
                                    search_query = str(args_dict)[:100]
                            except:
                                # Not JSON, use as-is
                                search_query = str(args)[:100]
                        
                        new_task = SearchTask(
                            type="web_search",
                            title=get_tool_title(tool_name),
                            title_query=search_query,  # Show query in title
                            queries=[search_query],
                            sources=[],  # Will be populated on output
                            status_indicator="loading"
                        )
                    else:
                        # Regular CustomTask for other tools
                        new_task = CustomTask(
                            type="custom",
                            title=get_tool_title(tool_name),
                            content=f"Processing...",
                            status_indicator="loading",
                            icon=get_tool_icon(tool_name)
                        )

                    workflow_tasks.append(new_task)
                    task_index = len(workflow_tasks) - 1

                    # First update previous tasks that were loading to complete
                    for prev_idx, prev_task in enumerate(workflow_tasks[:-1]):
                        if hasattr(prev_task, 'status_indicator') and prev_task.status_indicator == "complete":
                            yield ThreadItemUpdatedEvent(
                                type="thread.item.updated",
                                item_id=workflow_id,
                                update=WorkflowTaskUpdated(
                                    type="workflow.task.updated",
                                    task_index=prev_idx,
                                    task=prev_task
                                )
                            )

                    # Add new task
                    yield ThreadItemUpdatedEvent(
                        type="thread.item.updated",
                        item_id=workflow_id,
                        update=WorkflowTaskAdded(
                            type="workflow.task.added",
                            task_index=task_index,
                            task=new_task
                        )
                    )

                    logger.info(f"[Schema ChatKit] Tool call: {tool_name} (task {task_index})")

                elif event_type == "tool_output":
                    # Tool returned a result - update task to complete
                    tool_name = event.get("tool_name", "tool")
                    output_preview = event.get("output_preview", "")

                    # Find the task for this tool and update it
                    for i, t in enumerate(workflow_tasks):
                        if t.status_indicator == "loading":
                            t.status_indicator = "complete"

                            # For SearchTask, extract URLs with titles from markdown sources
                            if isinstance(t, SearchTask) and "google_search" in tool_name.lower():
                                import re as url_re

                                # Try to extract markdown links: [Title](URL)
                                markdown_links = url_re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', output_preview)

                                if markdown_links:
                                    # Use title and URL from markdown
                                    t.sources = [
                                        URLSource(url=url[:200], title=title[:50])
                                        for title, url in markdown_links[:5]
                                        if url.startswith('http')
                                    ]
                                    # Store sources as dicts for annotation creation
                                    search_sources.extend([
                                        {'url': url, 'title': title}
                                        for title, url in markdown_links[:5]
                                        if url.startswith('http')
                                    ])
                                else:
                                    # Fallback: just extract URLs
                                    urls = url_re.findall(r'https?://[^\s\)\]\"\'\<\>]+', output_preview)
                                    if urls:
                                        # Try to get domain as title
                                        t.sources = []
                                        for j, u in enumerate(urls[:5]):
                                            try:
                                                from urllib.parse import urlparse
                                                domain = urlparse(u).netloc
                                                title = domain or f"Source {j+1}"
                                                t.sources.append(URLSource(url=u[:200], title=title))
                                                # Store source as dict for annotation creation
                                                search_sources.append({'url': u, 'title': title})
                                            except:
                                                t.sources.append(URLSource(url=u[:200], title=f"Source {j+1}"))
                                                search_sources.append({'url': u, 'title': f"Source {j+1}"})
                            elif hasattr(t, 'content'):
                                # Truncate output for display
                                t.content = output_preview[:200] + "..." if len(output_preview) > 200 else output_preview
                            break

                    # Emit task update for the completed task
                    for update_idx, update_task in enumerate(workflow_tasks):
                        if update_task.status_indicator == "complete":
                            yield ThreadItemUpdatedEvent(
                                type="thread.item.updated",
                                item_id=workflow_id,
                                update=WorkflowTaskUpdated(
                                    type="workflow.task.updated",
                                    task_index=update_idx,
                                    task=update_task
                                )
                            )
                            break

                    logger.info(f"[Schema ChatKit] Tool output from {tool_name}")

                elif event_type == "thinking":
                    # Agent reasoning/thinking - add ThoughtTask
                    thinking_text = event.get("text", "")
                    if thinking_text:
                        # Extract the actual thought content (remove "Agent thinking:" prefix if present)
                        thought_content = thinking_text.replace("Agent thinking:", "").strip()
                        if thought_content:
                            thoughts_content.append(thought_content)

                            # Add or update ThoughtTask
                            thought_task = ThoughtTask(
                                type="thought",
                                title="Reasoning",
                                content=thought_content[:500]  # Limit content length
                            )

                            # Check if we already have a thought task, update it
                            thought_exists = False
                            for i, t in enumerate(workflow_tasks):
                                if isinstance(t, ThoughtTask):
                                    # Append to existing thoughts
                                    workflow_tasks[i].content = "\n".join(thoughts_content)[:500]
                                    thought_exists = True
                                    break

                            if not thought_exists:
                                workflow_tasks.append(thought_task)
                                yield ThreadItemUpdatedEvent(
                                    type="thread.item.updated",
                                    item_id=workflow_id,
                                    update=WorkflowTaskAdded(
                                        type="workflow.task.added",
                                        task_index=len(workflow_tasks) - 1,
                                        task=thought_task
                                    )
                                )
                            else:
                                # Update existing thought task
                                for thought_idx, t in enumerate(workflow_tasks):
                                    if isinstance(t, ThoughtTask):
                                        yield ThreadItemUpdatedEvent(
                                            type="thread.item.updated",
                                            item_id=workflow_id,
                                            update=WorkflowTaskUpdated(
                                                type="workflow.task.updated",
                                                task_index=thought_idx,
                                                task=t
                                            )
                                        )
                                        break

                elif event_type == "content_delta":
                    # Streaming content chunk - could update a "generating response" task
                    pass

                elif event_type == "complete":
                    # Final response - mark all tasks complete
                    response_text = event.get("response", "")
                    tools_used = event.get("tools_used", tools_used)

                    # Mark all tasks as complete
                    for t in workflow_tasks:
                        if hasattr(t, 'status_indicator'):
                            t.status_indicator = "complete"

                    # Add final "Done" task
                    done_task = CustomTask(
                        type="custom",
                        title="Done",
                        content=f"Completed {len(tools_used)} operation(s)",
                        status_indicator="complete",
                        icon="check"
                    )
                    workflow_tasks.append(done_task)

                    # Calculate duration
                    duration_seconds = int(time.time() - start_time)

                    # Create summary for collapsed state (DurationSummary 'duration' is in SECONDS)
                    summary = DurationSummary(
                        duration=duration_seconds
                    )

                    # Add done task
                    yield ThreadItemUpdatedEvent(
                        type="thread.item.updated",
                        item_id=workflow_id,
                        update=WorkflowTaskAdded(
                            type="workflow.task.added",
                            task_index=len(workflow_tasks) - 1,
                            task=done_task
                        )
                    )

                    # Update workflow to collapsed state with summary
                    workflow_item.workflow.tasks = workflow_tasks.copy()
                    workflow_item.workflow.summary = summary
                    workflow_item.workflow.expanded = False  # Collapse after completion

                    yield ThreadItemDoneEvent(type="thread.item.done", item=workflow_item)

                    logger.info(f"[Schema ChatKit] Query completed. Tools used: {tools_used}")

                elif event_type == "error":
                    # Error occurred
                    error_text = event.get("text", "An error occurred")
                    response_text = event.get("response", error_text)

                    # Mark current tasks as failed and add error task
                    for t in workflow_tasks:
                        if hasattr(t, 'status_indicator') and t.status_indicator == "loading":
                            t.status_indicator = "complete"  # Mark as done (no error state in ChatKit)

                    error_task = CustomTask(
                        type="custom",
                        title="Error",
                        content=error_text[:200],
                        status_indicator="complete",
                        icon="info"
                    )
                    workflow_tasks.append(error_task)

                    # Add error task
                    yield ThreadItemUpdatedEvent(
                        type="thread.item.updated",
                        item_id=workflow_id,
                        update=WorkflowTaskAdded(
                            type="workflow.task.added",
                            task_index=len(workflow_tasks) - 1,
                            task=error_task
                        )
                    )

                    workflow_item.workflow.tasks = workflow_tasks.copy()
                    workflow_item.workflow.expanded = False
                    yield ThreadItemDoneEvent(type="thread.item.done", item=workflow_item)

                    logger.error(f"[Schema ChatKit] Stream error: {error_text}")

            # Fallback if no response was captured
            if not response_text:
                logger.warning(f"[Schema ChatKit] No response from streaming! Using fallback.")
                # Fallback to non-streaming query
                result = await agent.query(user_message, thread_id=thread_id)
                response_text = result.get("response", "") if result else ""
                if not response_text:
                    response_text = "I processed your request but couldn't generate a response."

            # Clear file analysis context after use
            if attached_file_ids:
                try:
                    from app.mcp_server.tools_file_analysis import clear_file_analysis_context
                    clear_file_analysis_context()
                    logger.info(f"[Schema ChatKit] File analysis context cleared")
                except ImportError:
                    pass

            # Calculate total time
            total_time = time.time() - start_time
            logger.info(f"[Schema ChatKit] Query processed in {total_time:.1f}s with {len(tools_used)} tool calls")

            # Format response with inline citations and sources section
            # Uses markdown links since ChatKit annotations may not work with custom API
            logger.info(f"[Schema ChatKit] Response text length: {len(response_text)}")
            logger.info(f"[Schema ChatKit] Search sources collected: {len(search_sources)}")

            # Format with inline links and sources footer
            final_text = format_response_with_sources(response_text, search_sources)

            logger.info(f"[Schema ChatKit] Formatted text length: {len(final_text)}")

            # Create assistant message with formatted response
            msg_id = f"msg-{uuid.uuid4().hex[:12]}"

            assistant_msg = AssistantMessageItem(
                id=msg_id,
                thread_id=thread.id,
                created_at=datetime.now(),
                type="assistant_message",
                content=[AssistantMessageContent(
                    text=final_text
                )]
            )

            # Yield the final response
            yield ThreadItemAddedEvent(type="thread.item.added", item=assistant_msg)
            yield ThreadItemDoneEvent(type="thread.item.done", item=assistant_msg)

            # If user chose delete_immediately, remove these attachments now (best-effort)
            if attached_file_ids and db_session:
                try:
                    result = await db_session.execute(
                        select(UserSettings).where(UserSettings.user_id == user_id)
                    )
                    settings = result.scalar_one_or_none()
                    mode = settings.file_retention_mode if settings else "keep_24h"
                    if mode == "delete_immediately":
                        now = datetime.utcnow()
                        res_files = await db_session.execute(
                            select(UploadedFile).where(
                                UploadedFile.user_id == user_id,
                                UploadedFile.file_id.in_(attached_file_ids),
                                UploadedFile.deleted_at.is_(None),
                            )
                        )
                        files_to_delete = res_files.scalars().all()
                        for f in files_to_delete:
                            try:
                                if f.storage_path:
                                    from pathlib import Path
                                    p = Path(f.storage_path)
                                    if p.exists():
                                        p.unlink()
                            except Exception:
                                pass
                            f.status = "deleted"
                            f.deleted_at = now
                        if files_to_delete:
                            await db_session.commit()
                        logger.info(f"[Schema ChatKit] Deleted {len(files_to_delete)} attachment(s) after response (mode=delete_immediately)")
                except Exception as e:
                    logger.warning(f"[Schema ChatKit] Failed to delete attachments after response: {e}")

        except Exception as e:
            logger.error(f"[Schema ChatKit] Error: {e}", exc_info=True)
            yield ErrorEvent(
                type="error",
                code=ErrorCode.STREAM_ERROR,
                message=f"Error: {str(e)}",
                allow_retry=True
            )

# Global ChatKit instances - fallback in-memory store for backward compatibility
_fallback_store = SchemaAgentStore()

# Cache for per-user ChatKit servers (keyed by user_id)
_chatkit_server_cache: Dict[int, SchemaChatKitServer] = {}


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/connect", response_model=SchemaConnectResponse)
async def connect_schema_mode(
    request: SchemaConnectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Connect to user's database in schema-query-only mode.

    This mode:
    - Does NOT create any tables in user's database
    - Provides AI Agent + Analytics only (no Admin, no POS)
    - Discovers and caches user's existing schema
    """
    logger.info(f"User {user.id} connecting in schema-query mode")

    # Test connection first
    test_result = await test_connection(request.database_uri)
    if test_result["status"] != "success":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection failed: {test_result['message']}"
        )

    # Discover schema if requested
    schema_metadata = None
    tables_found = 0

    if request.auto_discover_schema:
        try:
            schema_metadata = await discover_schema(
                request.database_uri,
                request.allowed_schemas
            )
            tables_found = schema_metadata.get("total_tables", 0)
        except TooManyTablesError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except SchemaDiscoveryError as e:
            logger.error(f"Schema discovery failed: {e}")
            # Continue without schema - can be discovered later

    # Get or create user connection
    connection = await get_user_connection(user, db)

    if connection:
        # Update existing connection
        connection.connection_type = "schema_query_only"
        connection.connection_mode = "schema_query"
        connection.database_uri = request.database_uri
        connection.allowed_schemas = request.allowed_schemas
        connection.mcp_server_status = "connected"
        connection.last_connected_at = datetime.utcnow()
        if schema_metadata:
            connection.schema_metadata = schema_metadata
            connection.schema_last_updated = datetime.utcnow()
    else:
        # Create new connection
        connection = UserConnection(
            user_id=user.id,
            connection_type="schema_query_only",
            connection_mode="schema_query",
            database_uri=request.database_uri,
            allowed_schemas=request.allowed_schemas,
            mcp_server_status="connected",
            last_connected_at=datetime.utcnow(),
            schema_metadata=schema_metadata,
            schema_last_updated=datetime.utcnow() if schema_metadata else None
        )
        db.add(connection)

    await db.commit()
    await db.refresh(connection)

    return SchemaConnectResponse(
        status="connected",
        message="Successfully connected in schema-query mode. No tables will be created in your database.",
        tables_found=tables_found,
        schema_summary={
            "schemas": request.allowed_schemas,
            "table_count": tables_found,
            "column_count": schema_metadata.get("total_columns", 0) if schema_metadata else 0
        },
        mcp_session_id=str(connection.id)
    )


@router.post("/discover-schema", response_model=SchemaMetadataResponse)
async def discover_database_schema(
    allowed_schemas: Optional[List[str]] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Discover database schema from connected database.
    """
    connection = await require_schema_mode_connection(user, db)

    schemas = allowed_schemas or connection.allowed_schemas or ["public"]

    try:
        schema_metadata = await discover_schema(connection.database_uri, schemas)

        # Update cached schema
        connection.schema_metadata = schema_metadata
        connection.schema_last_updated = datetime.utcnow()
        connection.allowed_schemas = schemas
        await db.commit()

        return SchemaMetadataResponse(
            success=True,
            schema_metadata=schema_metadata,
            schema_prompt=format_schema_for_prompt(schema_metadata)
        )

    except TooManyTablesError as e:
        return SchemaMetadataResponse(
            success=False,
            error=str(e)
        )
    except SchemaDiscoveryError as e:
        return SchemaMetadataResponse(
            success=False,
            error=str(e)
        )


@router.get("/schema", response_model=SchemaMetadataResponse)
async def get_cached_schema(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get cached schema metadata.
    """
    connection = await require_schema_mode_connection(user, db)

    if not connection.schema_metadata:
        return SchemaMetadataResponse(
            success=False,
            error="Schema not cached. Please call /discover-schema first."
        )

    return SchemaMetadataResponse(
        success=True,
        schema_metadata=connection.schema_metadata,
        schema_prompt=format_schema_for_prompt(connection.schema_metadata)
    )


@router.post("/refresh-schema", response_model=SchemaMetadataResponse)
async def refresh_schema(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Force refresh schema cache.
    """
    connection = await require_schema_mode_connection(user, db)

    schemas = connection.allowed_schemas or ["public"]

    try:
        schema_metadata = await discover_schema(connection.database_uri, schemas)

        connection.schema_metadata = schema_metadata
        connection.schema_last_updated = datetime.utcnow()
        await db.commit()

        return SchemaMetadataResponse(
            success=True,
            schema_metadata=schema_metadata,
            schema_prompt=format_schema_for_prompt(schema_metadata)
        )

    except Exception as e:
        return SchemaMetadataResponse(
            success=False,
            error=str(e)
        )


@router.get("/status", response_model=ConnectionStatusResponse)
async def get_connection_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current connection status.
    """
    connection = await get_user_connection(user, db)

    if not connection:
        return ConnectionStatusResponse(
            connected=False,
            database_uri_set=False,
            schema_cached=False
        )

    # Check if it's schema query mode
    is_schema_mode = connection.connection_type == "schema_query_only"

    return ConnectionStatusResponse(
        connected=connection.mcp_server_status == "connected",
        connection_mode=connection.connection_mode,
        mcp_status=connection.mcp_server_status,
        database_uri_set=bool(connection.database_uri),
        schema_cached=bool(connection.schema_metadata) if is_schema_mode else False,
        schema_last_updated=connection.schema_last_updated if is_schema_mode else None,
        table_count=connection.schema_metadata.get("total_tables") if connection.schema_metadata else None
    )


@router.delete("/disconnect")
async def disconnect_database(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Disconnect from database and clear schema cache.
    Also clears the agent cache so new connection gets fresh agent.
    """
    connection = await get_user_connection(user, db)

    if not connection:
        return {"status": "not_connected", "message": "No connection to disconnect"}

    # Clear agent cache FIRST before clearing connection
    cleared = await clear_agent_cache_async(user.id)
    logger.info(f"[Schema Agent] Agent cache cleared on disconnect: {cleared}")

    # Clear connection data
    connection.mcp_server_status = "disconnected"
    connection.schema_metadata = None
    connection.schema_last_updated = None

    await db.commit()

    return {"status": "disconnected", "message": "Successfully disconnected from database"}


@router.get("/tables", response_model=TableListResponse)
async def list_tables(
    schema_name: str = "public",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all tables in the specified schema.
    """
    connection = await require_schema_mode_connection(user, db)

    result = await schema_list_tables(connection.database_uri, schema_name)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to list tables")
        )

    return TableListResponse(
        success=True,
        schema_name=schema_name,
        table_count=result["table_count"],
        tables=result["tables"]
    )


@router.get("/tables/{table_name}", response_model=TableDescribeResponse)
async def describe_table(
    table_name: str,
    schema_name: str = "public",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed structure of a specific table.
    """
    connection = await require_schema_mode_connection(user, db)

    result = await schema_describe_table(connection.database_uri, table_name, schema_name)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in result.get("error", "").lower()
            else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to describe table")
        )

    return TableDescribeResponse(
        success=True,
        table_name=result["table_name"],
        schema_name=result["schema"],
        estimated_rows=result["estimated_rows"],
        columns=result["columns"]
    )


@router.get("/tables/{table_name}/sample")
async def get_table_sample(
    table_name: str,
    schema_name: str = "public",
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get sample rows from a table.
    """
    connection = await require_schema_mode_connection(user, db)

    result = await schema_get_sample_data(
        connection.database_uri,
        table_name,
        schema_name,
        min(limit, 100)
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to get sample data")
        )

    return result


@router.get("/tables/{table_name}/stats")
async def get_table_statistics(
    table_name: str,
    schema_name: str = "public",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics for a specific table.
    """
    connection = await require_schema_mode_connection(user, db)

    result = await schema_get_table_stats(
        connection.database_uri,
        table_name,
        schema_name
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to get table stats")
        )

    return result


@router.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a SQL SELECT query directly.

    IMPORTANT: Only SELECT queries are allowed.
    """
    connection = await require_schema_mode_connection(user, db)

    result = await schema_execute_query(
        connection.database_uri,
        request.query,
        request.max_rows
    )

    if not result.get("success"):
        return QueryResponse(
            success=False,
            error=result.get("error"),
            sql_executed=request.query if request.include_sql else None
        )

    return QueryResponse(
        success=True,
        sql_executed=result.get("query") if request.include_sql else None,
        data=result.get("data"),
        columns=result.get("columns"),
        row_count=result.get("row_count")
    )


@router.post("/upgrade-to-full-ims")
async def upgrade_to_full_ims(
    confirm: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upgrade from schema-query mode to full IMS mode.

    WARNING: This will create IMS tables (inventory_items, inventory_bills, inventory_bill_items)
    in your database.
    """
    connection = await require_schema_mode_connection(user, db)

    if not confirm:
        return {
            "status": "confirmation_required",
            "message": "This will create IMS tables (inventory_items, inventory_bills, inventory_bill_items) "
                      "in your database. Set confirm=true to proceed.",
            "warning": "This action cannot be undone."
        }

    # Update connection type to full IMS
    connection.connection_type = "own_database"
    connection.connection_mode = "full_ims"
    await db.commit()

    return {
        "status": "upgraded",
        "message": "Successfully upgraded to Full IMS mode. You now have access to Admin and POS features.",
        "new_connection_type": "own_database",
        "new_connection_mode": "full_ims"
    }


# ============================================================================
# AI Agent Chat Endpoint
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request for natural language query"""
    message: str = Field(..., description="Natural language query")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation context")


class ChatResponse(BaseModel):
    """Chat response from agent"""
    success: bool
    response: str
    sql_executed: Optional[str] = None
    data: Optional[list] = None
    visualization_hint: Optional[dict] = None
    error: Optional[str] = None


# Cache for agent instances (keyed by "{user_id}:connectors_{count}" or "{user_id}")
_agent_cache: Dict[str, SchemaQueryAgent] = {}


async def clear_agent_cache_async(user_id: int) -> bool:
    """
    Clear ALL cached agents for a specific user (async version).
    Properly closes the MCP connection before removing from cache.

    This should be called when:
    - User disconnects their database
    - User connects to a different database
    - User connects/disconnects a connector

    Args:
        user_id: The user ID whose agents should be cleared

    Returns:
        True if any agent was cleared, False if no agent was cached
    """
    cleared = False
    # Find all cache keys for this user (handles both old and new key formats)
    keys_to_clear = [
        key for key in list(_agent_cache.keys())
        if key == str(user_id) or key.startswith(f"{user_id}:")
    ]

    for cache_key in keys_to_clear:
        agent = _agent_cache.get(cache_key)
        if agent:
            try:
                # Close MCP connection properly
                await agent.close()
                logger.info(f"[Schema Agent] Closed MCP connection for cache key {cache_key}")
            except Exception as e:
                logger.error(f"[Schema Agent] Error closing MCP connection for {cache_key}: {e}")
            finally:
                del _agent_cache[cache_key]
                logger.info(f"[Schema Agent] Cleared cached agent: {cache_key}")
                cleared = True

    if cleared:
        logger.info(f"[Schema Agent] Cleared {len(keys_to_clear)} cached agent(s) for user {user_id}")
    return cleared


def clear_agent_cache(user_id: int) -> bool:
    """
    Clear ALL cached agents for a specific user (sync version).
    Creates a new event loop if needed to close MCP connection.

    This should be called when:
    - User disconnects their database
    - User connects to a different database
    - User connects/disconnects a connector

    Args:
        user_id: The user ID whose agents should be cleared

    Returns:
        True if any agent was cleared, False if no agent was cached
    """
    cleared = False
    # Find all cache keys for this user (handles both old and new key formats)
    keys_to_clear = [
        key for key in list(_agent_cache.keys())
        if key == str(user_id) or key.startswith(f"{user_id}:")
    ]

    for cache_key in keys_to_clear:
        agent = _agent_cache.get(cache_key)
        if agent:
            try:
                # Try to close MCP connection
                import asyncio
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an async context, schedule the close
                    loop.create_task(agent.close())
                except RuntimeError:
                    # No running loop, create one
                    asyncio.run(agent.close())
                logger.info(f"[Schema Agent] Closed MCP connection for cache key {cache_key}")
            except Exception as e:
                logger.error(f"[Schema Agent] Error closing MCP connection for {cache_key}: {e}")
            finally:
                del _agent_cache[cache_key]
                logger.info(f"[Schema Agent] Cleared cached agent: {cache_key}")
                cleared = True

    if cleared:
        logger.info(f"[Schema Agent] Cleared {len(keys_to_clear)} cached agent(s) for user {user_id}")
    return cleared


async def clear_all_agent_cache_async() -> int:
    """
    Clear all cached agents (async version).
    Properly closes all MCP connections.

    Returns:
        Number of agents cleared
    """
    count = len(_agent_cache)
    for user_id in list(_agent_cache.keys()):
        await clear_agent_cache_async(user_id)
    logger.info(f"[Schema Agent] Cleared all {count} cached agents")
    return count


def clear_all_agent_cache() -> int:
    """
    Clear all cached agents (sync version).

    Returns:
        Number of agents cleared
    """
    count = len(_agent_cache)
    for user_id in list(_agent_cache.keys()):
        clear_agent_cache(user_id)
    logger.info(f"[Schema Agent] Cleared all {count} cached agents")
    return count


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with the Schema Query Agent using natural language.

    Send a natural language question and get back:
    - A human-readable response
    - The SQL that was executed (if any)
    - Query results data (if any)
    - Visualization suggestions

    Example questions:
    - "Show me the top 10 customers by total orders"
    - "What is the average order value this month?"
    - "List all products with low stock"
    """
    connection = await require_schema_mode_connection(user, db)

    if not connection.schema_metadata:
        return ChatResponse(
            success=False,
            response="Schema not discovered yet. Please wait while I analyze your database structure.",
            error="Schema metadata not available. Call /schema-agent/discover-schema first."
        )

    # Use session_id from request or generate default
    session_thread_id = request.session_id or f"chat-user-{user.id}"

    # Get or create agent for this user
    if user.id not in _agent_cache:
        try:
            agent = await create_schema_query_agent(
                database_uri=connection.database_uri,
                schema_metadata=connection.schema_metadata,
                auto_initialize=True,
                user_id=user.id,
                thread_id=session_thread_id,  # Pass session_id for persistent conversation
            )
            _agent_cache[user.id] = agent
            logger.info(f"Created new Schema Query Agent for user {user.id} with PostgreSQL session")
        except Exception as e:
            logger.error(f"Failed to create agent for user {user.id}: {e}")
            return ChatResponse(
                success=False,
                response="I'm having trouble initializing. Please try again.",
                error=str(e)
            )
    else:
        agent = _agent_cache[user.id]

    # Process the query with session persistence
    try:
        result = await agent.query(request.message, thread_id=session_thread_id)

        return ChatResponse(
            success=result.get("success", False),
            response=result.get("response", ""),
            visualization_hint=result.get("visualization_hint"),
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"Agent query failed for user {user.id}: {e}")
        return ChatResponse(
            success=False,
            response="I encountered an error processing your request. Please try rephrasing your question.",
            error=str(e)
        )


@router.post("/chat/clear-history")
async def clear_chat_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clear the conversation history for the current user's agent.
    """
    if user.id in _agent_cache:
        _agent_cache[user.id].clear_history()
        return {"status": "cleared", "message": "Conversation history cleared"}

    return {"status": "no_history", "message": "No conversation history to clear"}


@router.get("/chat/history")
async def get_chat_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the conversation history for the current user's agent.
    """
    if user.id in _agent_cache:
        history = _agent_cache[user.id].get_history()
        return {"history": history, "message_count": len(history)}

    return {"history": [], "message_count": 0}


@router.post("/reset-agent")
async def reset_agent(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset/clear the cached agent for current user.
    This forces a new agent to be created on next message.
    Useful when database connection changes or agent is in bad state.
    """
    cleared = await clear_agent_cache_async(user.id)
    if cleared:
        return {
            "success": True,
            "message": "Agent cache cleared. A new agent will be created on next message."
        }
    return {
        "success": True,
        "message": "No cached agent found. A new agent will be created on next message."
    }


# ============================================================================
# ChatKit Endpoint for OpenAI ChatKit UI
# ============================================================================

@router.post("/chatkit")
async def chatkit_endpoint(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Response:
    """
    ChatKit-compatible endpoint for the Schema Query Agent.

    This endpoint integrates with OpenAI's ChatKit web component,
    providing a rich chat UI experience with thinking indicators
    and streaming responses.
    """
    try:
        body = await request.body()
        logger.info(f"[Schema ChatKit] Request received from user {user.id}")

        # Parse raw body to extract operation type, tool selection, connector, and attachments
        selected_tool = None
        selected_connector_id = None
        selected_connector_url = None
        selected_connector_name = None
        attached_file_ids = []  # List of attached file IDs from ChatKit
        operation = None
        try:
            body_str = body.decode('utf-8')
            logger.info(f"[Schema ChatKit] Raw body (first 500 chars): {body_str[:500]}")

            # Extract operation type from body
            try:
                body_json = json.loads(body_str)
                operation = body_json.get('op')
                logger.info(f"[Schema ChatKit] Operation: {operation}")

                metadata = body_json.get('metadata', {})
                if metadata.get('selected_tool'):
                    selected_tool = metadata['selected_tool']
                    logger.info(f"[Schema ChatKit] Tool from metadata: {selected_tool}")

                # Check for connector selection in metadata
                if metadata.get('selected_connector_id'):
                    selected_connector_id = metadata['selected_connector_id']
                    selected_connector_url = metadata.get('selected_connector_url')
                    selected_connector_name = metadata.get('selected_connector_name')
                    logger.info(f"[Schema ChatKit] Connector from metadata: {selected_connector_name} ({selected_connector_id})")

                # Check for attachments in ChatKit message format
                # ChatKit sends attachments in user messages with structure: {type: 'file'|'image', id: 'file_id', ...}
                if body_json.get('item') and isinstance(body_json['item'], dict):
                    item = body_json['item']
                    if item.get('content') and isinstance(item['content'], list):
                        for content_part in item['content']:
                            if isinstance(content_part, dict):
                                # Check for attachments array in content
                                if content_part.get('attachments'):
                                    for attachment in content_part['attachments']:
                                        if isinstance(attachment, dict) and attachment.get('id'):
                                            attached_file_ids.append(attachment['id'])
                                            logger.info(f"[Schema ChatKit] Found attachment: {attachment.get('id')} ({attachment.get('type', 'file')})")

                # Also check for attached_file_id in metadata (legacy support)
                if metadata.get('attached_file_id'):
                    attached_file_ids.append(metadata['attached_file_id'])
                    logger.info(f"[Schema ChatKit] File from metadata: {metadata['attached_file_id']}")

            except json.JSONDecodeError:
                pass

            # Check for tool prefix in the raw body
            if '[TOOL:' in body_str:
                logger.info(f"[Schema ChatKit] TOOL PREFIX FOUND IN BODY!")
                # Extract tool name from prefix like [TOOL:GMAIL]
                tool_match = re.search(r'\[TOOL:(\w+)\]', body_str)
                if tool_match:
                    selected_tool = tool_match.group(1).lower()
                    logger.info(f"[Schema ChatKit] Extracted tool: {selected_tool}")

            # Check for connector prefix in the raw body [CONNECTOR:id:url]
            if '[CONNECTOR:' in body_str:
                logger.info(f"[Schema ChatKit] CONNECTOR PREFIX FOUND IN BODY!")
                connector_match = re.search(r'\[CONNECTOR:(\d+):([^\]]+)\]', body_str)
                if connector_match:
                    selected_connector_id = int(connector_match.group(1))
                    selected_connector_url = connector_match.group(2)
                    logger.info(f"[Schema ChatKit] Extracted connector: {selected_connector_id}")

        except Exception as e:
            logger.warning(f"[Schema ChatKit] Could not decode body: {e}")

        # Create PostgreSQL-backed store for persistent history (always create for history operations)
        try:
            db_store = create_chatkit_store(db, user.id)
            chatkit_server = SchemaChatKitServer(db_store, attachment_store=SchemaNoopAttachmentStore())
            logger.info(f"[Schema ChatKit] Using PostgreSQL-backed store for user {user.id}")
        except Exception as store_error:
            logger.warning(f"[Schema ChatKit] Failed to create DB store, using fallback: {store_error}")
            chatkit_server = SchemaChatKitServer(_fallback_store, attachment_store=SchemaNoopAttachmentStore())

        # For read-only history operations, we don't need database connection
        read_only_operations = ['threads.list', 'threads.get', 'threads.items', 'threads.delete']
        is_read_only = operation in read_only_operations

        # Get user's connection (needed for chat operations)
        connection = await get_user_connection(user, db)

        # Build context - for read-only operations, provide minimal context
        if is_read_only:
            context = {
                "headers": dict(request.headers),
                "user_id": user.id,
            }
            logger.info(f"[Schema ChatKit] Read-only operation {operation}, skipping connection check")
        else:
            # For chat operations, require database connection
            if not connection or connection.connection_type != "schema_query_only":
                return JSONResponse(
                    content={"error": "No schema query connection configured"},
                    status_code=400
                )

            if not connection.database_uri:
                return JSONResponse(
                    content={"error": "Database URI not configured"},
                    status_code=400
                )

            context = {
                "headers": dict(request.headers),
                "user_id": user.id,
                "database_uri": connection.database_uri,
                "schema_metadata": connection.schema_metadata,
                "allowed_schemas": connection.allowed_schemas or ["public"],
                "selected_tool": selected_tool,  # Pass tool selection to agent
                "selected_connector_id": selected_connector_id,
                "selected_connector_url": selected_connector_url,
                "selected_connector_name": selected_connector_name,
                "attached_file_ids": attached_file_ids,  # Pass attached file IDs for file analysis
                "db_session": db,  # Pass DB session for connector tools loading
            }

            if selected_tool:
                logger.info(f"[Schema ChatKit] Passing tool '{selected_tool}' to agent context")
            if selected_connector_id:
                logger.info(f"[Schema ChatKit] Passing connector '{selected_connector_name}' to agent context")
            if attached_file_ids:
                logger.info(f"[Schema ChatKit] Passing {len(attached_file_ids)} attached file(s) to agent context")

        # Process with ChatKit server
        result = await chatkit_server.process(body, context)

        # Handle different result types (streaming vs JSON)
        if hasattr(result, '__aiter__'):
            async def generate():
                try:
                    async for event in result:
                        if isinstance(event, bytes):
                            yield event
                        elif isinstance(event, str):
                            yield event.encode('utf-8')
                        elif hasattr(event, 'model_dump_json'):
                            yield f"data: {event.model_dump_json()}\n\n".encode('utf-8')
                        elif hasattr(event, 'model_dump'):
                            yield f"data: {json.dumps(event.model_dump())}\n\n".encode('utf-8')
                        else:
                            data = json.dumps(event) if isinstance(event, dict) else str(event)
                            yield f"data: {data}\n\n".encode('utf-8')
                except Exception as e:
                    logger.error(f"[Schema ChatKit] Streaming error: {e}", exc_info=True)
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n".encode('utf-8')

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )
        elif hasattr(result, 'json') and isinstance(result.json, bytes):
            # NonStreamingResult from ChatKit - has .json bytes attribute
            return Response(content=result.json, media_type="application/json")
        elif hasattr(result, 'model_dump_json'):
            return Response(content=result.model_dump_json(), media_type="application/json")
        elif hasattr(result, 'model_dump'):
            return Response(content=json.dumps(result.model_dump()), media_type="application/json")
        elif isinstance(result, bytes):
            return Response(content=result, media_type="application/json")
        else:
            return Response(
                content=json.dumps(result) if isinstance(result, dict) else str(result),
                media_type="application/json"
            )

    except Exception as e:
        logger.error(f"[Schema ChatKit] Endpoint error: {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)
