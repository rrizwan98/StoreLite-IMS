"""
Task Executor Service - Scheduled Task Execution

Executes scheduled tasks using the Schema Query Agent.
Called by APScheduler at the scheduled time.

Flow:
1. Load task from database
2. Create ChatKit thread for results
3. Run Schema Agent with selected tools only
4. Save result to thread and update task
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Optional, List, Any, Dict
from urllib.parse import urlparse, parse_qs

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models import ScheduledTask, User, UserConnection, ChatKitThread, ChatKitThreadItem
from app.database import get_database_url

logger = logging.getLogger(__name__)


def _prepare_async_url(database_url: str) -> tuple[str, dict]:
    """
    Prepare database URL for asyncpg.

    Removes query parameters that asyncpg doesn't support (like sslmode)
    and returns the clean URL with appropriate connect_args.

    Args:
        database_url: Original database URL

    Returns:
        Tuple of (clean_url, connect_args)
    """
    # Parse URL
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query) if parsed.query else {}

    # Remove query parameters from URL for asyncpg
    base_url = database_url.split("?")[0] if "?" in database_url else database_url

    # Build connect_args based on SSL settings
    connect_args = {}

    # Check for SSL mode
    sslmode = query_params.get("sslmode", [None])[0]
    if sslmode and sslmode != "disable":
        # For asyncpg, use ssl=True or ssl context
        connect_args["ssl"] = True

    return base_url, connect_args


async def execute_scheduled_task(task_id: str) -> None:
    """
    Execute a scheduled task - called by APScheduler at scheduled_time.

    Flow:
    1. Load task from DB
    2. Create new ChatKit thread
    3. Run Schema Agent with ONLY selected tools
    4. Save result to thread (ChatKit persists it)
    5. Update task with thread_id for user to view

    Args:
        task_id: UUID of the scheduled task to execute
    """
    logger.info(f"[TaskExecutor] Starting execution of task {task_id}")

    # Create database session
    database_url = get_database_url()
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://")

    # Prepare URL for asyncpg (removes sslmode query param, sets ssl in connect_args)
    clean_url, connect_args = _prepare_async_url(database_url)

    engine = create_async_engine(clean_url, connect_args=connect_args)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # 1. Get task from database
            result = await db.execute(
                select(ScheduledTask).where(ScheduledTask.id == task_id)
            )
            task = result.scalar_one_or_none()

            if not task:
                logger.error(f"[TaskExecutor] Task {task_id} not found")
                return

            if task.status != "pending":
                logger.warning(f"[TaskExecutor] Task {task_id} is not pending (status: {task.status})")
                return

            # Update status to running
            task.status = "running"
            await db.commit()

            logger.info(f"[TaskExecutor] Task {task_id} - Query: {task.query[:100]}...")
            logger.info(f"[TaskExecutor] Task {task_id} - Selected tools: {task.selected_tools}")

            # 2. Get user and connection info
            user_result = await db.execute(
                select(User).where(User.id == task.user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                raise ValueError(f"User {task.user_id} not found")

            conn_result = await db.execute(
                select(UserConnection).where(UserConnection.user_id == task.user_id)
            )
            connection = conn_result.scalar_one_or_none()

            if not connection or not connection.database_uri:
                raise ValueError(f"User {task.user_id} has no database connection")

            # 3. Create a new ChatKit thread for this task
            thread_id = f"scheduled_{task_id}_{uuid.uuid4().hex[:8]}"

            # Create thread record
            chatkit_thread = ChatKitThread(
                id=thread_id,
                user_id=task.user_id,
                title=f"Scheduled: {task.query[:50]}...",
                thread_metadata={
                    "type": "scheduled_task",
                    "task_id": task_id,
                    "scheduled_time": task.scheduled_time.isoformat(),
                    "selected_tools": task.selected_tools,
                }
            )
            db.add(chatkit_thread)

            # Save thread_id to task early so it's available even if task fails later
            task.thread_id = thread_id
            await db.flush()  # Flush to save thread_id without committing

            # 4. Build connector tools for ONLY selected tools
            connector_tools = await _build_selected_tools(
                task.selected_tools,
                task.user_id,
                db
            )

            logger.info(f"[TaskExecutor] Built {len(connector_tools)} connector tools for task")

            # 5. Create and run Schema Agent with scheduler-specific LLM model
            from app.agents.schema_query_agent import create_schema_query_agent, get_scheduler_llm_model

            agent = await create_schema_query_agent(
                database_uri=connection.database_uri,
                schema_metadata=connection.schema_metadata or {},
                user_id=task.user_id,
                thread_id=thread_id,
                connector_tools=connector_tools,
                model_getter=get_scheduler_llm_model,  # Use scheduler-specific model
            )

            # Prefix query with tool markers so agent knows which to use
            prefixed_query = task.query
            for tool_id in (task.selected_tools or []):
                tool_upper = tool_id.upper().replace("_", "_")
                prefixed_query = f"[TOOL:{tool_upper}] {prefixed_query}"

            logger.info(f"[TaskExecutor] Running agent with query: {prefixed_query[:150]}...")

            # Run the query
            result = await agent.query(prefixed_query, thread_id=thread_id)

            # 6. Save messages to ChatKit thread for viewing in UI
            response_text = result.get("response", "")

            # Create user message item
            user_msg_id = f"user-{uuid.uuid4().hex[:12]}"
            user_msg_content = {
                "id": user_msg_id,
                "type": "user_message",
                "thread_id": thread_id,
                "created_at": datetime.utcnow().isoformat(),
                "content": [{"type": "input_text", "text": task.query}],
                "attachments": [],
                "inference_options": {}
            }
            user_msg_item = ChatKitThreadItem(
                id=user_msg_id,
                thread_id=thread_id,
                item_type="user_message",
                content=json.dumps(user_msg_content),
                created_at=datetime.utcnow(),
            )
            db.add(user_msg_item)

            # Create assistant message item
            assistant_msg_id = f"assistant-{uuid.uuid4().hex[:12]}"
            assistant_msg_content = {
                "id": assistant_msg_id,
                "type": "assistant_message",
                "thread_id": thread_id,
                "created_at": datetime.utcnow().isoformat(),
                "content": [{"type": "output_text", "text": response_text, "annotations": []}]
            }
            assistant_msg_item = ChatKitThreadItem(
                id=assistant_msg_id,
                thread_id=thread_id,
                item_type="assistant_message",
                content=json.dumps(assistant_msg_content),
                created_at=datetime.utcnow(),
            )
            db.add(assistant_msg_item)

            # Update thread's updated_at
            chatkit_thread.updated_at = datetime.utcnow()

            # 7. Update task with results
            task.status = "completed"
            # thread_id already set earlier
            task.result_summary = response_text[:500]  # First 500 chars
            # Use naive UTC datetime for PostgreSQL TIMESTAMP WITHOUT TIME ZONE
            task.executed_at = datetime.utcnow()

            await db.commit()
            logger.info(f"[TaskExecutor] Task {task_id} completed successfully with messages saved to thread")

        except Exception as e:
            logger.error(f"[TaskExecutor] Task {task_id} failed: {e}", exc_info=True)

            # Update task with error
            try:
                await db.rollback()  # Rollback any failed transaction first

                # Re-fetch the task since rollback may have cleared it
                task_result = await db.execute(
                    select(ScheduledTask).where(ScheduledTask.id == task_id)
                )
                task = task_result.scalar_one_or_none()

                if task:
                    error_message = str(e)[:1000]

                    # If we have a thread_id, save error to ChatKit thread for viewing
                    if task.thread_id:
                        try:
                            # Ensure thread exists
                            thread_result = await db.execute(
                                select(ChatKitThread).where(ChatKitThread.id == task.thread_id)
                            )
                            existing_thread = thread_result.scalar_one_or_none()

                            if not existing_thread:
                                # Create thread if it doesn't exist
                                existing_thread = ChatKitThread(
                                    id=task.thread_id,
                                    user_id=task.user_id,
                                    title=f"Scheduled: {task.query[:50]}... (Failed)",
                                    thread_metadata={"type": "scheduled_task", "task_id": task_id, "status": "failed"}
                                )
                                db.add(existing_thread)

                            # Save user message
                            user_msg_id = f"user-{uuid.uuid4().hex[:12]}"
                            user_msg_item = ChatKitThreadItem(
                                id=user_msg_id,
                                thread_id=task.thread_id,
                                item_type="user_message",
                                content=json.dumps({
                                    "id": user_msg_id,
                                    "type": "user_message",
                                    "thread_id": task.thread_id,
                                    "created_at": datetime.utcnow().isoformat(),
                                    "content": [{"type": "input_text", "text": task.query}],
                                    "attachments": [],
                                    "inference_options": {}
                                }),
                                created_at=datetime.utcnow(),
                            )
                            db.add(user_msg_item)

                            # Save error as assistant message
                            error_msg_id = f"assistant-{uuid.uuid4().hex[:12]}"
                            error_msg_item = ChatKitThreadItem(
                                id=error_msg_id,
                                thread_id=task.thread_id,
                                item_type="assistant_message",
                                content=json.dumps({
                                    "id": error_msg_id,
                                    "type": "assistant_message",
                                    "thread_id": task.thread_id,
                                    "created_at": datetime.utcnow().isoformat(),
                                    "content": [{"type": "output_text", "text": f"❌ **Task Failed**\n\nError: {error_message}", "annotations": []}]
                                }),
                                created_at=datetime.utcnow(),
                            )
                            db.add(error_msg_item)
                        except Exception as thread_error:
                            logger.warning(f"[TaskExecutor] Could not save error to thread: {thread_error}")

                    task.status = "failed"
                    task.error_message = error_message
                    task.executed_at = datetime.utcnow()
                    await db.commit()
            except Exception as commit_error:
                logger.error(f"[TaskExecutor] Failed to update task status: {commit_error}")

        finally:
            await engine.dispose()


async def _build_selected_tools(
    selected_tool_ids: List[str],
    user_id: int,
    db: AsyncSession
) -> List[Any]:
    """
    Build connector tools for only the selected tool IDs.

    Args:
        selected_tool_ids: List of tool IDs (e.g., ["gmail", "analytics"])
        user_id: User ID for tool context
        db: Database session

    Returns:
        List of function tools for the agent
    """
    tools = []

    if not selected_tool_ids:
        return tools

    logger.info(f"[TaskExecutor] Building tools for: {selected_tool_ids}")

    for tool_id in selected_tool_ids:
        tool_id_lower = tool_id.lower()

        try:
            if tool_id_lower == "gmail":
                # Gmail connector tool
                from app.connector_agents.gmail_agent import create_gmail_connector_tool
                gmail_tool = await create_gmail_connector_tool(user_id)
                if gmail_tool:
                    tools.append(gmail_tool)
                    logger.info(f"[TaskExecutor] Added Gmail tool for user {user_id}")

            elif tool_id_lower == "analytics":
                # Analytics tool
                from app.mcp_server.tools_analytics import get_analytics_tool
                analytics_tool = get_analytics_tool()
                if analytics_tool:
                    tools.append(analytics_tool)
                    logger.info(f"[TaskExecutor] Added Analytics tool")

            elif tool_id_lower == "google_search":
                # Google Search tool
                from app.mcp_server.tools_google_search import get_google_search_tool
                search_tool = get_google_search_tool()
                if search_tool:
                    tools.append(search_tool)
                    logger.info(f"[TaskExecutor] Added Google Search tool")

            elif tool_id_lower == "file_search":
                # File Search tool
                from app.mcp_server.tools_file_search import get_file_search_tool
                file_tool = get_file_search_tool(user_id)
                if file_tool:
                    tools.append(file_tool)
                    logger.info(f"[TaskExecutor] Added File Search tool")

            elif tool_id_lower == "notion":
                # Notion connector tool
                from app.connector_agents.notion_agent import create_notion_connector_tool
                notion_tool = await create_notion_connector_tool(user_id)
                if notion_tool:
                    tools.append(notion_tool)
                    logger.info(f"[TaskExecutor] Added Notion tool for user {user_id}")

            elif tool_id_lower == "gdrive":
                # Google Drive connector tool
                from app.connector_agents.gdrive_agent import create_gdrive_connector_tool
                gdrive_tool = await create_gdrive_connector_tool(user_id)
                if gdrive_tool:
                    tools.append(gdrive_tool)
                    logger.info(f"[TaskExecutor] Added Google Drive tool for user {user_id}")

            elif tool_id_lower == "retell_ai":
                # Retell AI connector tool
                from app.connector_agents.retellai_agent import create_retellai_connector_tool
                retell_tool = await create_retellai_connector_tool(user_id)
                if retell_tool:
                    tools.append(retell_tool)
                    logger.info(f"[TaskExecutor] Added Retell AI tool for user {user_id}")

            else:
                logger.warning(f"[TaskExecutor] Unknown tool ID: {tool_id}")

        except ImportError as e:
            logger.warning(f"[TaskExecutor] Could not import tool {tool_id}: {e}")
        except Exception as e:
            logger.warning(f"[TaskExecutor] Error creating tool {tool_id}: {e}")

    return tools
