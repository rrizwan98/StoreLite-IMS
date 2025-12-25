"""
OAuth Connectors API Endpoints.

Handles OAuth flows for predefined connectors like Notion.
Implements the OAuth 2.0 authorization code flow.

HOW IT WORKS (Like ChatGPT):
1. Developer creates ONE Public Integration on Notion Developer Portal
2. Developer saves client_id and client_secret in .env file
3. ANY user can click "Connect Notion" and authorize access
4. User's token is stored encrypted in database
5. Schema Agent uses that token to access user's Notion workspace

Setup Instructions:
1. Go to https://www.notion.so/profile/integrations
2. Click "New Integration"
3. Select "Public" as the type
4. Configure OAuth settings:
   - Redirect URI: http://localhost:3000/connectors/callback (dev)
   - Or your production frontend URL + /connectors/callback
5. Copy Client ID and Client Secret
6. Add to backend/.env:
   NOTION_OAUTH_CLIENT_ID=your_client_id
   NOTION_OAUTH_CLIENT_SECRET=your_client_secret
"""

import os
import secrets
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode, quote
import base64
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserMCPConnection
from app.routers.auth import get_current_user
from app.connectors.encryption import encrypt_credentials

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/oauth", tags=["oauth-connectors"])

# In-memory state storage (use Redis in production)
oauth_states: dict[str, dict] = {}

# Frontend URL for redirects
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# ============================================================================
# OAuth Configuration for Predefined Connectors
# ============================================================================

class OAuthConnectorConfig:
    """
    Configuration for OAuth-based connectors.

    These are PUBLIC integrations - one integration serves ALL users.
    Each user authorizes access to their own workspace.
    """

    NOTION = {
        "name": "Notion",
        # These come from YOUR Notion Public Integration
        "client_id": os.getenv("NOTION_OAUTH_CLIENT_ID", ""),
        "client_secret": os.getenv("NOTION_OAUTH_CLIENT_SECRET", ""),
        # Notion OAuth endpoints
        "authorization_url": "https://api.notion.com/v1/oauth/authorize",
        "token_url": "https://api.notion.com/v1/oauth/token",
        # Notion's official MCP server URL
        "mcp_server_url": "https://mcp.notion.com/mcp",
        # No scopes needed for Notion - permissions are set in integration settings
        "scopes": [],
    }

    @classmethod
    def get(cls, connector_id: str) -> Optional[dict]:
        """Get configuration for a connector by ID."""
        configs = {
            "notion": cls.NOTION,
        }
        return configs.get(connector_id.lower())

    @classmethod
    def is_configured(cls, connector_id: str) -> bool:
        """Check if a connector has valid OAuth credentials configured."""
        config = cls.get(connector_id)
        if not config:
            return False
        return bool(config.get("client_id")) and bool(config.get("client_secret"))


# ============================================================================
# Request/Response Models
# ============================================================================

class InitiateOAuthRequest(BaseModel):
    """Request to start OAuth flow."""
    connector_id: str
    redirect_uri: str


class InitiateOAuthResponse(BaseModel):
    """Response with OAuth authorization URL."""
    authorization_url: str
    state: str


class OAuthCallbackResponse(BaseModel):
    """Response after OAuth callback."""
    success: bool
    connector_id: Optional[int] = None
    connector_name: Optional[str] = None
    message: str


# ============================================================================
# GET /api/oauth/config/{connector_id} - Check if OAuth is configured
# ============================================================================

@router.get("/config/{connector_id}")
async def check_oauth_config(connector_id: str):
    """
    Check if OAuth is configured for a connector.
    This endpoint is public (no auth required) so frontend can check before showing connect button.
    """
    config = OAuthConnectorConfig.get(connector_id)
    if not config:
        return {"configured": False, "error": "Unknown connector"}

    is_configured = OAuthConnectorConfig.is_configured(connector_id)
    return {
        "configured": is_configured,
        "connector_name": config["name"],
        "error": None if is_configured else "OAuth credentials not configured. Please contact administrator."
    }


# ============================================================================
# POST /api/oauth/initiate - Start OAuth flow
# ============================================================================

