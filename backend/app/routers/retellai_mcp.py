"""
Retell AI MCP Connector API Endpoints.

Provides REST endpoints for connecting to Retell AI via API key.
Uses the Retell AI MCP server (@abhaybabbar/retellai-mcp-server) for operations.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserMCPConnection
from app.routers.auth import get_current_user
from app.connectors.encryption import encrypt_credentials, decrypt_credentials

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/retellai", tags=["retellai"])

# Retell AI MCP server URL marker (used to identify Retell AI connectors)
RETELL_AI_MCP_URL = "retellai://mcp"


# ============================================================================
# Request/Response Models
# ============================================================================

class ConnectRequest(BaseModel):
    """Request to connect Retell AI with API key."""
    api_key: str


class ConnectResponse(BaseModel):
    """Response after successful Retell AI connection."""
    success: bool
    connector_id: Optional[int] = None
    connector_name: Optional[str] = None
    message: str
    tool_count: int = 0
    tools: List[Dict[str, Any]] = []


class StatusResponse(BaseModel):
    """Retell AI connection status."""
    connected: bool
    connector_id: Optional[int] = None
    connector_name: Optional[str] = None
    tool_count: int = 0
    last_verified: Optional[str] = None


class TestConnectionRequest(BaseModel):
    """Request to test Retell AI API key."""
    api_key: str


class TestConnectionResponse(BaseModel):
    """Response from API key test."""
    success: bool
    message: str
    tool_count: int = 0
    tools: List[Dict[str, Any]] = []
    error_code: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

# Known Retell AI MCP tools (from @abhaybabbar/retellai-mcp-server documentation)
# We use these because tools/list has a Zod v4 compatibility bug in the MCP SDK
RETELL_AI_TOOLS = [
    {"name": "list_calls", "description": "List all calls from Retell AI"},
    {"name": "create_phone_call", "description": "Create an outbound phone call"},
    {"name": "create_web_call", "description": "Create a web-based call"},
    {"name": "get_call", "description": "Get details of a specific call"},
    {"name": "delete_call", "description": "Delete a call record"},
    {"name": "list_agents", "description": "List all voice agents"},
    {"name": "create_agent", "description": "Create a new voice agent"},
    {"name": "get_agent", "description": "Get details of a specific agent"},
    {"name": "update_agent", "description": "Update an existing agent"},
    {"name": "delete_agent", "description": "Delete a voice agent"},
    {"name": "get_agent_versions", "description": "Get version history of an agent"},
    {"name": "list_phone_numbers", "description": "List all phone numbers"},
    {"name": "create_phone_number", "description": "Provision a new phone number"},
    {"name": "get_phone_number", "description": "Get details of a phone number"},
    {"name": "update_phone_number", "description": "Update a phone number"},
    {"name": "delete_phone_number", "description": "Delete a phone number"},
    {"name": "list_voices", "description": "List available voices"},
    {"name": "get_voice", "description": "Get details of a specific voice"},
]


def _run_mcp_server_sync(api_key: str) -> Dict[str, Any]:
    """
    Run MCP server synchronously using subprocess.
    This is needed because Windows doesn't support asyncio subprocess well.

    Instead of using tools/list (which has a Zod v4 bug), we:
    1. Initialize the MCP server
    2. Call list_agents tool to validate the API key
    3. Return the known tools list if successful
    """
    import subprocess

    print(f"[RetellAI] Starting MCP server validation...")
    print(f"[RetellAI] API key length: {len(api_key)}, starts with: {api_key[:8]}...")

    env = {**dict(os.environ), "RETELL_API_KEY": api_key}

    try:
        # Start the MCP server process
        process = subprocess.Popen(
            ["npx", "-y", "@abhaybabbar/retellai-mcp-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            shell=True,  # Needed for Windows to find npx
        )

        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "id": 1,
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "IMS-Agent", "version": "1.0"}
            }
        }

        logger.info("[RetellAI] Sending initialize request...")
        process.stdin.write((json.dumps(init_request) + "\n").encode())
        process.stdin.flush()

        # Read initialize response
        init_response = process.stdout.readline()

        if not init_response:
            stderr = process.stderr.read().decode()
            logger.error(f"[RetellAI] No init response. Stderr: {stderr[:500]}")
            process.terminate()
            return {
                "success": False,
                "error_code": "NO_RESPONSE",
                "error_message": f"MCP server did not respond. {stderr[:200]}"
            }

        init_data = json.loads(init_response.decode())
        print(f"[RetellAI] Init response: {str(init_data)[:200]}")

        if "error" in init_data:
            error = init_data["error"]
            process.terminate()
            return {
                "success": False,
                "error_code": "INIT_ERROR",
                "error_message": f"Init failed: {error.get('message', str(error))}"
            }

        # Send initialized notification (required by MCP protocol)
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        logger.info("[RetellAI] Sending initialized notification...")
        process.stdin.write((json.dumps(initialized_notification) + "\n").encode())
        process.stdin.flush()

        # Validate API key by calling list_agents tool
        # This actually hits the Retell AI API and will fail if API key is invalid
        call_tool_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 2,
            "params": {
                "name": "list_agents",
                "arguments": {}
            }
        }

        logger.info("[RetellAI] Calling list_agents to validate API key...")
        process.stdin.write((json.dumps(call_tool_request) + "\n").encode())
        process.stdin.flush()

        # Read tool call response
        tool_response = process.stdout.readline()

        if not tool_response:
            logger.error("[RetellAI] No tool response")
            process.terminate()
            return {
                "success": False,
                "error_code": "NO_RESPONSE",
                "error_message": "MCP server did not respond to tool call"
            }

        tool_data = json.loads(tool_response.decode())
        print(f"[RetellAI] Tool response: {str(tool_data)[:500]}")

        # Terminate process
        process.terminate()

        if "error" in tool_data:
            error = tool_data["error"]
            error_msg = error.get('message', str(error)) if isinstance(error, dict) else str(error)
            print(f"[RetellAI] Tool error: {error_msg}")

            # Check for auth errors (401, 403, unauthorized, invalid key, etc.)
            error_lower = str(error_msg).lower()

            # Be more specific - only treat actual auth errors as auth failures
            if any(x in error_lower for x in ["401", "403", "unauthorized", "authentication"]):
                return {
                    "success": False,
                    "error_code": "AUTH_FAILED",
                    "error_message": "Invalid API key. Please check your Retell AI API key."
                }

            # For other errors (like "invalid" in different context), return the actual message
            return {
                "success": False,
                "error_code": "TOOL_ERROR",
                "error_message": f"Tool call failed: {error_msg}"
            }

        # Check result for authentication errors in content
        result = tool_data.get("result", {})
        content = result.get("content", [])
        print(f"[RetellAI] Result: {result}")
        print(f"[RetellAI] Content length: {len(content) if content else 0}")

        # Check if isError flag is set
        if result.get("isError") == True:
            error_content = ""
            if content and isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        error_content = item.get("text", "")
                        break
            print(f"[RetellAI] Tool returned isError=True: {error_content}")

            # Check for specific auth errors
            error_lower = error_content.lower()
            if any(x in error_lower for x in ["401", "403", "unauthorized", "invalid api key"]):
                return {
                    "success": False,
                    "error_code": "AUTH_FAILED",
                    "error_message": "Invalid API key. Please check your Retell AI API key."
                }
            return {
                "success": False,
                "error_code": "API_ERROR",
                "error_message": error_content or "API call failed"
            }

        # If we have content with data, the API key is valid!
        if content and isinstance(content, list) and len(content) > 0:
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text", "")
                    # If we got JSON array or object data, it's a success
                    if text.startswith("[") or text.startswith("{"):
                        print(f"[RetellAI] SUCCESS! Got valid data response")
                        print(f"[RetellAI] API key validated. Returning {len(RETELL_AI_TOOLS)} known tools.")
                        return {
                            "success": True,
                            "tools": RETELL_AI_TOOLS
                        }

        # Success! API key is valid (even if empty response)
        print(f"[RetellAI] API key validated. Returning {len(RETELL_AI_TOOLS)} known tools.")

        return {
            "success": True,
            "tools": RETELL_AI_TOOLS
        }

    except subprocess.TimeoutExpired:
        logger.error("[RetellAI] Process timeout")
        return {
            "success": False,
            "error_code": "TIMEOUT",
            "error_message": "Connection timed out"
        }
    except json.JSONDecodeError as e:
        logger.error(f"[RetellAI] JSON decode error: {e}")
        return {
            "success": False,
            "error_code": "INVALID_RESPONSE",
            "error_message": "Invalid response from MCP server"
        }
    except FileNotFoundError:
        logger.error("[RetellAI] npx not found")
        return {
            "success": False,
            "error_code": "MISSING_DEPENDENCY",
            "error_message": "Node.js/npx not found. Please install Node.js."
        }
    except Exception as e:
        logger.error(f"[RetellAI] Error: {type(e).__name__}: {e}")
        return {
            "success": False,
            "error_code": "CONNECTION_FAILED",
            "error_message": f"Connection failed: {str(e)}"
        }


async def validate_retell_api_key(api_key: str) -> Dict[str, Any]:
    """
    Validate Retell AI API key by connecting to MCP server.

    Args:
        api_key: Retell AI API key to validate

    Returns:
        Dict with success, tools list, and error info if failed
    """
    logger.info("[RetellAI] Validating API key...")

    # Run synchronous subprocess in a thread pool to avoid blocking
    import concurrent.futures

    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor,
            _run_mcp_server_sync,
            api_key
        )

    return result


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/test", response_model=TestConnectionResponse)
async def test_connection(
    request: TestConnectionRequest,
    current_user: User = Depends(get_current_user)
) -> TestConnectionResponse:
    """
    Test Retell AI API key before saving.

    This validates the API key by connecting to the Retell AI MCP server
    and loading the available tools.
    """
    logger.info(f"[RetellAI] Testing API key for user {current_user.id}")

    if not request.api_key or not request.api_key.strip():
        return TestConnectionResponse(
            success=False,
            message="API key is required",
            error_code="MISSING_API_KEY"
        )

    # Validate the API key
    result = await validate_retell_api_key(request.api_key.strip())

    if result["success"]:
        tools = result.get("tools", [])
        return TestConnectionResponse(
            success=True,
            message=f"Successfully connected! Found {len(tools)} tools.",
            tool_count=len(tools),
            tools=tools
        )
    else:
        return TestConnectionResponse(
            success=False,
            message=result.get("error_message", "Connection failed"),
            error_code=result.get("error_code", "CONNECTION_FAILED")
        )


@router.post("/connect", response_model=ConnectResponse)
async def connect_retellai(
    request: ConnectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ConnectResponse:
    """
    Connect Retell AI with API key.

    This validates the API key, discovers tools, and creates a connector.
    """
    logger.info(f"[RetellAI] Connecting for user {current_user.id}")

    if not request.api_key or not request.api_key.strip():
        raise HTTPException(status_code=400, detail="API key is required")

    api_key = request.api_key.strip()

    # Validate the API key first
    result = await validate_retell_api_key(api_key)

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error_message", "Invalid API key")
        )

    tools = result.get("tools", [])

    # Check if user already has a Retell AI connector
    existing_query = select(UserMCPConnection).where(
        UserMCPConnection.user_id == current_user.id,
        UserMCPConnection.server_url == RETELL_AI_MCP_URL
    )
    existing_result = await db.execute(existing_query)
    existing_connector = existing_result.scalar_one_or_none()

    if existing_connector:
        # Update existing connector
        existing_connector.auth_config = encrypt_credentials({"api_key": api_key})
        existing_connector.discovered_tools = tools
        existing_connector.is_verified = True
        existing_connector.is_active = True
        existing_connector.last_verified_at = datetime.utcnow()
        existing_connector.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(existing_connector)

        logger.info(f"[RetellAI] Updated existing connector {existing_connector.id}")

        return ConnectResponse(
            success=True,
            connector_id=existing_connector.id,
            connector_name=existing_connector.name,
            message=f"Retell AI reconnected with {len(tools)} tools",
            tool_count=len(tools),
            tools=tools
        )

    # Check connector limit
    count_query = select(UserMCPConnection).where(
        UserMCPConnection.user_id == current_user.id
    )
    count_result = await db.execute(count_query)
    if len(count_result.scalars().all()) >= 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum number of connectors (10) reached."
        )

    # Create new connector
    connector = UserMCPConnection(
        user_id=current_user.id,
        name="Retell AI",
        description="AI Voice Agent for outbound phone calls",
        server_url=RETELL_AI_MCP_URL,
        auth_type="api_key",
        auth_config=encrypt_credentials({"api_key": api_key}),
        is_active=True,
        is_verified=True,
        discovered_tools=tools,
        last_verified_at=datetime.utcnow()
    )

    db.add(connector)
    await db.commit()
    await db.refresh(connector)

    logger.info(f"[RetellAI] Created connector {connector.id} with {len(tools)} tools")

    return ConnectResponse(
        success=True,
        connector_id=connector.id,
        connector_name=connector.name,
        message=f"Retell AI connected with {len(tools)} tools",
        tool_count=len(tools),
        tools=tools
    )


@router.get("/status", response_model=StatusResponse)
async def get_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> StatusResponse:
    """
    Check Retell AI connection status.
    """
    logger.info(f"[RetellAI] Checking status for user {current_user.id}")

    query = select(UserMCPConnection).where(
        UserMCPConnection.user_id == current_user.id,
        UserMCPConnection.server_url == RETELL_AI_MCP_URL
    )
    result = await db.execute(query)
    connector = result.scalar_one_or_none()

    if connector:
        return StatusResponse(
            connected=connector.is_verified and connector.is_active,
            connector_id=connector.id,
            connector_name=connector.name,
            tool_count=connector.tool_count,
            last_verified=connector.last_verified_at.isoformat() if connector.last_verified_at else None
        )

    return StatusResponse(connected=False)


@router.delete("/disconnect")
async def disconnect_retellai(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Disconnect Retell AI.
    """
    logger.info(f"[RetellAI] Disconnecting for user {current_user.id}")

    query = select(UserMCPConnection).where(
        UserMCPConnection.user_id == current_user.id,
        UserMCPConnection.server_url == RETELL_AI_MCP_URL
    )
    result = await db.execute(query)
    connector = result.scalar_one_or_none()

    if connector:
        await db.delete(connector)
        await db.commit()
        logger.info(f"[RetellAI] Deleted connector {connector.id}")
        return {"success": True, "message": "Retell AI disconnected"}

    return {"success": True, "message": "Retell AI was not connected"}


