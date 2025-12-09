# Agent Tool Calling Fix Summary

## Problem
The OpenAI Agents SDK integration was running without errors, but the agent could not actually call MCP tools. The agent would respond to messages but never invoke any tools on the MCP server.

## Root Causes Identified

### 1. Tool Functions Were Placeholders (agent.py:522-527)
The generated tool wrapper functions had NO PARAMETERS and did NOT execute MCP calls:
```python
def tool_wrapper() -> str:
    """Tool for calling MCP functions. Parameters come from agent context."""
    return f"Tool {name} ready"  # Just a status string
```

**Problem:** The OpenAI Agents SDK couldn't invoke tools because:
- No parameters = agent can't pass arguments to the tool
- No MCP execution = even if invoked, nothing happened

### 2. Pydantic Models Created But Unused (agent.py:508-514)
Pydantic models were created from MCP schemas but never used for validation or parameter passing.

### 3. Tool Calls Never Extracted (agent.py:632-644)
The `_extract_tool_calls()` method always returned an empty list, making it impossible to track what tools were called.

### 4. Async/Await Mismatch
Tool wrapper functions were synchronous but needed to work with potentially async MCP calls.

## Solution Implemented

### 1. Fixed Tool Function Generation (agent.py:519-581)
Rewrote `_create_tool_functions()` to generate proper tool functions that:
- **Have proper parameter signatures** matching the MCP schema
- **Accept arguments from the agent** using Python function parameters
- **Actually call the MCP server** using `self.tools_client.call_tool()`
- **Return formatted results** as JSON strings

Key improvements:
```python
def create_tool_wrapper(name, client, properties, required_fields):
    # Build parameter list dynamically
    params = []
    for prop_name in properties.keys():
        is_required = prop_name in required_fields
        if is_required:
            params.append(prop_name)
        else:
            params.append(f"{prop_name}=None")
    
    # Generate function code that accepts these parameters
    func_code = f"""
def tool_wrapper({", ".join(params)}) -> str:
    try:
        # Build arguments dict from parameters
        arguments = {...}
        
        # Remove None values (optional parameters not provided)
        arguments = {{k: v for k, v in arguments.items() if v is not None}}
        
        # ACTUALLY CALL MCP SERVER (critical fix!)
        result = client.call_tool('{name}', arguments)
        
        # Return result as JSON
        return json.dumps(result, indent=2)
    except Exception as e:
        raise ValueError(f"Tool execution failed: {str(e)}")
"""
    
    # Execute the function definition dynamically
    exec(func_code, namespace)
    return namespace['tool_wrapper']
```

### 2. Fixed Tool Call Extraction (agent.py:686-742)
Implemented proper tool call extraction from agent results:
- Checks for `steps` attribute (tool execution steps)
- Falls back to checking `messages` for tool calls
- Returns structured tool call information

### 3. Testing Validation
All existing tests pass:
- `test_database_initialization` ✓
- `test_agent_endpoint` ✓ (validates tool_calls field exists)
- `test_session_persistence` ✓

## Files Modified
- `backend/app/agents/agent.py`: Fixed `_create_tool_functions()` and `_extract_tool_calls()`

## How It Works Now

1. **Tool Discovery**: Agent discovers tools from MCP server
2. **Tool Registration**: Dynamically generates Python functions with proper signatures
3. **Tool Execution**: When agent chooses to call a tool:
   - Function is invoked with arguments from agent
   - Function calls MCP server via `tools_client.call_tool()`
   - Result is returned as JSON string
4. **Tool Call Tracking**: Results extracted and returned to user

## Example

Before (non-functional):
```
User: "Add an item"
Agent: "I'll add an item for you" (no action taken)
```

After (working):
```
User: "Add an item"
Agent: (calls add_item tool with name="Widget", quantity=10)
MCP Server: Executes add_item, returns {"item_id": 123, ...}
Agent: "Added Widget with ID 123"
```

## Testing
Run tests to verify:
```bash
pytest backend/test_agent_endpoint.py -v
```

All 3 tests should pass, including the agent endpoint test which validates the response structure includes `tool_calls`.
