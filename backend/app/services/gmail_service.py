"""
Gmail Service for sending emails via Gmail API.
Uses OAuth2 tokens to authenticate and send emails on behalf of users.
"""

import base64
import logging
import re
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


def format_email_html(body: str, subject: str = "") -> str:
    """
    Convert plain text or markdown-like body to professional HTML email.

    Args:
        body: Email body content (plain text or markdown-like)
        subject: Email subject for header

    Returns:
        Formatted HTML email string
    """
    # Escape HTML special characters first
    def escape_html(text: str) -> str:
        return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))

    # Process the body content
    lines = body.split('\n')
    html_lines = []
    in_table = False
    table_rows = []
    in_code_block = False
    code_lines = []

    for line in lines:
        stripped = line.strip()

        # Handle code blocks ```
        if stripped.startswith('```'):
            if in_code_block:
                # End code block
                code_content = '\n'.join(code_lines)
                html_lines.append(f'<pre style="background-color: #f4f4f4; padding: 12px; border-radius: 6px; overflow-x: auto; font-family: \'Courier New\', monospace; font-size: 13px; border: 1px solid #e0e0e0;">{escape_html(code_content)}</pre>')
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # Handle markdown tables
        if '|' in stripped and stripped.startswith('|') and stripped.endswith('|'):
            if not in_table:
                in_table = True
                table_rows = []
            # Skip separator rows (|---|---|)
            if re.match(r'^\|[\s\-:]+\|$', stripped.replace('|', '|').replace('-', '-')):
                continue
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            table_rows.append(cells)
            continue
        elif in_table:
            # End of table
            html_lines.append(_render_table(table_rows))
            table_rows = []
            in_table = False

        # Handle headers
        if stripped.startswith('### '):
            html_lines.append(f'<h3 style="color: #1a1a1a; font-size: 16px; margin: 20px 0 10px 0; font-weight: 600;">{escape_html(stripped[4:])}</h3>')
            continue
        elif stripped.startswith('## '):
            html_lines.append(f'<h2 style="color: #1a1a1a; font-size: 18px; margin: 24px 0 12px 0; font-weight: 600;">{escape_html(stripped[3:])}</h2>')
            continue
        elif stripped.startswith('# '):
            html_lines.append(f'<h1 style="color: #1a1a1a; font-size: 22px; margin: 28px 0 14px 0; font-weight: 700;">{escape_html(stripped[2:])}</h1>')
            continue

        # Handle bullet points
        if stripped.startswith('- ') or stripped.startswith('* '):
            content = escape_html(stripped[2:])
            content = _format_inline(content)
            html_lines.append(f'<div style="margin: 6px 0 6px 20px; padding-left: 10px; border-left: 3px solid #10b981;">&#8226; {content}</div>')
            continue

        # Handle numbered lists
        num_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if num_match:
            num, content = num_match.groups()
            content = _format_inline(escape_html(content))
            html_lines.append(f'<div style="margin: 6px 0 6px 20px;"><span style="color: #10b981; font-weight: 600;">{num}.</span> {content}</div>')
            continue

        # Handle horizontal rule
        if stripped in ['---', '***', '___']:
            html_lines.append('<hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;">')
            continue

        # Handle empty lines
        if not stripped:
            html_lines.append('<div style="height: 12px;"></div>')
            continue

        # Regular paragraph
        content = _format_inline(escape_html(stripped))
        html_lines.append(f'<p style="margin: 8px 0; line-height: 1.6; color: #333;">{content}</p>')

    # Handle any remaining table
    if in_table and table_rows:
        html_lines.append(_render_table(table_rows))

    # Handle any remaining code block
    if in_code_block and code_lines:
        code_content = '\n'.join(code_lines)
        html_lines.append(f'<pre style="background-color: #f4f4f4; padding: 12px; border-radius: 6px; overflow-x: auto; font-family: \'Courier New\', monospace; font-size: 13px;">{escape_html(code_content)}</pre>')

    body_html = '\n'.join(html_lines)

    # Wrap in professional email template
    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow: hidden; max-width: 100%;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 24px 30px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 20px; font-weight: 600;">
                                AI Data Assistant
                            </h1>
                            {f'<p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">{escape_html(subject)}</p>' if subject else ''}
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 30px;">
                            {body_html}
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 20px 30px; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0; color: #6b7280; font-size: 12px; text-align: center;">
                                Sent by AI Data Assistant<br>
                                <span style="color: #9ca3af;">This is an automated message from your database query assistant.</span>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''


def _format_inline(text: str) -> str:
    """Format inline markdown elements like bold, italic, code."""
    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    # Italic: *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    # Inline code: `code`
    text = re.sub(r'`(.+?)`', r'<code style="background-color: #f4f4f4; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px;">\1</code>', text)
    return text


def _render_table(rows: list) -> str:
    """Render a list of table rows as HTML table."""
    if not rows:
        return ""

    html = ['<table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px;">']

    for i, row in enumerate(rows):
        if i == 0:
            # Header row
            html.append('<thead><tr>')
            for cell in row:
                html.append(f'<th style="background-color: #10b981; color: white; padding: 12px 16px; text-align: left; font-weight: 600; border: 1px solid #059669;">{cell}</th>')
            html.append('</tr></thead><tbody>')
        else:
            # Data row
            bg_color = '#f9fafb' if i % 2 == 0 else '#ffffff'
            html.append(f'<tr style="background-color: {bg_color};">')
            for cell in row:
                html.append(f'<td style="padding: 10px 16px; border: 1px solid #e5e7eb; color: #374151;">{cell}</td>')
            html.append('</tr>')

    html.append('</tbody></table>')
    return '\n'.join(html)


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
