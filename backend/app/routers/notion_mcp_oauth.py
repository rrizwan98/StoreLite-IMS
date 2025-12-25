"""
Notion MCP OAuth - Zero Configuration OAuth Flow

This implements OAuth with Notion's hosted MCP server (mcp.notion.com)
using Dynamic Client Registration (RFC 7591) - NO developer credentials needed!

How it works:
1. User clicks "Connect Notion"
2. We discover Notion MCP's OAuth metadata (RFC 8414)
3. We dynamically register as a client (RFC 7591)
4. User is redirected to Notion's OAuth page
5. User authorizes, Notion redirects back with code
6. We exchange code for token
7. Token is stored, Schema Agent can access Notion

This is exactly how ChatGPT, Cursor, and Claude connect to Notion!
"""

import os
import secrets
import logging
import httpx
import hashlib
import base64
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserMCPConnection
from app.routers.auth import get_current_user
from app.connectors.encryption import encrypt_credentials

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notion-mcp", tags=["notion-mcp"])

# Notion MCP Server URL
NOTION_MCP_URL = "https://mcp.notion.com"

# Frontend URL for redirects
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# In-memory state storage (use Redis in production)
oauth_states: Dict[str, Dict] = {}

# Cached OAuth metadata and client registration
_oauth_metadata: Optional[Dict] = None
_registered_client: Optional[Dict] = None


# ============================================================================
# OAuth Metadata Discovery (RFC 8414)
# ============================================================================

async def discover_oauth_metadata() -> Dict[str, Any]:
    """
    Discover OAuth server metadata from Notion MCP.

    RFC 8414: OAuth 2.0 Authorization Server Metadata

    Notion MCP (mcp.notion.com) supports Dynamic Client Registration!
    """
    global _oauth_metadata

    if _oauth_metadata:
        return _oauth_metadata

    # Notion MCP OAuth metadata endpoint
    metadata_url = f"{NOTION_MCP_URL}/.well-known/oauth-authorization-server"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"[Notion MCP] Discovering OAuth metadata from {metadata_url}")
            response = await client.get(metadata_url)
            if response.status_code == 200:
                _oauth_metadata = response.json()
                logger.info(f"[Notion MCP] OAuth metadata discovered successfully!")
                logger.info(f"[Notion MCP] Endpoints: auth={_oauth_metadata.get('authorization_endpoint')}, "
                           f"token={_oauth_metadata.get('token_endpoint')}, "
                           f"register={_oauth_metadata.get('registration_endpoint')}")
                return _oauth_metadata
        except Exception as e:
            logger.error(f"[Notion MCP] Failed to get metadata: {e}")

    # Fallback - use known Notion MCP endpoints (these are correct as of 2025)
    logger.warning("[Notion MCP] Metadata discovery failed, using fallback endpoints")
    _oauth_metadata = {
        "issuer": "https://mcp.notion.com",
        "authorization_endpoint": "https://mcp.notion.com/authorize",
        "token_endpoint": "https://mcp.notion.com/token",
        "registration_endpoint": "https://mcp.notion.com/register",
        "code_challenge_methods_supported": ["plain", "S256"],
    }
    return _oauth_metadata


# ============================================================================
# Dynamic Client Registration (RFC 7591)
# ============================================================================

