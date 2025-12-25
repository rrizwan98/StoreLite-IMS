"""
MCP Client for User Connectors.

This module provides a client for connecting to external MCP servers
that users add as connectors. Supports both:
- HTTP POST with JSON-RPC (standard MCP)
- HTTP + SSE (Server-Sent Events) for streaming servers like Tavily

Supports the MCP (Model Context Protocol) specification:
- POST /mcp (or server endpoint) with JSON-RPC messages
- Methods: initialize, tools/list, tools/call

Authentication Types:
- none: No authentication
- oauth: Bearer token authentication (user provides OAuth token)
"""

import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of MCP connection validation"""
    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None


class UserMCPClient:
    """
    Client for connecting to user's external MCP servers.

    Supports MCP protocol via:
    1. HTTP POST with JSON-RPC (standard)
    2. HTTP + SSE for streaming responses (Tavily, etc.)

    Authentication:
    - none: No authentication headers
    - oauth: Bearer token in Authorization header

    Auto-detects transport based on response content-type.

    Attributes:
        server_url: MCP server endpoint URL (trailing slash stripped)
        timeout: Request timeout in seconds (default 10.0)
        auth_type: Authentication type ('none' or 'oauth')
        auth_token: Bearer token for OAuth authentication
    """

    def __init__(
        self,
        server_url: str,
        timeout: float = 10.0,
        auth_type: str = "none",
        auth_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize MCP client.

        Args:
            server_url: MCP server endpoint URL
            timeout: Request timeout in seconds (default 10.0, per FR-012)
            auth_type: Authentication type ('none' or 'oauth')
            auth_config: Authentication configuration with token for OAuth
        """
        # Strip whitespace and trailing slashes from URL
        self.server_url = server_url.strip().rstrip("/")
        self.timeout = timeout
        self.auth_type = auth_type
        self.auth_config = auth_config or {}
        self._initialized = False
        self._request_id = 0
        self._use_sse = False  # Auto-detected on first request
        self._session_id = None  # MCP session ID for Streamable HTTP transport

        # Extract token from auth_config for OAuth
        self._auth_token = None
        if auth_type == "oauth" and auth_config:
            # Support multiple token field names
            self._auth_token = (
                auth_config.get("token") or
                auth_config.get("access_token") or
                auth_config.get("api_key") or
                auth_config.get("bearer_token")
            )
            if self._auth_token:
                logger.info(f"[MCP Client] OAuth token configured for {server_url}")

    def _next_id(self) -> int:
        """Get next JSON-RPC request ID."""
        self._request_id += 1
        return self._request_id

    def _parse_sse_response(self, text: str) -> Dict[str, Any]:
        """
        Parse SSE (Server-Sent Events) response.

        SSE format:
        event: message
        data: {"jsonrpc": "2.0", ...}

        Args:
            text: Raw SSE response text

        Returns:
            Parsed JSON-RPC result
        """
        result = None
        lines = text.strip().split('\n')

        for line in lines:
            line = line.strip()

            # Skip empty lines and event lines
            if not line or line.startswith('event:'):
                continue

            # Parse data lines
            if line.startswith('data:'):
                data_str = line[5:].strip()
                if data_str:
                    try:
                        data = json.loads(data_str)
                        # Check for JSON-RPC result
                        if isinstance(data, dict):
                            if "result" in data:
                                result = data["result"]
                            elif "error" in data:
                                error = data["error"]
                                raise Exception(f"MCP error {error.get('code')}: {error.get('message')}")
                            # Some SSE sends just the result directly
                            elif "tools" in data or "content" in data:
                                result = data
                    except json.JSONDecodeError:
                        continue

        return result or {}

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers based on auth_type.

        Returns:
            Dict with Authorization header and any additional headers from auth_config
        """
        headers = {}

        if self.auth_type == "oauth" and self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
            logger.debug(f"[MCP Client] Adding Bearer token to request")

            # Add Notion-specific headers if connecting to Notion
            if "notion" in self.server_url.lower():
                headers["Notion-Version"] = self.auth_config.get(
                    "notion_version", "2022-06-28"
                )
                logger.debug(f"[MCP Client] Adding Notion-Version header")

        # Support for custom headers in auth_config
        custom_headers = self.auth_config.get("headers", {})
        if custom_headers:
            headers.update(custom_headers)

        return headers

    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send JSON-RPC request to MCP server.

        Supports MCP Streamable HTTP transport (2025-03-26 spec):
        - Accept header MUST include both application/json and text/event-stream
        - Mcp-Session-Id header for session continuity after initialization

        Args:
            method: JSON-RPC method name (e.g., 'initialize', 'tools/list')
            params: Method parameters

        Returns:
            Response result

        Raises:
            Exception: If request fails or returns error
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._next_id()
        }
        if params:
            payload["params"] = params

        # MCP Streamable HTTP transport requires BOTH content types in Accept header
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        # Add MCP session ID if we have one (required after initialization)
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        # Add authentication headers
        headers.update(self._get_auth_headers())

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.server_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()

            # Capture session ID from response headers
            if "mcp-session-id" in response.headers:
                self._session_id = response.headers["mcp-session-id"]
                logger.debug(f"[MCP Client] Session ID: {self._session_id[:8]}...")

            content_type = response.headers.get("content-type", "")
            logger.debug(f"[MCP Client] Response content-type: {content_type}")

            # Handle SSE response
            if "text/event-stream" in content_type:
                self._use_sse = True
                logger.info(f"[MCP Client] Using SSE transport for {self.server_url}")
                return self._parse_sse_response(response.text)

            # Handle JSON response
            try:
                data = response.json()
            except json.JSONDecodeError:
                # Try parsing as SSE if JSON fails
                logger.debug("[MCP Client] JSON parse failed, trying SSE parse")
                return self._parse_sse_response(response.text)

            if "error" in data:
                error = data["error"]
                raise Exception(f"MCP error {error.get('code')}: {error.get('message')}")

            return data.get("result", {})

    async def _send_sse_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send request and stream SSE response.

        For servers that require streaming (like Tavily, Notion MCP).

        Args:
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            Aggregated response result
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._next_id()
        }
        if params:
            payload["params"] = params

        # MCP Streamable HTTP transport requires BOTH content types
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        # Add MCP session ID if we have one
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        # Add authentication headers
        headers.update(self._get_auth_headers())

        result = {}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                self.server_url,
                json=payload,
                headers=headers
            ) as response:
                response.raise_for_status()

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk

                    # Process complete SSE messages
                    while "\n\n" in buffer:
                        message, buffer = buffer.split("\n\n", 1)
                        parsed = self._parse_sse_response(message)
                        if parsed:
                            # Merge results (for tools/list, etc.)
                            if "tools" in parsed:
                                result["tools"] = result.get("tools", []) + parsed["tools"]
                            elif "content" in parsed:
                                result["content"] = result.get("content", []) + parsed.get("content", [])
                            else:
                                result.update(parsed)

                # Process remaining buffer
                if buffer.strip():
                    parsed = self._parse_sse_response(buffer)
                    if parsed:
                        if "tools" in parsed:
                            result["tools"] = result.get("tools", []) + parsed["tools"]
                        else:
                            result.update(parsed)

        return result

    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize MCP session.

        Returns:
            Server info and capabilities
        """
        result = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "IMS-Agent",
                "version": "1.0"
            }
        })
        self._initialized = True
        return result

    async def discover_tools(self) -> List[Dict[str, Any]]:
        """
        Discover tools from the MCP server.

        Returns:
            List of tool definitions (each with name, description, inputSchema)

        Raises:
            httpx.TimeoutException: If request times out
            httpx.ConnectError: If cannot connect to server
            Exception: If server returns error
        """
        # Initialize first if not done
        if not self._initialized:
            await self.initialize()

        # Use SSE streaming if detected
        if self._use_sse:
            result = await self._send_sse_request("tools/list", {})
        else:
            result = await self._send_request("tools/list", {})

        return result.get("tools", [])

    async def validate_connection(self) -> ValidationResult:
        """
        Validate connection to MCP server with 10-second timeout.

        Attempts to connect and discover tools. Returns ValidationResult
        with appropriate error codes:
        - TIMEOUT: Connection timed out
        - CONNECTION_FAILED: Cannot connect to server
        - INVALID_MCP_SERVER: Not a valid MCP server

        Returns:
            ValidationResult with success status and discovered tools or error info
        """
        try:
            tools = await self.discover_tools()

            if not tools:
                return ValidationResult(
                    success=True,
                    error_message="Connected but no tools found on this MCP server.",
                    tools=[]
                )

            return ValidationResult(success=True, tools=tools)

        except httpx.TimeoutException:
            logger.warning(f"Connection to {self.server_url} timed out")
            return ValidationResult(
                success=False,
                error_code="TIMEOUT",
                error_message=f"Connection timed out after {self.timeout} seconds."
            )
        except httpx.ConnectError as e:
            logger.warning(f"Cannot connect to {self.server_url}: {e}")
            return ValidationResult(
                success=False,
                error_code="CONNECTION_FAILED",
                error_message="Cannot connect to server. Please check the URL."
            )
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error from {self.server_url}: {e}")
            status_code = e.response.status_code

            # Provide specific error messages based on status code
            if status_code == 401:
                error_message = "Authentication failed. "
                if "notion" in self.server_url.lower():
                    error_message += "Please verify your Notion Integration Token is correct and the integration has access to your workspace pages."
                else:
                    error_message += "Please check your API token is correct and not expired."
                return ValidationResult(
                    success=False,
                    error_code="AUTH_FAILED",
                    error_message=error_message
                )
            elif status_code == 403:
                return ValidationResult(
                    success=False,
                    error_code="AUTH_FAILED",
                    error_message="Access forbidden. The token may not have sufficient permissions."
                )
            else:
                return ValidationResult(
                    success=False,
                    error_code="INVALID_MCP_SERVER",
                    error_message=f"Server returned error: {status_code}"
                )
        except Exception as e:
            logger.error(f"Unexpected error validating {self.server_url}: {e}")
            return ValidationResult(
                success=False,
                error_code="INVALID_MCP_SERVER",
                error_message=f"This doesn't appear to be a valid MCP server: {e}"
            )

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result

        Raises:
            httpx.TimeoutException: If request times out
            httpx.ConnectError: If cannot connect to server
            Exception: If server returns error
        """
        # Initialize first if not done
        if not self._initialized:
            await self.initialize()

        # Use SSE streaming if detected
        if self._use_sse:
            result = await self._send_sse_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
        else:
            result = await self._send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })

        return result
