"""
MCP Client for User Connectors.

This module provides a client for connecting to external MCP servers
that users add as connectors. Uses HTTP/SSE transport with JSON-RPC protocol.

Supports the MCP (Model Context Protocol) specification:
- POST /mcp (or server endpoint) with JSON-RPC messages
- Methods: initialize, tools/list, tools/call
"""

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

    Supports MCP protocol via HTTP with JSON-RPC:
    - POST {server_url} with JSON-RPC messages
    - initialize → tools/list → tools/call

    Attributes:
        server_url: MCP server endpoint URL (trailing slash stripped)
        timeout: Request timeout in seconds (default 10.0)
    """

    def __init__(self, server_url: str, timeout: float = 10.0):
        """
        Initialize MCP client.

        Args:
            server_url: MCP server endpoint URL
            timeout: Request timeout in seconds (default 10.0, per FR-012)
        """
        # Strip whitespace and trailing slashes from URL
        self.server_url = server_url.strip().rstrip("/")
        self.timeout = timeout
        self._initialized = False
        self._request_id = 0

    def _next_id(self) -> int:
        """Get next JSON-RPC request ID."""
        self._request_id += 1
        return self._request_id

    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send JSON-RPC request to MCP server.

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

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.server_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error = data["error"]
                raise Exception(f"MCP error {error.get('code')}: {error.get('message')}")

            return data.get("result", {})

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
            return ValidationResult(
                success=False,
                error_code="INVALID_MCP_SERVER",
                error_message=f"Server returned error: {e.response.status_code}"
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

        result = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        return result