async def register_oauth_client(redirect_uri: str) -> Dict[str, Any]:
    """
    Dynamically register as an OAuth client.

    RFC 7591: OAuth 2.0 Dynamic Client Registration
    """
    global _registered_client

    # Check if already registered for this redirect_uri
    if _registered_client and _registered_client.get("redirect_uri") == redirect_uri:
        return _registered_client

    metadata = await discover_oauth_metadata()
    registration_endpoint = metadata.get("registration_endpoint")

    if not registration_endpoint:
        logger.warning("[Notion MCP] No registration endpoint, DCR not supported")
        # Return None - we'll need static credentials
        return None

    # Register client
    client_metadata = {
        "client_name": "IMS Simple Inventory",
        "redirect_uris": [redirect_uri],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",  # Public client
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                registration_endpoint,
                json=client_metadata,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code in [200, 201]:
                _registered_client = response.json()
                _registered_client["redirect_uri"] = redirect_uri
                logger.info(f"[Notion MCP] Client registered: {_registered_client.get('client_id', 'unknown')[:8]}...")
                return _registered_client
            else:
                logger.error(f"[Notion MCP] Registration failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"[Notion MCP] Registration error: {e}")
            return None


# ============================================================================
# PKCE Helper Functions
# ============================================================================

def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code verifier and challenge."""
    # Generate random verifier (43-128 characters)
    code_verifier = secrets.token_urlsafe(64)[:128]

    # Create SHA256 hash and base64url encode
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")

    return code_verifier, code_challenge


# ============================================================================
# Request/Response Models
# ============================================================================

class NotionConnectResponse(BaseModel):
    """Response with OAuth authorization URL."""
    authorization_url: str
    state: str
    method: str  # 'dcr' or 'fallback'


# ============================================================================
# POST /api/notion-mcp/connect - Start OAuth flow
# ============================================================================

@router.post("/connect", response_model=NotionConnectResponse)
async def connect_notion(
    current_user: User = Depends(get_current_user)
):
    """
    Start Notion MCP OAuth flow.

    Uses Dynamic Client Registration if available, otherwise falls back
    to requiring static credentials.
    """
    logger.info(f"[Notion MCP] Starting OAuth for user {current_user.id}")

    # Callback URL
    redirect_uri = f"{FRONTEND_URL}/connectors/callback"

    # Try to discover metadata
    try:
        metadata = await discover_oauth_metadata()
    except Exception as e:
        logger.error(f"[Notion MCP] Metadata discovery failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Failed to connect to Notion. Please try again later."
        )

    # Try Dynamic Client Registration
    registered_client = await register_oauth_client(redirect_uri)

    if registered_client:
        client_id = registered_client["client_id"]
        method = "dcr"
        logger.info(f"[Notion MCP] Using DCR with client_id: {client_id[:8]}...")
    else:
        # Fall back to static credentials
        client_id = os.getenv("NOTION_OAUTH_CLIENT_ID", "")
        if not client_id:
            raise HTTPException(
                status_code=400,
                detail="Notion OAuth is not configured. Dynamic Client Registration not available and no static credentials provided."
            )
        method = "fallback"
        logger.info(f"[Notion MCP] Using static client_id: {client_id[:8]}...")

    # Generate PKCE pair
    code_verifier, code_challenge = generate_pkce_pair()

    # Generate state token
    state = secrets.token_urlsafe(32)

    # Store OAuth state
    oauth_states[state] = {
        "user_id": current_user.id,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
        "client_id": client_id,
        "method": method,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Build authorization URL
    auth_endpoint = metadata.get("authorization_endpoint", "https://mcp.notion.com/authorize")

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    authorization_url = f"{auth_endpoint}?{urlencode(params)}"

    logger.info(f"[Notion MCP] Authorization URL generated, method={method}")

    return NotionConnectResponse(
        authorization_url=authorization_url,
        state=state,
        method=method
    )


# ============================================================================
# POST /api/notion-mcp/callback - Handle OAuth callback
# ============================================================================

@router.post("/callback")
async def notion_oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State token"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle OAuth callback and exchange code for token.
    """
    logger.info(f"[Notion MCP] OAuth callback, state={state[:8]}...")

    # Validate state
    state_data = oauth_states.pop(state, None)
    if not state_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state. Please try connecting again."
        )

    user_id = state_data["user_id"]
    redirect_uri = state_data["redirect_uri"]
    code_verifier = state_data["code_verifier"]
    client_id = state_data["client_id"]
    method = state_data["method"]

    # Get token endpoint
    metadata = await discover_oauth_metadata()
    token_endpoint = metadata.get("token_endpoint", "https://mcp.notion.com/token")

    # Exchange code for token - MUST use form-urlencoded, not JSON!
    token_request = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
        "client_id": client_id,
    }

    # Add client authentication
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    if method == "fallback":
        # Use Basic auth for static credentials
        client_secret = os.getenv("NOTION_OAUTH_CLIENT_SECRET", "")
        if client_secret:
            credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                token_endpoint,
                data=token_request,  # Use 'data' for form-urlencoded, not 'json'
                headers=headers
            )

            if response.status_code != 200:
                logger.error(f"[Notion MCP] Token exchange failed: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=400,
                    detail="Failed to complete authorization. Please try again."
                )

            token_data = response.json()
            logger.info(f"[Notion MCP] Token response keys: {list(token_data.keys())}")
            logger.info(f"[Notion MCP] Token obtained for workspace: {token_data.get('workspace_name', 'unknown')}")

            # Debug: Log token info (first 20 chars only for security)
            if 'access_token' in token_data:
                token = token_data['access_token']
                logger.info(f"[Notion MCP] Access token received: {token[:20]}... (len={len(token)})")
            else:
                logger.warning(f"[Notion MCP] No access_token in response! Keys: {list(token_data.keys())}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[Notion MCP] Token exchange error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to complete authorization."
            )

    # Save connector to database
    try:
        connector = await save_notion_connector(
            db=db,
            user_id=user_id,
            token_data=token_data
        )

        # Try to discover and save tools
        try:
            from app.connectors.mcp_client import UserMCPClient
            client = UserMCPClient(
                "https://mcp.notion.com/mcp",
                timeout=30.0,
                auth_type="oauth",
                auth_config={"access_token": token_data.get("access_token")}
            )
            tools = await client.discover_tools()
            if tools:
                connector.discovered_tools = [
                    {"name": t.get("name"), "description": t.get("description", "")}
                    for t in tools
                ]
                await db.commit()
                logger.info(f"[Notion MCP] Discovered {len(tools)} tools")
        except Exception as e:
            logger.warning(f"[Notion MCP] Failed to discover tools: {e}")

        return {
            "success": True,
            "connector_id": connector.id,
            "connector_name": connector.name,
            "workspace_name": token_data.get("workspace_name"),
            "tools_count": len(connector.discovered_tools) if connector.discovered_tools else 0,
            "message": "Successfully connected to Notion!"
        }

    except Exception as e:
        logger.error(f"[Notion MCP] Failed to save connector: {e}")
        raise HTTPException(
            status_code=500,
            detail="Connected to Notion but failed to save. Please try again."
        )


