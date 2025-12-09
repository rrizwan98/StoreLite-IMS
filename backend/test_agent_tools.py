"""Test that the agent can actually call MCP tools."""
import asyncio
import pytest
from app.agents import OpenAIAgent, MCPClient
from unittest.mock import Mock, patch
import json


@pytest.mark.asyncio
async def test_agent_discovers_tools():
    """Test that agent can discover tools from MCP server."""
    # Mock the MCPClient to return sample tools
    mock_client = Mock(spec=MCPClient)
    mock_client.discover_tools.return_value = [
        {
            "name": "add_item",
            "description": "Add a new inventory item",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Item name"},
                    "quantity": {"type": "integer", "description": "Item quantity"},
                    "price": {"type": "number", "description": "Item price"}
                },
                "required": ["name", "quantity"]
            }
        },
        {
            "name": "list_items",
            "description": "List all inventory items",
            "schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    ]

    # Create agent with mocked client
    agent = OpenAIAgent(
        gemini_api_key="test-key",
        tools_client=mock_client
    )

    # Discover tools
    tools = await agent.discover_and_register_tools()

    # Verify
    assert len(tools) == 2
    assert tools[0]["name"] == "add_item"
    assert tools[1]["name"] == "list_items"
    
    # Verify agent was initialized
    assert agent.agent is not None
    
    # Verify agent has tools
    assert agent.agent.tools is not None
    assert len(agent.agent.tools) == 2
    
    print("✓ Agent successfully discovered and registered 2 tools")


@pytest.mark.asyncio
async def test_agent_tool_functions_have_parameters():
    """Test that generated tool functions accept the proper parameters."""
    mock_client = Mock(spec=MCPClient)
    mock_client.discover_tools.return_value = [
        {
            "name": "add_item",
            "description": "Add a new inventory item",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "price": {"type": "number", "description": "Optional price"}
                },
                "required": ["name", "quantity"]
            }
        }
    ]

    agent = OpenAIAgent(
        gemini_api_key="test-key",
        tools_client=mock_client
    )

    # Generate tool functions
    tools = agent._create_tool_functions(mock_client.discover_tools())

    # Get the tool function
    tool_func = None
    if hasattr(tools[0], '__wrapped__'):
        tool_func = tools[0].__wrapped__
    else:
        tool_func = tools[0]

    # Check function signature
    import inspect
    sig = inspect.signature(tool_func)
    params = list(sig.parameters.keys())
    
    # Should have parameters: name (required), quantity (required), price (optional)
    assert "name" in params, f"Expected 'name' param, got {params}"
    assert "quantity" in params, f"Expected 'quantity' param, got {params}"
    assert "price" in params, f"Expected 'price' param, got {params}"
    
    print(f"✓ Tool function has proper parameters: {params}")


@pytest.mark.asyncio
async def test_agent_tool_calls_mcp_server():
    """Test that tool functions actually call the MCP server."""
    mock_client = Mock(spec=MCPClient)
    mock_client.discover_tools.return_value = [
        {
            "name": "add_item",
            "description": "Add a new inventory item",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "quantity": {"type": "integer"}
                },
                "required": ["name", "quantity"]
            }
        }
    ]
    
    # Mock the tool execution result
    mock_client.call_tool.return_value = {
        "status": "success",
        "item_id": 123,
        "name": "Widget",
        "quantity": 10
    }

    agent = OpenAIAgent(
        gemini_api_key="test-key",
        tools_client=mock_client
    )

    # Generate tool functions
    tools = agent._create_tool_functions(mock_client.discover_tools())

    # Get the tool function
    tool_func = None
    if hasattr(tools[0], '__wrapped__'):
        tool_func = tools[0].__wrapped__
    else:
        tool_func = tools[0]

    # Call the tool with parameters
    result = tool_func(name="Widget", quantity=10)

    # Verify MCP server was called
    mock_client.call_tool.assert_called_once_with(
        "add_item",
        {"name": "Widget", "quantity": 10}
    )
    
    # Verify result is returned as JSON string
    result_dict = json.loads(result)
    assert result_dict["status"] == "success"
    assert result_dict["item_id"] == 123
    
    print("✓ Tool function successfully called MCP server and returned result")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