@router.post("/initiate", response_model=InitiateOAuthResponse)
async def initiate_oauth(
    request: InitiateOAuthRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Initiate OAuth authorization flow for a predefined connector.

    This starts the OAuth 2.0 authorization code flow:
    1. Generate a secure state token (CSRF protection)
    2. Build the authorization URL with your Public Integration's client_id
    3. Return URL - frontend redirects user to Notion's OAuth page
    4. User logs in to Notion and grants permission
    5. Notion redirects back to our callback URL with authorization code

    Args:
        request: Contains connector_id and redirect_uri

    Returns:
        Authorization URL to redirect user to

    Raises:
        HTTPException 400: If connector not supported or not configured
    """
    connector_id = request.connector_id.lower()
    logger.info(f"[OAuth] Initiating OAuth for connector '{connector_id}' for user {current_user.id}")

    # Get connector configuration
    config = OAuthConnectorConfig.get(connector_id)
    if not config:
        raise HTTPException(
            status_code=400,
            detail=f"Connector '{connector_id}' is not supported for OAuth"
        )

    # Check if OAuth is configured
    if not OAuthConnectorConfig.is_configured(connector_id):
        logger.error(f"[OAuth] OAuth not configured for {connector_id}")
        raise HTTPException(
            status_code=400,
            detail=f"OAuth credentials not configured for {connector_id}. Please contact administrator."
        )

    # Generate secure state token (CSRF protection)
    state = secrets.token_urlsafe(32)

    # Store state with user info (expires in 10 minutes)
    # In production, use Redis with TTL
    oauth_states[state] = {
        "user_id": current_user.id,
        "connector_id": connector_id,
        "redirect_uri": request.redirect_uri,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Build Notion OAuth authorization URL
    # See: https://developers.notion.com/docs/authorization
    params = {
        "client_id": config["client_id"],
        "redirect_uri": request.redirect_uri,
        "response_type": "code",
        "owner": "user",  # Required by Notion
        "state": state,
    }

    authorization_url = f"{config['authorization_url']}?{urlencode(params)}"

    logger.info(f"[OAuth] Authorization URL generated for {connector_id}")
    logger.info(f"[OAuth] State: {state[:8]}..., Redirect URI: {request.redirect_uri}")

    return InitiateOAuthResponse(
        authorization_url=authorization_url,
        state=state
    )


# ============================================================================
# POST /api/oauth/exchange - Exchange authorization code for token
# ============================================================================

@router.post("/exchange")
async def exchange_oauth_code(
    connector_id: str = Query(..., description="Connector ID (e.g., 'notion')"),
    code: str = Query(..., description="Authorization code from OAuth provider"),
    state: str = Query(..., description="State token for verification"),
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange OAuth authorization code for access token.

    This endpoint is called by the frontend after user completes OAuth flow.
    The frontend receives the code and state from Notion's redirect, then
    calls this endpoint to complete the token exchange.

    Flow:
    1. User clicks "Connect Notion" → redirected to Notion OAuth
    2. User authorizes → Notion redirects to frontend /connectors/callback?code=xxx&state=xxx
    3. Frontend calls this endpoint with code and state
    4. We exchange code for token and save connector

    Args:
        connector_id: The connector ID (e.g., 'notion')
        code: Authorization code from OAuth provider
        state: State token for CSRF verification

    Returns:
        Success status with connector info
    """
    logger.info(f"[OAuth] Token exchange for {connector_id}, state={state[:8] if state else 'none'}...")

    # Validate state
    state_data = oauth_states.pop(state, None)
    if not state_data:
        logger.warning(f"[OAuth] Invalid or expired OAuth state: {state[:8] if state else 'none'}...")
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state. Please try connecting again."
        )

    # Verify connector ID matches
    if state_data["connector_id"] != connector_id.lower():
        logger.warning(f"[OAuth] Connector ID mismatch: {connector_id} vs {state_data['connector_id']}")
        raise HTTPException(
            status_code=400,
            detail="Connector mismatch. Please try connecting again."
        )

    user_id = state_data["user_id"]
    redirect_uri = state_data["redirect_uri"]

    # Get connector configuration
    config = OAuthConnectorConfig.get(connector_id)
    if not config:
        raise HTTPException(status_code=400, detail="Unknown connector")

    try:
        # Exchange code for access token
        token_response = await exchange_code_for_token(
            config=config,
            code=code,
            redirect_uri=redirect_uri
        )

        if not token_response:
            raise HTTPException(
                status_code=400,
                detail="Failed to exchange code for access token. Please try again."
            )

        # Create or update connector in database
        connector = await create_or_update_oauth_connector(
            db=db,
            user_id=user_id,
            connector_id=connector_id,
            config=config,
            access_token=token_response
        )

        logger.info(f"[OAuth] Connector created/updated: {connector.id} for user {user_id}")

        return {
            "success": True,
            "connector_id": connector.id,
            "connector_name": connector.name,
            "message": f"Successfully connected to {config['name']}!"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OAuth] Token exchange error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete OAuth: {str(e)}"
        )


