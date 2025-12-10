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
    from app.mcp_server.tools_inventory import (
        inventory_add_item,
        inventory_update_item,
        inventory_delete_item,
        inventory_list_items,
    )
    from app.mcp_server.tools_billing import (
        billing_create_bill,
        billing_get_bill,
        billing_list_bills,
    )
    from app.mcp_server.tools_analytics import (
        get_sales_by_month,
        compare_sales,
        get_sales_trends,
        get_inventory_analytics,
    )

    server = create_server()

    # Register tools excluding 'session' parameter (managed internally)
    # Inventory tools
    server.tool(exclude_args=["session"])(inventory_add_item)
    server.tool(exclude_args=["session"])(inventory_update_item)
    server.tool(exclude_args=["session"])(inventory_delete_item)
    server.tool(exclude_args=["session"])(inventory_list_items)

    # Billing tools
    server.tool(exclude_args=["session"])(billing_create_bill)
    server.tool(exclude_args=["session"])(billing_get_bill)
    server.tool(exclude_args=["session"])(billing_list_bills)

    # Analytics tools (Task T025 - AI Dashboard)
    server.tool(exclude_args=["session"])(get_sales_by_month)
    server.tool(exclude_args=["session"])(compare_sales)
    server.tool(exclude_args=["session"])(get_sales_trends)
    server.tool(exclude_args=["session"])(get_inventory_analytics)

    # Run server with stdio transport
    await server.run_stdio_async()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_server())
