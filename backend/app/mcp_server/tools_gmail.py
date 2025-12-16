"""
Gmail Tool for OpenAI Agents SDK.
Enables agents to send emails via user's connected Gmail account.
"""

import logging
from typing import Optional, Any

from agents import function_tool, RunContextWrapper

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.services.gmail_service import (
    get_gmail_service,
    GmailSendError,
)
from app.services.gmail_oauth_service import (
    GmailNotConnectedError,
    GmailTokenError,
)

logger = logging.getLogger(__name__)


# Database session factory for tool context
_async_engine = None
_async_session_maker = None


def _get_db_session_maker():
    """Get or create async session maker for database access in tools."""
    global _async_engine, _async_session_maker

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

        _async_engine = create_async_engine(database_url, echo=False)
        _async_session_maker = sessionmaker(
            _async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

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

        # Get database session
        session_maker = _get_db_session_maker()
        async with session_maker() as db:
            gmail_service = get_gmail_service()

            logger.info("send_email: Calling gmail_service.send_email...")
            result = await gmail_service.send_email(
                db=db,
                user_id=user_id,
                subject=subject,
                body=body,
                to_email=to_email,
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

        # Get database session
        session_maker = _get_db_session_maker()
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

    except Exception as e:
        logger.error(f"Error checking email status: {e}")
        return "Unable to check email status. Please try again."


# Export tools for agent registration
GMAIL_TOOLS = [send_email, check_email_status]
