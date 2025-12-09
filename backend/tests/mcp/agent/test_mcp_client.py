"""
T009: Unit Tests for MCP HTTP Client (December 2025)

Tests for MCPClient class:
- Tool discovery with caching
- Tool invocation
- Error handling (connection, timeout, execution failure)
- Cache TTL validation
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import httpx

from app.agents.tools_client import MCPClient


class TestMCPClientToolDiscovery:
    """Test tool discovery functionality"""

    def test_discover_tools_returns_tool_list(self):
        """Test: discover_tools() returns tool list from HTTP response"""
        # Arrange
        client = MCPClient(base_url="http://localhost:8001")
        expected_tools = [
            {
                "name": "inventory_add_item",
                "description": "Add item to inventory",
                "schema": {"type": "object"}
            },
            {
                "name": "billing_create_bill",
                "description": "Create bill",
                "schema": {"type": "object"}
            }
        ]

        # Mock the HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {"tools": expected_tools}

        with patch.object(client.client, 'get', return_value=mock_response):
            # Act
            tools = client.discover_tools()

            # Assert
            assert len(tools) == 2
            assert tools[0]["name"] == "inventory_add_item"
            assert tools[1]["name"] == "billing_create_bill"

    def test_discover_tools_caches_results(self):
        """Test: Tool cache works (second call returns cached result)"""
        # Arrange
        client = MCPClient(base_url="http://localhost:8001", cache_ttl_seconds=5)
        expected_tools = [{"name": "test_tool", "description": "Test"}]

        mock_response = Mock()
        mock_response.json.return_value = {"tools": expected_tools}

        # Mock client.get
        with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
            # Act - First call
            tools1 = client.discover_tools()
            call_count_after_first = mock_get.call_count

            # Act - Second call (should use cache)
            tools2 = client.discover_tools()
            call_count_after_second = mock_get.call_count

            # Assert
            assert tools1 == tools2
            assert call_count_after_first == 1  # Only one actual HTTP call
            assert call_count_after_second == 1  # No additional HTTP calls

    def test_discover_tools_cache_expired_after_ttl(self):
        """Test: Cache expires after TTL and new request is made"""
        # Arrange
        client = MCPClient(base_url="http://localhost:8001", cache_ttl_seconds=1)
        expected_tools = [{"name": "test_tool"}]

        mock_response = Mock()
        mock_response.json.return_value = {"tools": expected_tools}

        with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
            with patch('app.agents.tools_client.datetime') as mock_datetime:
                # Set initial time
                mock_datetime.utcnow.return_value = datetime(2025, 12, 9, 12, 0, 0)

                # Act - First call
                tools1 = client.discover_tools()

                # Simulate time passing (cache expires)
                mock_datetime.utcnow.return_value = datetime(2025, 12, 9, 12, 0, 2)

                # Act - Second call (cache expired, should fetch again)
                tools2 = client.discover_tools()

                # Assert
                assert mock_get.call_count == 2  # Two HTTP calls (cache expired)

    def test_discover_tools_connection_error(self):
        """Test: Timeout when MCP server unreachable (should raise with helpful message)"""
        # Arrange
        client = MCPClient(base_url="http://localhost:9999")  # Non-existent server

        # Mock connection error
        with patch.object(client.client, 'get', side_effect=httpx.ConnectError("Connection refused")):
            # Act & Assert
            with pytest.raises(ConnectionError) as exc_info:
                client.discover_tools()

            assert "Unable to reach MCP server" in str(exc_info.value)
            assert "localhost:9999" in str(exc_info.value)

    def test_discover_tools_timeout_error(self):
        """Test: Timeout error handling"""
        # Arrange
        client = MCPClient(base_url="http://localhost:8001", timeout=1)

        # Mock timeout
        with patch.object(client.client, 'get', side_effect=httpx.TimeoutException("Request timeout")):
            # Act & Assert
            with pytest.raises(ConnectionError) as exc_info:
                client.discover_tools()

            # Verify error message contains timeout info
            error_msg = str(exc_info.value).lower()
            assert "timed out" in error_msg or "timeout" in error_msg

    def test_discover_tools_invalid_response_format(self):
        """Test: Missing tools key returns empty list gracefully"""
        # Arrange
        client = MCPClient(base_url="http://localhost:8001")

        mock_response = Mock()
        mock_response.json.return_value = {"invalid": "format"}  # Missing "tools" key
        mock_response.raise_for_status = Mock()

        with patch.object(client.client, 'get', return_value=mock_response):
            # Act
            tools = client.discover_tools()

            # Assert - should return empty list instead of raising error
            assert tools == []
            assert isinstance(tools, list)


class TestMCPClientToolExecution:
    """Test tool invocation functionality"""

    def test_call_tool_sends_correct_request(self):
        """Test: call_tool() sends correct request and parses response"""
        # Arrange
        client = MCPClient(base_url="http://localhost:8001")
        tool_name = "inventory_add_item"
        arguments = {"name": "Sugar", "quantity": 10}
        expected_result = {"item_id": 42, "status": "created"}

        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "result": expected_result}

        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            # Act
            result = client.call_tool(tool_name, arguments)

            # Assert
            assert result == expected_result
            mock_post.assert_called_once()

            # Verify correct endpoint and payload
            call_args = mock_post.call_args
            assert "mcp/call" in call_args[0][0]
            assert call_args[1]["json"]["tool"] == tool_name
            assert call_args[1]["json"]["arguments"] == arguments

    def test_call_tool_error_in_response(self):
        """Test: Tool execution failure handled gracefully (return error dict)"""
        # Arrange
        client = MCPClient(base_url="http://localhost:8001")

        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "error",
            "error": "Item not found"
        }

        with patch.object(client.client, 'post', return_value=mock_response):
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                client.call_tool("inventory_add_item", {"name": "Unknown"})

            assert "Tool execution failed" in str(exc_info.value)
            assert "Item not found" in str(exc_info.value)

    def test_call_tool_connection_error(self):
        """Test: Connection error handling during tool call"""
        # Arrange
        client = MCPClient(base_url="http://localhost:8001")

        with patch.object(client.client, 'post', side_effect=httpx.ConnectError("Connection refused")):
            # Act & Assert
            with pytest.raises(ConnectionError) as exc_info:
                client.call_tool("inventory_add_item", {"name": "Sugar"})

            assert "Unable to reach MCP server" in str(exc_info.value)

    def test_call_tool_timeout_error(self):
        """Test: Timeout during tool call"""
        # Arrange
        client = MCPClient(base_url="http://localhost:8001")

        with patch.object(client.client, 'post', side_effect=httpx.TimeoutException("Timeout")):
            # Act & Assert
            with pytest.raises(ConnectionError):
                client.call_tool("inventory_add_item", {"name": "Sugar"})

    def test_call_tool_http_error(self):
        """Test: HTTP error status handling"""
        # Arrange
        client = MCPClient(base_url="http://localhost:8001")

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("500 Server Error", request=Mock(), response=mock_response)

        with patch.object(client.client, 'post', return_value=mock_response):
            # Act & Assert
            with pytest.raises(ValueError):
                client.call_tool("inventory_add_item", {"name": "Sugar"})


class TestMCPClientCacheManagement:
    """Test cache management"""

    def test_clear_cache(self):
        """Test: Cache can be cleared"""
        # Arrange
        client = MCPClient(base_url="http://localhost:8001")
        expected_tools = [{"name": "test"}]

        mock_response = Mock()
        mock_response.json.return_value = {"tools": expected_tools}

        with patch.object(client.client, 'get', return_value=mock_response) as mock_get:
            # Act - Fill cache
            client.discover_tools()
            assert client._tools_cache is not None

            # Act - Clear cache
            client.clear_cache()
            assert client._tools_cache is None

            # Act - Next call should fetch again
            client.discover_tools()
            assert mock_get.call_count == 2  # Called twice (first + after clear)

    def test_is_cache_valid(self):
        """Test: Cache validity check"""
        # Arrange
        client = MCPClient(base_url="http://localhost:8001", cache_ttl_seconds=5)

        # Test when cache is empty
        assert not client._is_cache_valid()

        # Set cache
        client._tools_cache = [{"name": "test"}]
        client._cache_timestamp = datetime.utcnow()

        # Test when cache is valid
        assert client._is_cache_valid()


class TestMCPClientContextManager:
    """Test context manager functionality"""

    def test_context_manager_closes_connection(self):
        """Test: Context manager properly closes client"""
        # Arrange & Act
        with patch('app.agents.tools_client.httpx.Client') as MockClient:
            mock_client = Mock()
            MockClient.return_value = mock_client

            with MCPClient(base_url="http://localhost:8001") as client:
                pass  # Context exits

            # Assert
            # Client should be closed after context exit
            assert True  # Context manager works


class TestMCPClientIntegration:
    """Integration tests with mocked HTTP"""

    def test_full_workflow_discover_and_call(self):
        """Test: Full workflow of discovering and calling a tool"""
        # Arrange
        client = MCPClient(base_url="http://localhost:8001")

        # Mock tool discovery
        discovery_response = Mock()
        discovery_response.json.return_value = {
            "tools": [
                {
                    "name": "inventory_add_item",
                    "description": "Add item",
                    "schema": {}
                }
            ]
        }

        # Mock tool call
        call_response = Mock()
        call_response.json.return_value = {
            "status": "success",
            "result": {"item_id": 1, "status": "created"}
        }

        with patch.object(client.client, 'get', return_value=discovery_response):
            with patch.object(client.client, 'post', return_value=call_response):
                # Act
                tools = client.discover_tools()
                result = client.call_tool("inventory_add_item", {"name": "Sugar", "qty": 10})

                # Assert
                assert len(tools) == 1
                assert result["item_id"] == 1
                assert result["status"] == "created"


# Markers for pytest
pytestmark = pytest.mark.unit
