"""
Retell AI Connector Sub-Agent.

Specialized agent for handling Retell AI voice agent operations.
Uses the Retell AI MCP server via npx for outbound phone calls.

Retell AI MCP Server: @abhaybabbar/retellai-mcp-server
"""

import json
import logging
import subprocess
import asyncio
import os
import concurrent.futures
from typing import List, Dict, Any, Optional

from agents.tool import FunctionTool

from .base import BaseConnectorAgent

logger = logging.getLogger(__name__)

# Known Retell AI MCP tools (from @abhaybabbar/retellai-mcp-server documentation)
# We use these because tools/list has a Zod v4 compatibility bug in the MCP SDK
RETELL_AI_TOOLS = [
    {
        "name": "list_calls",
        "description": "List all calls from Retell AI with optional filters",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_phone_call",
        "description": "Create an outbound phone call using Retell AI",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "The agent ID to use for the call"},
                "from_number": {"type": "string", "description": "The phone number to call from (must be provisioned)"},
                "to_number": {"type": "string", "description": "The phone number to call"}
            },
            "required": ["agent_id", "from_number", "to_number"]
        }
    },
    {
        "name": "create_web_call",
        "description": "Create a web-based call session",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "The agent ID to use for the call"}
            },
            "required": ["agent_id"]
        }
    },
    {
        "name": "get_call",
        "description": "Get details of a specific call by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "call_id": {"type": "string", "description": "The call ID to retrieve"}
            },
            "required": ["call_id"]
        }
    },
    {
        "name": "delete_call",
        "description": "Delete a call record",
        "inputSchema": {
            "type": "object",
            "properties": {
                "call_id": {"type": "string", "description": "The call ID to delete"}
            },
            "required": ["call_id"]
        }
    },
    {
        "name": "list_agents",
        "description": "List all voice agents configured in Retell AI",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_agent",
        "description": "Create a new voice agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string", "description": "Name of the agent"},
                "voice_id": {"type": "string", "description": "Voice ID to use"},
                "language": {"type": "string", "description": "Language code (e.g., en-US)"}
            },
            "required": ["agent_name"]
        }
    },
    {
        "name": "get_agent",
        "description": "Get details of a specific agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "The agent ID to retrieve"}
            },
            "required": ["agent_id"]
        }
    },
    {
        "name": "update_agent",
        "description": "Update an existing agent's configuration",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "The agent ID to update"},
                "agent_name": {"type": "string", "description": "New name for the agent"},
                "voice_id": {"type": "string", "description": "New voice ID"}
            },
            "required": ["agent_id"]
        }
    },
    {
        "name": "delete_agent",
        "description": "Delete a voice agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "The agent ID to delete"}
            },
            "required": ["agent_id"]
        }
    },
    {
        "name": "get_agent_versions",
        "description": "Get version history of an agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "The agent ID"}
            },
            "required": ["agent_id"]
        }
    },
    {
        "name": "list_phone_numbers",
        "description": "List all phone numbers provisioned in Retell AI",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_phone_number",
        "description": "Provision a new phone number",
        "inputSchema": {
            "type": "object",
            "properties": {
                "area_code": {"type": "string", "description": "Area code for the phone number"}
            },
            "required": []
        }
    },
    {
        "name": "get_phone_number",
        "description": "Get details of a specific phone number",
        "inputSchema": {
            "type": "object",
            "properties": {
                "phone_number": {"type": "string", "description": "The phone number to retrieve"}
            },
            "required": ["phone_number"]
        }
    },
    {
        "name": "update_phone_number",
        "description": "Update phone number settings",
        "inputSchema": {
            "type": "object",
            "properties": {
                "phone_number": {"type": "string", "description": "The phone number to update"},
                "agent_id": {"type": "string", "description": "Agent ID to associate"}
            },
            "required": ["phone_number"]
        }
    },
    {
        "name": "delete_phone_number",
        "description": "Delete a phone number",
        "inputSchema": {
            "type": "object",
            "properties": {
                "phone_number": {"type": "string", "description": "The phone number to delete"}
            },
            "required": ["phone_number"]
        }
    },
    {
        "name": "list_voices",
        "description": "List all available voices for Retell AI agents",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_voice",
        "description": "Get details of a specific voice",
        "inputSchema": {
            "type": "object",
            "properties": {
                "voice_id": {"type": "string", "description": "The voice ID to retrieve"}
            },
            "required": ["voice_id"]
        }
    },
]


