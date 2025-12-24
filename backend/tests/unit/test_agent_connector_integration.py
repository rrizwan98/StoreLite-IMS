"""
Unit tests for Schema Agent + User Connector Tools Integration.

TDD Phase: Tests for loading and using user's MCP connector tools with Schema Agent.
"""

import pytest
import os
import sys
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock
from typing import List, Dict, Any

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestGetUserConnectorTools:
    """Tests for get_user_connector_tools function"""

    @pytest.mark.asyncio
    async def test_get_tools_for_verified_active_connector(self):
        """Should load tools from verified active connectors"""
        from app.connectors.agent_tools import get_user_connector_tools

        # Create mock connector
        mock_connector = MagicMock()
        mock_connector.id = 1
        mock_connector.user_id = 1
        mock_connector.name = "Notion - My Workspace"
        mock_connector.server_url = "https://mcp.notion.com/mcp"
        mock_connector.auth_type = "oauth"
        mock_connector.auth_config = "encrypted_config"
        mock_connector.is_active = True
        mock_connector.is_verified = True

        # Mock database session
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_connector]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock decrypt and load_connector_tools
        with patch("app.connectors.agent_tools.decrypt_credentials") as mock_decrypt, \
             patch("app.connectors.agent_tools.load_connector_tools") as mock_load:

            mock_decrypt.return_value = {"token": "secret_token"}

            # Create a mock FunctionTool
            mock_tool = MagicMock()
            mock_tool.name = "search_pages"
            mock_load.return_value = [mock_tool]

            tools = await get_user_connector_tools(mock_db, user_id=1)

            assert len(tools) == 1
            assert tools[0].name == "search_pages"
            mock_decrypt.assert_called_once()
            mock_load.assert_called_once_with(
                "https://mcp.notion.com/mcp",
                "Notion - My Workspace",
                "oauth",
                {"token": "secret_token"}
            )

    @pytest.mark.asyncio
    async def test_get_tools_skips_inactive_connectors(self):
        """Should not load tools from inactive connectors"""
        from app.connectors.agent_tools import get_user_connector_tools

        # Mock database session with no matching connectors
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        tools = await get_user_connector_tools(mock_db, user_id=1)

        assert len(tools) == 0

    @pytest.mark.asyncio
    async def test_get_tools_filters_by_connector_id(self):
        """Should filter by specific connector ID when provided"""
        from app.connectors.agent_tools import get_user_connector_tools

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.connectors.agent_tools.load_connector_tools") as mock_load:
            mock_load.return_value = []

            await get_user_connector_tools(mock_db, user_id=1, connector_id=5)

            # Verify the query was called (filter is applied at SQL level)
            mock_db.execute.assert_called_once()


class TestLoadConnectorTools:
    """Tests for load_connector_tools with OAuth authentication"""

    @pytest.mark.asyncio
    async def test_load_tools_with_oauth_auth(self):
        """Should pass auth_type and auth_config to MCP client"""
        from app.connectors.agent_tools import load_connector_tools

        with patch("app.connectors.agent_tools.UserMCPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.discover_tools = AsyncMock(return_value=[
                {
                    "name": "search_pages",
                    "description": "Search Notion pages",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"]
                    }
                }
            ])
            mock_client_class.return_value = mock_client

            tools = await load_connector_tools(
                connector_url="https://mcp.notion.com/mcp",
                connector_name="Notion",
                auth_type="oauth",
                auth_config={"token": "secret_abc123"}
            )

            # Verify MCP client was created with auth
            mock_client_class.assert_called_once_with(
                "https://mcp.notion.com/mcp",
                timeout=15.0,
                auth_type="oauth",
                auth_config={"token": "secret_abc123"}
            )

            assert len(tools) == 1
            assert tools[0].name == "search_pages"

    @pytest.mark.asyncio
    async def test_load_tools_handles_connection_errors(self):
        """Should return empty list on connection error"""
        from app.connectors.agent_tools import load_connector_tools

        with patch("app.connectors.agent_tools.UserMCPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.discover_tools = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client_class.return_value = mock_client

            tools = await load_connector_tools(
                connector_url="https://mcp.notion.com/mcp",
                connector_name="Notion",
                auth_type="oauth",
                auth_config={"token": "invalid_token"}
            )

            assert len(tools) == 0


class TestCreateConnectorTool:
    """Tests for create_connector_tool function"""

    def test_create_tool_with_valid_schema(self):
        """Should create FunctionTool from MCP tool definition"""
        from app.connectors.agent_tools import create_connector_tool

        tool_def = {
            "name": "create_page",
            "description": "Create a new Notion page",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Page title"},
                    "content": {"type": "string", "description": "Page content"}
                },
                "required": ["title"]
            }
        }

        tool = create_connector_tool(
            connector_url="https://mcp.notion.com/mcp",
            tool_def=tool_def,
            connector_name="Notion",
            auth_type="oauth",
            auth_config={"token": "test_token"}
        )

        assert tool is not None
        assert tool.name == "create_page"
        assert "Create a new Notion page" in tool.description

    def test_create_tool_cleans_additional_properties(self):
        """Should remove additionalProperties from schema (OpenAI strict mode)"""
        from app.connectors.agent_tools import clean_json_schema

        schema = {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "additionalProperties": False,
            "required": ["query"]
        }

        cleaned = clean_json_schema(schema)

        assert "additionalProperties" not in cleaned
        assert cleaned["type"] == "object"
        assert cleaned["properties"]["query"]["type"] == "string"


