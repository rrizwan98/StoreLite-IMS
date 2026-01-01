"""
Gmail MCP OAuth Router

Implements OAuth 2.0 flow for Gmail integration via MCP connector pattern.
Uses standard Google OAuth with PKCE for security.

Flow:
1. User clicks "Connect Gmail"
2. Backend generates authorization URL with PKCE
3. User is redirected to Google's OAuth consent page
4. User authorizes, Google redirects back with code
5. Backend exchanges code for access token
6. Token is stored encrypted, Schema Agent can access Gmail via sub-agent

Note: Requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env
"""

import os
import secrets
import logging
import httpx
import hashlib
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserMCPConnection, UserConnection
from app.routers.auth import get_current_user
from app.connectors.encryption import encrypt_credentials
from app.services.encryption_service import encrypt_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gmail", tags=["gmail-connector"])

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/gmail/callback")

# Frontend URL for redirects
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Google OAuth Endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# Gmail MCP Server URL (placeholder - we'll use the access token directly)
GMAIL_MCP_URL = "gmail://mcp"

# Required OAuth Scopes for Gmail
GMAIL_SCOPES = [
    "openid",
    "email",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
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

class GmailConnectResponse(BaseModel):
    """Response with OAuth authorization URL."""
    authorization_url: str
    state: str


class GmailCallbackResponse(BaseModel):
    """Response after OAuth callback."""
    success: bool
    connector_id: Optional[int] = None
    connector_name: Optional[str] = None
    email: Optional[str] = None
    message: str


# ============================================================================
# GET /api/gmail/config - Check OAuth configuration
# ============================================================================

@router.get("/config")
async def check_gmail_config():
    """
    Check if Gmail OAuth is configured.
    This is a public endpoint (no auth required).
    """
    is_configured = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

    return {
        "configured": is_configured,
        "connector_name": "Gmail",
        "error": None if is_configured else "Gmail OAuth credentials not configured. Please add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env"
    }


# ============================================================================
# POST /api/gmail/connect - Start OAuth flow
# ============================================================================

@router.post("/connect", response_model=GmailConnectResponse)
async def connect_gmail(
    current_user: User = Depends(get_current_user)
):
    """
    Start Gmail OAuth flow.

    Returns authorization URL for redirecting user to Google's consent page.
    """
    logger.info(f"[Gmail] Starting OAuth for user {current_user.id}")

    # Check if OAuth is configured
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=400,
            detail="Gmail OAuth is not configured. Please contact administrator."
        )

    # Callback URL - uses frontend callback page
    redirect_uri = f"{FRONTEND_URL}/connectors/callback/gmail"

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
        "scope": " ".join(GMAIL_SCOPES),
        "access_type": "offline",  # Get refresh token
        "prompt": "consent",  # Force consent to get refresh token
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    authorization_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    logger.info(f"[Gmail] Authorization URL generated for user {current_user.id}")

    return GmailConnectResponse(
        authorization_url=authorization_url,
        state=state
    )


# ============================================================================
# POST /api/gmail/callback - Handle OAuth callback
# ============================================================================

