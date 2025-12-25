"""
Unit tests for UserMCPClient module.

TDD Phase: RED - Write failing tests FIRST.

These tests define the expected behavior of the MCP client
before implementation exists. All tests should FAIL initially.
"""

import pytest
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestUserMCPClientBasic:
    """Basic tests for UserMCPClient initialization and configuration"""

    def test_client_initialization(self):
        """Client should initialize with server URL"""
        from app.connectors.mcp_client import UserMCPClient

        client = UserMCPClient("http://localhost:8001")
        assert client.server_url == "http://localhost:8001"

    def test_client_strips_trailing_slash(self):
        """Client should strip trailing slash from URL"""
        from app.connectors.mcp_client import UserMCPClient

        client = UserMCPClient("http://localhost:8001/")
        assert client.server_url == "http://localhost:8001"

    def test_client_default_timeout(self):
        """Client should have 10 second default timeout"""
        from app.connectors.mcp_client import UserMCPClient

        client = UserMCPClient("http://localhost:8001")
        assert client.timeout == 10.0

    def test_client_custom_timeout(self):
        """Client should accept custom timeout"""
        from app.connectors.mcp_client import UserMCPClient

        client = UserMCPClient("http://localhost:8001", timeout=5.0)
        assert client.timeout == 5.0


class TestUserMCPClientDiscoverTools:
    """Tests for tool discovery functionality"""

    @pytest.mark.asyncio
    async def test_discover_tools_returns_list(self):
        """discover_tools should return a list"""
        from app.connectors.mcp_client import UserMCPClient

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tools": [
                {"name": "tool1", "description": "First tool"},
                {"name": "tool2", "description": "Second tool"}
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = UserMCPClient("http://localhost:8001")
            tools = await client.discover_tools()

            assert isinstance(tools, list)
            assert len(tools) == 2
            assert tools[0]["name"] == "tool1"

    @pytest.mark.asyncio
    async def test_discover_tools_empty_list(self):
        """discover_tools should return empty list if server has no tools"""
        from app.connectors.mcp_client import UserMCPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tools": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = UserMCPClient("http://localhost:8001")
            tools = await client.discover_tools()

            assert isinstance(tools, list)
            assert len(tools) == 0


class TestValidationResult:
    """Tests for ValidationResult data class"""

    def test_validation_result_success(self):
        """ValidationResult should represent success state"""
        from app.connectors.mcp_client import ValidationResult

        result = ValidationResult(
            success=True,
            tools=[{"name": "tool1"}]
        )
        assert result.success is True
        assert result.error_code is None
        assert result.error_message is None
        assert len(result.tools) == 1

    def test_validation_result_failure(self):
        """ValidationResult should represent failure state"""
        from app.connectors.mcp_client import ValidationResult

        result = ValidationResult(
            success=False,
            error_code="TIMEOUT",
            error_message="Connection timed out"
        )
        assert result.success is False
        assert result.error_code == "TIMEOUT"
        assert result.error_message == "Connection timed out"
        assert result.tools is None


class TestUserMCPClientValidateConnection:
    """Tests for connection validation functionality"""

    @pytest.mark.asyncio
    async def test_validate_connection_success(self):
        """validate_connection should return success with tools on valid connection"""
        from app.connectors.mcp_client import UserMCPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tools": [{"name": "tool1", "description": "Test tool"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = UserMCPClient("http://localhost:8001")
            result = await client.validate_connection()

            assert result.success is True
            assert result.error_code is None
            assert len(result.tools) == 1

    @pytest.mark.asyncio
    async def test_validate_connection_no_tools_warning(self):
        """validate_connection should return success but with warning when no tools found"""
        from app.connectors.mcp_client import UserMCPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tools": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = UserMCPClient("http://localhost:8001")
            result = await client.validate_connection()

            assert result.success is True
            assert result.error_message is not None
            assert "no tools" in result.error_message.lower()
            assert result.tools == []

    @pytest.mark.asyncio
    async def test_validate_connection_timeout(self):
        """validate_connection should return TIMEOUT error on timeout"""
        from app.connectors.mcp_client import UserMCPClient
        import asyncio

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = UserMCPClient("http://localhost:8001")
            result = await client.validate_connection()

            assert result.success is False
            assert result.error_code == "TIMEOUT"
            assert "timed out" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_validate_connection_connect_error(self):
        """validate_connection should return CONNECTION_FAILED on connection error"""
        from app.connectors.mcp_client import UserMCPClient

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Cannot connect"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = UserMCPClient("http://localhost:8001")
            result = await client.validate_connection()

            assert result.success is False
            assert result.error_code == "CONNECTION_FAILED"

    @pytest.mark.asyncio
    async def test_validate_connection_invalid_response(self):
        """validate_connection should return INVALID_MCP_SERVER on non-MCP response"""
        from app.connectors.mcp_client import UserMCPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"not_tools": "invalid"}  # Missing "tools" key
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = UserMCPClient("http://localhost:8001")
            result = await client.validate_connection()

            # Should still succeed but with empty tools if server doesn't have "tools" key
            # Or fail if we strictly require MCP format
            assert result.success is True or result.error_code == "INVALID_MCP_SERVER"

    @pytest.mark.asyncio
    async def test_validate_connection_http_error(self):
        """validate_connection should handle HTTP errors"""
        from app.connectors.mcp_client import UserMCPClient

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_response)
            )
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = UserMCPClient("http://localhost:8001")
            result = await client.validate_connection()

            assert result.success is False
            assert result.error_code in ["INVALID_MCP_SERVER", "CONNECTION_FAILED"]


class TestUserMCPClientCallTool:
    """Tests for tool calling functionality"""

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """call_tool should return result on success"""
        from app.connectors.mcp_client import UserMCPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"status": "success", "data": "test"}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = UserMCPClient("http://localhost:8001")
            result = await client.call_tool("test_tool", {"arg1": "value1"})

            assert result["status"] == "success"
            assert result["data"] == "test"

    @pytest.mark.asyncio
    async def test_call_tool_with_correct_payload(self):
        """call_tool should send correct JSON payload"""
        from app.connectors.mcp_client import UserMCPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = UserMCPClient("http://localhost:8001")
            await client.call_tool("my_tool", {"key": "value"})

            # Verify the POST was called with correct URL and payload
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "/mcp/call" in call_args[0][0]
            assert call_args[1]["json"]["tool"] == "my_tool"
            assert call_args[1]["json"]["arguments"] == {"key": "value"}
