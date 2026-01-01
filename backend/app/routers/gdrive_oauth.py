"""
Google Drive MCP OAuth Router

Implements OAuth 2.0 flow for Google Drive integration.
Uses standard Google OAuth with PKCE for security.

Flow:
1. User clicks "Connect Google Drive"
2. Backend generates authorization URL with PKCE
3. User is redirected to Google's OAuth consent page
4. User authorizes, Google redirects back with code
5. Backend exchanges code for access token
6. Token is stored encrypted, Schema Agent can access Google Drive

Note: Requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env
"""

import os
import secrets
import logging
import httpx
import hashlib
import base64
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserMCPConnection
from app.routers.auth import get_current_user
from app.connectors.encryption import encrypt_credentials

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gdrive", tags=["google-drive"])

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GDRIVE_REDIRECT_URI = os.getenv("GDRIVE_REDIRECT_URI", "http://localhost:8000/gdrive/callback")

# Frontend URL for redirects
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Google OAuth Endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# Google Drive MCP Server URL (placeholder - we'll use the access token directly)
GDRIVE_MCP_URL = "gdrive://mcp"

# Required OAuth Scopes
GOOGLE_SCOPES = [
    "openid",
    "email",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# In-memory state storage (use Redis in production)
oauth_states: Dict[str, Dict] = {}


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

class GDriveConnectResponse(BaseModel):
    """Response with OAuth authorization URL."""
    authorization_url: str
    state: str


class GDriveCallbackResponse(BaseModel):
    """Response after OAuth callback."""
    success: bool
    connector_id: Optional[int] = None
    connector_name: Optional[str] = None
    email: Optional[str] = None
    message: str


# ============================================================================
# GET /api/gdrive/config - Check OAuth configuration
# ============================================================================

@router.get("/config")
async def check_gdrive_config():
    """
    Check if Google Drive OAuth is configured.
    This is a public endpoint (no auth required).
    """
    is_configured = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

    return {
        "configured": is_configured,
        "connector_name": "Google Drive",
        "error": None if is_configured else "Google Drive OAuth credentials not configured. Please add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env"
    }


# ============================================================================
# POST /api/gdrive/connect - Start OAuth flow
# ============================================================================

@router.post("/connect", response_model=GDriveConnectResponse)
async def connect_gdrive(
    current_user: User = Depends(get_current_user)
):
    """
    Start Google Drive OAuth flow.

    Returns authorization URL for redirecting user to Google's consent page.
    """
    logger.info(f"[GDrive] Starting OAuth for user {current_user.id}")

    # Check if OAuth is configured
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=400,
            detail="Google Drive OAuth is not configured. Please contact administrator."
        )

    # Callback URL - uses frontend callback page
    redirect_uri = f"{FRONTEND_URL}/connectors/callback/google_drive"

    # Generate PKCE pair
    code_verifier, code_challenge = generate_pkce_pair()

    # Generate state token
    state = secrets.token_urlsafe(32)

    # Store OAuth state
    oauth_states[state] = {
        "user_id": current_user.id,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Build authorization URL
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",  # Get refresh token
        "prompt": "consent",  # Force consent to get refresh token
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    authorization_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    logger.info(f"[GDrive] Authorization URL generated for user {current_user.id}")

    return GDriveConnectResponse(
        authorization_url=authorization_url,
        state=state
    )


# ============================================================================
# POST /api/gdrive/callback - Handle OAuth callback
# ============================================================================

@router.post("/callback")
async def gdrive_oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State token"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle OAuth callback and exchange code for token.

    Called by the frontend after user completes OAuth on Google.
    """
    logger.info(f"[GDrive] OAuth callback received")
    logger.info(f"[GDrive] State: {state[:16]}... (truncated)")
    logger.info(f"[GDrive] Available states in memory: {len(oauth_states)}")

    # Validate state - use get first, pop only on success
    state_data = oauth_states.get(state)
    if not state_data:
        logger.error(f"[GDrive] State not found in memory!")
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state. Please try connecting again. (Backend may have restarted)"
        )

    user_id = state_data["user_id"]
    redirect_uri = state_data["redirect_uri"]
    code_verifier = state_data["code_verifier"]

    logger.info(f"[GDrive] State valid for user_id={user_id}")

    # Exchange code for tokens
    token_request = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code_verifier": code_verifier,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Exchange code for token
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data=token_request,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if token_response.status_code != 200:
                logger.error(f"[GDrive] Token exchange failed: {token_response.status_code} - {token_response.text}")
                raise HTTPException(
                    status_code=400,
                    detail="Failed to complete authorization. Please try again."
                )

            token_data = token_response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")

            logger.info(f"[GDrive] Token obtained, has_refresh={bool(refresh_token)}")

            # Get user info to get email
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            user_info = {}
            if userinfo_response.status_code == 200:
                user_info = userinfo_response.json()
                logger.info(f"[GDrive] User email: {user_info.get('email', 'unknown')}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[GDrive] Token exchange error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to complete authorization."
            )

    # Save connector to database
    try:
        connector = await save_gdrive_connector(
            db=db,
            user_id=user_id,
            token_data=token_data,
            user_info=user_info
        )

        email = user_info.get("email", "")

        # Only pop state after successful save
        oauth_states.pop(state, None)
        logger.info(f"[GDrive] Successfully connected Google Drive for user {user_id}, email={email}")

        return {
            "success": True,
            "connector_id": connector.id,
            "connector_name": connector.name,
            "email": email,
            "message": f"Successfully connected to Google Drive ({email})!"
        }

    except Exception as e:
        logger.error(f"[GDrive] Failed to save connector: {e}")
        raise HTTPException(
            status_code=500,
            detail="Connected to Google but failed to save. Please try again."
        )


# ============================================================================
# Helper Functions
# ============================================================================

async def save_gdrive_connector(
    db: AsyncSession,
    user_id: int,
    token_data: Dict[str, Any],
    user_info: Dict[str, Any]
) -> UserMCPConnection:
    """Save Google Drive connector to database."""

    # Check if connector already exists - get all matching and clean up duplicates
    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == user_id,
            UserMCPConnection.server_url == GDRIVE_MCP_URL
        ).order_by(UserMCPConnection.id.desc())  # Most recent first
    )
    existing_connectors = result.scalars().all()

    # Clean up duplicates - keep only the most recent one
    existing = None
    if existing_connectors:
        existing = existing_connectors[0]  # Keep the most recent
        # Delete any duplicates
        for duplicate in existing_connectors[1:]:
            logger.info(f"[GDrive] Removing duplicate connector {duplicate.id}")
            await db.delete(duplicate)

    # Prepare auth config
    auth_config = {
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "token_type": token_data.get("token_type", "Bearer"),
        "expires_in": token_data.get("expires_in"),
        "scope": token_data.get("scope"),
        "email": user_info.get("email"),
        "name": user_info.get("name"),
        "picture": user_info.get("picture"),
    }

    encrypted_config = encrypt_credentials(auth_config)

    # Clean connector name (without email)
    connector_name = "Google Drive"
    connector_email = user_info.get("email") or None  # None if empty

    # Discovered tools for Google Drive MCP
    # These are the standard tools available via Google Drive MCP
    gdrive_tools = [
        {"name": "gdrive_search", "description": "Search for files in Google Drive"},
        {"name": "gdrive_read_file", "description": "Read contents of a file from Google Drive"},
        {"name": "gdrive_list_files", "description": "List files in Google Drive"},
        {"name": "gdrive_get_file_info", "description": "Get metadata about a file"},
    ]

    if existing:
        # Update existing
        existing.name = connector_name
        existing.email = connector_email
        existing.auth_config = encrypted_config
        existing.is_active = True
        existing.is_verified = True
        existing.last_verified_at = datetime.utcnow()
        existing.updated_at = datetime.utcnow()
        existing.discovered_tools = gdrive_tools
        await db.commit()
        await db.refresh(existing)
        logger.info(f"[GDrive] Updated existing connector {existing.id}")
        return existing

    # Create new
    connector = UserMCPConnection(
        user_id=user_id,
        name=connector_name,
        email=connector_email,
        description="Connected via Google OAuth",
        server_url=GDRIVE_MCP_URL,
        auth_type="oauth",
        auth_config=encrypted_config,
        is_active=True,
        is_verified=True,
        last_verified_at=datetime.utcnow(),
        discovered_tools=gdrive_tools,
    )

    db.add(connector)
    await db.commit()
    await db.refresh(connector)

    logger.info(f"[GDrive] Created new connector {connector.id}")
    return connector


# ============================================================================
# GET /api/gdrive/status - Check connection status
# ============================================================================

@router.get("/status")
async def get_gdrive_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if user has Google Drive connected."""

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == current_user.id,
            UserMCPConnection.server_url == GDRIVE_MCP_URL,
            UserMCPConnection.is_active == True
        ).order_by(UserMCPConnection.id.desc())  # Get most recent
    )
    connector = result.scalars().first()  # Use first() to handle duplicates

    if connector:
        return {
            "connected": True,
            "connector_id": connector.id,
            "connector_name": connector.name,
            "last_verified": connector.last_verified_at.isoformat() if connector.last_verified_at else None
        }

    return {"connected": False}


