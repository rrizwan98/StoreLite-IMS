"""
MCP (Model Context Protocol) HTTP Client for discovering and calling tools.

This client communicates with the FastMCP server to:
1. Discover available tools and their schemas
2. Call tools with specific arguments
3. Cache tool list for performance
"""

import httpx
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MCPClient:
    """HTTP client for FastMCP server communication."""

    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        timeout: int = 10,
        cache_ttl_seconds: int = 300,
    ):
        """
        Initialize MCP client.

        Args:
            base_url: FastMCP server base URL
            timeout: HTTP request timeout in seconds
            cache_ttl_seconds: Tool list cache time-to-live
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.cache_ttl_seconds = cache_ttl_seconds
        self.client = httpx.Client(timeout=timeout)
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._cache_timestamp: Optional[datetime] = None

    def discover_tools(self) -> List[Dict[str, Any]]:
        """
        Discover available tools from MCP server.

        Returns:
            List of tool schemas with name, description, and input schema

        Raises:
            ConnectionError: If MCP server is unreachable
            ValueError: If response format is invalid
        """
        # Check cache
        if self._tools_cache and self._is_cache_valid():
            logger.debug("Returning cached tools list")
            return self._tools_cache

        try:
            logger.debug(f"Discovering tools from {self.base_url}/mcp/tools")
            response = self.client.get(f"{self.base_url}/mcp/tools")
            response.raise_for_status()

            data = response.json()
            tools = data.get("tools", [])

            # Cache the result
            self._tools_cache = tools
            self._cache_timestamp = datetime.utcnow()

            logger.info(f"Discovered {len(tools)} tools from MCP server")
            return tools

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to MCP server at {self.base_url}: {e}")
            raise ConnectionError(
                f"Unable to reach MCP server at {self.base_url}. "
                "Please ensure the FastMCP server is running."
            ) from e

        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to MCP server: {e}")
            raise ConnectionError(
                f"MCP server connection timed out after {self.timeout}s"
            ) from e

        except Exception as e:
            logger.error(f"Error discovering tools: {e}")
            raise ValueError(f"Invalid response from MCP server: {e}") from e

    def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result

        Raises:
            ConnectionError: If MCP server is unreachable
            ValueError: If tool not found or execution fails
        """
        try:
            logger.debug(f"Calling tool: {tool_name} with args: {arguments}")

            response = self.client.post(
                f"{self.base_url}/mcp/call",
                json={"tool": tool_name, "arguments": arguments},
            )
            response.raise_for_status()

            data = response.json()

            # Check for error in response
            if data.get("status") == "error":
                error_msg = data.get("error", "Unknown error")
                logger.error(f"Tool execution error: {error_msg}")
                raise ValueError(f"Tool execution failed: {error_msg}")

            result = data.get("result", {})
            logger.debug(f"Tool {tool_name} executed successfully")

            return result

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise ConnectionError(
                f"Unable to reach MCP server. Please try again."
            ) from e

        except httpx.TimeoutException as e:
            logger.error(f"Timeout calling tool {tool_name}: {e}")
            raise ConnectionError(
                f"MCP server request timed out. Please try again."
            ) from e

        except httpx.HTTPStatusError as e:
            logger.error(f"MCP server returned error {e.response.status_code}: {e}")
            raise ValueError(
                f"MCP server error: {e.response.status_code}"
            ) from e

        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise ValueError(f"Failed to call tool {tool_name}: {e}") from e

    def _is_cache_valid(self) -> bool:
        """Check if tool cache is still valid."""
        if not self._cache_timestamp:
            return False

        age = datetime.utcnow() - self._cache_timestamp
        return age < timedelta(seconds=self.cache_ttl_seconds)

    def clear_cache(self) -> None:
        """Clear the tool cache."""
        self._tools_cache = None
        self._cache_timestamp = None
        logger.debug("Tool cache cleared")

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()
        logger.debug("MCP client closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
