"""
User MCP Connectors API Endpoints.

Provides REST endpoints for managing user's custom MCP server connections.
Requires authentication - users can only access their own connectors.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserMCPConnection
from app.routers.auth import get_current_user
from app.schemas import ConnectorCreateRequest, ConnectorResponse, ConnectorUpdateRequest
from app.connectors.validator import validate_mcp_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


# ============================================================================
# GET /api/connectors - List user's connectors
# ============================================================================

@router.get("")
async def list_connectors(
    active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    List all MCP connectors for the current user.

    Args:
        active: If provided, filter by is_active status

    Returns:
        List of user's connectors (without sensitive auth_config)
    """
    logger.info(f"Listing connectors for user {current_user.id} (active={active})")

    # Build query
    query = select(UserMCPConnection).where(
        UserMCPConnection.user_id == current_user.id
    )

    if active is not None:
        query = query.where(UserMCPConnection.is_active == active)

    query = query.order_by(UserMCPConnection.created_at.desc())

    result = await db.execute(query)
    connectors = result.scalars().all()

    # Convert to response format (hide auth_config)
    response_list = []
    for conn in connectors:
        response_list.append({
            "id": conn.id,
            "name": conn.name,
            "description": conn.description,
            "server_url": conn.server_url,
            "auth_type": conn.auth_type,
            "is_active": conn.is_active,
            "is_verified": conn.is_verified,
            "discovered_tools": conn.discovered_tools or [],
            "tool_count": conn.tool_count,
            "last_verified_at": conn.last_verified_at.isoformat() if conn.last_verified_at else None,
            "created_at": conn.created_at.isoformat() if conn.created_at else None,
            "updated_at": conn.updated_at.isoformat() if conn.updated_at else None,
        })

    logger.info(f"Returning {len(response_list)} connectors for user {current_user.id}")
    return response_list


# ============================================================================
# GET /api/connectors/{connector_id} - Get specific connector
# ============================================================================

@router.get("/{connector_id}")
async def get_connector(
    connector_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a specific connector by ID.

    Args:
        connector_id: Connector ID

    Returns:
        Connector details (without sensitive auth_config)

    Raises:
        HTTPException 404: If connector not found or belongs to another user
    """
    logger.info(f"Getting connector {connector_id} for user {current_user.id}")

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.id == connector_id,
            UserMCPConnection.user_id == current_user.id
        )
    )
    connector = result.scalar_one_or_none()

    if connector is None:
        logger.warning(f"Connector {connector_id} not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail="Connector not found")

    return {
        "id": connector.id,
        "name": connector.name,
        "description": connector.description,
        "server_url": connector.server_url,
        "auth_type": connector.auth_type,
        "is_active": connector.is_active,
        "is_verified": connector.is_verified,
        "discovered_tools": connector.discovered_tools or [],
        "tool_count": connector.tool_count,
        "last_verified_at": connector.last_verified_at.isoformat() if connector.last_verified_at else None,
        "created_at": connector.created_at.isoformat() if connector.created_at else None,
        "updated_at": connector.updated_at.isoformat() if connector.updated_at else None,
    }


# ============================================================================
# POST /api/connectors - Create new connector
# ============================================================================

@router.post("", status_code=201)
async def create_connector(
    request: ConnectorCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new MCP connector.

    Args:
        request: Connector creation request

    Returns:
        Created connector details

    Raises:
        HTTPException 400: If user already has 10 connectors
        HTTPException 422: If validation fails
    """
    logger.info(f"Creating connector '{request.name}' for user {current_user.id}")

    # Check connector limit (max 10 per user)
    count_result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == current_user.id
        )
    )
    existing_count = len(count_result.scalars().all())

    if existing_count >= 10:
        logger.warning(f"User {current_user.id} has reached connector limit (10)")
        raise HTTPException(
            status_code=400,
            detail="Maximum number of connectors (10) reached. Please delete an existing connector first."
        )

    # Encrypt auth_config if provided
    encrypted_config = None
    if request.auth_config:
        from app.connectors.encryption import encrypt_credentials
        encrypted_config = encrypt_credentials(request.auth_config)

    # Clean URL
    server_url = str(request.server_url).strip()

    # Validate and discover tools before saving
    validation_result = await validate_mcp_connection(
        server_url=server_url,
        auth_type=request.auth_type.value if hasattr(request.auth_type, 'value') else request.auth_type,
        auth_config=request.auth_config or {}
    )

    # Prepare discovered tools data
    discovered_tools = None
    is_verified = False
    last_verified_at = None

    if validation_result.success:
        is_verified = True
        last_verified_at = datetime.utcnow()
        if validation_result.tools:
            discovered_tools = validation_result.tools
        logger.info(f"Connector verified with {len(discovered_tools) if discovered_tools else 0} tools")
    else:
        logger.warning(f"Connector validation failed: {validation_result.error_message}")

    # Create connector (strip whitespace from URL)
    # Note: tool_count is a computed property, not set directly
    connector = UserMCPConnection(
        user_id=current_user.id,
        name=request.name.strip(),
        description=request.description,
        server_url=server_url,
        auth_type=request.auth_type.value if hasattr(request.auth_type, 'value') else request.auth_type,
        auth_config=encrypted_config,
        is_active=True,
        is_verified=is_verified,
        discovered_tools=discovered_tools,
        last_verified_at=last_verified_at,
    )

    db.add(connector)
    await db.commit()
    await db.refresh(connector)

    logger.info(f"Created connector {connector.id} for user {current_user.id} (verified={is_verified}, tools={connector.tool_count})")

    return {
        "id": connector.id,
        "name": connector.name,
        "description": connector.description,
        "server_url": connector.server_url,
        "auth_type": connector.auth_type,
        "is_active": connector.is_active,
        "is_verified": connector.is_verified,
        "discovered_tools": connector.discovered_tools or [],
        "tool_count": connector.tool_count,
        "last_verified_at": connector.last_verified_at.isoformat() if connector.last_verified_at else None,
        "created_at": connector.created_at.isoformat() if connector.created_at else None,
    }


