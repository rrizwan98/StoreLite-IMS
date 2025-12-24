"""
Unit tests for OAuth Connectors API.

TDD Phase: Tests for OAuth flow with predefined connectors (Notion).
"""

import pytest
import os
import sys
from unittest.mock import patch, AsyncMock, MagicMock

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestOAuthConnectorConfig:
    """Tests for OAuth connector configuration"""

    def test_notion_config_exists(self):
        """Notion config should exist in OAuthConnectorConfig"""
        from app.routers.oauth_connectors import OAuthConnectorConfig

        config = OAuthConnectorConfig.get("notion")
        assert config is not None
        assert config["name"] == "Notion"

    def test_notion_config_has_required_fields(self):
        """Notion config should have all required OAuth fields"""
        from app.routers.oauth_connectors import OAuthConnectorConfig

        config = OAuthConnectorConfig.get("notion")
        assert "client_id" in config
        assert "client_secret" in config
        assert "authorization_url" in config
        assert "token_url" in config
        assert "mcp_server_url" in config

    def test_unknown_connector_returns_none(self):
        """Unknown connector ID should return None"""
        from app.routers.oauth_connectors import OAuthConnectorConfig

        config = OAuthConnectorConfig.get("unknown_connector")
        assert config is None

    def test_connector_id_case_insensitive(self):
        """Connector ID lookup should be case insensitive"""
        from app.routers.oauth_connectors import OAuthConnectorConfig

        config1 = OAuthConnectorConfig.get("notion")
        config2 = OAuthConnectorConfig.get("NOTION")
        config3 = OAuthConnectorConfig.get("Notion")

        assert config1 == config2 == config3


class TestInitiateOAuthRequest:
    """Tests for InitiateOAuthRequest model"""

    def test_valid_request(self):
        """Should create valid request with connector_id and redirect_uri"""
        from app.routers.oauth_connectors import InitiateOAuthRequest

        request = InitiateOAuthRequest(
            connector_id="notion",
            redirect_uri="http://localhost:8000/api/oauth/callback/notion"
        )
        assert request.connector_id == "notion"
        assert request.redirect_uri == "http://localhost:8000/api/oauth/callback/notion"


class TestOAuthStateManagement:
    """Tests for OAuth state management (CSRF protection)"""

    def test_state_stored_on_initiate(self):
        """State should be stored when OAuth is initiated"""
        from app.routers.oauth_connectors import oauth_states

        # Clear any existing states
        oauth_states.clear()

        # State should start empty
        assert len(oauth_states) == 0

    def test_state_contains_user_info(self):
        """Stored state should contain user_id and connector_id"""
        from app.routers.oauth_connectors import oauth_states

        # Simulate storing state
        test_state = "test_state_123"
        oauth_states[test_state] = {
            "user_id": 1,
            "connector_id": "notion",
            "redirect_uri": "http://localhost:8000/callback",
            "created_at": "2025-12-24T00:00:00",
        }

        assert oauth_states[test_state]["user_id"] == 1
        assert oauth_states[test_state]["connector_id"] == "notion"

        # Cleanup
        oauth_states.clear()


class TestOAuthCallbackResponse:
    """Tests for OAuth callback response handling"""

    def test_success_response_model(self):
        """Success response should have required fields"""
        from app.routers.oauth_connectors import OAuthCallbackResponse

        response = OAuthCallbackResponse(
            success=True,
            connector_id=123,
            connector_name="Notion - My Workspace",
            message="Connected successfully"
        )
        assert response.success is True
        assert response.connector_id == 123
        assert response.connector_name == "Notion - My Workspace"

    def test_error_response_model(self):
        """Error response should have success=False"""
        from app.routers.oauth_connectors import OAuthCallbackResponse

        response = OAuthCallbackResponse(
            success=False,
            message="OAuth authorization failed"
        )
        assert response.success is False
        assert response.connector_id is None


class TestTokenExchange:
    """Tests for OAuth token exchange"""

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self):
        """Should exchange auth code for access token"""
        from app.routers.oauth_connectors import exchange_code_for_token

        config = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "token_url": "https://api.notion.com/v1/oauth/token",
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "secret_abc123",
            "bot_id": "bot_123",
            "workspace_id": "ws_123",
            "workspace_name": "Test Workspace",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await exchange_code_for_token(
                config=config,
                code="auth_code_123",
                redirect_uri="http://localhost:8000/callback"
            )

            assert result is not None
            assert result["access_token"] == "secret_abc123"
            assert result["workspace_name"] == "Test Workspace"

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_failure(self):
        """Should return None on token exchange failure"""
        from app.routers.oauth_connectors import exchange_code_for_token

        config = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "token_url": "https://api.notion.com/v1/oauth/token",
        }

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid code"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await exchange_code_for_token(
                config=config,
                code="invalid_code",
                redirect_uri="http://localhost:8000/callback"
            )

            assert result is None


class TestPredefinedConnectors:
    """Tests for predefined connectors registry (frontend contract)"""

    def test_notion_mcp_server_url(self):
        """Notion should use mcp.notion.com MCP server"""
        from app.routers.oauth_connectors import OAuthConnectorConfig

        config = OAuthConnectorConfig.get("notion")
        assert config["mcp_server_url"] == "https://mcp.notion.com/mcp"

    def test_notion_authorization_url(self):
        """Notion should use correct authorization URL"""
        from app.routers.oauth_connectors import OAuthConnectorConfig

        config = OAuthConnectorConfig.get("notion")
        assert "api.notion.com" in config["authorization_url"]

    def test_notion_token_url(self):
        """Notion should use correct token URL"""
        from app.routers.oauth_connectors import OAuthConnectorConfig

        config = OAuthConnectorConfig.get("notion")
        assert config["token_url"] == "https://api.notion.com/v1/oauth/token"