@router.post("/callback")
async def gmail_oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State token"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle OAuth callback and exchange code for token.

    Called by the frontend after user completes OAuth on Google.
    """
    logger.info(f"[Gmail] OAuth callback received")
    logger.info(f"[Gmail] State: {state[:16]}... (truncated)")
    logger.info(f"[Gmail] Code: {code[:20]}... (truncated)")
    logger.info(f"[Gmail] Available states in memory: {len(oauth_states)}")

    # Validate state - use get first, pop only on success
    state_data = oauth_states.get(state)
    if not state_data:
        logger.error(f"[Gmail] State not found in memory!")
        logger.error(f"[Gmail] Known states: {list(oauth_states.keys())[:3]}...")
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state. Please try connecting again. (State was cleared - backend may have restarted)"
        )

    user_id = state_data["user_id"]
    redirect_uri = state_data["redirect_uri"]
    code_verifier = state_data["code_verifier"]

    logger.info(f"[Gmail] State valid for user_id={user_id}")

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
                logger.error(f"[Gmail] Token exchange failed: {token_response.status_code} - {token_response.text}")
                raise HTTPException(
                    status_code=400,
                    detail="Failed to complete authorization. Please try again."
                )

            token_data = token_response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")

            logger.info(f"[Gmail] Token obtained, has_refresh={bool(refresh_token)}")

            # Get user info to get email
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            user_info = {}
            if userinfo_response.status_code == 200:
                user_info = userinfo_response.json()
                logger.info(f"[Gmail] User email: {user_info.get('email', 'unknown')}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[Gmail] Token exchange error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to complete authorization."
            )

    # Save connector to database
    try:
        connector = await save_gmail_connector(
            db=db,
            user_id=user_id,
            token_data=token_data,
            user_info=user_info
        )

        email = user_info.get("email", "")

        # Only pop state after successful save
        oauth_states.pop(state, None)
        logger.info(f"[Gmail] Successfully connected Gmail for user {user_id}, email={email}")

        return {
            "success": True,
            "connector_id": connector.id,
            "connector_name": connector.name,
            "email": email,
            "message": f"Successfully connected to Gmail ({email})!"
        }

    except Exception as e:
        logger.error(f"[Gmail] Failed to save connector: {e}")
        raise HTTPException(
            status_code=500,
            detail="Connected to Gmail but failed to save. Please try again."
        )


# ============================================================================
# Helper Functions
# ============================================================================

async def save_gmail_connector(
    db: AsyncSession,
    user_id: int,
    token_data: Dict[str, Any],
    user_info: Dict[str, Any]
) -> UserMCPConnection:
    """Save Gmail connector to database.

    IMPORTANT: Saves tokens to BOTH tables:
    - UserMCPConnection: For connector UI/management
    - UserConnection: For actual Gmail service to use tokens
    """

    # =========================================================================
    # STEP 1: Save to UserConnection (for gmail_service.py to use)
    # =========================================================================
    await _save_to_user_connection(db, user_id, token_data, user_info)

    # =========================================================================
    # STEP 2: Save to UserMCPConnection (for connector management UI)
    # =========================================================================
    # Check if connector already exists - get all matching and clean up duplicates
    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == user_id,
            UserMCPConnection.server_url == GMAIL_MCP_URL
        ).order_by(UserMCPConnection.id.desc())  # Most recent first
    )
    existing_connectors = result.scalars().all()

    # Clean up duplicates - keep only the most recent one
    existing = None
    if existing_connectors:
        existing = existing_connectors[0]  # Keep the most recent
        # Delete any duplicates
        for duplicate in existing_connectors[1:]:
            logger.info(f"[Gmail] Removing duplicate connector {duplicate.id}")
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
    connector_name = "Gmail"
    connector_email = user_info.get("email") or None  # None if empty

    # Discovered tools for Gmail MCP
    # These are the standard tools available via Gmail sub-agent
    gmail_tools = [
        {"name": "gmail_send", "description": "Send an email via Gmail"},
        {"name": "gmail_status", "description": "Check Gmail connection status"},
        {"name": "gmail_read_inbox", "description": "Read recent emails from inbox"},
        {"name": "gmail_search", "description": "Search for emails"},
        {"name": "gmail_get_message", "description": "Get full email content by message ID"},
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
        existing.discovered_tools = gmail_tools
        await db.commit()
        await db.refresh(existing)
        logger.info(f"[Gmail] Updated existing connector {existing.id}")
        return existing

    # Create new
    connector = UserMCPConnection(
        user_id=user_id,
        name=connector_name,
        email=connector_email,
        description="Connected via Google OAuth",
        server_url=GMAIL_MCP_URL,
        auth_type="oauth",
        auth_config=encrypted_config,
        is_active=True,
        is_verified=True,
        last_verified_at=datetime.utcnow(),
        discovered_tools=gmail_tools,
    )

    db.add(connector)
    await db.commit()
    await db.refresh(connector)

    logger.info(f"[Gmail] Created new connector {connector.id}")
    return connector


async def _save_to_user_connection(
    db: AsyncSession,
    user_id: int,
    token_data: Dict[str, Any],
    user_info: Dict[str, Any]
) -> None:
    """
    Save Gmail tokens to UserConnection table.
    This is required for gmail_service.py which reads tokens from UserConnection.
    """
    # Get or create UserConnection
    result = await db.execute(
        select(UserConnection).where(UserConnection.user_id == user_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        logger.warning(f"[Gmail] No UserConnection found for user {user_id}, creating one")
        connection = UserConnection(
            user_id=user_id,
            connection_type="schema_query_only",
            connection_mode="schema_query",
        )
        db.add(connection)
        await db.flush()

    # Calculate token expiry (naive datetime for TIMESTAMP WITHOUT TIME ZONE)
    expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
    token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

    # Get scopes
    scope_str = token_data.get("scope", "")
    scopes = scope_str.split() if scope_str else [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ]

    # Update Gmail fields (encrypted)
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if access_token:
        connection.gmail_access_token = encrypt_token(access_token)
    if refresh_token:
        connection.gmail_refresh_token = encrypt_token(refresh_token)

    # Use naive datetime for database (TIMESTAMP WITHOUT TIME ZONE)
    connection.gmail_token_expiry = token_expiry
    connection.gmail_email = user_info.get("email")
    connection.gmail_connected_at = datetime.utcnow()
    connection.gmail_scopes = scopes

    logger.info(f"[Gmail] Saved tokens to UserConnection for user {user_id}, email={user_info.get('email')}")


# ============================================================================
# GET /api/gmail/status - Check connection status
# ============================================================================

@router.get("/status")
async def get_gmail_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if user has Gmail connected."""

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == current_user.id,
            UserMCPConnection.server_url == GMAIL_MCP_URL,
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
# DELETE /api/gmail/disconnect - Disconnect Gmail
# ============================================================================

