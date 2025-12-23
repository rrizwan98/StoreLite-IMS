"""
System Tools API Endpoints.

Provides REST endpoints for viewing and managing available system tools (Gmail, Analytics, Export).
Includes connect/disconnect functionality for user tool status.
"""

import logging
from dataclasses import asdict
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models import User, UserToolStatus
from app.routers.auth import get_current_user, get_optional_user as auth_get_optional_user
from app.tools.registry import (
    get_all_system_tools,
    get_system_tool,
    get_enabled_tools,
    get_tools_by_category,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["tools"])


async def _get_user_tool_status(
    db: AsyncSession,
    user_id: int,
    tool_id: str
) -> tuple[bool, str | None]:
    """Get user's connection status for a specific tool."""
    result = await db.execute(
        select(UserToolStatus).where(
            UserToolStatus.user_id == user_id,
            UserToolStatus.tool_id == tool_id
        )
    )
    status = result.scalar_one_or_none()
    if status and status.is_connected:
        connected_at = status.connected_at.isoformat() if status.connected_at else None
        return True, connected_at
    return False, None


def _add_default_status(tool_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add default status fields to tool dict (for unauthenticated requests)."""
    tool_dict["is_connected"] = False
    tool_dict["config"] = None
    return tool_dict


# ============================================================================
# GET /api/tools - List all system tools
# ============================================================================

@router.get("")
async def list_tools(
    enabled: Optional[bool] = Query(None, description="Filter to only enabled, non-beta tools"),
    category: Optional[str] = Query(None, description="Filter by category (communication, insights, utilities)"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(auth_get_optional_user)
) -> List[Dict[str, Any]]:
    """
    List all available system tools with user-specific connection status.

    Args:
        enabled: If true, only return enabled non-beta tools
        category: Filter by tool category

    Returns:
        List of system tools matching filters, with is_connected based on user's status
    """
    logger.info(f"Listing system tools (enabled={enabled}, category={category}, user={current_user.id if current_user else 'anonymous'})")

    # Apply filters
    if enabled:
        tools = get_enabled_tools()
    elif category:
        tools = get_tools_by_category(category)
    else:
        tools = get_all_system_tools()

    # If both enabled and category, filter further
    if enabled and category:
        tools = [t for t in tools if t["category"] == category]

    # Add user-specific status if authenticated
    result_tools = []
    for tool in tools:
        tool_dict = dict(tool) if isinstance(tool, dict) else tool

        if current_user:
            # Get user's actual connection status
            is_connected, connected_at = await _get_user_tool_status(
                db, current_user.id, tool_dict["id"]
            )
            tool_dict["is_connected"] = is_connected
            tool_dict["connected_at"] = connected_at
            tool_dict["config"] = None
        else:
            # Anonymous user - show default status
            tool_dict = _add_default_status(tool_dict)

        result_tools.append(tool_dict)

    logger.info(f"Returning {len(result_tools)} system tools")
    return result_tools


# ============================================================================
# GET /api/tools/{tool_id} - Get specific tool by ID
# ============================================================================

@router.get("/{tool_id}")
async def get_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(auth_get_optional_user)
) -> Dict[str, Any]:
    """
    Get a specific system tool by ID.

    Args:
        tool_id: Tool identifier (e.g., 'gmail', 'analytics', 'export')

    Returns:
        Tool details with user-specific connection status

    Raises:
        HTTPException 404: If tool not found
    """
    logger.info(f"Getting system tool: {tool_id}")

    tool = get_system_tool(tool_id)
    if tool is None:
        logger.warning(f"System tool not found: {tool_id}")
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    # Convert dataclass to dict and add user-specific status
    tool_dict = asdict(tool)

    if current_user:
        is_connected, connected_at = await _get_user_tool_status(
            db, current_user.id, tool_id
        )
        tool_dict["is_connected"] = is_connected
        tool_dict["connected_at"] = connected_at
        tool_dict["config"] = None
    else:
        tool_dict = _add_default_status(tool_dict)

    return tool_dict


# ============================================================================
# POST /api/tools/{tool_id}/connect - Connect to a system tool
# ============================================================================

@router.post("/{tool_id}/connect")
async def connect_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Connect to a system tool.

    For tools with auth_type='none', this immediately marks the tool as connected.
    For OAuth tools, this returns a redirect URL for the OAuth flow.

    Args:
        tool_id: Tool identifier (e.g., 'gmail', 'analytics', 'export')

    Returns:
        Updated tool status with is_connected=True

    Raises:
        HTTPException 404: If tool not found
        HTTPException 400: If tool is beta/disabled
    """
    logger.info(f"Connecting tool {tool_id} for user {current_user.id}")

    tool = get_system_tool(tool_id)
    if tool is None:
        logger.warning(f"Tool not found: {tool_id}")
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    # Check if tool is enabled
    if not tool.is_enabled or tool.is_beta:
        raise HTTPException(
            status_code=400,
            detail=f"Tool '{tool_id}' is not available yet"
        )

    # Check for existing status
    result = await db.execute(
        select(UserToolStatus).where(
            UserToolStatus.user_id == current_user.id,
            UserToolStatus.tool_id == tool_id
        )
    )
    status = result.scalar_one_or_none()

    if status is None:
        # Create new status
        status = UserToolStatus(
            user_id=current_user.id,
            tool_id=tool_id,
            is_connected=True,
            connected_at=datetime.utcnow()
        )
        db.add(status)
    else:
        # Update existing status
        status.is_connected = True
        status.connected_at = datetime.utcnow()

    await db.commit()
    await db.refresh(status)

    logger.info(f"Connected tool {tool_id} for user {current_user.id}")

    # Return tool with updated status
    tool_dict = asdict(tool)
    tool_dict["is_connected"] = True
    tool_dict["connected_at"] = status.connected_at.isoformat() if status.connected_at else None

    # For OAuth tools, we'd return a redirect URL here
    if tool.auth_type == "oauth":
        tool_dict["oauth_redirect"] = f"/api/auth/{tool_id}/authorize"

    return tool_dict


# ============================================================================
# POST /api/tools/{tool_id}/disconnect - Disconnect from a system tool
# ============================================================================

@router.post("/{tool_id}/disconnect")
async def disconnect_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Disconnect from a system tool.

    Marks the tool as disconnected and clears any stored credentials.

    Args:
        tool_id: Tool identifier

    Returns:
        Updated tool status with is_connected=False

    Raises:
        HTTPException 404: If tool not found
    """
    logger.info(f"Disconnecting tool {tool_id} for user {current_user.id}")

    tool = get_system_tool(tool_id)
    if tool is None:
        logger.warning(f"Tool not found: {tool_id}")
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    # Update status
    result = await db.execute(
        select(UserToolStatus).where(
            UserToolStatus.user_id == current_user.id,
            UserToolStatus.tool_id == tool_id
        )
    )
    status = result.scalar_one_or_none()

    if status is not None:
        status.is_connected = False
        status.oauth_token = None
        status.token_expiry = None
        await db.commit()
        await db.refresh(status)

    logger.info(f"Disconnected tool {tool_id} for user {current_user.id}")

    # Return tool with updated status
    tool_dict = asdict(tool)
    tool_dict["is_connected"] = False
    tool_dict["connected_at"] = None

    return tool_dict