class RetellAIConnectorAgent(BaseConnectorAgent):
    """
    Specialized agent for Retell AI voice operations.

    Handles:
    - Creating outbound phone calls
    - Managing voice agents
    - Provisioning phone numbers
    - Viewing call analytics
    - Managing call recordings

    This agent knows:
    - Retell AI terminology (Agent, Phone Number, Call, Voice)
    - Retell AI API structure and required formats
    - Common voice agent workflows
    """

    CONNECTOR_TYPE = "RetellAI"
    TOOL_NAME = "retellai_connector"
    TOOL_DESCRIPTION = (
        "Handle ALL Retell AI voice operations including: "
        "creating outbound phone calls, managing voice agents, "
        "provisioning phone numbers, viewing call analytics, "
        "and managing call recordings. "
        "Use this for ANY Retell AI voice-related task."
    )

    def get_system_prompt(self) -> str:
        """Get Retell AI-specific system prompt."""
        return """You are a Retell AI Voice Agent Expert. Your job is to execute Retell AI operations using the available tools.

## AUTONOMOUS EXECUTION
Execute tasks immediately. Make intelligent decisions based on the context.
- Need an agent? List available agents first
- Need a phone number? List available phone numbers first
- Need to make a call? Specify the agent and phone number

Execute, don't ask unnecessary questions.

## YOUR CAPABILITIES
- List and manage voice agents
- List and manage phone numbers
- Create outbound phone calls
- View call details and analytics
- Delete call recordings
- List available voices

## TERMINOLOGY
- "Agent" = AI voice agent configured with personality and instructions
- "Phone Number" = Provisioned phone number for making/receiving calls
- "Call" = Voice conversation with analytics (duration, transcript, etc.)
- "Voice" = Text-to-speech voice configuration

## AVAILABLE TOOLS (from Retell AI MCP)
The actual tool names from Retell AI MCP server:
- `list_calls` - List all calls with optional filters
- `create_phone_call` - Create an outbound phone call
- `create_web_call` - Create a web-based call
- `get_call` - Get details of a specific call
- `delete_call` - Delete a call record
- `list_agents` - List all voice agents
- `create_agent` - Create a new voice agent
- `get_agent` - Get details of a specific agent
- `update_agent` - Update an existing agent
- `delete_agent` - Delete an agent
- `get_agent_versions` - Get version history of an agent
- `list_phone_numbers` - List all phone numbers
- `create_phone_number` - Provision a new phone number
- `get_phone_number` - Get details of a phone number
- `update_phone_number` - Update phone number settings
- `delete_phone_number` - Delete a phone number
- `list_voices` - List available voices
- `get_voice` - Get details of a specific voice

## EXECUTION RULES

1. ALWAYS USE TOOLS - Never pretend without calling a tool
2. LIST FIRST - When creating, list existing resources first
3. CHAIN OPERATIONS - Complete multi-step tasks automatically
4. REPORT RESULTS - Confirm what was done with relevant details

## WORKFLOW: MAKE A PHONE CALL

Step 1: List available agents
```
list_agents
```

Step 2: List available phone numbers
```
list_phone_numbers
```

Step 3: Create the call
```
create_phone_call with agent_id, from_number, to_number
```

## WORKFLOW: CREATE A VOICE AGENT

Step 1: List available voices (optional)
```
list_voices
```

Step 2: Create the agent
```
create_agent with name, voice, instructions, etc.
```

## ERROR HANDLING
If an operation fails:
- Check if the resource exists
- Verify permissions and quotas
- Provide clear error message to user

## RESPONSE FORMAT
After completing operations, provide:
- Action taken (call placed, agent created, etc.)
- Relevant IDs and details
- Any errors or warnings

Execute tasks completely using tools."""

    async def load_tools(self) -> List[FunctionTool]:
        """
        Load Retell AI MCP tools.

        Uses predefined tool definitions (due to MCP SDK Zod v4 bug)
        and creates FunctionTool wrappers that call MCP server at runtime.
        """
        print(f"[RetellAIAgent] Loading tools for connector {self.connector_id}")

        try:
            # Get API key from auth config
            api_key = self._get_api_key()
            if not api_key:
                print("[RetellAIAgent] No API key found in auth_config")
                return []

            print(f"[RetellAIAgent] API key found, length: {len(api_key)}")

            # Use predefined tools (MCP tools/list has Zod v4 bug)
            mcp_tools = RETELL_AI_TOOLS
            print(f"[RetellAIAgent] Using {len(mcp_tools)} predefined MCP tools")

            # Convert MCP tools to FunctionTool format
            function_tools = []
            for tool_def in mcp_tools:
                func_tool = self._create_function_tool(tool_def, api_key)
                if func_tool:
                    function_tools.append(func_tool)
                    print(f"[RetellAIAgent] Created tool: {tool_def['name']}")

            print(f"[RetellAIAgent] Created {len(function_tools)} function tools")
            return function_tools

        except Exception as e:
            print(f"[RetellAIAgent] Failed to load tools: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _get_api_key(self) -> Optional[str]:
        """Extract API key from auth_config."""
        if not self.auth_config:
            return None
        return (
            self.auth_config.get("api_key") or
            self.auth_config.get("token") or
            self.auth_config.get("access_token") or
            self.auth_config.get("retell_api_key")
        )


    def _create_function_tool(self, tool_def: Dict[str, Any], api_key: str) -> Optional[FunctionTool]:
        """
        Create a FunctionTool from MCP tool definition.

        Args:
            tool_def: Tool definition from MCP server
            api_key: Retell AI API key for authentication

        Returns:
            FunctionTool instance
        """
        tool_name = tool_def.get("name", "unknown_tool")
        tool_description = tool_def.get("description", f"Retell AI tool: {tool_name}")
        input_schema = tool_def.get("inputSchema", {})

        # Clean schema for compatibility
        cleaned_schema = self._clean_json_schema(input_schema)

        # Ensure proper structure
        if cleaned_schema.get("type") != "object":
            cleaned_schema = {
                "type": "object",
                "properties": cleaned_schema.get("properties", {}),
                "required": cleaned_schema.get("required", []),
            }

        if "properties" not in cleaned_schema:
            cleaned_schema["properties"] = {}

        # Create the tool caller function
        tool_func = self._create_tool_caller(tool_name, api_key)

        # Set function metadata
        tool_func.__name__ = tool_name
        tool_func.__doc__ = tool_description

        # Create FunctionTool
        return FunctionTool(
            name=tool_name,
            description=tool_description,
            params_json_schema=cleaned_schema,
            on_invoke_tool=tool_func,
            strict_json_schema=False,
        )

    def _create_tool_caller(self, tool_name: str, api_key: str):
        """
        Create a callable function for invoking an MCP tool.

        Args:
            tool_name: Name of the tool to call
            api_key: Retell AI API key

        Returns:
            Async function that calls the MCP tool
        """
        connector_name = self.connector_name

        async def mcp_tool_caller(ctx, args: str) -> str:
            """Call Retell AI MCP tool with given arguments."""
            try:
                kwargs = json.loads(args) if args else {}

                # Log with clear connector context
                logger.info(f"[RetellAIAgent] =====================================")
                logger.info(f"[RetellAIAgent] TOOL CALL: {tool_name}")
                logger.info(f"[RetellAIAgent] Args: {str(kwargs)[:500]}...")

                # Create progress message
                progress_prefix = f"[{connector_name}] Calling {tool_name}..."
                logger.info(progress_prefix)

                # Call the MCP tool via stdio
                result = await self._call_mcp_tool(tool_name, kwargs, api_key)

                logger.info(f"[RetellAIAgent] Result type: {type(result).__name__}")
                logger.info(f"[RetellAIAgent] Result: {str(result)[:500]}...")

                # Format result
                result_text = ""
                if isinstance(result, dict):
                    if "content" in result:
                        contents = result["content"]
                        if isinstance(contents, list):
                            texts = []
                            for c in contents:
                                if isinstance(c, dict) and c.get("type") == "text":
                                    texts.append(c.get("text", ""))
                            if texts:
                                result_text = "\n".join(texts)
                    if not result_text:
                        result_text = json.dumps(result, indent=2)
                else:
                    result_text = str(result)

                logger.info(f"[RetellAIAgent] {connector_name}/{tool_name} completed")
                return f"[{connector_name}:{tool_name}] {result_text}"

            except json.JSONDecodeError as e:
                error_msg = f"[{connector_name}:{tool_name}] Error: Invalid arguments - {e}"
                logger.error(f"[RetellAIAgent] {error_msg}")
                return error_msg
            except Exception as e:
                error_msg = f"[{connector_name}:{tool_name}] Error: {str(e)}"
                logger.error(f"[RetellAIAgent] {error_msg}")
                return error_msg

        return mcp_tool_caller

    def _call_mcp_tool_sync(self, tool_name: str, arguments: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        """
        Call a specific MCP tool synchronously (Windows-compatible).

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            api_key: Retell AI API key

        Returns:
            Tool execution result
        """
        env = {**dict(os.environ), "RETELL_API_KEY": api_key}

        try:
            # Start MCP server process
            process = subprocess.Popen(
                ["npx", "-y", "@abhaybabbar/retellai-mcp-server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                shell=True,  # Needed for Windows
            )

            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "id": 1,
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "IMS-Agent", "version": "1.0"}
                }
            }
            process.stdin.write((json.dumps(init_request) + "\n").encode())
            process.stdin.flush()

            # Read initialize response
            init_response = process.stdout.readline()
            if not init_response:
                stderr = process.stderr.read().decode()
                process.terminate()
                raise Exception(f"MCP server did not respond: {stderr[:200]}")

            print(f"[RetellAIAgent] MCP Init OK")

            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            process.stdin.write((json.dumps(initialized_notification) + "\n").encode())
            process.stdin.flush()

            # Send tools/call request
            call_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 2,
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            print(f"[RetellAIAgent] Calling MCP tool: {tool_name}")
            process.stdin.write((json.dumps(call_request) + "\n").encode())
            process.stdin.flush()

            # Read response
            response_line = process.stdout.readline()
            process.terminate()

            if not response_line:
                raise Exception("No response from MCP tool call")

            # Parse response
            response_data = json.loads(response_line.decode())
            print(f"[RetellAIAgent] MCP response: {str(response_data)[:300]}")

            if "error" in response_data:
                error = response_data["error"]
                error_msg = error.get("message", str(error)) if isinstance(error, dict) else str(error)
                raise Exception(f"MCP error: {error_msg}")

            return response_data.get("result", {})

        except subprocess.TimeoutExpired:
            print(f"[RetellAIAgent] Tool call timeout: {tool_name}")
            raise Exception("Tool call timed out")
        except Exception as e:
            print(f"[RetellAIAgent] Tool call failed: {e}")
            raise

    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        """
        Call a specific MCP tool (async wrapper for sync implementation).

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            api_key: Retell AI API key

        Returns:
            Tool execution result
        """
        # Run synchronous subprocess in thread pool (Windows compatibility)
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                self._call_mcp_tool_sync,
                tool_name,
                arguments,
                api_key
            )
        return result

    def _clean_json_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean JSON schema for OpenAI compatibility.

        Removes additionalProperties and other incompatible fields.
        """
        if not isinstance(schema, dict):
            return schema

        cleaned = {}
        for key, value in schema.items():
            if key == "additionalProperties":
                continue
            if isinstance(value, dict):
                cleaned[key] = self._clean_json_schema(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    self._clean_json_schema(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                cleaned[key] = value

        return cleaned