# ============================================================================
# Helper Functions
# ============================================================================

async def save_notion_connector(
    db: AsyncSession,
    user_id: int,
    token_data: Dict[str, Any]
) -> UserMCPConnection:
    """Save Notion connector to database."""

    # Check if connector already exists
    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == user_id,
            UserMCPConnection.server_url == "https://mcp.notion.com/mcp"
        )
    )
    existing = result.scalar_one_or_none()

    # Prepare auth config
    auth_config = {
        "access_token": token_data.get("access_token"),
        "token_type": token_data.get("token_type", "bearer"),
        "bot_id": token_data.get("bot_id"),
        "workspace_id": token_data.get("workspace_id"),
        "workspace_name": token_data.get("workspace_name"),
    }

    encrypted_config = encrypt_credentials(auth_config)

    # Connector name
    workspace_name = token_data.get("workspace_name", "")
    connector_name = f"Notion - {workspace_name}" if workspace_name else "Notion"

    if existing:
        # Update existing
        existing.name = connector_name
        existing.auth_config = encrypted_config
        existing.is_active = True
        existing.is_verified = True
        existing.last_verified_at = datetime.utcnow()
        existing.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing

    # Create new
    connector = UserMCPConnection(
        user_id=user_id,
        name=connector_name,
        description="Connected via Notion MCP OAuth",
        server_url="https://mcp.notion.com/mcp",
        auth_type="oauth",
        auth_config=encrypted_config,
        is_active=True,
        is_verified=True,
        last_verified_at=datetime.utcnow(),
        discovered_tools=[],
    )

    db.add(connector)
    await db.commit()
    await db.refresh(connector)

    return connector


# ============================================================================
# GET /api/notion-mcp/status - Check connection status
# ============================================================================

@router.get("/status")
async def get_notion_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if user has Notion connected."""

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == current_user.id,
            UserMCPConnection.server_url == "https://mcp.notion.com/mcp",
            UserMCPConnection.is_active == True
        )
    )
    connector = result.scalar_one_or_none()

    if connector:
        return {
            "connected": True,
            "connector_id": connector.id,
            "connector_name": connector.name,
            "last_verified": connector.last_verified_at.isoformat() if connector.last_verified_at else None
        }

    return {"connected": False}


# ============================================================================
# DELETE /api/notion-mcp/disconnect - Disconnect Notion
# ============================================================================

@router.delete("/disconnect")
async def disconnect_notion(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect Notion."""

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == current_user.id,
            UserMCPConnection.server_url == "https://mcp.notion.com/mcp"
        )
    )
    connector = result.scalar_one_or_none()

    if not connector:
        raise HTTPException(status_code=404, detail="Notion not connected")

    await db.delete(connector)
    await db.commit()

    logger.info(f"[Notion MCP] Disconnected for user {current_user.id}")

    return {"success": True, "message": "Notion disconnected successfully"}
