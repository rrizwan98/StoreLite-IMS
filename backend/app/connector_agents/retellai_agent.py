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
                "agentId": {"type": "string", "description": "The agent ID to use for the call"},
                "fromNumber": {"type": "string", "description": "The phone number to call from (must be provisioned in Retell AI)"},
                "toNumber": {"type": "string", "description": "The phone number to call (E.164 format like +1234567890)"}
            },
            "required": ["agentId", "fromNumber", "toNumber"]
        }
    },
    {
        "name": "create_web_call",
        "description": "Create a web-based call session",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agentId": {"type": "string", "description": "The agent ID to use for the call"}
            },
            "required": ["agentId"]
        }
    },
    {
        "name": "get_call",
        "description": "Get details of a specific call by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "callId": {"type": "string", "description": "The call ID to retrieve"}
            },
            "required": ["callId"]
        }
    },
    {
        "name": "delete_call",
        "description": "Delete a call record",
        "inputSchema": {
            "type": "object",
            "properties": {
                "callId": {"type": "string", "description": "The call ID to delete"}
            },
            "required": ["callId"]
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
                "agentName": {"type": "string", "description": "Name of the agent"},
                "voiceId": {"type": "string", "description": "Voice ID to use"},
                "language": {"type": "string", "description": "Language code (e.g., en-US)"}
            },
            "required": ["agentName"]
        }
    },
    {
        "name": "get_agent",
        "description": "Get details of a specific agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agentId": {"type": "string", "description": "The agent ID to retrieve"}
            },
            "required": ["agentId"]
        }
    },
    {
        "name": "update_agent",
        "description": "Update an existing agent's configuration",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agentId": {"type": "string", "description": "The agent ID to update"},
                "agentName": {"type": "string", "description": "New name for the agent"},
                "voiceId": {"type": "string", "description": "New voice ID"}
            },
            "required": ["agentId"]
        }
    },
    {
        "name": "delete_agent",
        "description": "Delete a voice agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agentId": {"type": "string", "description": "The agent ID to delete"}
            },
            "required": ["agentId"]
        }
    },
    {
        "name": "get_agent_versions",
        "description": "Get version history of an agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agentId": {"type": "string", "description": "The agent ID"}
            },
            "required": ["agentId"]
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
                "areaCode": {"type": "string", "description": "Area code for the phone number"}
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
                "phoneNumber": {"type": "string", "description": "The phone number to retrieve"}
            },
            "required": ["phoneNumber"]
        }
    },
    {
        "name": "update_phone_number",
        "description": "Update phone number settings",
        "inputSchema": {
            "type": "object",
            "properties": {
                "phoneNumber": {"type": "string", "description": "The phone number to update"},
                "agentId": {"type": "string", "description": "Agent ID to associate"}
            },
            "required": ["phoneNumber"]
        }
    },
    {
        "name": "delete_phone_number",
        "description": "Delete a phone number",
        "inputSchema": {
            "type": "object",
            "properties": {
                "phoneNumber": {"type": "string", "description": "The phone number to delete"}
            },
            "required": ["phoneNumber"]
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
                "voiceId": {"type": "string", "description": "The voice ID to retrieve"}
            },
            "required": ["voiceId"]
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
        "IMMEDIATELY make outbound phone calls to users. "
        "When user wants to call someone or provides a phone number, use this tool. "
        "This tool will automatically: 1) Find available voice agents, "
        "2) Get a phone number to call from, 3) Execute the call immediately. "
        "Also handles: viewing calls, managing agents, and phone numbers. "
        "Use this whenever user mentions: call, phone, dial, ring, contact by phone."
    )

    def get_system_prompt(self) -> str:
        """Get Retell AI-specific system prompt."""
        return """You are an AUTONOMOUS Retell AI Voice Call Executor. Your PRIMARY job is to IMMEDIATELY MAKE PHONE CALLS when asked.

## CRITICAL: IMMEDIATE CALL EXECUTION

When user says "call this number", "make a call", "call the user" or provides a phone number:
1. IMMEDIATELY call `list_agents` to get available agents
2. IMMEDIATELY call `list_phone_numbers` to get FROM numbers
3. IMMEDIATELY call `create_phone_call` with EXACT parameter names (camelCase):
   - agentId: Use the agent_id from list_agents (or match user-specified agent name)
   - fromNumber: Use phone_number from list_phone_numbers (first one or matching)
   - toNumber: The phone number user wants to call

DO NOT ask for confirmation. DO NOT explain what you will do. JUST EXECUTE THE CALL.

## PHONE NUMBER FORMAT
- Always use E.164 format: +1XXXXXXXXXX (e.g., +12025551234)
- If user provides number without +, add +1 for US numbers
- Pakistan numbers: +92XXXXXXXXXX

## AUTONOMOUS EXECUTION RULES

1. **NEVER ASK** - Don't ask "which agent?", just use the first one
2. **NEVER EXPLAIN** - Don't say "I will now...", just do it
3. **CHAIN TOOLS** - Call list_agents, list_phone_numbers, then create_phone_call in sequence
4. **EXECUTE IMMEDIATELY** - When user wants a call, make it happen NOW

## CRITICAL: PARAMETER FORMAT FOR create_phone_call
ALWAYS use camelCase parameters:
- ✅ CORRECT: agentId, fromNumber, toNumber
- ❌ WRONG: agent_id, from_number, to_number

## WORKFLOW EXAMPLE

When user wants to call someone:
1. Call `list_agents` → extract `agent_id` from response
2. Call `list_phone_numbers` → extract `phone_number` from response
3. Call `create_phone_call` with camelCase params:
   - agentId: (value from step 1)
   - fromNumber: (value from step 2)
   - toNumber: (user's target number)

## AVAILABLE TOOLS

CALL MANAGEMENT:
- `create_phone_call` - **PRIMARY TOOL** - Create outbound phone call
  - Required params (camelCase!): agentId, fromNumber, toNumber
- `create_web_call` - Create web-based call session (agentId)
- `list_calls` - List all calls
- `get_call` - Get call details by callId
- `delete_call` - Delete a call by callId

AGENT MANAGEMENT:
- `list_agents` - List all voice agents (USE THIS FIRST to get agentId)
- `get_agent` - Get agent details by agentId
- `create_agent` - Create new agent (agentName, voiceId)
- `update_agent` - Update agent (agentId)
- `delete_agent` - Delete agent (agentId)

PHONE NUMBER MANAGEMENT:
- `list_phone_numbers` - List provisioned numbers (USE THIS to get fromNumber)
- `get_phone_number` - Get number details by phoneNumber
- `create_phone_number` - Provision new number (areaCode)
- `update_phone_number` - Update number (phoneNumber, agentId)
- `delete_phone_number` - Delete number (phoneNumber)

VOICE MANAGEMENT:
- `list_voices` - List available voices
- `get_voice` - Get voice details by voiceId

## RESPONSE FORMAT

After making a call successfully, respond with a PROFESSIONAL and DETAILED message:

```
### 📞 Call Initiated Successfully!

Great news! I've placed the call for you. Here are the details:

---

#### 📋 **Call Details**

| Field | Value |
|-------|-------|
| **Call ID** | `[call_id from response]` |
| **Status** | 🟢 [status from response, e.g., "registered", "in_progress"] |

---

#### 🤖 **Agent Information**

| Field | Value |
|-------|-------|
| **Agent ID** | `[agentId used]` |
| **Agent Name** | [agent_name from list_agents] |

---

#### 📱 **Phone Numbers**

| Field | Value |
|-------|-------|
| **From** | `[fromNumber used]` |
| **To** | `[toNumber - user's target]` |

---

> 💡 **What happens next?** The AI agent is now connecting to the recipient. The agent will deliver your message as instructed.

```

If call fails, respond with:
```
### ❌ Call Failed

Unfortunately, the call could not be placed.

---

#### 🔍 **Error Details**

| Field | Value |
|-------|-------|
| **Error** | [error message] |
| **Attempted From** | `[fromNumber]` |
| **Attempted To** | `[toNumber]` |
| **Agent** | [agent_name] |

---

#### 🛠️ **Suggested Actions**
- Verify the phone number format (should be E.164: +1234567890)
- Check if the FROM number is provisioned in Retell AI
- Ensure the agent is properly configured

```

## REMEMBER

You are a CALL EXECUTOR. When someone asks to call a number:
1. Get agent_id (list_agents)
2. Get from_number (list_phone_numbers)
3. MAKE THE CALL (create_phone_call)

That's it. Don't overthink. Just call."""

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
