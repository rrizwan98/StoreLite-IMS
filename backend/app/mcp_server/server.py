"""
FastMCP server initialization and configuration
"""
from fastmcp import FastMCP


def create_server() -> FastMCP:
    """
    Create and configure FastMCP server with stdio and HTTP transports.

    Returns:
        FastMCP: Configured FastMCP server instance
    """
    # Initialize FastMCP server
    server = FastMCP("ims-mcp-server")

    # Transports will be configured when server is started:
    # - stdio: For Claude Code integration
    # - HTTP: For localhost:3000 access

    return server


async def run_server():
    """
    Start the MCP server with stdio transport (for Claude Code).
    """
    server = create_server()

    # Register tools will be added here in subsequent tasks

    # Run server with stdio transport
    async with server.stdio():
        # Server is now listening on stdio
        pass


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_server())
