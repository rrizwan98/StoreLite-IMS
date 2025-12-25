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
from chatkit.types import (
    ThreadItemDoneEvent,
    ThreadItemAddedEvent,
    AssistantMessageItem,
    AssistantMessageContent,
    ProgressUpdateEvent,
    ErrorEvent,
    ErrorCode,
    Page,
)

from app.database import get_db
from app.models import User, UserConnection
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
from app.connectors.agent_tools import load_connector_tools, get_user_connector_tools

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schema-agent", tags=["schema-agent"])

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
        return Page(data=threads[:limit], has_more=len(threads) > limit)

    async def add_thread_item(self, thread_id: str, item: ThreadItem, context: Any) -> None:
        if thread_id not in self._items:
            self._items[thread_id] = []
        self._items[thread_id].append(item)

    async def load_thread_items(self, thread_id: str, after: str | None, limit: int, order: str, context: Any) -> Any:
        items = self._items.get(thread_id, [])
        return Page(data=items[:limit], has_more=len(items) > limit)

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

    async def load_attachment(self, attachment_id: str, context: Any) -> Any:
        return self._attachments.get(attachment_id)

    async def delete_attachment(self, attachment_id: str, context: Any) -> None:
        if attachment_id in self._attachments:
            del self._attachments[attachment_id]


# ============================================================================
# ChatKit Server for Schema Agent
# ============================================================================

