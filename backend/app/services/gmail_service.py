"""
Gmail Service for sending emails via Gmail API.
Uses OAuth2 tokens to authenticate and send emails on behalf of users.
"""

import base64
import logging
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Optional
from dataclasses import dataclass

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import UserConnection
from app.services.gmail_oauth_service import (
    get_gmail_oauth_service,
    GmailNotConnectedError,
    GmailTokenError,
    GMAIL_SCOPES,
)

logger = logging.getLogger(__name__)


class GmailSendError(Exception):
    """Raised when email sending fails"""
    pass


@dataclass
class SendResult:
    """Result of sending an email"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    sent_at: Optional[datetime] = None


class GmailService:
    """
    Service for sending emails via Gmail API.
    Handles email composition and sending using user's connected Gmail account.
    """

    def __init__(self):
        """Initialize Gmail service."""
        self.oauth_service = get_gmail_oauth_service()

    async def send_email(
        self,
        db: AsyncSession,
        user_id: int,
        subject: str,
        body: str,
        to_email: Optional[str] = None,
        content_type: str = "text/plain",
    ) -> SendResult:
        """
        Send an email via Gmail API.

        Args:
            db: Database session
            user_id: User ID whose Gmail to use
            subject: Email subject line
            body: Email body content
            to_email: Recipient email (uses saved default if not provided)
            content_type: "text/plain" or "text/html"

        Returns:
            SendResult with success status and message ID

        Raises:
            GmailNotConnectedError: If Gmail not connected
            GmailSendError: If sending fails
        """
        try:
            # Get recipient email
            recipient = to_email
            if not recipient:
                recipient = await self._get_default_recipient(db, user_id)

            if not recipient:
                raise GmailSendError(
                    "No recipient email provided and no default recipient saved. "
                    "Please specify a recipient or set a default in settings."
                )

            # Get valid access token (auto-refreshes if needed)
            access_token = await self.oauth_service.get_valid_access_token(db, user_id)

            # Get sender email
            connection = await self._get_connection(db, user_id)
            sender_email = connection.gmail_email

            if not sender_email:
                raise GmailSendError("Sender email not found. Please reconnect Gmail.")

            # Build and send email
            logger.info(f"Building email: From={sender_email}, To={recipient}, Subject={subject[:30]}...")

            message = self._build_message(
                to_email=recipient,
                from_email=sender_email,
                subject=subject,
                body=body,
                content_type=content_type,
            )

            logger.info(f"Sending email via Gmail API...")
            result = await self._send_message(access_token, message)

            logger.info(
                f"EMAIL SENT SUCCESSFULLY!\n"
                f"  From: {sender_email}\n"
                f"  To: {recipient}\n"
                f"  Subject: {subject[:50]}...\n"
                f"  Message ID: {result.message_id}"
            )

            return result

        except GmailNotConnectedError:
            raise
        except GmailTokenError as e:
            raise GmailSendError(f"Authentication error: {e}")
        except HttpError as e:
            error_msg = self._parse_http_error(e)
            logger.error(f"Gmail API error: {error_msg}")
            raise GmailSendError(error_msg)
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise GmailSendError(f"Failed to send email: {e}")

    async def _get_connection(self, db: AsyncSession, user_id: int) -> UserConnection:
        """Get user connection from database."""
        result = await db.execute(
            select(UserConnection).where(UserConnection.user_id == user_id)
        )
        connection = result.scalar_one_or_none()

        if not connection:
            raise GmailNotConnectedError("User connection not found")

        return connection

    async def _get_default_recipient(self, db: AsyncSession, user_id: int) -> Optional[str]:
        """Get default recipient email for user."""
        connection = await self._get_connection(db, user_id)
        return connection.gmail_recipient_email

    def _build_message(
        self,
        to_email: str,
        from_email: str,
        subject: str,
        body: str,
        content_type: str = "text/plain",
    ) -> dict:
        """
        Build email message in Gmail API format.

        Args:
            to_email: Recipient email
            from_email: Sender email
            subject: Email subject
            body: Email body
            content_type: MIME type for body

        Returns:
            Message dict ready for Gmail API
        """
        message = EmailMessage()

        # Set headers
        message["To"] = to_email
        message["From"] = from_email
        message["Subject"] = subject

        # Set content based on type
        if content_type == "text/html":
            message.set_content(body, subtype="html")
        else:
            message.set_content(body)

        # Encode message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        return {"raw": encoded_message}

    async def _send_message(self, access_token: str, message: dict) -> SendResult:
        """
        Send message via Gmail API.

        Args:
            access_token: Valid OAuth access token
            message: Message dict with "raw" field

        Returns:
            SendResult with message ID
        """
        credentials = Credentials(
            token=access_token,
            scopes=GMAIL_SCOPES,
        )

        service = build("gmail", "v1", credentials=credentials)

        sent_message = service.users().messages().send(
            userId="me",
            body=message,
        ).execute()

        return SendResult(
            success=True,
            message_id=sent_message.get("id"),
            sent_at=datetime.now(timezone.utc),
        )

    def _parse_http_error(self, error: HttpError) -> str:
        """Parse Gmail API HTTP error into user-friendly message."""
        status = error.resp.status

        if status == 401:
            return "Authentication failed. Please reconnect your Gmail account."
        elif status == 403:
            return "Permission denied. Please ensure you granted 'Send Email' permission."
        elif status == 429:
            return "Rate limit exceeded. Please try again later."
        elif status == 400:
            return f"Invalid request: {error.reason}"
        else:
            return f"Gmail API error ({status}): {error.reason}"

    async def get_gmail_status(self, db: AsyncSession, user_id: int) -> dict:
        """
        Get Gmail connection status for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Status dict with connected, email, connected_at, recipient_email
        """
        try:
            result = await db.execute(
                select(UserConnection).where(UserConnection.user_id == user_id)
            )
            connection = result.scalar_one_or_none()

            if not connection or not connection.gmail_access_token:
                return {
                    "connected": False,
                    "email": None,
                    "connected_at": None,
                    "recipient_email": None,
                }

            return {
                "connected": True,
                "email": connection.gmail_email,
                "connected_at": connection.gmail_connected_at.isoformat() if connection.gmail_connected_at else None,
                "recipient_email": connection.gmail_recipient_email,
            }

        except Exception as e:
            logger.error(f"Failed to get Gmail status: {e}")
            return {
                "connected": False,
                "email": None,
                "connected_at": None,
                "recipient_email": None,
                "error": str(e),
            }

    async def update_recipient_email(
        self,
        db: AsyncSession,
        user_id: int,
        recipient_email: str,
    ) -> bool:
        """
        Update default recipient email for a user.

        Args:
            db: Database session
            user_id: User ID
            recipient_email: New recipient email

        Returns:
            True if updated successfully
        """
        try:
            result = await db.execute(
                select(UserConnection).where(UserConnection.user_id == user_id)
            )
            connection = result.scalar_one_or_none()

            if not connection:
                raise GmailNotConnectedError("User connection not found")

            connection.gmail_recipient_email = recipient_email
            await db.commit()

            logger.info(f"Updated recipient email for user {user_id}: {recipient_email}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update recipient email: {e}")
            raise GmailSendError(f"Failed to update recipient email: {e}")

    async def get_recipient_email(self, db: AsyncSession, user_id: int) -> Optional[str]:
        """
        Get default recipient email for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Recipient email or None
        """
        connection = await self._get_connection(db, user_id)
        return connection.gmail_recipient_email


# Singleton instance
_gmail_service: Optional[GmailService] = None


def get_gmail_service() -> GmailService:
    """Get singleton Gmail service instance."""
    global _gmail_service
    if _gmail_service is None:
        _gmail_service = GmailService()
    return _gmail_service