@router.post("/refresh")
async def refresh_retellai(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Refresh Retell AI tools by re-validating the connection.
    """
    logger.info(f"[RetellAI] Refreshing for user {current_user.id}")

    query = select(UserMCPConnection).where(
        UserMCPConnection.user_id == current_user.id,
        UserMCPConnection.server_url == RETELL_AI_MCP_URL
    )
    result = await db.execute(query)
    connector = result.scalar_one_or_none()

    if not connector:
        raise HTTPException(status_code=404, detail="Retell AI not connected")

    # Decrypt API key
    auth_config = decrypt_credentials(connector.auth_config)
    api_key = auth_config.get("api_key")

    if not api_key:
        raise HTTPException(status_code=400, detail="No API key found")

    # Validate and refresh tools
    result = await validate_retell_api_key(api_key)

    if not result["success"]:
        connector.is_verified = False
        connector.updated_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail=result.get("error_message", "Refresh failed")
        )

    tools = result.get("tools", [])

    # Update connector
    connector.discovered_tools = tools
    connector.is_verified = True
    connector.last_verified_at = datetime.utcnow()
    connector.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(connector)

    logger.info(f"[RetellAI] Refreshed connector {connector.id} with {len(tools)} tools")

    return {
        "success": True,
        "message": f"Refreshed {len(tools)} tools",
        "tool_count": len(tools),
        "tools": tools
    }
