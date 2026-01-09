"""
Scheduler Router - API endpoints for task scheduling

Provides endpoints for:
- Creating scheduled tasks
- Listing user's scheduled tasks
- Getting task details
- Cancelling pending tasks
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, ScheduledTask, UserConnection
from app.routers.auth import get_current_user
from app.services.scheduler_service import get_scheduler
from app.services.task_executor_service import execute_scheduled_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class CreateTaskRequest(BaseModel):
    """Request to create a scheduled task."""
    query: str = Field(..., min_length=1, max_length=2000, description="Natural language query for the agent")
    selected_tools: List[str] = Field(..., min_items=1, max_items=3, description="Tool IDs to use (max 3)")
    scheduled_time: datetime = Field(..., description="When to run the task (ISO 8601 format)")

    @validator('selected_tools')
    def validate_tools(cls, v):
        if len(v) > 3:
            raise ValueError('Maximum 3 tools allowed')
        if len(v) < 1:
            raise ValueError('At least 1 tool required')
        # Validate tool IDs
        valid_tools = {
            'gmail', 'analytics', 'google_search', 'file_search',
            'notion', 'gdrive', 'retell_ai', 'export'
        }
        for tool in v:
            if tool.lower() not in valid_tools:
                raise ValueError(f'Invalid tool ID: {tool}')
        return [t.lower() for t in v]

    @validator('scheduled_time')
    def validate_scheduled_time(cls, v):
        # Ensure time is in the future
        now = datetime.now(timezone.utc)
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v <= now:
            raise ValueError('Scheduled time must be in the future')
        # Convert to naive UTC datetime for PostgreSQL TIMESTAMP WITHOUT TIME ZONE
        # This avoids "can't subtract offset-naive and offset-aware datetimes" error
        return v.astimezone(timezone.utc).replace(tzinfo=None)


class TaskResponse(BaseModel):
    """Response for a scheduled task."""
    id: str
    query: str
    selected_tools: List[str]
    scheduled_time: datetime
    status: str
    thread_id: Optional[str] = None
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    executed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreateTaskResponse(BaseModel):
    """Response after creating a task."""
    task_id: str
    status: str
    scheduled_time: datetime
    message: str


class TaskListResponse(BaseModel):
    """Response for listing tasks."""
    tasks: List[TaskResponse]
    total: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/tasks", response_model=CreateTaskResponse)
async def create_scheduled_task(
    request: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new scheduled task.

    The task will run at the specified time using the Schema Agent
    with only the selected tools.
    """
    logger.info(f"[Scheduler] Creating task for user {current_user.id}")

    # Verify user has database connection (required for schema agent)
    conn_result = await db.execute(
        select(UserConnection).where(UserConnection.user_id == current_user.id)
    )
    connection = conn_result.scalar_one_or_none()

    if not connection or not connection.database_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database connection required. Please connect your database first."
        )

    if connection.connection_type != "schema_query_only":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduler is only available for schema_query_only users."
        )

    # Get scheduler
    scheduler = get_scheduler()
    if not scheduler or not scheduler.is_running:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scheduler service is not available. Please try again later."
        )

    # Create task in database
    task_id = str(uuid.uuid4())
    task = ScheduledTask(
        id=task_id,
        user_id=current_user.id,
        query=request.query,
        selected_tools=request.selected_tools,
        scheduled_time=request.scheduled_time,
        status="pending",
    )
    db.add(task)

    try:
        # Schedule with APScheduler
        job_id = await scheduler.schedule_task(
            task_id=task_id,
            run_time=request.scheduled_time,
            task_func=execute_scheduled_task,
        )

        # Update task with job ID
        task.apscheduler_job_id = job_id
        await db.commit()

        logger.info(f"[Scheduler] Task {task_id} created and scheduled for {request.scheduled_time}")

        return CreateTaskResponse(
            task_id=task_id,
            status="scheduled",
            scheduled_time=request.scheduled_time,
            message=f"Task scheduled successfully with {len(request.selected_tools)} tool(s)",
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"[Scheduler] Failed to create task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule task: {str(e)}"
        )


