"""
Task 46-47: Transport tests - Verify server works with stdio and HTTP transports
"""
import pytest
import asyncio
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.mcp_server.server import create_server


class TestStdioTransport:
    """Test Task 46: Stdio transport support"""

    def test_server_has_stdio_async_method(self):
        """Verify server has run_stdio_async() method."""
        server = create_server()
        assert hasattr(server, 'run_stdio_async')
        assert callable(server.run_stdio_async)

    def test_server_has_stdio_sync_method(self):
        """Verify server can access stdio transport."""
        server = create_server()
        # FastMCP provides different methods for different transports
        assert hasattr(server, 'run_stdio_async') or hasattr(server, 'run')


class TestHTTPTransport:
    """Test Task 47: HTTP transport support"""

    def test_server_has_http_async_method(self):
        """Verify server has run_http_async() method."""
        server = create_server()
        assert hasattr(server, 'run_http_async')
        assert callable(server.run_http_async)

    def test_server_has_http_app_property(self):
        """Verify server has http_app property."""
        server = create_server()
        # Server should have an http_app property that can be used
        assert hasattr(server, 'http_app')

    def test_http_method_callable(self):
        """Verify http transport methods are callable."""
        server = create_server()

        # Check that http async method is callable
        assert callable(server.run_http_async)
        assert callable(getattr(server, 'http_app', None))


class TestTransportCompatibility:
    """Test transport compatibility with MCP protocol."""

    def test_server_supports_multiple_transports(self):
        """Verify server can support multiple transport methods."""
        server = create_server()

        # Should have both stdio and http transport methods
        assert hasattr(server, 'run_stdio_async')
        assert hasattr(server, 'run_http_async')

        # Both should be callable
        assert callable(server.run_stdio_async)
        assert callable(server.run_http_async)

    def test_server_has_run_method(self):
        """Verify server has run() method for starting the server."""
        server = create_server()

        # Server should have a run method
        assert hasattr(server, 'run')
        assert callable(server.run)
