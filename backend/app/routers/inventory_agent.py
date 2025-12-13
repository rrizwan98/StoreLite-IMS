"""
Specialized Inventory Management Agent with postgres-mcp MCP Server

This agent connects to user's PostgreSQL database via postgres-mcp MCP server
and uses MCP tools (execute_sql, list_objects, etc.) for all database operations.

Architecture:
1. User provides DATABASE_URI (or retrieves from stored user connection)
2. Backend starts postgres-mcp server via MCPServerStdio (subprocess)
3. Agent uses MCP tools from the postgres-mcp server
4. All database operations go through MCP protocol
"""

import logging
import json
import os
import uuid
import asyncio
import asyncpg
from typing import Optional, Dict, Any, List, AsyncIterator
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.responses import Response
from pydantic import BaseModel

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from agents.model_settings import ModelSettings
from agents.extensions.models.litellm_model import LitellmModel

from chatkit.server import (
    ChatKitServer,
    Store,
    ThreadMetadata,
    ThreadItem,
    UserMessageItem,
    ThreadStreamEvent,
)
from chatkit.types import (
    AssistantMessageContentPartTextDelta,
    AssistantMessageContentPartDone,
    ThreadItemDoneEvent,
    ThreadItemAddedEvent,
    AssistantMessageItem,
    AssistantMessageContent,
    ThoughtTask,
    WorkflowTaskAdded,
    WorkflowTaskUpdated,
    Page,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory-agent", tags=["inventory-agent"])

# ============================================================================
# Session Management - Stores active MCP server connections
# ============================================================================

# Store active sessions with their MCP server instances (in-memory)
_sessions: Dict[str, Dict[str, Any]] = {}

# Database URL for session persistence
DATABASE_URL = os.getenv("DATABASE_URL", "")

# LiteLLM model configuration for Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini/gemini-robotics-er-1.5-preview")


def get_llm_model():
    """
    Get the LLM model instance.
    Uses Gemini via LiteLLM if GEMINI_API_KEY is set, otherwise falls back to OpenAI.
    """
    if GEMINI_API_KEY:
        logger.info(f"[MCP] Using Gemini model: {GEMINI_MODEL}")
        return LitellmModel(
            model=GEMINI_MODEL,
            api_key=GEMINI_API_KEY,
        )
    else:
        # Fallback to OpenAI if no Gemini key
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(f"[MCP] Using OpenAI model: {openai_model}")
        return openai_model


class ConnectRequest(BaseModel):
    """Request to connect to a PostgreSQL database."""
    database_uri: Optional[str] = None  # postgresql://user:password@host:port/dbname
    user_id: Optional[int] = None  # User ID to retrieve stored database_uri


# ============================================================================
# PostgreSQL Session Persistence - Stores sessions in database
# ============================================================================

class SessionPersistence:
    """
    Manages session persistence in PostgreSQL database.
    Sessions are stored so they survive page refreshes and server restarts.
    """

    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def get_pool(cls) -> Optional[asyncpg.Pool]:
        """Get or create database connection pool."""
        if cls._pool is None and DATABASE_URL:
            try:
                # Clean up DATABASE_URL - remove channel_binding parameter if present
                db_url = DATABASE_URL.split('#')[0]  # Remove comments
                if 'channel_binding' in db_url:
                    # Remove channel_binding parameter
                    parts = db_url.split('?')
                    if len(parts) > 1:
                        base = parts[0]
                        params = '&'.join([p for p in parts[1].split('&') if 'channel_binding' not in p])
                        db_url = f"{base}?{params}" if params else base

                cls._pool = await asyncpg.create_pool(
                    db_url,
                    min_size=1,
                    max_size=5,
                    command_timeout=30,
                )
                logger.info("[SessionDB] Database pool created successfully")
            except Exception as e:
                logger.error(f"[SessionDB] Failed to create pool: {e}")
                return None
        return cls._pool

    @classmethod
    async def init_table(cls) -> bool:
        """Create the mcp_sessions table if it doesn't exist."""
        pool = await cls.get_pool()
        if not pool:
            logger.warning("[SessionDB] No database pool available")
            return False

        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS mcp_sessions (
                        session_id VARCHAR(50) PRIMARY KEY,
                        user_database_uri TEXT NOT NULL,
                        mcp_tools TEXT[] DEFAULT '{}',
                        connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                logger.info("[SessionDB] mcp_sessions table ready")
                return True
        except Exception as e:
            logger.error(f"[SessionDB] Failed to create table: {e}")
            return False

    @classmethod
    async def save_session(cls, session_id: str, database_uri: str, mcp_tools: List[str]) -> bool:
        """Save a new session to the database."""
        pool = await cls.get_pool()
        if not pool:
            return False

        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO mcp_sessions (session_id, user_database_uri, mcp_tools, is_active)
                    VALUES ($1, $2, $3, TRUE)
                    ON CONFLICT (session_id) DO UPDATE SET
                        user_database_uri = $2,
                        mcp_tools = $3,
                        last_active_at = CURRENT_TIMESTAMP,
                        is_active = TRUE
                """, session_id, database_uri, mcp_tools)
                logger.info(f"[SessionDB] Session {session_id} saved")
                return True
        except Exception as e:
            logger.error(f"[SessionDB] Failed to save session: {e}")
            return False

    @classmethod
    async def get_active_session(cls) -> Optional[Dict[str, Any]]:
        """Get the most recent active session."""
        pool = await cls.get_pool()
        if not pool:
            return None

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT session_id, user_database_uri, mcp_tools, connected_at, is_active
                    FROM mcp_sessions
                    WHERE is_active = TRUE
                    ORDER BY last_active_at DESC
                    LIMIT 1
                """)
                if row:
                    return {
                        "session_id": row["session_id"],
                        "user_database_uri": row["user_database_uri"],
                        "mcp_tools": list(row["mcp_tools"]) if row["mcp_tools"] else [],
                        "connected_at": row["connected_at"].isoformat() if row["connected_at"] else None,
                        "is_active": row["is_active"],
                    }
                return None
        except Exception as e:
            logger.error(f"[SessionDB] Failed to get active session: {e}")
            return None

    @classmethod
    async def update_activity(cls, session_id: str) -> bool:
        """Update the last_active_at timestamp."""
        pool = await cls.get_pool()
        if not pool:
            return False

        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE mcp_sessions
                    SET last_active_at = CURRENT_TIMESTAMP
                    WHERE session_id = $1
                """, session_id)
                return True
        except Exception as e:
            logger.error(f"[SessionDB] Failed to update activity: {e}")
            return False

    @classmethod
    async def deactivate_session(cls, session_id: str) -> bool:
        """Mark a session as inactive (disconnect)."""
        pool = await cls.get_pool()
        if not pool:
            return False

        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE mcp_sessions
                    SET is_active = FALSE, last_active_at = CURRENT_TIMESTAMP
                    WHERE session_id = $1
                """, session_id)
                logger.info(f"[SessionDB] Session {session_id} deactivated")
                return True
        except Exception as e:
            logger.error(f"[SessionDB] Failed to deactivate session: {e}")
            return False

    @classmethod
    async def deactivate_all_sessions(cls) -> bool:
        """Mark all sessions as inactive."""
        pool = await cls.get_pool()
        if not pool:
            return False

        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE mcp_sessions SET is_active = FALSE
                """)
                logger.info("[SessionDB] All sessions deactivated")
                return True
        except Exception as e:
            logger.error(f"[SessionDB] Failed to deactivate all sessions: {e}")
            return False


# ============================================================================
# MCP Server Manager - Manages postgres-mcp subprocess per session
# ============================================================================

class MCPSessionManager:
    """
    Manages MCP server sessions for each user database connection.

    Each session gets its own postgres-mcp subprocess via MCPServerStdio.
    """

    def __init__(self):
        self._servers: Dict[str, MCPServerStdio] = {}
        self._agents: Dict[str, Agent] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, session_id: str, database_uri: str) -> Dict[str, Any]:
        """
        Create a new MCP session with postgres-mcp server.

        Args:
            session_id: Unique session identifier
            database_uri: PostgreSQL connection URI

        Returns:
            Session info including connection status
        """
        async with self._lock:
            if session_id in self._servers:
                return {"error": "Session already exists"}

            try:
                # Create MCP server using postgres-mcp via stdio
                # This starts postgres-mcp as a subprocess
                # NOTE: postgres-mcp takes database_url as positional argument, not env var
                # NOTE: Increase timeout for cloud databases (Neon, etc.) that need SSL/network time
                server = MCPServerStdio(
                    name=f"postgres-mcp-{session_id}",
                    params={
                        "command": "postgres-mcp",
                        "args": [database_uri, "--access-mode=unrestricted"],
                    },
                    cache_tools_list=True,
                    client_session_timeout_seconds=60.0,  # 60 seconds for cloud DB connections
                )

                logger.info(f"[MCP] Starting postgres-mcp for session {session_id}...")

                # Start the MCP server (enters async context)
                await server.__aenter__()

                # Get available tools from the MCP server
                tools = await server.list_tools()
                tool_names = [t.name for t in tools]

                logger.info(f"[MCP] Session {session_id}: Connected with tools: {tool_names}")

                # Create specialized inventory agent with MCP tools
                # Uses Gemini via LiteLLM if GEMINI_API_KEY is set
                agent = Agent(
                    name="Inventory Manager",
                    instructions=INVENTORY_SYSTEM_PROMPT,
                    model=get_llm_model(),
                    mcp_servers=[server],
                    model_settings=ModelSettings(tool_choice="auto"),
                )

                self._servers[session_id] = server
                self._agents[session_id] = agent

                # Store session info
                _sessions[session_id] = {
                    "database_uri": database_uri,
                    "connected_at": datetime.now().isoformat(),
                    "mcp_tools": tool_names,
                    "status": "connected",
                }

                return {
                    "success": True,
                    "session_id": session_id,
                    "message": "Connected via postgres-mcp MCP server!",
                    "mcp_info": {
                        "server": "postgres-mcp",
                        "tools": tool_names,
                        "mode": "unrestricted",
                    }
                }

            except FileNotFoundError:
                logger.error(f"[MCP] postgres-mcp not found. Install with: pipx install postgres-mcp")
                return {
                    "success": False,
                    "error": "postgres-mcp not installed",
                    "install_instructions": "Install postgres-mcp with: pipx install postgres-mcp",
                }
            except Exception as e:
                logger.error(f"[MCP] Failed to create session: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                }

    async def get_agent(self, session_id: str) -> Optional[Agent]:
        """Get the Agent for a session."""
        return self._agents.get(session_id)

    async def run_agent(self, session_id: str, message: str) -> str:
        """
        Run the agent with a user message.

        This uses the MCP tools from postgres-mcp to execute SQL and other operations.
        """
        agent = self._agents.get(session_id)
        if not agent:
            return "Error: Session not found. Please connect to a database first."

        try:
            # Run the agent - it will use MCP tools automatically
            result = await Runner.run(agent, message)
            return result.final_output
        except Exception as e:
            logger.error(f"[MCP] Agent run error: {e}", exc_info=True)
            return f"Error: {str(e)}"

    async def close_session(self, session_id: str) -> bool:
        """Close an MCP session and cleanup resources."""
        async with self._lock:
            if session_id not in self._servers:
                return False

            try:
                server = self._servers.pop(session_id)
                self._agents.pop(session_id, None)
                _sessions.pop(session_id, None)

                # Close the MCP server (exits async context)
                await server.__aexit__(None, None, None)

                logger.info(f"[MCP] Session {session_id}: Closed")
                return True
            except Exception as e:
                logger.error(f"[MCP] Error closing session: {e}")
                return False

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        return _sessions.get(session_id)


# Global MCP session manager
_mcp_manager = MCPSessionManager()


# ============================================================================
# Inventory Agent System Prompt
# ============================================================================

INVENTORY_SYSTEM_PROMPT = """You are an EXPERT AI DATABASE ANALYTICS ASSISTANT connected to a PostgreSQL database via MCP (Model Context Protocol).