# ============================================================================
# DELETE /api/gdrive/disconnect - Disconnect Google Drive
# ============================================================================

@router.delete("/disconnect")
async def disconnect_gdrive(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect Google Drive - removes ALL GDrive connectors for user."""

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == current_user.id,
            UserMCPConnection.server_url == GDRIVE_MCP_URL
        )
    )
    connectors = result.scalars().all()  # Get all duplicates

    if not connectors:
        raise HTTPException(status_code=404, detail="Google Drive not connected")

    # Delete all GDrive connectors (cleanup duplicates)
    for connector in connectors:
        await db.delete(connector)
    await db.commit()

    logger.info(f"[GDrive] Disconnected {len(connectors)} connector(s) for user {current_user.id}")

    return {"success": True, "message": "Google Drive disconnected successfully"}


# ============================================================================
# POST /api/gdrive/refresh - Refresh access token
# ============================================================================

@router.post("/refresh")
async def refresh_gdrive_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Refresh Google Drive access token using refresh token."""

    from app.connectors.encryption import decrypt_credentials

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == current_user.id,
            UserMCPConnection.server_url == GDRIVE_MCP_URL,
            UserMCPConnection.is_active == True
        )
    )
    connector = result.scalar_one_or_none()

    if not connector:
        raise HTTPException(status_code=404, detail="Google Drive not connected")

    # Decrypt auth config
    try:
        auth_config = decrypt_credentials(connector.auth_config)
    except Exception as e:
        logger.error(f"[GDrive] Failed to decrypt auth config: {e}")
        raise HTTPException(status_code=500, detail="Failed to decrypt credentials")

    refresh_token = auth_config.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token available. Please reconnect.")

    # Request new access token
    token_request = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data=token_request,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code != 200:
                logger.error(f"[GDrive] Token refresh failed: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=400,
                    detail="Failed to refresh token. Please reconnect."
                )

            token_data = response.json()

            # Update auth config with new token
            auth_config["access_token"] = token_data.get("access_token")
            if token_data.get("refresh_token"):
                auth_config["refresh_token"] = token_data["refresh_token"]
            auth_config["expires_in"] = token_data.get("expires_in")

            # Save updated config
            connector.auth_config = encrypt_credentials(auth_config)
            connector.last_verified_at = datetime.utcnow()
            await db.commit()

            # Clear cached agent so it picks up new token
            try:
                from app.connector_agents.registry import get_registry
                get_registry().clear_cache(connector.id)
                logger.info(f"[GDrive] Cleared agent cache for connector {connector.id}")
            except Exception as cache_error:
                logger.warning(f"[GDrive] Could not clear cache: {cache_error}")

            logger.info(f"[GDrive] Token refreshed for user {current_user.id}")

            return {"success": True, "message": "Token refreshed successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[GDrive] Token refresh error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to refresh token."
            )