# ============================================================================
# POST /api/connectors/test - Test connection before saving
# ============================================================================

class TestConnectionRequest(BaseModel):
    """Request to test an MCP connection."""
    server_url: str
    auth_type: str = "none"
    auth_config: Optional[Dict[str, Any]] = None


@router.post("/test")
async def test_connection(
    request: TestConnectionRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test an MCP connection before saving it.

    Args:
        request: Connection test request with URL and optional auth

    Returns:
        Connection test result with discovered tools or error details
    """
    # Strip whitespace from URL (common copy-paste issue)
    server_url = request.server_url.strip()
    logger.info(f"Testing connection to '{server_url}' for user {current_user.id}")

    try:
        result = await validate_mcp_connection(
            server_url=server_url,
            auth_type=request.auth_type,
            auth_config=request.auth_config or {}
        )

        # ValidationResult is a dataclass, access via attributes not dict
        if result.success:
            tool_count = len(result.tools) if result.tools else 0
            logger.info(f"Connection test successful: {tool_count} tools found")
            return {
                "success": True,
                "message": f"Successfully connected and discovered {tool_count} tools",
                "tools": result.tools or [],
                "tool_count": tool_count,
            }
        else:
            logger.warning(f"Connection test failed: {result.error_message}")
            return {
                "success": False,
                "message": result.error_message or "Connection failed",
                "error_type": result.error_code or "connection_failed",
            }
    except Exception as e:
        logger.error(f"Connection test error: {str(e)}")
        return {
            "success": False,
            "message": str(e),
            "error_type": "unexpected_error",
        }


# ============================================================================
# PUT /api/connectors/{connector_id} - Update connector
# ============================================================================

@router.put("/{connector_id}")
async def update_connector(
    connector_id: int,
    request: ConnectorUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update an existing connector.

    Args:
        connector_id: Connector ID to update
        request: Updated connector data

    Returns:
        Updated connector details

    Raises:
        HTTPException 404: If connector not found
    """
    logger.info(f"Updating connector {connector_id} for user {current_user.id}")

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.id == connector_id,
            UserMCPConnection.user_id == current_user.id
        )
    )
    connector = result.scalar_one_or_none()

    if connector is None:
        raise HTTPException(status_code=404, detail="Connector not found")

    # Update fields if provided
    if request.name is not None:
        connector.name = request.name
    if request.description is not None:
        connector.description = request.description

    connector.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(connector)

    logger.info(f"Updated connector {connector_id}")

    return {
        "id": connector.id,
        "name": connector.name,
        "description": connector.description,
        "server_url": connector.server_url,
        "auth_type": connector.auth_type,
        "is_active": connector.is_active,
        "is_verified": connector.is_verified,
        "discovered_tools": connector.discovered_tools or [],
        "tool_count": connector.tool_count,
        "updated_at": connector.updated_at.isoformat() if connector.updated_at else None,
    }


# ============================================================================
# POST /api/connectors/{connector_id}/verify - Verify/Re-verify connector
# ============================================================================