## YOUR ROLE:
You provide AI-powered analytics dashboard services, helping users understand and analyze their database data with professional-level insights.

## YOUR MCP TOOLS:
You have access to these database tools via postgres-mcp:
- **execute_sql**: Run SQL queries (SELECT, INSERT, UPDATE, DELETE)
- **list_schemas**: List database schemas
- **list_objects**: List tables, views in a schema
- **get_object_details**: Get table columns and constraints

## CRITICAL RULES FOR RESPONSES:

### 1. ALWAYS EXPLORE THE DATABASE FIRST
When a user asks about their data, FIRST use list_objects or list_schemas to discover what tables exist. NEVER assume table names - always check first!

### 2. FORMAT DATA FOR VISUALIZATION
When presenting query results with numerical data, format them clearly so the dashboard can visualize them:

**For item counts:**
"There is a total of **X items** in your database."

**For individual items with quantities:**
- "**ItemName**: X units"
- Or use a table format:
  | Name | Quantity | Price |
  |------|----------|-------|
  | Rice | 50 | $2.50 |

**For totals:**
"Total value: **$X,XXX.XX**"

### 3. BE ACCURATE - NEVER INVENT DATA
- Only report data that EXISTS in the database
- If a query returns 0 results, say "No items found" - don't make up examples
- If you can't find a table, say so clearly

