"""
Gmail OAuth2 Router - API endpoints for Gmail integration.
Handles OAuth2 flow, connection status, and email sending.
"""

import os
import secrets
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.routers.auth import get_current_user
from app.services.gmail_oauth_service import (
    get_gmail_oauth_service,
    GmailOAuthError,
    GmailNotConnectedError,
    GmailTokenError,
)
from app.services.gmail_service import (
    get_gmail_service,
    GmailSendError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/gmail",
    tags=["gmail"],
    responses={401: {"description": "Not authenticated"}},
)

# In-memory state storage for OAuth (use Redis in production)
_oauth_states: dict[str, dict] = {}

# Environment
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# ============================================================================
# Pydantic Models
# ============================================================================

class GmailAuthorizeResponse(BaseModel):
    """Response for authorize endpoint"""
    authorization_url: str
    state: str


class GmailStatusResponse(BaseModel):
    """Response for status endpoint"""
    connected: bool
    email: Optional[str] = None
    connected_at: Optional[str] = None
    recipient_email: Optional[str] = None


class UpdateRecipientRequest(BaseModel):
    """Request to update recipient email"""
    email: EmailStr


class UpdateRecipientResponse(BaseModel):
    """Response for update recipient endpoint"""
    success: bool
    email: str


class SendEmailRequest(BaseModel):
    """Request to send email"""
    to: Optional[EmailStr] = None
    subject: str
    body: str
    content_type: str = "text/plain"


class SendEmailResponse(BaseModel):
    """Response for send email endpoint"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class DisconnectResponse(BaseModel):
    """Response for disconnect endpoint"""
    success: bool
    message: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/authorize", response_model=GmailAuthorizeResponse)
async def authorize_gmail(
    current_user: User = Depends(get_current_user),
):
    """
    Initiate Gmail OAuth2 authorization flow.

    Returns authorization URL to redirect user to Google consent screen.
    """
    try:
        oauth_service = get_gmail_oauth_service()

        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state with user_id (expires in 10 minutes)
        _oauth_states[state] = {
            "user_id": current_user.id,
            "created_at": datetime.utcnow().timestamp(),
        }

        # Clean up old states (older than 10 minutes)
        current_time = datetime.utcnow().timestamp()
        expired_states = [
            s for s, data in _oauth_states.items()
            if current_time - data["created_at"] > 600
        ]
        for s in expired_states:
            del _oauth_states[s]

        authorization_url = oauth_service.get_authorization_url(state)

        logger.info(f"Gmail authorization initiated for user {current_user.id}")

        return GmailAuthorizeResponse(
            authorization_url=authorization_url,
            state=state,
        )

    except GmailOAuthError as e:
        logger.error(f"Gmail OAuth error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/callback")
async def gmail_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State token for CSRF validation"),
    error: Optional[str] = Query(None, description="Error from OAuth"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle OAuth2 callback from Google.

    Exchanges authorization code for tokens and saves to database.
    Redirects to frontend with success/error status.
    """
    # Handle OAuth errors
    if error:
        logger.warning(f"OAuth callback received error: {error}")
        redirect_url = f"{FRONTEND_URL}/dashboard?gmail_error={error}"
        return RedirectResponse(url=redirect_url)

    # Validate state
    if state not in _oauth_states:
        logger.warning(f"Invalid OAuth state: {state[:8]}...")
        redirect_url = f"{FRONTEND_URL}/dashboard?gmail_error=invalid_state"
        return RedirectResponse(url=redirect_url)

    state_data = _oauth_states.pop(state)
    user_id = state_data["user_id"]

    # Check state expiration (10 minutes)
    if datetime.utcnow().timestamp() - state_data["created_at"] > 600:
        logger.warning(f"Expired OAuth state for user {user_id}")
        redirect_url = f"{FRONTEND_URL}/dashboard?gmail_error=expired_state"
        return RedirectResponse(url=redirect_url)

    try:
        oauth_service = get_gmail_oauth_service()

        # Exchange code for tokens
        token_data = await oauth_service.exchange_code_for_tokens(code)

        # Save tokens to database
        await oauth_service.save_tokens_to_db(db, user_id, token_data)

        logger.info(f"Gmail connected successfully for user {user_id}")

        # Redirect to frontend with success
        redirect_url = f"{FRONTEND_URL}/dashboard?gmail_connected=true"
        return RedirectResponse(url=redirect_url)

    except GmailTokenError as e:
        logger.error(f"Token exchange failed for user {user_id}: {e}")
        error_msg = str(e).replace(" ", "_")[:50]  # URL-safe error
        redirect_url = f"{FRONTEND_URL}/dashboard?gmail_error={error_msg}"
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        logger.error(f"OAuth callback error for user {user_id}: {e}")
        redirect_url = f"{FRONTEND_URL}/dashboard?gmail_error=server_error"
        return RedirectResponse(url=redirect_url)


@router.get("/status", response_model=GmailStatusResponse)
async def get_gmail_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get Gmail connection status for current user.

    Returns whether Gmail is connected and associated email.
    """
    gmail_service = get_gmail_service()
    status = await gmail_service.get_gmail_status(db, current_user.id)

    return GmailStatusResponse(
        connected=status["connected"],
        email=status.get("email"),
        connected_at=status.get("connected_at"),
        recipient_email=status.get("recipient_email"),
    )


@router.delete("/disconnect", response_model=DisconnectResponse)
async def disconnect_gmail(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Disconnect Gmail account for current user.

    Revokes tokens with Google and clears from database.
    """
    try:
        oauth_service = get_gmail_oauth_service()
        success = await oauth_service.disconnect_gmail(db, current_user.id)

        if success:
            logger.info(f"Gmail disconnected for user {current_user.id}")
            return DisconnectResponse(
                success=True,
                message="Gmail disconnected successfully",
            )
        else:
            return DisconnectResponse(
                success=False,
                message="Gmail was not connected",
            )

    except GmailOAuthError as e:
        logger.error(f"Failed to disconnect Gmail: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recipient")
async def get_recipient_email(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get saved recipient email for current user.
    """
    gmail_service = get_gmail_service()
    recipient = await gmail_service.get_recipient_email(db, current_user.id)

    return {"email": recipient}


@router.put("/recipient", response_model=UpdateRecipientResponse)
async def update_recipient_email(
    request: UpdateRecipientRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update default recipient email for current user.

    This email will be used when sending via the agent tool
    unless overridden at send time.
    """
    try:
        gmail_service = get_gmail_service()
        await gmail_service.update_recipient_email(
            db,
            current_user.id,
            request.email,
        )

        return UpdateRecipientResponse(
            success=True,
            email=request.email,
        )

    except GmailNotConnectedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GmailSendError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send", response_model=SendEmailResponse)
async def send_email(
    request: SendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send an email via Gmail API.

    Uses connected Gmail account to send email.
    If 'to' is not provided, uses saved default recipient.
    """
    try:
        gmail_service = get_gmail_service()
        result = await gmail_service.send_email(
            db=db,
            user_id=current_user.id,
            subject=request.subject,
            body=request.body,
            to_email=request.to,
            content_type=request.content_type,
        )

        return SendEmailResponse(
            success=result.success,
            message_id=result.message_id,
        )

    except GmailNotConnectedError as e:
        return SendEmailResponse(
            success=False,
            error="Gmail is not connected. Please connect your Gmail account first.",
        )
    except GmailSendError as e:
        return SendEmailResponse(
            success=False,
            error=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        return SendEmailResponse(
            success=False,
            error="An unexpected error occurred while sending email.",
        )