@router.post("/{connector_id}/verify")
async def verify_connector(
    connector_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verify or re-verify an existing connector.

    Connects to the MCP server, discovers tools, and updates verification status.

    Args:
        connector_id: Connector ID to verify

    Returns:
        Updated connector with verification status and discovered tools

    Raises:
        HTTPException 404: If connector not found
    """
    logger.info(f"Verifying connector {connector_id} for user {current_user.id}")

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.id == connector_id,
            UserMCPConnection.user_id == current_user.id
        )
    )
    connector = result.scalar_one_or_none()

    if connector is None:
        raise HTTPException(status_code=404, detail="Connector not found")

    # Validate connection and discover tools
    validation_result = await validate_mcp_connection(
        server_url=connector.server_url,
        auth_type=connector.auth_type,
        auth_config={}  # TODO: decrypt auth_config if needed
    )

    if validation_result.success:
        connector.is_verified = True
        connector.last_verified_at = datetime.utcnow()
        connector.discovered_tools = validation_result.tools or []
        # Note: tool_count is a computed property from discovered_tools
        connector.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(connector)

        logger.info(f"Connector {connector_id} verified with {connector.tool_count} tools")

        return {
            "success": True,
            "message": f"Connector verified successfully with {connector.tool_count} tools",
            "connector": {
                "id": connector.id,
                "name": connector.name,
                "description": connector.description,
                "server_url": connector.server_url,
                "auth_type": connector.auth_type,
                "is_active": connector.is_active,
                "is_verified": connector.is_verified,
                "discovered_tools": connector.discovered_tools or [],
                "tool_count": connector.tool_count,
                "last_verified_at": connector.last_verified_at.isoformat() if connector.last_verified_at else None,
            }
        }
    else:
        connector.is_verified = False
        connector.updated_at = datetime.utcnow()
        await db.commit()

        logger.warning(f"Connector {connector_id} verification failed: {validation_result.error_message}")

        return {
            "success": False,
            "message": validation_result.error_message or "Verification failed",
            "error_type": validation_result.error_code or "verification_failed",
        }


# ============================================================================
# DELETE /api/connectors/{connector_id} - Delete connector
# ============================================================================

@router.delete("/{connector_id}", status_code=204)
async def delete_connector(
    connector_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a connector.

    Args:
        connector_id: Connector ID to delete

    Raises:
        HTTPException 404: If connector not found
    """
    logger.info(f"Deleting connector {connector_id} for user {current_user.id}")

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.id == connector_id,
            UserMCPConnection.user_id == current_user.id
        )
    )
    connector = result.scalar_one_or_none()

    if connector is None:
        raise HTTPException(status_code=404, detail="Connector not found")

    await db.delete(connector)
    await db.commit()

    logger.info(f"Deleted connector {connector_id}")


# ============================================================================
# POST /api/connectors/{connector_id}/toggle - Toggle active status
# ============================================================================

class ToggleRequest(BaseModel):
    """Request to toggle connector active status."""
    is_active: bool


