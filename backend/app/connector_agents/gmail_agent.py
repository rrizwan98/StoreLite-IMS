"""
Gmail Connector Sub-Agent.

Specialized agent for handling all Gmail operations.
This agent uses the Gmail API via OAuth tokens to
send emails and manage email on behalf of the user.
"""

import os
import json
import base64
import logging
import httpx
from email.message import EmailMessage
from typing import List, Dict, Any, Optional

from agents.tool import FunctionTool

from .base import BaseConnectorAgent

logger = logging.getLogger(__name__)

# Gmail API endpoints
GMAIL_API = "https://gmail.googleapis.com/gmail/v1"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Google OAuth credentials (for token refresh)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")


class GmailConnectorAgent(BaseConnectorAgent):
    """
    Specialized agent for Gmail operations.

    Handles:
    - Sending emails
    - Checking email connection status
    - Reading inbox emails
    - Searching emails
    - Getting email details

    This agent uses direct Gmail API calls with the stored OAuth token.
    """

    CONNECTOR_TYPE = "Gmail"
    TOOL_NAME = "gmail_connector"
    TOOL_DESCRIPTION = (
        "Handle ALL Gmail operations including: "
        "sending emails, checking connection status, reading inbox, "
        "searching emails, and getting email details. "
        "Use this for ANY email-related task."
    )

    def get_system_prompt(self) -> str:
        """Get Gmail-specific system prompt."""
        return """You are a Gmail Expert Agent. Your job is to execute Gmail operations using the available tools.

## AUTONOMOUS EXECUTION
Execute tasks immediately. Make intelligent decisions based on the request.
- Need to send an email? → Use gmail_send with proper formatting
- Need to check connection? → Use gmail_status
- Need to find emails? → Use gmail_search
- Need to read emails? → Use gmail_read_inbox

Execute, don't ask unnecessary questions.

## YOUR CAPABILITIES
- Send emails with HTML formatting
- Check Gmail connection status
- Read inbox emails
- Search for specific emails
- Get email details

## EMAIL FORMATTING GUIDELINES
When sending emails:
- Always use professional formatting
- Include greeting and sign-off
- Format data in readable tables when applicable
- Use markdown-like formatting (converted to HTML)

## EXECUTION RULES

1. ALWAYS USE TOOLS - Never pretend to complete operations without calling tools
2. FORMAT PROFESSIONALLY - All emails should be well-formatted
3. CONFIRM ACTIONS - Report what was done with specific details
4. HANDLE ERRORS - Provide helpful error messages

## WORKFLOW: SEND EMAIL

Step 1: Prepare the email content
- Subject should be descriptive
- Body should be well-formatted with greeting and sign-off

Step 2: Send the email
```
gmail_send with to_email, subject, and body
```

Step 3: Confirm success
- Report the message ID
- Confirm recipient

## WORKFLOW: READ EMAILS

Step 1: Get inbox messages
```
gmail_read_inbox with optional max_results
```

Step 2: For specific email content
```
gmail_get_message with message_id
```

## ERROR HANDLING
If sending fails:
- Check if Gmail is connected
- Verify recipient email format
- Report specific error

## RESPONSE FORMAT
After completing operations, provide:
- What was done
- Relevant details (message ID, recipient, etc.)
- Errors if any occurred

Execute tasks completely using tools."""

    async def _refresh_access_token(self) -> Optional[str]:
        """
        Refresh the access token using the refresh token.

        Returns:
            New access token if successful, None otherwise
        """
        refresh_token = self.auth_config.get("refresh_token")
        if not refresh_token:
            logger.error("[GmailAgent] No refresh token available")
            return None

        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            logger.error("[GmailAgent] Google OAuth credentials not configured")
            return None

        token_request = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    GOOGLE_TOKEN_URL,
                    data=token_request,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )

                if response.status_code == 200:
                    token_data = response.json()
                    new_access_token = token_data.get("access_token")

                    # Update auth config with new token
                    self.auth_config["access_token"] = new_access_token
                    if token_data.get("refresh_token"):
                        self.auth_config["refresh_token"] = token_data["refresh_token"]

                    logger.info("[GmailAgent] Successfully refreshed access token")
                    return new_access_token
                else:
                    logger.error(f"[GmailAgent] Token refresh failed: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"[GmailAgent] Token refresh error: {e}")
            return None

    async def _get_valid_token(self) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token or None
        """
        access_token = self.auth_config.get("access_token")
        if not access_token:
            return await self._refresh_access_token()
        return access_token

    async def load_tools(self) -> List[FunctionTool]:
        """Load Gmail tools."""
        logger.info(f"[GmailAgent] Loading tools with OAuth token")

        # Get access token from auth config (we'll refresh on-demand if needed)
        access_token = self.auth_config.get("access_token")
        if not access_token:
            logger.error("[GmailAgent] No access token in auth config!")
            return []

        # Get user email from auth config (for sender info)
        user_email = self.auth_config.get("email", "")

        # Create tools with the access token (tools will handle refresh on 401)
        tools = [
            self._create_send_tool(user_email),
            self._create_status_tool(user_email),
            self._create_read_inbox_tool(),
            self._create_search_tool(),
            self._create_get_message_tool(),
        ]

        logger.info(f"[GmailAgent] Created {len(tools)} tools")
        return tools

    def _create_send_tool(self, user_email: str) -> FunctionTool:
        """Create the send email tool."""
        agent_self = self  # Capture self for closure

        async def gmail_send(ctx, args: str) -> str:
            """Send an email via Gmail API."""
            try:
                kwargs = json.loads(args) if args else {}
                to_email = kwargs.get("to_email", "")
                subject = kwargs.get("subject", "")
                body = kwargs.get("body", "")

                if not to_email:
                    return "[Gmail:gmail_send] Error: to_email parameter is required"
                if not subject:
                    return "[Gmail:gmail_send] Error: subject parameter is required"
                if not body:
                    return "[Gmail:gmail_send] Error: body parameter is required"

                logger.info(f"[GmailAgent] Sending email to: {to_email}")

                # Convert body to HTML with robust error handling
                try:
                    html_body = agent_self._format_email_html(body, subject)
                except Exception as fmt_error:
                    logger.error(f"[GmailAgent] Email formatting error: {fmt_error}")
                    # Ultimate fallback - just use plain text wrapped in basic HTML
                    html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
<pre style="white-space: pre-wrap; font-family: inherit;">{body}</pre>
</body>
</html>"""

                # Build email message
                message = EmailMessage()
                message["To"] = to_email
                message["From"] = user_email
                message["Subject"] = subject
                message.set_content(html_body, subtype="html")

                # Encode message
                encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

                # Get current access token
                access_token = agent_self.auth_config.get("access_token")

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{GMAIL_API}/users/me/messages/send",
                        json={"raw": encoded_message},
                        headers={"Authorization": f"Bearer {access_token}"}
                    )

                    # If token expired, refresh and retry
                    if response.status_code in (401, 403):
                        logger.info("[GmailAgent] Token expired, refreshing...")
                        new_token = await agent_self._refresh_access_token()
                        if new_token:
                            response = await client.post(
                                f"{GMAIL_API}/users/me/messages/send",
                                json={"raw": encoded_message},
                                headers={"Authorization": f"Bearer {new_token}"}
                            )
                        else:
                            return "[Gmail:gmail_send] Error: Failed to refresh access token. Please reconnect Gmail."

                    if response.status_code != 200:
                        error_msg = f"API error: {response.status_code} - {response.text}"
                        logger.error(f"[GmailAgent] {error_msg}")
                        return f"[Gmail:gmail_send] Error: {error_msg}"

                    data = response.json()
                    message_id = data.get("id", "unknown")

                    return (
                        f"[Gmail:gmail_send] Email sent successfully!\n"
                        f"To: {to_email}\n"
                        f"Subject: {subject}\n"
                        f"Message ID: {message_id}"
                    )

            except Exception as e:
                error_msg = f"[Gmail:gmail_send] Error: {str(e)}"
                logger.error(error_msg)
                return error_msg

        gmail_send.__name__ = "gmail_send"
        gmail_send.__doc__ = "Send an email via Gmail"

        return FunctionTool(
            name="gmail_send",
            description="Send an email via Gmail. Requires recipient email, subject, and body.",
            params_json_schema={
                "type": "object",
                "properties": {
                    "to_email": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content (will be converted to HTML)"
                    }
                },
                "required": ["to_email", "subject", "body"]
            },
            on_invoke_tool=gmail_send,
            strict_json_schema=False,
        )

    def _create_status_tool(self, user_email: str) -> FunctionTool:
        """Create the status check tool."""
        agent_self = self

        async def gmail_status(ctx, args: str) -> str:
            """Check Gmail connection status."""
            try:
                access_token = agent_self.auth_config.get("access_token")

                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(
                        f"{GMAIL_API}/users/me/profile",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )

                    # If token expired, refresh and retry
                    if response.status_code in (401, 403):
                        logger.info("[GmailAgent] Token expired, refreshing...")
                        new_token = await agent_self._refresh_access_token()
                        if new_token:
                            response = await client.get(
                                f"{GMAIL_API}/users/me/profile",
                                headers={"Authorization": f"Bearer {new_token}"}
                            )
                        else:
                            return "[Gmail:gmail_status] Error: Failed to refresh access token. Please reconnect Gmail."

                    if response.status_code == 200:
                        data = response.json()
                        return (
                            f"[Gmail:gmail_status] Gmail is connected!\n"
                            f"Email: {data.get('emailAddress', user_email)}\n"
                            f"Messages Total: {data.get('messagesTotal', 'N/A')}\n"
                            f"Threads Total: {data.get('threadsTotal', 'N/A')}"
                        )
                    else:
                        return f"[Gmail:gmail_status] Gmail connection error: {response.status_code}"

            except Exception as e:
                error_msg = f"[Gmail:gmail_status] Error: {str(e)}"
                logger.error(error_msg)
                return error_msg

        gmail_status.__name__ = "gmail_status"
        gmail_status.__doc__ = "Check Gmail connection status"

        return FunctionTool(
            name="gmail_status",
            description="Check Gmail connection status and get account info.",
            params_json_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            on_invoke_tool=gmail_status,
            strict_json_schema=False,
        )

    def _create_read_inbox_tool(self) -> FunctionTool:
        """Create the read inbox tool."""
        agent_self = self

        async def gmail_read_inbox(ctx, args: str) -> str:
            """Read recent emails from inbox."""
            try:
                kwargs = json.loads(args) if args else {}
                max_results = kwargs.get("max_results", 10)

                logger.info(f"[GmailAgent] Reading inbox, max results: {max_results}")

                access_token = agent_self.auth_config.get("access_token")

                async with httpx.AsyncClient(timeout=30.0) as client:
                    # List messages
                    response = await client.get(
                        f"{GMAIL_API}/users/me/messages",
                        params={
                            "maxResults": max_results,
                            "labelIds": "INBOX"
                        },
                        headers={"Authorization": f"Bearer {access_token}"}
                    )

                    # If token expired, refresh and retry
                    if response.status_code in (401, 403):
                        logger.info("[GmailAgent] Token expired, refreshing...")
                        new_token = await agent_self._refresh_access_token()
                        if new_token:
                            access_token = new_token
                            response = await client.get(
                                f"{GMAIL_API}/users/me/messages",
                                params={
                                    "maxResults": max_results,
                                    "labelIds": "INBOX"
                                },
                                headers={"Authorization": f"Bearer {access_token}"}
                            )
                        else:
                            return "[Gmail:gmail_read_inbox] Error: Failed to refresh access token. Please reconnect Gmail."

                    if response.status_code != 200:
                        error_msg = f"API error: {response.status_code} - {response.text}"
                        return f"[Gmail:gmail_read_inbox] Error: {error_msg}"

                    data = response.json()
                    messages = data.get("messages", [])

                    if not messages:
                        return "[Gmail:gmail_read_inbox] No messages in inbox"

                    # Get details for each message
                    results = []
                    for msg in messages[:max_results]:
                        msg_response = await client.get(
                            f"{GMAIL_API}/users/me/messages/{msg['id']}",
                            params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
                            headers={"Authorization": f"Bearer {access_token}"}
                        )

                        if msg_response.status_code == 200:
                            msg_data = msg_response.json()
                            headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
                            snippet = msg_data.get("snippet", "")[:100]
                            results.append(
                                f"- ID: {msg['id']}\n"
                                f"  From: {headers.get('From', 'Unknown')}\n"
                                f"  Subject: {headers.get('Subject', 'No Subject')}\n"
                                f"  Date: {headers.get('Date', 'Unknown')}\n"
                                f"  Preview: {snippet}..."
                            )

                    return f"[Gmail:gmail_read_inbox] Found {len(results)} emails:\n\n" + "\n\n".join(results)

            except Exception as e:
                error_msg = f"[Gmail:gmail_read_inbox] Error: {str(e)}"
                logger.error(error_msg)
                return error_msg

        gmail_read_inbox.__name__ = "gmail_read_inbox"
        gmail_read_inbox.__doc__ = "Read recent emails from inbox"

        return FunctionTool(
            name="gmail_read_inbox",
            description="Read recent emails from inbox. Returns subject, sender, date, and preview.",
            params_json_schema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of emails to return (default: 10)"
                    }
                },
                "required": []
            },
            on_invoke_tool=gmail_read_inbox,
            strict_json_schema=False,
        )

    def _create_search_tool(self) -> FunctionTool:
        """Create the search emails tool."""
        agent_self = self

        async def gmail_search(ctx, args: str) -> str:
            """Search for emails."""
            try:
                kwargs = json.loads(args) if args else {}
                query = kwargs.get("query", "")
                max_results = kwargs.get("max_results", 10)

                if not query:
                    return "[Gmail:gmail_search] Error: query parameter is required"

                logger.info(f"[GmailAgent] Searching emails: {query}")

                access_token = agent_self.auth_config.get("access_token")

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        f"{GMAIL_API}/users/me/messages",
                        params={
                            "q": query,
                            "maxResults": max_results
                        },
                        headers={"Authorization": f"Bearer {access_token}"}
                    )

                    # If token expired, refresh and retry
                    if response.status_code in (401, 403):
                        logger.info("[GmailAgent] Token expired, refreshing...")
                        new_token = await agent_self._refresh_access_token()
                        if new_token:
                            access_token = new_token
                            response = await client.get(
                                f"{GMAIL_API}/users/me/messages",
                                params={
                                    "q": query,
                                    "maxResults": max_results
                                },
                                headers={"Authorization": f"Bearer {access_token}"}
                            )
                        else:
                            return "[Gmail:gmail_search] Error: Failed to refresh access token. Please reconnect Gmail."

                    if response.status_code != 200:
                        error_msg = f"API error: {response.status_code} - {response.text}"
                        return f"[Gmail:gmail_search] Error: {error_msg}"

                    data = response.json()
                    messages = data.get("messages", [])

                    if not messages:
                        return f"[Gmail:gmail_search] No emails found matching '{query}'"

                    # Get details for each message
                    results = []
                    for msg in messages[:max_results]:
                        msg_response = await client.get(
                            f"{GMAIL_API}/users/me/messages/{msg['id']}",
                            params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
                            headers={"Authorization": f"Bearer {access_token}"}
                        )

                        if msg_response.status_code == 200:
                            msg_data = msg_response.json()
                            headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
                            snippet = msg_data.get("snippet", "")[:100]
                            results.append(
                                f"- ID: {msg['id']}\n"
                                f"  From: {headers.get('From', 'Unknown')}\n"
                                f"  Subject: {headers.get('Subject', 'No Subject')}\n"
                                f"  Date: {headers.get('Date', 'Unknown')}\n"
                                f"  Preview: {snippet}..."
                            )

                    return f"[Gmail:gmail_search] Found {len(results)} emails matching '{query}':\n\n" + "\n\n".join(results)

            except Exception as e:
                error_msg = f"[Gmail:gmail_search] Error: {str(e)}"
                logger.error(error_msg)
                return error_msg

        gmail_search.__name__ = "gmail_search"
        gmail_search.__doc__ = "Search for emails by query"

        return FunctionTool(
            name="gmail_search",
            description="Search for emails using Gmail search syntax (e.g., 'from:user@example.com', 'subject:invoice').",
            params_json_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gmail search query (e.g., 'from:user@example.com', 'is:unread', 'subject:report')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of emails to return (default: 10)"
                    }
                },
                "required": ["query"]
            },
            on_invoke_tool=gmail_search,
            strict_json_schema=False,
        )

    def _create_get_message_tool(self) -> FunctionTool:
        """Create the get message details tool."""
        agent_self = self

        async def gmail_get_message(ctx, args: str) -> str:
            """Get full email content."""
            try:
                kwargs = json.loads(args) if args else {}
                message_id = kwargs.get("message_id", "")

                if not message_id:
                    return "[Gmail:gmail_get_message] Error: message_id parameter is required"

                logger.info(f"[GmailAgent] Getting message: {message_id}")

                access_token = agent_self.auth_config.get("access_token")

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        f"{GMAIL_API}/users/me/messages/{message_id}",
                        params={"format": "full"},
                        headers={"Authorization": f"Bearer {access_token}"}
                    )

                    # If token expired, refresh and retry
                    if response.status_code in (401, 403):
                        logger.info("[GmailAgent] Token expired, refreshing...")
                        new_token = await agent_self._refresh_access_token()
                        if new_token:
                            response = await client.get(
                                f"{GMAIL_API}/users/me/messages/{message_id}",
                                params={"format": "full"},
                                headers={"Authorization": f"Bearer {new_token}"}
                            )
                        else:
                            return "[Gmail:gmail_get_message] Error: Failed to refresh access token. Please reconnect Gmail."

                    if response.status_code != 200:
                        error_msg = f"API error: {response.status_code} - {response.text}"
                        return f"[Gmail:gmail_get_message] Error: {error_msg}"

                    msg_data = response.json()
                    headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}

                    # Extract body
                    body = ""
                    payload = msg_data.get("payload", {})

                    # Try to get body from parts
                    if "parts" in payload:
                        for part in payload["parts"]:
                            if part.get("mimeType") == "text/plain":
                                body_data = part.get("body", {}).get("data", "")
                                if body_data:
                                    body = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")
                                    break
                    else:
                        # Direct body
                        body_data = payload.get("body", {}).get("data", "")
                        if body_data:
                            body = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")

                    if not body:
                        body = msg_data.get("snippet", "No content available")

                    # Truncate long bodies
                    if len(body) > 5000:
                        body = body[:5000] + "\n\n[Content truncated]"

                    return (
                        f"[Gmail:gmail_get_message]\n"
                        f"From: {headers.get('From', 'Unknown')}\n"
                        f"To: {headers.get('To', 'Unknown')}\n"
                        f"Subject: {headers.get('Subject', 'No Subject')}\n"
                        f"Date: {headers.get('Date', 'Unknown')}\n"
                        f"---\n"
                        f"{body}"
                    )

            except Exception as e:
                error_msg = f"[Gmail:gmail_get_message] Error: {str(e)}"
                logger.error(error_msg)
                return error_msg

        gmail_get_message.__name__ = "gmail_get_message"
        gmail_get_message.__doc__ = "Get full email content by message ID"

        return FunctionTool(
            name="gmail_get_message",
            description="Get full email content by message ID. Use this after search/inbox to read full message.",
            params_json_schema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "The Gmail message ID (obtained from search or inbox)"
                    }
                },
                "required": ["message_id"]
            },
            on_invoke_tool=gmail_get_message,
            strict_json_schema=False,
        )

    def _format_email_html(self, body: str, subject: str = "") -> str:
        """
        Convert Markdown body to professional HTML email.

        Uses markdown2 library to properly render:
        - Headers (# ## ###)
        - Bold (**text**) and Italic (*text*)
        - Lists (- item, 1. item)
        - Tables (| col | col |)
        - Code blocks (```code```)
        - Links [text](url)
        - And more...
        """
        import re

        def escape_html(text: str) -> str:
            return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

        # Ensure body is a string
        if not isinstance(body, str):
            body = str(body) if body else ""

        # Try to use markdown2, fallback to simple formatting if not available
        body_html = ""
        try:
            import markdown2
            body_html = markdown2.markdown(
                body,
                extras=[
                    "tables",           # Support tables
                    "fenced-code-blocks",  # ```code``` blocks
                    "code-friendly",    # Better code handling
                    "cuddled-lists",    # Lists without blank lines
                    "strike",           # ~~strikethrough~~
                ]
            )
            logger.info("[GmailAgent] Markdown converted to HTML successfully")
        except ImportError:
            logger.warning("[GmailAgent] markdown2 not installed, using simple formatting")
            try:
                body_html = self._simple_markdown_to_html(body)
            except Exception as e2:
                logger.error(f"[GmailAgent] Simple markdown fallback failed: {e2}")
                body_html = f"<p>{escape_html(body)}</p>"
        except Exception as e:
            logger.error(f"[GmailAgent] Markdown conversion error: {e}, using simple formatting")
            try:
                body_html = self._simple_markdown_to_html(body)
            except Exception as e2:
                logger.error(f"[GmailAgent] Simple markdown fallback failed: {e2}")
                body_html = f"<p>{escape_html(body)}</p>"

        # Ensure body_html is not empty
        if not body_html:
            body_html = f"<p>{escape_html(body)}</p>"

        # Apply inline styles for email compatibility (email clients don't support <style> tags well)
        # Wrap in try-except to handle any regex errors
        try:
            # Style headers
            body_html = re.sub(
                r'<h1([^>]*)>',
                r'<h1\1 style="color: #1a1a1a; font-size: 24px; font-weight: 700; margin: 24px 0 12px 0; border-bottom: 2px solid #10b981; padding-bottom: 8px;">',
                body_html
            )
            body_html = re.sub(
                r'<h2([^>]*)>',
                r'<h2\1 style="color: #1a1a1a; font-size: 20px; font-weight: 600; margin: 20px 0 10px 0;">',
                body_html
            )
            body_html = re.sub(
                r'<h3([^>]*)>',
                r'<h3\1 style="color: #1a1a1a; font-size: 16px; font-weight: 600; margin: 16px 0 8px 0;">',
                body_html
            )

            # Style paragraphs
            body_html = re.sub(
                r'<p>',
                r'<p style="margin: 12px 0; line-height: 1.6; color: #333333;">',
                body_html
            )

            # Style lists
            body_html = re.sub(
                r'<ul>',
                r'<ul style="margin: 12px 0; padding-left: 24px; color: #333333;">',
                body_html
            )
            body_html = re.sub(
                r'<ol>',
                r'<ol style="margin: 12px 0; padding-left: 24px; color: #333333;">',
                body_html
            )
            body_html = re.sub(
                r'<li>',
                r'<li style="margin: 6px 0; line-height: 1.5;">',
                body_html
            )

            # Style tables (common in data reports)
            body_html = re.sub(
                r'<table>',
                r'<table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px;">',
                body_html
            )
            body_html = re.sub(
                r'<thead>',
                r'<thead style="background-color: #10b981; color: white;">',
                body_html
            )
            body_html = re.sub(
                r'<th([^>]*)>',
                r'<th\1 style="padding: 12px 16px; text-align: left; font-weight: 600; border: 1px solid #e5e7eb;">',
                body_html
            )
            body_html = re.sub(
                r'<td([^>]*)>',
                r'<td\1 style="padding: 10px 16px; border: 1px solid #e5e7eb; color: #374151;">',
                body_html
            )
            body_html = re.sub(
                r'<tr>',
                r'<tr style="background-color: #ffffff;">',
                body_html
            )
            # Alternate row colors for better readability
            body_html = re.sub(
                r'(<tr style="background-color: #ffffff;">.*?</tr>\s*)(<tr style="background-color: #ffffff;">)',
                r'\1<tr style="background-color: #f9fafb;">',
                body_html,
                flags=re.DOTALL
            )

            # Style code blocks
            body_html = re.sub(
                r'<pre>',
                r'<pre style="background-color: #1f2937; color: #e5e7eb; padding: 16px; border-radius: 8px; overflow-x: auto; font-family: \'Monaco\', \'Menlo\', monospace; font-size: 13px; margin: 16px 0;">',
                body_html
            )
            body_html = re.sub(
                r'<code>',
                r'<code style="font-family: \'Monaco\', \'Menlo\', monospace;">',
                body_html
            )

            # Style inline code (not inside pre)
            body_html = re.sub(
                r'(?<!<pre[^>]*>)<code style="font-family: \'Monaco\', \'Menlo\', monospace;">([^<]+)</code>(?!</pre>)',
                r'<code style="background-color: #f3f4f6; color: #ef4444; padding: 2px 6px; border-radius: 4px; font-family: \'Monaco\', \'Menlo\', monospace; font-size: 13px;">\1</code>',
                body_html
            )

            # Style blockquotes
            body_html = re.sub(
                r'<blockquote>',
                r'<blockquote style="border-left: 4px solid #10b981; margin: 16px 0; padding: 12px 20px; background-color: #f0fdf4; color: #166534;">',
                body_html
            )

            # Style links
            body_html = re.sub(
                r'<a href="([^"]+)">',
                r'<a href="\1" style="color: #10b981; text-decoration: underline;">',
                body_html
            )

            # Style strong/bold
            body_html = re.sub(
                r'<strong>',
                r'<strong style="font-weight: 600; color: #111827;">',
                body_html
            )

            # Style horizontal rules
            body_html = re.sub(
                r'<hr\s*/?>',
                r'<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">',
                body_html
            )
        except Exception as style_error:
            logger.warning(f"[GmailAgent] Error applying inline styles: {style_error}, continuing with unstyled HTML")

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

    def _simple_markdown_to_html(self, body: str) -> str:
        """
        Simple fallback Markdown to HTML converter.
        Used when markdown2 is not available or fails.
        """
        import re

        def escape_html(text: str) -> str:
            return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

        lines = body.split('\n')
        html_lines = []
        in_list = False
        list_type = None

        for line in lines:
            stripped = line.strip()

            # Handle headers
            if stripped.startswith('### '):
                if in_list:
                    html_lines.append(f'</{list_type}>')
                    in_list = False
                html_lines.append(f'<h3>{escape_html(stripped[4:])}</h3>')
                continue
            elif stripped.startswith('## '):
                if in_list:
                    html_lines.append(f'</{list_type}>')
                    in_list = False
                html_lines.append(f'<h2>{escape_html(stripped[3:])}</h2>')
                continue
            elif stripped.startswith('# '):
                if in_list:
                    html_lines.append(f'</{list_type}>')
                    in_list = False
                html_lines.append(f'<h1>{escape_html(stripped[2:])}</h1>')
                continue

            # Handle bullet points
            if stripped.startswith('- ') or stripped.startswith('* '):
                if not in_list or list_type != 'ul':
                    if in_list:
                        html_lines.append(f'</{list_type}>')
                    html_lines.append('<ul>')
                    in_list = True
                    list_type = 'ul'
                content = stripped[2:]
                # Handle bold and italic
                content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
                content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
                html_lines.append(f'<li>{escape_html(content) if "strong" not in content and "em" not in content else content}</li>')
                continue

            # Handle numbered lists
            num_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
            if num_match:
                if not in_list or list_type != 'ol':
                    if in_list:
                        html_lines.append(f'</{list_type}>')
                    html_lines.append('<ol>')
                    in_list = True
                    list_type = 'ol'
                content = num_match.group(2)
                content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
                content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
                html_lines.append(f'<li>{escape_html(content) if "strong" not in content and "em" not in content else content}</li>')
                continue

            # Close list if we're no longer in one
            if in_list and stripped:
                html_lines.append(f'</{list_type}>')
                in_list = False

            # Handle empty lines
            if not stripped:
                continue

            # Regular paragraph with bold/italic support
            content = stripped
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
            if "<strong>" in content or "<em>" in content:
                html_lines.append(f'<p>{content}</p>')
            else:
                html_lines.append(f'<p>{escape_html(content)}</p>')

        # Close any open list
        if in_list:
            html_lines.append(f'</{list_type}>')

        return '\n'.join(html_lines)