class SchemaChatKitServer(ChatKitServer):
    """
    Schema Agent ChatKit Server implementation.

    Uses Schema Query Agent to process natural language queries
    against user's database.
    """

    def __init__(self, store: Store):
        super().__init__(store)

    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Process user message using Schema Query Agent."""
        import time

        try:
            if input_user_message is None:
                return

            # Extract user message text
            user_message = ""
            if hasattr(input_user_message, 'content'):
                for content in input_user_message.content:
                    if hasattr(content, 'text'):
                        user_message += content.text

            # Log the raw message for debugging
            logger.info(f"[Schema ChatKit] Raw user message: {user_message[:100]}...")

            # Check if tool prefix is present (from frontend tool selection)
            if '[TOOL:' in user_message:
                logger.info(f"[Schema ChatKit] Tool prefix detected in message!")

            # Get selected tool from context (set by chatkit_endpoint)
            selected_tool = context.get("selected_tool")
            if selected_tool:
                logger.info(f"[Schema ChatKit] Tool from context: {selected_tool}")
                # Prepend the tool instruction if not already in message
                if f'[TOOL:{selected_tool.upper()}]' not in user_message:
                    user_message = f"[TOOL:{selected_tool.upper()}] {user_message}"
                    logger.info(f"[Schema ChatKit] Prepended tool prefix to message")

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

            # Track timing
            start_time = time.time()

            # Show progress indicator using ProgressUpdateEvent (valid ThreadStreamEvent)
            yield ProgressUpdateEvent(
                type="progress_update",
                text="Analyzing your question..."
            )

            # Get thread_id from ChatKit thread for session persistence
            thread_id = thread.id if thread else None
            logger.info(f"[Schema ChatKit] Thread ID for session: {thread_id}")

            # Load ALL user's connector tools (not just selected ones)
            # This ensures the agent always has access to all connected services
            connector_tools = []
            db_session = context.get("db_session")

            if db_session:
                try:
                    # Load ALL verified connectors for this user
                    logger.info(f"[Schema ChatKit] Loading ALL connector tools for user {user_id}")
                    connector_tools = await get_user_connector_tools(
                        db_session,
                        user_id,
                        connector_id=None  # None = load ALL connectors
                    )
                    if connector_tools:
                        tool_names = [getattr(t, 'name', str(t)) for t in connector_tools]
                        logger.info(f"[Schema ChatKit] Loaded {len(connector_tools)} connector tools: {tool_names[:5]}...")
                    else:
                        logger.info(f"[Schema ChatKit] No connector tools found for user {user_id}")
                except Exception as e:
                    logger.warning(f"[Schema ChatKit] Failed to load connector tools: {e}")

            # Create a cache key - include connector count to invalidate when connectors change
            connector_count = len(connector_tools)
            cache_key = f"{user_id}:connectors_{connector_count}"

            # Get or create agent for this user (with connector tools if selected)
            if cache_key not in _agent_cache:
                try:
                    yield ProgressUpdateEvent(
                        type="progress_update",
                        text="Initializing AI agent..."
                    )
                    agent = await create_schema_query_agent(
                        database_uri=database_uri,
                        schema_metadata=schema_metadata,
                        auto_initialize=True,
                        user_id=user_id,  # Pass user_id for Gmail tool context
                        enable_gmail=True,
                        thread_id=thread_id,  # Pass thread_id for persistent session
                        connector_tools=connector_tools,  # Pass connector tools
                    )
                    _agent_cache[cache_key] = agent
                    logger.info(f"Created new Schema Query Agent for user {user_id} with Gmail + {len(connector_tools)} connector tools")
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

            # Show query progress
            yield ProgressUpdateEvent(
                type="progress_update",
                text="Processing your query..."
            )

            # Run agent query with thread_id for session persistence
            logger.info(f"[Schema ChatKit] Running agent query...")
            result = await agent.query(user_message, thread_id=thread_id)
            logger.info(f"[Schema ChatKit] Agent query completed. Result keys: {list(result.keys()) if result else 'None'}")
            response_text = result.get("response", "I couldn't process your request.")
            logger.info(f"[Schema ChatKit] Response text length: {len(response_text) if response_text else 0}")

            # Calculate total time
            total_time = time.time() - start_time
            logger.info(f"[Schema ChatKit] Query processed in {total_time:.1f}s")

            # Create the assistant message with the response
            msg_id = f"msg-{uuid.uuid4().hex[:12]}"

            assistant_msg = AssistantMessageItem(
                id=msg_id,
                thread_id=thread.id,
                created_at=datetime.now().isoformat(),
                type="assistant_message",
                content=[AssistantMessageContent(
                    type="output_text",
                    text=response_text,
                    annotations=[]
                )]
            )

            # Yield the proper ThreadStreamEvent types
            yield ThreadItemAddedEvent(type="thread.item.added", item=assistant_msg)
            yield ThreadItemDoneEvent(type="thread.item.done", item=assistant_msg)

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
                user_id=user.id,  # Pass user_id for Gmail tool context
                enable_gmail=True,
                thread_id=session_thread_id,  # Pass session_id for persistent conversation
            )
            _agent_cache[user.id] = agent
            logger.info(f"Created new Schema Query Agent for user {user.id} with Gmail tools and PostgreSQL session")
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

        # Parse raw body to extract operation type, tool selection, and connector
        selected_tool = None
        selected_connector_id = None
        selected_connector_url = None
        selected_connector_name = None
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
            chatkit_server = SchemaChatKitServer(db_store)
            logger.info(f"[Schema ChatKit] Using PostgreSQL-backed store for user {user.id}")
        except Exception as store_error:
            logger.warning(f"[Schema ChatKit] Failed to create DB store, using fallback: {store_error}")
            chatkit_server = SchemaChatKitServer(_fallback_store)

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
                "db_session": db,  # Pass DB session for connector tools loading
            }

            if selected_tool:
                logger.info(f"[Schema ChatKit] Passing tool '{selected_tool}' to agent context")
            if selected_connector_id:
                logger.info(f"[Schema ChatKit] Passing connector '{selected_connector_name}' to agent context")

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
        elif hasattr(result, 'model_dump_json'):
            return Response(content=result.model_dump_json(), media_type="application/json")
        elif hasattr(result, 'model_dump'):
            return Response(content=json.dumps(result.model_dump()), media_type="application/json")
        else:
            return Response(
                content=json.dumps(result) if isinstance(result, dict) else str(result),
                media_type="application/json"
            )

    except Exception as e:
        logger.error(f"[Schema ChatKit] Endpoint error: {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)