@router.post("/{connector_id}/toggle")
async def toggle_connector(
    connector_id: int,
    request: ToggleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Set a connector's active status.

    Args:
        connector_id: Connector ID to update
        request: New active status

    Returns:
        Updated connector with new active status

    Raises:
        HTTPException 404: If connector not found
    """
    logger.info(f"Setting connector {connector_id} is_active={request.is_active} for user {current_user.id}")

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.id == connector_id,
            UserMCPConnection.user_id == current_user.id
        )
    )
    connector = result.scalar_one_or_none()

    if connector is None:
        raise HTTPException(status_code=404, detail="Connector not found")

    connector.is_active = request.is_active
    connector.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(connector)

    logger.info(f"Toggled connector {connector_id} to is_active={connector.is_active}")

    return {
        "id": connector.id,
        "name": connector.name,
        "description": connector.description,
        "server_url": connector.server_url,
        "auth_type": connector.auth_type,
        "is_active": connector.is_active,
        "is_verified": connector.is_verified,
        "discovered_tools": connector.discovered_tools or [],
        "tool_count": connector.tool_count,
        "last_verified_at": connector.last_verified_at.isoformat() if connector.last_verified_at else None,
        "created_at": connector.created_at.isoformat() if connector.created_at else None,
        "updated_at": connector.updated_at.isoformat() if connector.updated_at else None,
    }


# ============================================================================
# GET /api/connectors/{connector_id}/health - Health check (real-time status)
# ============================================================================

@router.get("/{connector_id}/health")
async def health_check_connector(
    connector_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Perform a real-time health check on a connector.

    Tests actual connection to the MCP server WITHOUT modifying database.
    Use this to get current connection status (e.g., OAuth token validity).

    Args:
        connector_id: Connector ID to check

    Returns:
        Health status with is_healthy, error details if unhealthy

    Raises:
        HTTPException 404: If connector not found
    """
    logger.info(f"Health check for connector {connector_id} by user {current_user.id}")

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.id == connector_id,
            UserMCPConnection.user_id == current_user.id
        )
    )
    connector = result.scalar_one_or_none()

    if connector is None:
        raise HTTPException(status_code=404, detail="Connector not found")

    # Decrypt auth config if present
    auth_config = {}
    if connector.auth_config:
        from app.connectors.encryption import decrypt_credentials
        auth_config = decrypt_credentials(connector.auth_config)
        logger.info(f"[Health Check] Decrypted auth config for {connector.name}, keys: {list(auth_config.keys())}")

    # Use longer timeout for OAuth connectors (Notion MCP needs 30s)
    timeout = 30.0 if connector.auth_type == "oauth" else 15.0
    logger.info(f"[Health Check] Testing {connector.name} with timeout={timeout}s, auth_type={connector.auth_type}")

    # Test connection
    try:
        validation_result = await validate_mcp_connection(
            server_url=connector.server_url,
            auth_type=connector.auth_type,
            auth_config=auth_config,
            timeout=timeout
        )

        if validation_result.success:
            tool_count = len(validation_result.tools) if validation_result.tools else 0
            logger.info(f"Connector {connector_id} health check: HEALTHY ({tool_count} tools)")
            return {
                "is_healthy": True,
                "connector_id": connector.id,
                "connector_name": connector.name,
                "tool_count": tool_count,
                "message": f"Connected successfully with {tool_count} tools"
            }
        else:
            logger.warning(f"Connector {connector_id} health check: UNHEALTHY - {validation_result.error_message}")
            return {
                "is_healthy": False,
                "connector_id": connector.id,
                "connector_name": connector.name,
                "error_code": validation_result.error_code or "connection_failed",
                "error_message": validation_result.error_message or "Connection failed",
                "message": validation_result.error_message or "Connection failed"
            }
    except Exception as e:
        logger.error(f"Connector {connector_id} health check exception: {e}")
        return {
            "is_healthy": False,
            "connector_id": connector.id,
            "connector_name": connector.name,
            "error_code": "exception",
            "error_message": str(e),
            "message": f"Health check failed: {str(e)}"
        }


# ============================================================================
# POST /api/connectors/{connector_id}/refresh - Refresh tools from server
# ============================================================================

@router.post("/{connector_id}/refresh")
async def refresh_connector(
    connector_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Refresh a connector's tools by re-validating the connection.

    Args:
        connector_id: Connector ID to refresh

    Returns:
        Updated connector with refreshed tools

    Raises:
        HTTPException 404: If connector not found
        HTTPException 400: If connection validation fails
    """
    logger.info(f"Refreshing connector {connector_id} for user {current_user.id}")

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.id == connector_id,
            UserMCPConnection.user_id == current_user.id
        )
    )
    connector = result.scalar_one_or_none()

    if connector is None:
        raise HTTPException(status_code=404, detail="Connector not found")

    # Decrypt auth config if present
    auth_config = {}
    if connector.auth_config:
        from app.connectors.encryption import decrypt_credentials
        auth_config = decrypt_credentials(connector.auth_config)

    # Validate connection and discover tools
    try:
        validation_result = await validate_mcp_connection(
            server_url=connector.server_url,
            auth_type=connector.auth_type,
            auth_config=auth_config
        )
    except Exception as e:
        logger.error(f"Refresh failed for connector {connector_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")

    # ValidationResult is a dataclass - access via attributes
    if not validation_result.success:
        connector.is_verified = False
        connector.updated_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(status_code=400, detail=validation_result.error_message or "Connection failed")

    # Update connector with new tools (tool_count is computed property)
    connector.discovered_tools = validation_result.tools or []
    connector.is_verified = True
    connector.last_verified_at = datetime.utcnow()
    connector.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(connector)

    logger.info(f"Refreshed connector {connector_id}: {connector.tool_count} tools")

    return {
        "id": connector.id,
        "name": connector.name,
        "is_verified": connector.is_verified,
        "discovered_tools": connector.discovered_tools or [],
        "tool_count": connector.tool_count,
        "last_verified_at": connector.last_verified_at.isoformat() if connector.last_verified_at else None,
    }
