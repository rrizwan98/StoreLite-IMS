"""
Agent Tools Integration for User MCP Connectors.

This module provides integration between user's MCP connectors and OpenAI Agents SDK.
Converts MCP tools to Agents SDK function_tool format.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from agents.tool import FunctionTool

from .mcp_client import UserMCPClient

logger = logging.getLogger(__name__)


def clean_json_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean JSON schema to be compatible with OpenAI strict mode.

    Removes additionalProperties and ensures proper structure.
    """
    if not isinstance(schema, dict):
        return schema

    cleaned = {}
    for key, value in schema.items():
        # Remove additionalProperties as it's not allowed in strict mode
        if key == "additionalProperties":
            continue
        # Recursively clean nested objects
        if isinstance(value, dict):
            cleaned[key] = clean_json_schema(value)
        elif isinstance(value, list):
            cleaned[key] = [clean_json_schema(item) if isinstance(item, dict) else item for item in value]
        else:
            cleaned[key] = value

    # For object types, ensure additionalProperties is not present
    if cleaned.get("type") == "object" and "additionalProperties" in cleaned:
        del cleaned["additionalProperties"]

    return cleaned


def create_mcp_tool_function(connector_url: str, tool_name: str, connector_name: str):
    """
    Create a callable function that invokes an MCP tool.

    Returns a function that can be used with FunctionTool.
    """
    async def mcp_tool_caller(ctx, **kwargs) -> str:
        """Call MCP tool with given arguments."""
        try:
            logger.info(f"[MCP Tool] Calling {tool_name} on {connector_name} with args: {list(kwargs.keys())}")
            client = UserMCPClient(connector_url, timeout=30.0)
            result = await client.call_tool(tool_name, kwargs)

            # Format result for agent
            if isinstance(result, dict):
                # Check for content array (MCP response format)
                if "content" in result:
                    contents = result["content"]
                    if isinstance(contents, list):
                        texts = []
                        for c in contents:
                            if isinstance(c, dict) and c.get("type") == "text":
                                texts.append(c.get("text", ""))
                        if texts:
                            return "\n".join(texts)
                # Return as JSON string
                return json.dumps(result, indent=2)
            return str(result)

        except Exception as e:
            logger.error(f"[MCP Tool] Error calling {tool_name}: {e}")
            return f"Error calling {tool_name}: {str(e)}"

    return mcp_tool_caller


def create_connector_tool(
    connector_url: str,
    tool_def: Dict[str, Any],
    connector_name: str = "MCP"
) -> Optional[FunctionTool]:
    """
    Create an Agents SDK FunctionTool from an MCP tool definition.

    Args:
        connector_url: URL of the MCP server
        tool_def: Tool definition from MCP server (name, description, inputSchema)
        connector_name: Human-readable connector name for logging

    Returns:
        FunctionTool compatible with OpenAI Agents SDK, or None if creation fails
    """
    tool_name = tool_def.get("name", "unknown_tool")
    tool_description = tool_def.get("description", f"Tool from {connector_name}")
    input_schema = tool_def.get("inputSchema", {})

    logger.info(f"[Connector Tools] Creating tool: {tool_name} from {connector_name}")

    try:
        # Clean the schema to remove additionalProperties
        cleaned_schema = clean_json_schema(input_schema)

        # Ensure the schema has proper structure for OpenAI
        if cleaned_schema.get("type") != "object":
            cleaned_schema = {
                "type": "object",
                "properties": cleaned_schema.get("properties", {}),
                "required": cleaned_schema.get("required", [])
            }

        # Ensure properties exist
        if "properties" not in cleaned_schema:
            cleaned_schema["properties"] = {}

        # Create the tool function
        tool_func = create_mcp_tool_function(connector_url, tool_name, connector_name)

        # Set function metadata
        tool_func.__name__ = tool_name
        tool_func.__doc__ = tool_description

        # Create FunctionTool directly with proper schema
        # Use non-strict mode to allow flexibility with MCP schemas
        func_tool = FunctionTool(
            name=tool_name,
            description=tool_description,
            params_json_schema=cleaned_schema,
            on_invoke_tool=tool_func,
            strict_json_schema=False,  # Disable strict mode for MCP compatibility
        )

        logger.info(f"[Connector Tools] Successfully created tool: {tool_name}")
        return func_tool

    except Exception as e:
        logger.error(f"[Connector Tools] Failed to create tool {tool_name}: {e}")
        return None


async def load_connector_tools(
    connector_url: str,
    connector_name: str = "MCP Connector"
) -> List[FunctionTool]:
    """
    Load all tools from an MCP connector.

    Args:
        connector_url: URL of the MCP server
        connector_name: Human-readable connector name

    Returns:
        List of FunctionTool objects for use with Agents SDK
    """
    logger.info(f"[Connector Tools] Loading tools from {connector_name}: {connector_url}")

    try:
        client = UserMCPClient(connector_url, timeout=15.0)
        tools = await client.discover_tools()

        function_tools = []
        for tool_def in tools:
            # create_connector_tool is now synchronous
            func_tool = create_connector_tool(
                connector_url,
                tool_def,
                connector_name
            )
            if func_tool:
                function_tools.append(func_tool)

        logger.info(f"[Connector Tools] Loaded {len(function_tools)} tools from {connector_name}")
        return function_tools

    except Exception as e:
        logger.error(f"[Connector Tools] Failed to load tools from {connector_name}: {e}")
        return []


async def get_user_connector_tools(
    db_session: Any,
    user_id: int,
    connector_id: Optional[int] = None
) -> List[FunctionTool]:
    """
    Get tools from user's verified MCP connectors.

    Args:
        db_session: Database session
        user_id: User ID
        connector_id: Optional specific connector ID to load tools from

    Returns:
        List of FunctionTool objects from user's connectors
    """
    from sqlalchemy import select
    from app.models import UserMCPConnection

    logger.info(f"[Connector Tools] Getting tools for user {user_id}, connector: {connector_id}")

    try:
        # Build query
        query = select(UserMCPConnection).where(
            UserMCPConnection.user_id == user_id,
            UserMCPConnection.is_active == True,
            UserMCPConnection.is_verified == True
        )

        if connector_id:
            query = query.where(UserMCPConnection.id == connector_id)

        result = await db_session.execute(query)
        connectors = result.scalars().all()

        all_tools = []
        for connector in connectors:
            tools = await load_connector_tools(
                connector.server_url,
                connector.name
            )
            all_tools.extend(tools)

        logger.info(f"[Connector Tools] Total {len(all_tools)} tools loaded for user {user_id}")
        return all_tools

    except Exception as e:
        logger.error(f"[Connector Tools] Error getting user connector tools: {e}")
        return []