@router.get("/tasks", response_model=TaskListResponse)
async def list_scheduled_tasks(
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's scheduled tasks.

    Optional filter by status: pending, running, completed, failed, cancelled
    """
    query = select(ScheduledTask).where(
        ScheduledTask.user_id == current_user.id
    )

    if status_filter:
        valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
        if status_filter.lower() not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter. Must be one of: {valid_statuses}"
            )
        query = query.where(ScheduledTask.status == status_filter.lower())

    # Order by scheduled_time descending (newest first)
    query = query.order_by(desc(ScheduledTask.scheduled_time))
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    tasks = result.scalars().all()

    # Get total count
    count_query = select(ScheduledTask).where(
        ScheduledTask.user_id == current_user.id
    )
    if status_filter:
        count_query = count_query.where(ScheduledTask.status == status_filter.lower())
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_details(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get details of a specific scheduled task.

    Returns task configuration, status, and result (if completed).
    """
    result = await db.execute(
        select(ScheduledTask).where(
            ScheduledTask.id == task_id,
            ScheduledTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return TaskResponse.model_validate(task)


@router.delete("/tasks/{task_id}")
async def cancel_scheduled_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a pending scheduled task.

    Only pending tasks can be cancelled.
    """
    result = await db.execute(
        select(ScheduledTask).where(
            ScheduledTask.id == task_id,
            ScheduledTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task with status: {task.status}"
        )

    # Cancel in APScheduler
    scheduler = get_scheduler()
    if scheduler and scheduler.is_running:
        await scheduler.cancel_task(task_id)

    # Update status
    task.status = "cancelled"
    await db.commit()

    logger.info(f"[Scheduler] Task {task_id} cancelled by user {current_user.id}")

    return {"message": "Task cancelled successfully", "task_id": task_id}


@router.get("/tools")
async def get_available_tools(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of available tools for scheduling.

    Returns tools that the user can select for scheduled tasks.
    """
    # Base tools available to all users
    tools = [
        {
            "id": "analytics",
            "name": "Analytics",
            "description": "Generate charts and visualizations from query results",
            "icon": "chart",
            "available": True,
        },
        {
            "id": "google_search",
            "name": "Google Search",
            "description": "Search the web for real-time information",
            "icon": "globe",
            "available": True,
        },
        {
            "id": "file_search",
            "name": "File Search",
            "description": "Search through your uploaded files",
            "icon": "notebook",
            "available": True,
        },
    ]

    # Check for connected services
    conn_result = await db.execute(
        select(UserConnection).where(UserConnection.user_id == current_user.id)
    )
    connection = conn_result.scalar_one_or_none()

    if connection:
        # Gmail
        if connection.gmail_access_token:
            tools.append({
                "id": "gmail",
                "name": "Gmail",
                "description": "Send query results via email",
                "icon": "mail",
                "available": True,
            })

    # Check for MCP connectors (Notion, GDrive, etc.)
    from app.models import UserMCPConnection
    mcp_result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == current_user.id,
            UserMCPConnection.is_active == True,
            UserMCPConnection.is_verified == True,
        )
    )
    mcp_connections = mcp_result.scalars().all()

    for conn in mcp_connections:
        name_lower = conn.name.lower()
        if "notion" in name_lower:
            tools.append({
                "id": "notion",
                "name": "Notion",
                "description": "Save results to Notion pages or databases",
                "icon": "cube",
                "available": True,
            })
        elif "drive" in name_lower or "gdrive" in name_lower:
            tools.append({
                "id": "gdrive",
                "name": "Google Drive",
                "description": "Save results to Google Drive",
                "icon": "cloud",
                "available": True,
            })
        elif "retell" in name_lower:
            tools.append({
                "id": "retell_ai",
                "name": "Retell AI",
                "description": "Make voice calls based on results",
                "icon": "phone",
                "available": True,
            })

    return {"tools": tools}