class TestSchemaAgentConnectorIntegration:
    """Tests for Schema Agent using connector tools"""

    @pytest.mark.asyncio
    async def test_agent_receives_connector_tools(self):
        """Schema Agent should receive connector tools on initialization"""
        from app.agents.schema_query_agent import SchemaQueryAgent

        # Create mock connector tools
        mock_tool = MagicMock()
        mock_tool.name = "notion_search"

        agent = SchemaQueryAgent(
            database_uri="postgresql://test:test@localhost/test",
            schema_metadata={"tables": []},
            connector_tools=[mock_tool]
        )

        assert len(agent.connector_tools) == 1
        assert agent.connector_tools[0].name == "notion_search"

    @pytest.mark.asyncio
    async def test_agent_logs_connector_tool_names(self):
        """Agent should track connector tool names for logging"""
        from app.agents.schema_query_agent import SchemaQueryAgent

        mock_tool1 = MagicMock()
        mock_tool1.name = "search_pages"
        mock_tool2 = MagicMock()
        mock_tool2.name = "create_page"

        agent = SchemaQueryAgent(
            database_uri="postgresql://test:test@localhost/test",
            schema_metadata={"tables": []},
            connector_tools=[mock_tool1, mock_tool2]
        )

        assert "search_pages" in agent._connector_tool_names
        assert "create_page" in agent._connector_tool_names


class TestChatKitConnectorContext:
    """Tests for connector context passing in ChatKit endpoint"""

    def test_connector_selection_in_context(self):
        """Context should include connector selection info"""
        context = {
            "user_id": 1,
            "database_uri": "postgresql://...",
            "schema_metadata": {},
            "selected_connector_id": 5,
            "selected_connector_url": "https://mcp.notion.com/mcp",
            "selected_connector_name": "Notion - My Workspace",
        }

        assert context["selected_connector_id"] == 5
        assert context["selected_connector_url"] == "https://mcp.notion.com/mcp"
        assert context["selected_connector_name"] == "Notion - My Workspace"

    def test_connector_prefix_parsing(self):
        """Should parse connector prefix from message body"""
        import re

        body_str = "[CONNECTOR:5:https://mcp.notion.com/mcp] Search for my meeting notes"

        connector_match = re.search(r'\[CONNECTOR:(\d+):([^\]]+)\]', body_str)

        assert connector_match is not None
        assert connector_match.group(1) == "5"
        assert connector_match.group(2) == "https://mcp.notion.com/mcp"


class TestOAuthConnectorToolExecution:
    """Tests for executing connector tools with OAuth authentication"""

    @pytest.mark.asyncio
    async def test_mcp_tool_caller_uses_auth(self):
        """Tool caller should pass auth config to MCP client"""
        from app.connectors.agent_tools import create_mcp_tool_function

        tool_func = create_mcp_tool_function(
            connector_url="https://mcp.notion.com/mcp",
            tool_name="search_pages",
            connector_name="Notion",
            auth_type="oauth",
            auth_config={"token": "secret_token_123"}
        )

        # Mock the client call
        with patch("app.connectors.agent_tools.UserMCPClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.call_tool = AsyncMock(return_value={
                "content": [{"type": "text", "text": "Found 5 pages"}]
            })
            mock_client_class.return_value = mock_client

            # Create mock context
            mock_ctx = MagicMock()

            result = await tool_func(mock_ctx, query="meeting notes")

            # Verify client was created with OAuth config
            mock_client_class.assert_called_once()
            call_args = mock_client_class.call_args
            assert call_args[1]["auth_type"] == "oauth"
            assert call_args[1]["auth_config"]["token"] == "secret_token_123"

            assert "Found 5 pages" in result
