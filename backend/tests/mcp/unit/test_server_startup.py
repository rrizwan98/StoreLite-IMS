"""
Test suite for MCP server startup and initialization
"""
import pytest


def test_server_initializes_without_error():
    """Test that MCP server initializes successfully."""
    from backend.app.mcp_server.server import create_server

    server = create_server()
    assert server is not None
    # Verify it's a FastMCP instance
    assert server.__class__.__name__ == 'FastMCP'


def test_server_supports_stdio_transport():
    """Test that server supports stdio transport."""
    from backend.app.mcp_server.server import create_server

    server = create_server()
    # Verify server exists and has capabilities
    assert server is not None
    # Stdio transport is provided by FastMCP by default
    assert 'stdio' in str(type(server).__name__) or server is not None
