"""
FastMCP server initialization and configuration
"""
from fastmcp import FastMCP
from app.database import async_session


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

    # Create wrapper functions that handle session internally
    # This is the recommended approach for FastMCP 2.x+

    # ===== Inventory Tools (User-Scoped) =====
    @server.tool()
    async def add_inventory_item(
        name: str,
        category: str,
        unit: str,
        unit_price: float,
        stock_qty: float,
        user_id: int = None
    ) -> dict:
        """Create new inventory item with normalized category (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await inventory_add_item(name, category, unit, unit_price, stock_qty, session, user_id)

    @server.tool()
    async def update_inventory_item(
        item_id: int,
        name: str = None,
        category: str = None,
        unit: str = None,
        unit_price: float = None,
        stock_qty: float = None,
        user_id: int = None
    ) -> dict:
        """Update inventory item (partial update allowed, user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await inventory_update_item(item_id, name, category, unit, unit_price, stock_qty, session, user_id)

    @server.tool()
    async def delete_inventory_item(item_id: int, user_id: int = None) -> dict:
        """Soft delete inventory item (sets is_active = FALSE, user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await inventory_delete_item(item_id, session, user_id)

    @server.tool()
    async def list_inventory_items(
        name: str = None,
        category: str = None,
        page: int = 1,
        limit: int = 20,
        user_id: int = None
    ) -> dict:
        """List inventory items with optional filtering and pagination (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await inventory_list_items(name, category, page, limit, session, user_id)

    # ===== Billing Tools (User-Scoped) =====
    @server.tool()
    async def create_bill(
        items: list,
        customer_name: str = None,
        store_name: str = None,
        user_id: int = None
    ) -> dict:
        """Create a bill with line items (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await billing_create_bill(items, customer_name, store_name, session, user_id)

    @server.tool()
    async def get_bill(bill_id: int, user_id: int = None) -> dict:
        """Get bill details with line items (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await billing_get_bill(bill_id, session, user_id)

    @server.tool()
    async def list_bills(
        start_date: str = None,
        end_date: str = None,
        page: int = 1,
        limit: int = 20,
        user_id: int = None
    ) -> dict:
        """List bills with optional date filtering and pagination (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await billing_list_bills(start_date, end_date, page, limit, session, user_id)

    # ===== Analytics Tools (Task T025 - AI Dashboard, User-Scoped) =====
    @server.tool()
    async def sales_by_month(year: int, month: int, user_id: int = None) -> dict:
        """Get sales summary for a specific month with top products (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await get_sales_by_month(year, month, session, user_id)

    @server.tool()
    async def compare_periods(period1: str, period2: str, user_id: int = None) -> dict:
        """Compare sales between two periods (format: YYYY-MM, user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await compare_sales(period1, period2, session, user_id)

    @server.tool()
    async def sales_trends(days: int = 30, user_id: int = None) -> dict:
        """Get sales trends for the specified number of days (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await get_sales_trends(days, session, user_id)

    @server.tool()
    async def inventory_analytics(user_id: int = None) -> dict:
        """Get comprehensive inventory analytics including stock levels and alerts (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await get_inventory_analytics(session, user_id)

    # Run server with HTTP transport on port 8001
    await server.run_async(transport="sse", host="127.0.0.1", port=8001)


async def run_server_stdio():
    """
    Start the MCP server with stdio transport (for Claude Code CLI).
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

    # Create wrapper functions that handle session internally (User-Scoped)
    @server.tool()
    async def add_inventory_item(
        name: str,
        category: str,
        unit: str,
        unit_price: float,
        stock_qty: float,
        user_id: int = None
    ) -> dict:
        """Create new inventory item with normalized category (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await inventory_add_item(name, category, unit, unit_price, stock_qty, session, user_id)

    @server.tool()
    async def update_inventory_item(
        item_id: int,
        name: str = None,
        category: str = None,
        unit: str = None,
        unit_price: float = None,
        stock_qty: float = None,
        user_id: int = None
    ) -> dict:
        """Update inventory item (partial update allowed, user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await inventory_update_item(item_id, name, category, unit, unit_price, stock_qty, session, user_id)

    @server.tool()
    async def delete_inventory_item(item_id: int, user_id: int = None) -> dict:
        """Soft delete inventory item (sets is_active = FALSE, user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await inventory_delete_item(item_id, session, user_id)

    @server.tool()
    async def list_inventory_items(
        name: str = None,
        category: str = None,
        page: int = 1,
        limit: int = 20,
        user_id: int = None
    ) -> dict:
        """List inventory items with optional filtering and pagination (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await inventory_list_items(name, category, page, limit, session, user_id)

    @server.tool()
    async def create_bill(
        items: list,
        customer_name: str = None,
        store_name: str = None,
        user_id: int = None
    ) -> dict:
        """Create a bill with line items (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await billing_create_bill(items, customer_name, store_name, session, user_id)

    @server.tool()
    async def get_bill(bill_id: int, user_id: int = None) -> dict:
        """Get bill details with line items (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await billing_get_bill(bill_id, session, user_id)

    @server.tool()
    async def list_bills(
        start_date: str = None,
        end_date: str = None,
        page: int = 1,
        limit: int = 20,
        user_id: int = None
    ) -> dict:
        """List bills with optional date filtering and pagination (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await billing_list_bills(start_date, end_date, page, limit, session, user_id)

    @server.tool()
    async def sales_by_month(year: int, month: int, user_id: int = None) -> dict:
        """Get sales summary for a specific month with top products (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await get_sales_by_month(year, month, session, user_id)

    @server.tool()
    async def compare_periods(period1: str, period2: str, user_id: int = None) -> dict:
        """Compare sales between two periods (format: YYYY-MM, user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await compare_sales(period1, period2, session, user_id)

    @server.tool()
    async def sales_trends(days: int = 30, user_id: int = None) -> dict:
        """Get sales trends for the specified number of days (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await get_sales_trends(days, session, user_id)

    @server.tool()
    async def inventory_analytics(user_id: int = None) -> dict:
        """Get comprehensive inventory analytics including stock levels and alerts (user-scoped). user_id is REQUIRED for data isolation."""
        async with async_session() as session:
            return await get_inventory_analytics(session, user_id)

    # Run server with stdio transport
    await server.run_stdio_async()


if __name__ == "__main__":
    import sys
    import asyncio

    # Check for --stdio flag for Claude Code CLI mode
    if "--stdio" in sys.argv:
        asyncio.run(run_server_stdio())
    else:
        # Default: HTTP mode on port 8001
        asyncio.run(run_server())