### 4. INTELLIGENT QUERY BUILDING
- First discover the schema (list_objects)
- Then check column names (get_object_details)
- Then build appropriate queries
- Handle any table structure - not just the default schema

## EXAMPLE RESPONSE PATTERNS:

**When user asks "how many items are in my database?"**
1. First: list_objects to find tables
2. Then: execute_sql to count rows
3. Response: "Based on the **items** table, you have a total of **5 items** in your database."

**When user asks for stock levels:**
1. Query the inventory/items table
2. Response with clear data:
   "Here are your current stock levels:
   - **Rice**: 50 units ($2.50 each)
   - **Wheat**: 30 units ($3.00 each)
   - **Sugar**: 25 units ($1.50 each)

   Total inventory value: **$XXX.XX**"

**When data is not found:**
"I checked your database but found no inventory tables. Would you like me to:
1. List all available tables?
2. Help you create an inventory table?"

## YOUR CAPABILITIES:
1. **Data Analysis** - Query and analyze any table in the database
2. **Product Management** - Add, update, delete, search products
3. **Reports** - Generate summaries, totals, trends
4. **Stock Management** - Check levels, low stock alerts
5. **Database Exploration** - List tables, view structure

## RESTRICTIONS (IMPORTANT):
- Do NOT modify system tables
- Do NOT access sensitive auth/user data unless specifically requested
- Be cautious with DELETE/DROP operations - always confirm first

