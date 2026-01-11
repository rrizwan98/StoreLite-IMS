"""
Task Executor Service - Scheduled Task Execution

Executes scheduled tasks using the Schema Query Agent.
Called by APScheduler at the scheduled time.

SIMPLIFIED FLOW:
1. Load task from database
2. Create ChatKit thread for results
3. Call schema_agent's chat function directly (same as ChatKit uses)
4. Save result to thread and update task

This uses the SAME schema_agent that ChatKit uses, ensuring
all connector tools (gdrive, gmail, notion, etc.) work correctly.
"""

import logging
import json
import uuid
from datetime import datetime, timezone


from typing import Optional, List, Any, Dict
from urllib.parse import urlparse, parse_qs


def _utc_now_naive() -> datetime:
    """
    Get current UTC time as naive datetime (without timezone info).
    PostgreSQL TIMESTAMP WITHOUT TIME ZONE columns require naive datetimes.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

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

    SIMPLIFIED FLOW:
    1. Load task from DB
    2. Create new ChatKit thread
    3. Use SAME schema_agent logic that ChatKit uses (with all connector tools)
    4. Save result to thread
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

            # 4. Use the SAME schema_agent that ChatKit uses
            # This ensures all connector tools (gdrive, gmail, notion, etc.) work correctly
            from app.agents.schema_query_agent import create_schema_query_agent, get_scheduler_llm_model
            from app.connector_agents import get_connector_agent_tools

            # Get connector tools the same way ChatKit does (requires db session)
            connector_tools = await get_connector_agent_tools(db, task.user_id)
            logger.info(f"[TaskExecutor] Got {len(connector_tools)} connector tools from registry")

            # Create agent with all connector tools (same as ChatKit)
            agent = await create_schema_query_agent(
                database_uri=connection.database_uri,
                schema_metadata=connection.schema_metadata or {},
                user_id=task.user_id,
                thread_id=thread_id,
                connector_tools=connector_tools,
                model_getter=get_scheduler_llm_model,  # Use scheduler-specific model
            )

            # Build query with tool hints so agent knows which tools user wants to use
            tool_hints = _build_tool_hints(task.selected_tools or [])
            enhanced_query = f"{tool_hints}\n\n{task.query}" if tool_hints else task.query

            logger.info(f"[TaskExecutor] Running agent with query: {enhanced_query[:200]}...")

            # Run the query (same as ChatKit's agent.query())
            result = await agent.query(enhanced_query, thread_id=thread_id)

            # 5. Save messages to ChatKit thread for viewing in UI
            response_text = result.get("response", "")

            # Create user message item
            user_msg_id = f"user-{uuid.uuid4().hex[:12]}"
            user_msg_content = {
                "id": user_msg_id,
                "type": "user_message",
                "thread_id": thread_id,
                "created_at": _utc_now_naive().isoformat(),
                "content": [{"type": "input_text", "text": task.query}],
                "attachments": [],
                "inference_options": {}
            }
            user_msg_item = ChatKitThreadItem(
                id=user_msg_id,
                thread_id=thread_id,
                item_type="user_message",
                content=json.dumps(user_msg_content),
                created_at=_utc_now_naive(),
            )
            db.add(user_msg_item)

            # Create assistant message item
            assistant_msg_id = f"assistant-{uuid.uuid4().hex[:12]}"
            assistant_msg_content = {
                "id": assistant_msg_id,
                "type": "assistant_message",
                "thread_id": thread_id,
                "created_at": _utc_now_naive().isoformat(),
                "content": [{"type": "output_text", "text": response_text, "annotations": []}]
            }
            assistant_msg_item = ChatKitThreadItem(
                id=assistant_msg_id,
                thread_id=thread_id,
                item_type="assistant_message",
                content=json.dumps(assistant_msg_content),
                created_at=_utc_now_naive(),
            )
            db.add(assistant_msg_item)

            # Update thread's updated_at
            chatkit_thread.updated_at = _utc_now_naive()

            # 7. Update task with results
            task.status = "completed"
            # thread_id already set earlier
            task.result_summary = response_text[:500]  # First 500 chars
            # Use naive UTC datetime for PostgreSQL TIMESTAMP WITHOUT TIME ZONE
            task.executed_at = _utc_now_naive()

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
                                    "created_at": _utc_now_naive().isoformat(),
                                    "content": [{"type": "input_text", "text": task.query}],
                                    "attachments": [],
                                    "inference_options": {}
                                }),
                                created_at=_utc_now_naive(),
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
                                    "created_at": _utc_now_naive().isoformat(),
                                    "content": [{"type": "output_text", "text": f"❌ **Task Failed**\n\nError: {error_message}", "annotations": []}]
                                }),
                                created_at=_utc_now_naive(),
                            )
                            db.add(error_msg_item)
                        except Exception as thread_error:
                            logger.warning(f"[TaskExecutor] Could not save error to thread: {thread_error}")

                    task.status = "failed"
                    task.error_message = error_message
                    task.executed_at = _utc_now_naive()
                    await db.commit()
            except Exception as commit_error:
                logger.error(f"[TaskExecutor] Failed to update task status: {commit_error}")

        finally:
            await engine.dispose()


def _build_tool_hints(selected_tool_ids: List[str]) -> str:
    """
    Build a natural language hint for the agent about which tools to use.

    This tells the agent which specific tools the user wants for this task,
    so it prioritizes those tools in its response.

    Args:
        selected_tool_ids: List of tool IDs (e.g., ["gmail", "gdrive", "analytics"])

    Returns:
        A hint string to prepend to the user's query
    """
    if not selected_tool_ids:
        return ""

    # Map tool IDs to their descriptions
    tool_descriptions = {
        "gmail": "Gmail (for sending emails)",
        "gdrive": "Google Drive (for accessing files)",
        "notion": "Notion (for accessing pages/databases)",
        "analytics": "Analytics (for generating charts/visualizations)",
        "google_search": "Google Search (for web searches)",
        "file_search": "File Search (for searching uploaded files)",
        "retell_ai": "Retell AI (for voice calls)",
        "export": "Export (for exporting data)",
    }

    # Build tool list
    tool_names = []
    for tool_id in selected_tool_ids:
        tool_id_lower = tool_id.lower()
        if tool_id_lower in tool_descriptions:
            tool_names.append(tool_descriptions[tool_id_lower])
        else:
            tool_names.append(tool_id)

    tools_str = ", ".join(tool_names)

    hint = f"""[SCHEDULED TASK - TOOL INSTRUCTIONS]
This is a scheduled task. The user has specifically selected these tools: {tools_str}

Please use the selected tools to complete the task. For example:
- If "Google Drive" is selected, use the google_drive_connector tool
- If "Gmail" is selected, use the gmail_connector tool
- If "Notion" is selected, use the notion_connector tool
- If "Analytics" is selected, generate visualizations/charts

USER'S QUERY:"""

    logger.info(f"[TaskExecutor] Built tool hints for: {selected_tool_ids}")
    return hint