@router.delete("/disconnect")
async def disconnect_gmail(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect Gmail - removes ALL Gmail connectors for user."""

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == current_user.id,
            UserMCPConnection.server_url == GMAIL_MCP_URL
        )
    )
    connectors = result.scalars().all()  # Get all duplicates

    if not connectors:
        raise HTTPException(status_code=404, detail="Gmail not connected")

    # Delete all Gmail connectors (cleanup duplicates)
    for connector in connectors:
        await db.delete(connector)
    await db.commit()

    logger.info(f"[Gmail] Disconnected {len(connectors)} connector(s) for user {current_user.id}")

    return {"success": True, "message": "Gmail disconnected successfully"}


# ============================================================================
# POST /api/gmail/refresh - Refresh access token
# ============================================================================

@router.post("/refresh")
async def refresh_gmail_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Refresh Gmail access token using refresh token."""

    from app.connectors.encryption import decrypt_credentials

    result = await db.execute(
        select(UserMCPConnection).where(
            UserMCPConnection.user_id == current_user.id,
            UserMCPConnection.server_url == GMAIL_MCP_URL,
            UserMCPConnection.is_active == True
        )
    )
    connector = result.scalar_one_or_none()

    if not connector:
        raise HTTPException(status_code=404, detail="Gmail not connected")

    # Decrypt auth config
    try:
        auth_config = decrypt_credentials(connector.auth_config)
    except Exception as e:
        logger.error(f"[Gmail] Failed to decrypt auth config: {e}")
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
                logger.error(f"[Gmail] Token refresh failed: {response.status_code} - {response.text}")
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

            # Save updated config to UserMCPConnection
            connector.auth_config = encrypt_credentials(auth_config)
            connector.last_verified_at = datetime.utcnow()

            # Also update UserConnection table (for gmail_service.py)
            user_info = {"email": auth_config.get("email", "")}
            await _save_to_user_connection(db, current_user.id, token_data, user_info)

            await db.commit()

            # Clear cached agent so it picks up new token
            try:
                from app.connector_agents.registry import get_registry
                get_registry().clear_cache(connector.id)
                logger.info(f"[Gmail] Cleared agent cache for connector {connector.id}")
            except Exception as cache_error:
                logger.warning(f"[Gmail] Could not clear cache: {cache_error}")

            logger.info(f"[Gmail] Token refreshed for user {current_user.id}")

            return {"success": True, "message": "Token refreshed successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[Gmail] Token refresh error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to refresh token."
            )