## RESPONSE STYLE:
- Professional and helpful
- Use **bold** for important numbers and names
- Format data in tables when showing multiple items
- Be concise but complete
- If no data found, say so clearly (don't invent)
"""


# ============================================================================
# ChatKit Store for Inventory Agent
# ============================================================================

class InventoryStore(Store):
    """Simple in-memory store for Inventory ChatKit threads and messages."""

    def __init__(self):
        self._threads: dict[str, ThreadMetadata] = {}
        self._items: dict[str, list[ThreadItem]] = {}
        self._attachments: dict[str, Any] = {}

    def generate_thread_id(self, context: Any) -> str:
        return f"inv-thread-{uuid.uuid4().hex[:12]}"

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
# ChatKit Server for Inventory Agent
# ============================================================================

class InventoryChatKitServer(ChatKitServer):
    """
    Inventory-specific ChatKit Server implementation.

    Uses MCP session manager to run agent with postgres-mcp tools.
    """

    def __init__(self, store: Store):
        super().__init__(store)

    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Process user message using MCP-based agent."""
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

            # Get session ID from context (passed via headers)
            session_id = context.get("session_id", "")

            if not session_id:
                error_text = "No session ID provided. Please connect to a database first."
                yield AssistantMessageContentPartTextDelta(
                    type="assistant_message.content_part.text_delta",
                    content_index=0,
                    delta=error_text
                )
                return

            # Check if session exists
            session_info = _mcp_manager.get_session_info(session_id)
            if not session_info:
                error_text = "Session not found. Please connect to a PostgreSQL database first."
                yield AssistantMessageContentPartTextDelta(
                    type="assistant_message.content_part.text_delta",
                    content_index=0,
                    delta=error_text
                )
                return

            logger.info(f"[MCP ChatKit] Processing message for session {session_id}: {user_message[:50]}...")

            # Track timing
            start_time = time.time()

            # Show thinking indicator
            thinking_steps = self._generate_thinking_steps(user_message)
            initial_thought = ThoughtTask(
                type="thought",
                status_indicator="loading",
                title=thinking_steps[0] if thinking_steps else "Connecting to MCP server...",
                content=""
            )
            yield WorkflowTaskAdded(
                type="workflow.task.added",
                task_index=0,
                task=initial_thought
            )

            # Update thinking progressively
            accumulated_reasoning = ""
            for step in thinking_steps:
                accumulated_reasoning += f"• {step}\n"
                updated_thought = ThoughtTask(
                    type="thought",
                    status_indicator="loading",
                    title=step,
                    content=accumulated_reasoning
                )
                yield WorkflowTaskUpdated(
                    type="workflow.task.updated",
                    task_index=0,
                    task=updated_thought
                )
                await asyncio.sleep(0.1)

            # Run agent with MCP tools
            response_text = await _mcp_manager.run_agent(session_id, user_message)

            # Calculate total time
            total_time = time.time() - start_time

            # Add MCP info to reasoning
            mcp_tools = session_info.get("mcp_tools", [])
            accumulated_reasoning += f"\nMCP Tools Available: {', '.join(mcp_tools)}\n"

            # Final thought update
            final_thought = ThoughtTask(
                type="thought",
                status_indicator="complete",
                title=f"Processed via MCP in {total_time:.1f}s",
                content=accumulated_reasoning
            )
            yield WorkflowTaskUpdated(
                type="workflow.task.updated",
                task_index=0,
                task=final_thought
            )

            # Stream the response
            msg_id = f"msg-{uuid.uuid4().hex[:12]}"

            yield AssistantMessageContentPartTextDelta(
                type="assistant_message.content_part.text_delta",
                content_index=0,
                delta=response_text
            )

            yield AssistantMessageContentPartDone(
                type="assistant_message.content_part.done",
                content_index=0,
                content=AssistantMessageContent(
                    type="output_text",
                    text=response_text,
                    annotations=[]
                )
            )

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
            yield ThreadItemAddedEvent(type="thread.item.added", item=assistant_msg)
            yield ThreadItemDoneEvent(type="thread.item.done", item=assistant_msg)

        except Exception as e:
            logger.error(f"[MCP ChatKit] Error: {e}", exc_info=True)
            error_text = f"Error: {str(e)}"
            yield AssistantMessageContentPartTextDelta(
                type="assistant_message.content_part.text_delta",
                content_index=0,
                delta=error_text
            )

    def _generate_thinking_steps(self, user_message: str) -> list[str]:
        """Generate thinking steps based on the user's message."""
        steps = []
        message_lower = user_message.lower()

        steps.append("Connecting to postgres-mcp server...")

        if any(word in message_lower for word in ['add', 'insert', 'new product', 'create']):
            steps.append("Preparing INSERT via MCP execute_sql...")
        elif any(word in message_lower for word in ['update', 'edit', 'change']):
            steps.append("Preparing UPDATE via MCP execute_sql...")
        elif any(word in message_lower for word in ['delete', 'remove']):
            steps.append("Preparing DELETE via MCP execute_sql...")
        elif any(word in message_lower for word in ['show', 'list', 'all', 'view', 'get']):
            steps.append("Querying via MCP execute_sql...")
        elif any(word in message_lower for word in ['table', 'schema', 'structure']):
            steps.append("Using MCP list_objects tool...")
        elif any(word in message_lower for word in ['bill', 'invoice']):
            steps.append("Processing billing via MCP...")
        else:
            steps.append("Processing request via MCP...")

        steps.append("Executing MCP tool call...")

        return steps


# Global instances
_inventory_store = InventoryStore()
_inventory_server = InventoryChatKitServer(_inventory_store)


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/connect")
async def connect_database(request: ConnectRequest) -> Dict[str, Any]:
    """
    Connect to a PostgreSQL database using DATABASE_URI via postgres-mcp.

    This will:
    1. Get database_uri from request or retrieve from user's stored connection
    2. Validate the DATABASE_URI format
    3. Start a postgres-mcp MCP server subprocess
    4. Save session to PostgreSQL for persistence
    5. If new database_uri provided, update user_connections table
    6. Return session_id and available MCP tools
    """
    database_uri = None
    should_save_new_uri = False

    # Check if user provided a new database_uri directly
    if request.database_uri:
        database_uri = request.database_uri.strip()
        should_save_new_uri = True  # User is providing a new/different URI
        logger.info(f"[MCP] Using provided database_uri for user {request.user_id}")
    # Otherwise, try to get stored database_uri
    elif request.user_id:
        try:
            pool = await SessionPersistence.get_pool()
            if pool:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT database_uri FROM user_connections WHERE user_id = $1",
                        request.user_id
                    )
                    if row and row["database_uri"]:
                        database_uri = row["database_uri"]
                        logger.info(f"[MCP] Retrieved stored database_uri for user {request.user_id}")
        except Exception as e:
            logger.warning(f"[MCP] Failed to retrieve stored database_uri: {e}")

    # Validate we have a database_uri
    if not database_uri:
        raise HTTPException(
            status_code=400,
            detail="No database URI provided. Please provide database_uri or ensure your connection has a stored URI."
        )

    # Validate URI format
    if not database_uri.startswith("postgresql://") and not database_uri.startswith("postgres://"):
        raise HTTPException(
            status_code=400,
            detail="Invalid DATABASE_URI. Must start with postgresql:// or postgres://"
        )

    # Initialize session table if needed
    await SessionPersistence.init_table()

    # Generate session ID
    session_id = str(uuid.uuid4())[:8]

    # Create MCP session
    result = await _mcp_manager.create_session(session_id, database_uri)

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to connect")
        )

    # Save session to PostgreSQL for persistence
    mcp_tools = result.get("mcp_info", {}).get("tools", [])
    await SessionPersistence.save_session(session_id, database_uri, mcp_tools)

    # If user provided a new database_uri, update their stored connection
    if should_save_new_uri and request.user_id:
        try:
            pool = await SessionPersistence.get_pool()
            if pool:
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE user_connections
                        SET database_uri = $1, updated_at = NOW()
                        WHERE user_id = $2
                        """,
                        database_uri,
                        request.user_id
                    )
                    logger.info(f"[MCP] Updated stored database_uri for user {request.user_id}")
        except Exception as e:
            logger.warning(f"[MCP] Failed to update stored database_uri: {e}")

    return result


@router.post("/setup-tables")
async def setup_inventory_tables(session_id: str) -> Dict[str, Any]:
    """
    Create inventory tables using MCP execute_sql tool.
    """
    session_info = _mcp_manager.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=400, detail="Session not found. Please connect first.")

    # Use the agent to create tables via MCP
    create_tables_prompt = """Please create the following inventory tables if they don't exist:

