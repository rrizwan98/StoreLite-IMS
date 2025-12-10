"""
FastMCP Server HTTP Wrapper
Provides HTTP endpoints for MCP tool discovery and execution
"""

import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

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
from app.database import async_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app for MCP HTTP wrapper
app = FastAPI(title="IMS MCP Server", version="1.0.0")

# Tool registry
TOOLS = {
    "inventory_add_item": {
        "func": inventory_add_item,
        "description": "Add item to inventory",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "category": {"type": "string"},
                "unit": {"type": "string"},
                "unit_price": {"type": "number"},
                "stock_qty": {"type": "number"},
            },
            "required": ["name", "category", "unit", "unit_price", "stock_qty"],
        },
    },
    "inventory_update_item": {
        "func": inventory_update_item,
        "description": "Update item in inventory",
        "schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "integer"},
                "name": {"type": "string"},
                "unit_price": {"type": "number"},
                "stock_qty": {"type": "number"},
            },
            "required": ["item_id"],
        },
    },
    "inventory_delete_item": {
        "func": inventory_delete_item,
        "description": "Delete item from inventory",
        "schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "integer"},
            },
            "required": ["item_id"],
        },
    },
    "inventory_list_items": {
        "func": inventory_list_items,
        "description": "List all items in inventory",
        "schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "nullable": True},
            },
        },
    },
    "billing_create_bill": {
        "func": billing_create_bill,
        "description": "Create a new bill",
        "schema": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item_id": {"type": "integer"},
                            "quantity": {"type": "number"},
                        },
                    },
                },
            },
            "required": ["customer_name", "items"],
        },
    },
    "billing_get_bill": {
        "func": billing_get_bill,
        "description": "Get bill details",
        "schema": {
            "type": "object",
            "properties": {
                "bill_id": {"type": "integer"},
            },
            "required": ["bill_id"],
        },
    },
    "billing_list_bills": {
        "func": billing_list_bills,
        "description": "List all bills",
        "schema": {
            "type": "object",
            "properties": {},
        },
    },
    # Analytics tools (Task T025 - AI Dashboard)
    "get_sales_by_month": {
        "func": get_sales_by_month,
        "description": "Get sales summary for a specific month with top products, daily trends, and statistics",
        "schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer", "description": "Year (e.g., 2025)"},
                "month": {"type": "integer", "description": "Month (1-12)"},
            },
            "required": ["year", "month"],
        },
    },
    "compare_sales": {
        "func": compare_sales,
        "description": "Compare sales between two periods with percentage changes and product differences",
        "schema": {
            "type": "object",
            "properties": {
                "period1": {"type": "string", "description": "First period in YYYY-MM format (e.g., '2025-11')"},
                "period2": {"type": "string", "description": "Second period in YYYY-MM format (e.g., '2025-12')"},
            },
            "required": ["period1", "period2"],
        },
    },
    "get_sales_trends": {
        "func": get_sales_trends,
        "description": "Get sales trends for specified days with moving averages, best/worst days, and category breakdown",
        "schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Number of days to analyze (default 30, max 365)"},
            },
        },
    },
    "get_inventory_analytics": {
        "func": get_inventory_analytics,
        "description": "Get inventory analytics with stock levels, alerts (out-of-stock, low stock), category breakdown, and recommendations",
        "schema": {
            "type": "object",
            "properties": {},
        },
    },
}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "mcp-server"}


@app.get("/mcp/tools")
async def get_tools():
    """Discover available MCP tools"""
    tools = []
    for tool_name, tool_info in TOOLS.items():
        tools.append({
            "name": tool_name,
            "description": tool_info["description"],
            "schema": tool_info["schema"],
        })
    return {"tools": tools}


@app.post("/mcp/call")
async def call_tool(request: dict):
    """Call an MCP tool with database session"""
    tool_name = request.get("tool")
    arguments = request.get("arguments", {})

    if tool_name not in TOOLS:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

    # Create a database session for this tool call
    async with async_session() as session:
        try:
            tool_func = TOOLS[tool_name]["func"]

            # Add session to arguments for tools that need it
            arguments_with_session = {**arguments, "session": session}

            # Call the tool function with session
            # Most tools are async, so we need to handle both async and sync
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**arguments_with_session)
            else:
                result = tool_func(**arguments_with_session)

            return {
                "status": "success",
                "result": result,
            }
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
            }


if __name__ == "__main__":
    logger.info("Starting MCP HTTP Server on http://0.0.0.0:8001")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
    )
