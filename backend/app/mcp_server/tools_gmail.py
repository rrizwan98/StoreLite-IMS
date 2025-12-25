"""
Gmail Tool for OpenAI Agents SDK.
Enables agents to send emails via user's connected Gmail account.
"""

import logging
from typing import Optional, Any

from agents import function_tool, RunContextWrapper

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.services.gmail_service import (
    get_gmail_service,
    GmailSendError,
    format_email_html,
)
from app.services.gmail_oauth_service import (
    GmailNotConnectedError,
    GmailTokenError,
)

logger = logging.getLogger(__name__)


# Database session factory for tool context
_async_engine = None
_async_session_maker = None


def _reset_db_connection():
    """Reset database connection - call when connection errors occur."""
    global _async_engine, _async_session_maker
    logger.info("Resetting database connection for Gmail tools...")
    if _async_engine is not None:
        # Don't await dispose in sync context - just reset references
        _async_engine = None
    _async_session_maker = None


def _get_db_session_maker(force_new: bool = False):
    """Get or create async session maker for database access in tools.

    Args:
        force_new: If True, force creation of a new connection pool
    """
    global _async_engine, _async_session_maker

    if force_new:
        _reset_db_connection()

    if _async_session_maker is None:
        import os
        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

        database_url = os.getenv("DATABASE_URL", "")

        # Convert to async URL if needed
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Handle sslmode for asyncpg - convert to ssl=require format
        # asyncpg uses 'ssl' parameter, not 'sslmode'
        if "sslmode=" in database_url:
            parsed = urlparse(database_url)
            query_params = parse_qs(parsed.query)

            # Remove sslmode and add ssl if sslmode was 'require'
            sslmode = query_params.pop("sslmode", ["disable"])[0]
            if sslmode == "require":
                query_params["ssl"] = ["require"]

            # Rebuild URL
            new_query = urlencode(query_params, doseq=True)
            database_url = urlunparse(parsed._replace(query=new_query))

        # Use NullPool to avoid stale connection issues
        # Each request gets a fresh connection
        _async_engine = create_async_engine(
            database_url,
            echo=False,
            poolclass=NullPool,  # No connection pooling - fresh connection each time
        )
        _async_session_maker = async_sessionmaker(
            _async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Created new database session maker for Gmail tools")

    return _async_session_maker


@function_tool
async def send_email(
    context: RunContextWrapper[Any],
    subject: str,
    body: str,
    to_email: Optional[str] = None,
) -> str:
    """
    Send an email via the user's connected Gmail account.

    IMPORTANT: Always format the email body professionally with proper structure:
    - Use clear paragraphs and line breaks
    - For data/tables, format them readably
    - Include a greeting and sign-off
    - Make the content easy to read

    Use this tool when the user explicitly requests to email something, or
    when they select the Gmail tool from the tools menu.

    Args:
        context: Agent run context containing user information
        subject: Email subject line (be descriptive and professional)
        body: Email body content - MUST be well-formatted with:
              - Professional greeting (e.g., "Hello,")
              - Clear content with proper line breaks
              - Data formatted in readable tables if applicable
              - Professional sign-off
        to_email: Optional recipient email address. If not provided,
                 uses the user's saved default recipient.

    Returns:
        A confirmation message if successful, or an error message
        explaining what went wrong and how to fix it.

    Example email body format:
        Hello,

        Here is the data you requested:

        | Column 1 | Column 2 | Column 3 |
        |----------|----------|----------|
        | Value 1  | Value 2  | Value 3  |

        Summary: [brief summary of the data]

        Best regards,
        AI Data Assistant
    """
    try:
        logger.info("=" * 60)
        logger.info("SEND_EMAIL TOOL INVOKED!")
        logger.info(f"Subject: {subject[:50]}...")
        logger.info(f"Body length: {len(body)} chars")
        logger.info(f"To: {to_email or 'default recipient'}")
        logger.info("=" * 60)

        # Get user_id from context
        user_context = context.context if hasattr(context, 'context') else {}
        user_id = user_context.get("user_id")

        if not user_id:
            logger.warning("No user_id in context for send_email tool")
            return (
                "I cannot send an email because I don't have access to your user session. "
                "Please ensure you're logged in and try again."
            )

        logger.info(f"send_email: user_id={user_id}, getting database session...")

        # Retry logic for database connection issues
        max_retries = 2
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # Force new connection on retry
                force_new = attempt > 0
                if force_new:
                    logger.info(f"send_email: Retry attempt {attempt} with fresh connection...")

                # Get database session
                session_maker = _get_db_session_maker(force_new=force_new)
                async with session_maker() as db:
                    gmail_service = get_gmail_service()

                    logger.info("send_email: Converting body to HTML format...")
                    html_body = format_email_html(body, subject)

                    logger.info("send_email: Calling gmail_service.send_email with HTML...")
                    result = await gmail_service.send_email(
                        db=db,
                        user_id=user_id,
                        subject=subject,
                        body=html_body,
                        to_email=to_email,
                        content_type="text/html",
                    )

                    if result.success:
                        recipient_info = f" to {to_email}" if to_email else " to your default recipient"
                        logger.info(f"send_email: SUCCESS - Message ID: {result.message_id}")
                        return (
                            f"✅ Email sent successfully{recipient_info}!\n\n"
                            f"📧 Subject: {subject}\n"
                            f"🆔 Message ID: {result.message_id}\n\n"
                            "The email has been delivered to the recipient's inbox."
                        )
                    else:
                        logger.error(f"send_email: FAILED - {result.error}")
                        return f"❌ Failed to send email: {result.error}"

            except Exception as db_error:
                error_str = str(db_error).lower()
                # Check for connection-related errors that might be recoverable
                is_connection_error = any(x in error_str for x in [
                    "connection is closed",
                    "connection was closed",
                    "connection reset",
                    "interfaceerror",
                    "connection refused",
                    "server closed the connection",
                ])

                if is_connection_error and attempt < max_retries:
                    logger.warning(f"send_email: Connection error on attempt {attempt + 1}: {db_error}")
                    last_error = db_error
                    _reset_db_connection()  # Reset before retry
                    continue
                else:
                    # Not a connection error or out of retries, re-raise
                    raise

        # If we get here, all retries failed
        if last_error:
            raise last_error

    except GmailNotConnectedError:
        logger.warning("send_email: Gmail not connected")
        return (
            "❌ Your Gmail account is not connected.\n\n"
            "To send emails, please:\n"
            "1. Go to Dashboard\n"
            "2. Find the 'Connect Tools' section\n"
            "3. Click 'Sign in with Google' to connect your Gmail\n\n"
            "Once connected, I'll be able to send emails on your behalf."
        )

    except GmailTokenError as e:
        logger.error(f"Gmail token error: {e}")
        return (
            "❌ Authentication issue with Gmail.\n\n"
            "Please:\n"
            "1. Go to Dashboard > Connect Tools\n"
            "2. Click 'Disconnect' on Gmail\n"
            "3. Click 'Sign in with Google' again\n\n"
            f"Error: {str(e)}"
        )

    except GmailSendError as e:
        logger.error(f"Gmail send error: {e}")
        return (
            f"❌ Failed to send email.\n\n"
            f"Error: {str(e)}\n\n"
            "Please check your Gmail connection and try again."
        )

    except Exception as e:
        logger.error(f"Unexpected error in send_email tool: {e}", exc_info=True)
        return (
            f"❌ An unexpected error occurred.\n\n"
            f"Error: {str(e)}\n\n"
            "Please try again. If the problem persists, reconnect your Gmail."
        )


@function_tool
async def check_email_status(
    context: RunContextWrapper[Any],
) -> str:
    """
    Check if the user's Gmail account is connected and ready to send emails.

    Use this tool to verify email capability before attempting to send,
    or when the user asks about their email connection status.

    Args:
        context: Agent run context containing user information

    Returns:
        A message describing the Gmail connection status and any configured recipient.
    """
    try:
        # Get user_id from context
        user_context = context.context if hasattr(context, 'context') else {}
        user_id = user_context.get("user_id")

        if not user_id:
            return "I cannot check email status without access to your user session."

        # Retry logic for database connection issues
        max_retries = 2
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # Force new connection on retry
                force_new = attempt > 0

                # Get database session
                session_maker = _get_db_session_maker(force_new=force_new)
                async with session_maker() as db:
                    gmail_service = get_gmail_service()
                    status = await gmail_service.get_gmail_status(db, user_id)

                    if status["connected"]:
                        recipient_info = (
                            f"\nDefault recipient: {status['recipient_email']}"
                            if status.get('recipient_email')
                            else "\nNo default recipient configured."
                        )
                        return (
                            f"Gmail is connected!\n"
                            f"Account: {status['email']}\n"
                            f"Connected since: {status['connected_at']}"
                            f"{recipient_info}\n\n"
                            "I can send emails on your behalf. Just ask me to email any content!"
                        )
                    else:
                        return (
                            "Gmail is not connected.\n"
                            "To enable email functionality, please go to Dashboard > Connect Tools "
                            "and connect your Gmail account."
                        )

            except Exception as db_error:
                error_str = str(db_error).lower()
                is_connection_error = any(x in error_str for x in [
                    "connection is closed",
                    "connection was closed",
                    "connection reset",
                    "interfaceerror",
                    "connection refused",
                ])

                if is_connection_error and attempt < max_retries:
                    logger.warning(f"check_email_status: Connection error on attempt {attempt + 1}: {db_error}")
                    last_error = db_error
                    _reset_db_connection()
                    continue
                else:
                    raise

        if last_error:
            raise last_error

    except Exception as e:
        logger.error(f"Error checking email status: {e}")
        return "Unable to check email status. Please try again."


# Export tools for agent registration
GMAIL_TOOLS = [send_email, check_email_status]