# ============================================================================
# Helper Functions
# ============================================================================

async def exchange_code_for_token(
    config: dict,
    code: str,
    redirect_uri: str
) -> Optional[dict]:
    """
    Exchange authorization code for access token.

    Args:
        config: OAuth connector configuration
        code: Authorization code from provider
        redirect_uri: Redirect URI used in authorization

    Returns:
        Token response with access_token, or None if failed
    """
    # Create Basic auth header
    credentials = f"{config['client_id']}:{config['client_secret']}"
    encoded = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            config["token_url"],
            json=payload,
            headers=headers
        )

        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            return None

        data = response.json()
        logger.info(f"Token exchange successful, workspace: {data.get('workspace_name', 'unknown')}")

        return data


async def create_or_update_oauth_connector(
    db: AsyncSession,
    user_id: int,
    connector_id: str,
    config: dict,
    access_token: dict
) -> UserMCPConnection:
    """
    Create or update an OAuth-based connector.

    Args:
        db: Database session
        user_id: User ID
        connector_id: Connector ID (e.g., 'notion')
        config: Connector configuration
        access_token: Token response from OAuth provider

    Returns:
        Created or updated connector
    """
    # Check if connector already exists
    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == user_id,
            UserMCPConnection.server_url == config["mcp_server_url"]
        )
    )
    existing = result.scalar_one_or_none()

    # Prepare auth config with token
    auth_config = {
        "token": access_token.get("access_token"),
        "refresh_token": access_token.get("refresh_token"),
        "bot_id": access_token.get("bot_id"),
        "workspace_id": access_token.get("workspace_id"),
        "workspace_name": access_token.get("workspace_name"),
    }

    encrypted_config = encrypt_credentials(auth_config)

    if existing:
        # Update existing connector
        existing.auth_config = encrypted_config
        existing.is_active = True
        existing.is_verified = True
        existing.last_verified_at = datetime.utcnow()
        existing.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing

    # Create new connector
    connector_name = f"{config['name']}"
    workspace_name = access_token.get("workspace_name")
    if workspace_name:
        connector_name = f"{config['name']} - {workspace_name}"

    connector = UserMCPConnection(
        user_id=user_id,
        name=connector_name,
        description=f"Connected via OAuth to {config['name']}",
        server_url=config["mcp_server_url"],
        auth_type="oauth",
        auth_config=encrypted_config,
        is_active=True,
        is_verified=True,
        last_verified_at=datetime.utcnow(),
        discovered_tools=[],  # Will be populated on first use
    )

    db.add(connector)
    await db.commit()
    await db.refresh(connector)

    return connector


# ============================================================================
# GET /api/oauth/status/{connector_id} - Check OAuth connection status
# ============================================================================

@router.get("/status/{connector_id}")
async def check_oauth_status(
    connector_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Check if user has an OAuth connection for a specific connector.

    Args:
        connector_id: The connector ID (e.g., 'notion')

    Returns:
        Connection status and connector info if connected
    """
    config = OAuthConnectorConfig.get(connector_id)
    if not config:
        raise HTTPException(status_code=404, detail="Connector not found")

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == current_user.id,
            UserMCPConnection.server_url == config["mcp_server_url"],
            UserMCPConnection.is_active == True
        )
    )
    connector = result.scalar_one_or_none()

    if connector:
        return {
            "connected": True,
            "connector_id": connector.id,
            "connector_name": connector.name,
            "verified": connector.is_verified,
            "last_verified_at": connector.last_verified_at.isoformat() if connector.last_verified_at else None,
        }

    return {
        "connected": False,
    }


# ============================================================================
# DELETE /api/oauth/disconnect/{connector_id} - Disconnect OAuth
# ============================================================================

@router.delete("/disconnect/{connector_id}")
async def disconnect_oauth(
    connector_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Disconnect an OAuth connector.

    Args:
        connector_id: The connector ID (e.g., 'notion')

    Returns:
        Disconnection status
    """
    config = OAuthConnectorConfig.get(connector_id)
    if not config:
        raise HTTPException(status_code=404, detail="Connector not found")

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == current_user.id,
            UserMCPConnection.server_url == config["mcp_server_url"]
        )
    )
    connector = result.scalar_one_or_none()

    if not connector:
        raise HTTPException(status_code=404, detail="Connection not found")

    await db.delete(connector)
    await db.commit()

    logger.info(f"OAuth connector {connector_id} disconnected for user {current_user.id}")

    return {
        "success": True,
        "message": f"{config['name']} disconnected successfully"
    }
