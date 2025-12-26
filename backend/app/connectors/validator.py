"""
Connection Validator for User MCP Connectors.

This module provides URL validation and connection testing for MCP servers.
Validates:
1. URL format (must be HTTP/HTTPS)
2. Actual connection (timeout, connection errors, MCP validity)
"""

import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from .mcp_client import UserMCPClient, ValidationResult

logger = logging.getLogger(__name__)


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid HTTP/HTTPS format.

    Args:
        url: URL string to validate

    Returns:
        True if valid HTTP/HTTPS URL, False otherwise
    """
    try:
        parsed = urlparse(url)
        # Must have scheme and netloc (host)
        if not parsed.scheme or not parsed.netloc:
            return False
        # Must be HTTP or HTTPS
        if parsed.scheme.lower() not in ("http", "https"):
            return False
        return True
    except Exception:
        return False


async def validate_mcp_connection(
    server_url: str,
    auth_type: str = "none",
    auth_config: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0
) -> ValidationResult:
    """
    Validate MCP server connection.

    Performs two-step validation:
    1. URL format validation (fast, no network)
    2. Connection validation (network call, 10-second timeout)

    Args:
        server_url: MCP server URL to validate
        auth_type: Authentication type ('none', 'oauth', 'api_key')
        auth_config: Authentication configuration (encrypted)
        timeout: Connection timeout in seconds (default 10.0)

    Returns:
        ValidationResult with:
        - success: True if connection successful
        - error_code: Error code if failed (INVALID_URL, TIMEOUT, CONNECTION_FAILED,
                     AUTH_FAILED, INVALID_MCP_SERVER)
        - error_message: Human-readable error message
        - tools: List of discovered tools (on success)

    Error Codes:
        - INVALID_URL: URL format is invalid (not HTTP/HTTPS)
        - CONNECTION_FAILED: Cannot connect to server
        - TIMEOUT: Connection timed out after 10 seconds
        - AUTH_FAILED: Authentication failed
        - INVALID_MCP_SERVER: Server is not a valid MCP server
    """
    # Step 1: URL format validation (fast, no network)
    if not is_valid_url(server_url):
        logger.warning(f"Invalid URL format: {server_url}")
        return ValidationResult(
            success=False,
            error_code="INVALID_URL",
            error_message="Invalid URL format. Must be a valid HTTP or HTTPS URL."
        )

    # Step 2: Connection validation (network call)
    logger.info(f"Validating MCP connection to {server_url} (auth_type={auth_type}, timeout={timeout}s)")

    # Create MCP client with authentication
    client = UserMCPClient(
        server_url,
        timeout=timeout,
        auth_type=auth_type,
        auth_config=auth_config
    )
    result = await client.validate_connection()

    # Log the result
    if result.success:
        tool_count = len(result.tools) if result.tools else 0
        logger.info(f"MCP connection validated: {server_url} ({tool_count} tools)")
    else:
        logger.warning(f"MCP connection failed: {server_url} - {result.error_code}: {result.error_message}")

    return result
