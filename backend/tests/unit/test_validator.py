"""
Unit tests for connection validator module.

TDD Phase: RED - Write failing tests FIRST.

These tests define the expected behavior of the connection validator
before implementation exists. All tests should FAIL initially.
"""

import pytest
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestURLValidation:
    """Tests for URL format validation"""

    @pytest.mark.asyncio
    async def test_invalid_url_format(self):
        """Invalid URL format should return INVALID_URL error"""
        from app.connectors.validator import validate_mcp_connection

        result = await validate_mcp_connection("not-a-url")
        assert result.success is False
        assert result.error_code == "INVALID_URL"
        assert "url" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_missing_scheme(self):
        """URL without scheme should return INVALID_URL error"""
        from app.connectors.validator import validate_mcp_connection

        result = await validate_mcp_connection("localhost:8001")
        assert result.success is False
        assert result.error_code == "INVALID_URL"

    @pytest.mark.asyncio
    async def test_invalid_scheme(self):
        """URL with non-http scheme should return INVALID_URL error"""
        from app.connectors.validator import validate_mcp_connection

        result = await validate_mcp_connection("ftp://server.com/mcp")
        assert result.success is False
        assert result.error_code == "INVALID_URL"

    @pytest.mark.asyncio
    async def test_valid_http_url_format(self):
        """Valid HTTP URL should pass format validation"""
        from app.connectors.validator import validate_mcp_connection

        # This will fail connection but should pass URL validation
        # (won't get INVALID_URL error code)
        with patch("app.connectors.mcp_client.UserMCPClient.validate_connection") as mock:
            mock.return_value = MagicMock(success=True, tools=[])
            from app.connectors.mcp_client import ValidationResult
            mock.return_value = ValidationResult(success=True, tools=[])

            result = await validate_mcp_connection("http://localhost:8001")
            # Should not be INVALID_URL since format is valid
            assert result.error_code != "INVALID_URL" or result.success is True

    @pytest.mark.asyncio
    async def test_valid_https_url_format(self):
        """Valid HTTPS URL should pass format validation"""
        from app.connectors.validator import validate_mcp_connection

        with patch("app.connectors.mcp_client.UserMCPClient.validate_connection") as mock:
            from app.connectors.mcp_client import ValidationResult
            mock.return_value = ValidationResult(success=True, tools=[])

            result = await validate_mcp_connection("https://mcp.example.com")
            # Should not be INVALID_URL since format is valid
            assert result.error_code != "INVALID_URL" or result.success is True


class TestConnectionValidation:
    """Tests for actual connection validation"""

    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Connection timeout should return TIMEOUT error"""
        from app.connectors.validator import validate_mcp_connection

        with patch("app.connectors.mcp_client.UserMCPClient.validate_connection") as mock:
            from app.connectors.mcp_client import ValidationResult
            mock.return_value = ValidationResult(
                success=False,
                error_code="TIMEOUT",
                error_message="Connection timed out"
            )

            result = await validate_mcp_connection("http://slow-server.example.com")
            assert result.success is False
            assert result.error_code == "TIMEOUT"

    @pytest.mark.asyncio
    async def test_connection_failed(self):
        """Unreachable server should return CONNECTION_FAILED error"""
        from app.connectors.validator import validate_mcp_connection

        with patch("app.connectors.mcp_client.UserMCPClient.validate_connection") as mock:
            from app.connectors.mcp_client import ValidationResult
            mock.return_value = ValidationResult(
                success=False,
                error_code="CONNECTION_FAILED",
                error_message="Cannot connect"
            )

            result = await validate_mcp_connection("http://192.0.2.1:9999")
            assert result.success is False
            assert result.error_code == "CONNECTION_FAILED"

    @pytest.mark.asyncio
    async def test_invalid_mcp_server(self):
        """Non-MCP server should return INVALID_MCP_SERVER error"""
        from app.connectors.validator import validate_mcp_connection

        with patch("app.connectors.mcp_client.UserMCPClient.validate_connection") as mock:
            from app.connectors.mcp_client import ValidationResult
            mock.return_value = ValidationResult(
                success=False,
                error_code="INVALID_MCP_SERVER",
                error_message="Not a valid MCP server"
            )

            result = await validate_mcp_connection("http://example.com")
            assert result.success is False
            assert result.error_code == "INVALID_MCP_SERVER"


class TestSuccessfulValidation:
    """Tests for successful connection validation"""

    @pytest.mark.asyncio
    async def test_successful_connection_with_tools(self):
        """Successful connection should return tools"""
        from app.connectors.validator import validate_mcp_connection

        with patch("app.connectors.mcp_client.UserMCPClient.validate_connection") as mock:
            from app.connectors.mcp_client import ValidationResult
            mock.return_value = ValidationResult(
                success=True,
                tools=[
                    {"name": "tool1", "description": "First tool"},
                    {"name": "tool2", "description": "Second tool"}
                ]
            )

            result = await validate_mcp_connection("http://valid-mcp.example.com")
            assert result.success is True
            assert result.error_code is None
            assert len(result.tools) == 2

    @pytest.mark.asyncio
    async def test_successful_connection_no_tools_warning(self):
        """Successful connection with no tools should include warning"""
        from app.connectors.validator import validate_mcp_connection

        with patch("app.connectors.mcp_client.UserMCPClient.validate_connection") as mock:
            from app.connectors.mcp_client import ValidationResult
            mock.return_value = ValidationResult(
                success=True,
                error_message="No tools found",
                tools=[]
            )

            result = await validate_mcp_connection("http://empty-mcp.example.com")
            assert result.success is True
            assert result.error_message is not None  # Has warning
            assert result.tools == []


class TestAuthTypeValidation:
    """Tests for authentication type handling"""

    @pytest.mark.asyncio
    async def test_oauth_auth_type(self):
        """OAuth auth type should be passed to client"""
        from app.connectors.validator import validate_mcp_connection

        with patch("app.connectors.mcp_client.UserMCPClient.validate_connection") as mock:
            from app.connectors.mcp_client import ValidationResult
            mock.return_value = ValidationResult(success=True, tools=[])

            result = await validate_mcp_connection(
                "http://oauth-server.example.com",
                auth_type="oauth",
                auth_config={"access_token": "token123"}
            )
            assert result.success is True

    @pytest.mark.asyncio
    async def test_api_key_auth_type(self):
        """API key auth type should be passed to client"""
        from app.connectors.validator import validate_mcp_connection

        with patch("app.connectors.mcp_client.UserMCPClient.validate_connection") as mock:
            from app.connectors.mcp_client import ValidationResult
            mock.return_value = ValidationResult(success=True, tools=[])

            result = await validate_mcp_connection(
                "http://api-key-server.example.com",
                auth_type="api_key",
                auth_config={"api_key": "sk-123"}
            )
            assert result.success is True

    @pytest.mark.asyncio
    async def test_auth_failed(self):
        """Authentication failure should return AUTH_FAILED error"""
        from app.connectors.validator import validate_mcp_connection

        with patch("app.connectors.mcp_client.UserMCPClient.validate_connection") as mock:
            from app.connectors.mcp_client import ValidationResult
            mock.return_value = ValidationResult(
                success=False,
                error_code="AUTH_FAILED",
                error_message="Authentication failed"
            )

            result = await validate_mcp_connection(
                "http://auth-server.example.com",
                auth_type="oauth",
                auth_config={"access_token": "invalid"}
            )
            assert result.success is False
            assert result.error_code == "AUTH_FAILED"