1. inventory_items table with columns: id (serial primary key), name (varchar 255), category (varchar 100), unit (varchar 50 default 'piece'), unit_price (decimal 12,2), stock_qty (decimal 12,3), min_stock_level (decimal 12,3 default 10), description (text), is_active (boolean default true), created_at (timestamp default now())

2. inventory_bills table with columns: id (serial primary key), bill_number (varchar 50 unique), customer_name (varchar 255), customer_phone (varchar 20), total_amount (decimal 12,2), discount (decimal 12,2 default 0), tax (decimal 12,2 default 0), grand_total (decimal 12,2), payment_method (varchar 50 default 'cash'), status (varchar 20 default 'completed'), notes (text), created_at (timestamp default now())

3. inventory_bill_items table with columns: id (serial primary key), bill_id (integer references inventory_bills), item_id (integer references inventory_items), item_name (varchar 255), quantity (decimal 12,3), unit_price (decimal 12,2), total_price (decimal 12,2), created_at (timestamp default now())

Use CREATE TABLE IF NOT EXISTS for each table."""

    try:
        result = await _mcp_manager.run_agent(session_id, create_tables_prompt)

        return {
            "success": True,
            "message": "Inventory tables created via MCP!",
            "tables_created": ["inventory_items", "inventory_bills", "inventory_bill_items"],
            "agent_response": result
        }
    except Exception as e:
        logger.error(f"[MCP] Table setup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")


@router.post("/chatkit")
async def chatkit_endpoint(request: Request) -> Response:
    """
    ChatKit-compatible endpoint for the inventory agent.

    All messages are processed through the MCP-based agent.
    """
    try:
        body = await request.body()
        logger.info(f"[MCP ChatKit] Request received: {body[:200]}...")

        # Get session_id from header
        session_id = request.headers.get("x-session-id", "")

        # Get context from request
        context = {
            "headers": dict(request.headers),
            "session_id": session_id,
        }

        # Process with ChatKit server
        result = await _inventory_server.process(body, context)

        # Handle different result types
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
                    logger.error(f"[MCP ChatKit] Streaming error: {e}", exc_info=True)
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
        logger.error(f"[MCP ChatKit] Endpoint error: {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/chat")
async def chat_with_agent(request: Request) -> StreamingResponse:
    """
    Simple chat endpoint (SSE streaming).

    Uses MCP-based agent for all operations.
    """
    try:
        body = await request.json()
        session_id = body.get("session_id", "")
        message = body.get("message", "")

        if not session_id:
            async def error_stream():
                yield f"data: {json.dumps({'type': 'error', 'message': 'session_id is required'})}\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")

        session_info = _mcp_manager.get_session_info(session_id)
        if not session_info:
            async def error_stream():
                yield f"data: {json.dumps({'type': 'error', 'message': 'Session not found. Please connect via MCP first.'})}\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")

        if not message:
            async def error_stream():
                yield f"data: {json.dumps({'type': 'error', 'message': 'message is required'})}\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")

        async def response_stream():
            try:
                # Run agent with MCP tools
                response = await _mcp_manager.run_agent(session_id, message)
                yield f"data: {json.dumps({'type': 'content', 'text': response})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                logger.error(f"[MCP] Chat error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return StreamingResponse(response_stream(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"[MCP] Request error: {e}")
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")


@router.get("/status/{session_id}")
async def get_session_status(session_id: str) -> Dict[str, Any]:
    """Check if a session is connected via MCP."""
    session_info = _mcp_manager.get_session_info(session_id)
    if session_info:
        return {
            "connected": True,
            "connected_at": session_info.get("connected_at"),
            "mcp_tools": session_info.get("mcp_tools", []),
            "status": session_info.get("status"),
        }
    return {"connected": False}


@router.delete("/disconnect/{session_id}")
async def disconnect_session(session_id: str) -> Dict[str, Any]:
    """Disconnect a session and close MCP server."""
    # Close in-memory session
    success = await _mcp_manager.close_session(session_id)

    # Deactivate in database
    await SessionPersistence.deactivate_session(session_id)

    if success:
        return {"success": True, "message": "MCP session closed successfully"}
    return {"success": False, "message": "Session not found"}


@router.get("/mcp-status")
async def get_mcp_status() -> Dict[str, Any]:
    """Check if postgres-mcp is installed and available."""
    import shutil

    postgres_mcp_path = shutil.which("postgres-mcp")

    return {
        "postgres_mcp_installed": postgres_mcp_path is not None,
        "postgres_mcp_path": postgres_mcp_path,
        "install_instructions": "pipx install postgres-mcp" if not postgres_mcp_path else None,
        "active_sessions": len(_sessions),
    }


@router.get("/active-session")
async def get_active_session() -> Dict[str, Any]:
    """
    Get the active session from database (for page refresh/restore).

    Returns the most recent active session if it exists.
    """
    # Initialize table if needed
    await SessionPersistence.init_table()

    # Get active session from database
    stored_session = await SessionPersistence.get_active_session()

    if stored_session:
        session_id = stored_session["session_id"]
        # Check if session is still in memory (MCP server running)
        in_memory = _mcp_manager.get_session_info(session_id) is not None

        return {
            "has_active_session": True,
            "session": stored_session,
            "mcp_server_running": in_memory,
        }

    return {
        "has_active_session": False,
        "session": None,
        "mcp_server_running": False,
    }


@router.post("/restore")
async def restore_session() -> Dict[str, Any]:
    """
    Restore the active session from database.

    If a session exists in database, reconnect to the user's database via MCP.
    """
    # Initialize table if needed
    await SessionPersistence.init_table()

    # Get active session from database
    stored_session = await SessionPersistence.get_active_session()

    if not stored_session:
        return {
            "success": False,
            "message": "No active session found",
        }

    session_id = stored_session["session_id"]
    database_uri = stored_session["user_database_uri"]

    # Check if already in memory
    if _mcp_manager.get_session_info(session_id):
        return {
            "success": True,
            "session_id": session_id,
            "message": "Session already active",
            "mcp_info": {
                "server": "postgres-mcp",
                "tools": stored_session.get("mcp_tools", []),
                "mode": "unrestricted",
            }
        }

    # Reconnect MCP session
    try:
        result = await _mcp_manager.create_session(session_id, database_uri)

        if result.get("success"):
            # Update last activity in database
            await SessionPersistence.update_activity(session_id)

            return {
                "success": True,
                "session_id": session_id,
                "message": "Session restored successfully!",
                "mcp_info": result.get("mcp_info", {}),
            }
        else:
            # Session failed to restore, deactivate it
            await SessionPersistence.deactivate_session(session_id)
            return {
                "success": False,
                "message": result.get("error", "Failed to restore session"),
            }
    except Exception as e:
        logger.error(f"[MCP] Session restore failed: {e}")
        await SessionPersistence.deactivate_session(session_id)
        return {
            "success": False,
            "message": f"Restore failed: {str(e)}",
        }
