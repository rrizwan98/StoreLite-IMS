"""
OpenAI Agent Orchestration for Phase 5 (December 2025).

Orchestrates conversation flows using the OpenAI Agents SDK (v0.6.2+) with LiteLLM Gemini 2.0 Flash Lite,
integrating with local FastMCP server for tool discovery and calling.

Latest Features:
- LiteLLMModel with Gemini 2.0 Flash Lite (cheaper, better quality than GPT-4o-mini)
- Local MCP server support (STDIO transport)
- Async SQLAlchemy 2.0 PostgreSQL session persistence
- Comprehensive error handling with retry logic
"""

import logging
import os
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, create_model

from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from agents.exceptions import ModelBehaviorError, MaxTurnsExceeded

try:
    from litellm.exceptions import RateLimitError, AuthenticationError
except ImportError:
    RateLimitError = Exception  # Fallback if litellm not available
    AuthenticationError = Exception

from app.agents.tools_client import MCPClient
from app.agents.session_manager import SessionManager
from app.agents.confirmation_flow import ConfirmationFlow

logger = logging.getLogger(__name__)


class OpenAIAgent:
    """
    OpenAI Agent orchestrator using the Agents SDK.

    Responsibilities:
    - Discover MCP tools dynamically
    - Register tools with OpenAI Agent
    - Process user messages with conversation history
    - Handle tool calling and error recovery
    - Manage confirmation flow for destructive actions
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        mcp_server_script: Optional[str] = None,
        session_manager: Optional[SessionManager] = None,
        tools_client: Optional[MCPClient] = None,
        confirmation_flow: Optional[ConfirmationFlow] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ):
        """
        Initialize OpenAI Agent with LiteLLM Gemini 2.0 Flash Lite (December 2025).

        Args:
            gemini_api_key: Google Gemini API key (GEMINI_API_KEY env var)
            mcp_server_script: Path to local MCP server script (for STDIO transport)
            session_manager: SessionManager for PostgreSQL conversation history
            tools_client: MCPClient for local MCP server communication
            confirmation_flow: ConfirmationFlow for destructive action handling
            temperature: Model temperature (0.0-1.0)
            max_tokens: Max output tokens
        """
        # Validate Gemini API Key
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY must be provided or set in environment")

        # Model configuration (Gemini 2.0 Flash Lite - latest December 2025)
        self.model_name = "gemini/gemini-robotics-er-1.5-preview"
        self.temperature = temperature
        self.max_tokens = max_tokens

        # MCP server configuration (local STDIO transport)
        self.mcp_server_script = mcp_server_script or os.getenv(
            "MCP_SERVER_SCRIPT",
            "backend/app/mcp_server/main.py"
        )

        # Component initialization
        self.session_manager = session_manager  # Will be initialized lazily if None
        self.tools_client = tools_client or MCPClient(
            base_url=os.getenv("MCP_SERVER_URL", "http://localhost:8001")
        )
        self.confirmation_flow = confirmation_flow or ConfirmationFlow()

        # Agent instance (created dynamically)
        self.agent: Optional[Agent] = None
        self._discovered_tools: List[Dict[str, Any]] = []
        self._mcp_tool_mapping: Dict[str, Dict[str, Any]] = {}
        self._model: Optional[LitellmModel] = None

        logger.info(
            f"Initializing OpenAI Agent with LiteLLM Gemini 2.0 Flash Lite "
            f"(temp={temperature}, max_tokens={max_tokens})"
        )

    async def discover_and_register_tools(self, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Discover tools from local MCP server and register with OpenAI Agent.

        Latest December 2025 approach:
        1. Initialize LiteLLMModel with Gemini 2.0 Flash Lite
        2. Discover tools from MCP (with retry logic)
        3. Register tools with Agent
        4. Handle connection failures gracefully

        Args:
            max_retries: Number of times to retry tool discovery

        Returns:
            List of registered tool schemas

        Raises:
            ConnectionError: If MCP server unreachable after retries
        """
        # Step 1: Initialize LiteLLMModel (Latest December 2025 import path)
        try:
            self._model = LitellmModel(
                model=self.model_name,
                api_key=self.gemini_api_key,
            )
            logger.info(f"LiteLLMModel initialized: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize LiteLLMModel: {e}")
            raise ValueError(f"Model initialization failed: {e}") from e

        # Step 2: Discover tools from MCP server with retry logic
        tools = []
        mcp_available = False
        
        for attempt in range(max_retries):
            try:
                tools = self.tools_client.discover_tools()
                logger.info(f"Discovered {len(tools)} tools from MCP server (attempt {attempt + 1})")
                mcp_available = True
                break

            except ConnectionError as e:
                logger.warning(
                    f"MCP server connection failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                else:
                    logger.warning("MCP server not available - agent will run without tools")

            except Exception as e:
                logger.error(f"Unexpected error discovering tools: {e}")
                # Continue without tools rather than failing completely
                break

        if not mcp_available:
            logger.warning("No MCP tools available - agent will provide basic responses only")

        # Step 3: Store tools for reference
        self._discovered_tools = tools
        for tool in tools:
            tool_name = tool.get("name", "unknown")
            self._mcp_tool_mapping[tool_name] = tool
            logger.debug(f"Mapped tool: {tool_name}")

        # Step 4: Create tool functions for agent (if tools available)
        tool_functions = self._create_tool_functions(tools) if tools else []

        # Step 5: Generate system prompt (different for with/without tools)
        if mcp_available and tools:
            system_prompt = self._generate_system_prompt()
        else:
            system_prompt = self._generate_fallback_system_prompt()

        # Step 6: Initialize Agent with LiteLLMModel
        try:
            self.agent = Agent(
                name="InventoryManagementAgent",
                instructions=system_prompt,
                model=self._model,
                tools=tool_functions if tool_functions else None,
            )
            if mcp_available:
                logger.info(f"Agent initialized with {len(tool_functions)} tools")
            else:
                logger.info("Agent initialized in basic mode (no MCP tools)")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise

        return tools

    async def process_message(
        self, session_id: str, user_message: str
    ) -> Dict[str, Any]:
        """
        Process a user message through the agent with latest December 2025 patterns.

        Loads session history from PostgreSQL, passes message to Gemini agent,
        handles tool calls, detects destructive actions requiring confirmation.

        Latest Features:
        - Async/await throughout
        - Proper error handling with ModelBehaviorError, MaxTurnsExceeded
        - PostgreSQL session persistence
        - Exponential backoff retry for transient failures
        - Comprehensive logging

        Args:
            session_id: Session ID for conversation context
            user_message: User's natural language message

        Returns:
            Response dict with:
            - response: Agent's natural language response
            - status: "success", "pending_confirmation", or "error"
            - tool_calls: List of tools called
            - session_id: Session ID for follow-up
            - pending_action: Action waiting for confirmation (if applicable)

        Raises:
            ValueError: If session not found or message invalid
        """
        # Validate input
        if not user_message or not user_message.strip():
            logger.debug(f"Empty message for session {session_id}")
            return {
                "response": "How can I help with inventory or billing?",
                "status": "success",
                "session_id": session_id,
                "tool_calls": [],
            }

        try:
            # Load or create session from PostgreSQL (if SessionManager available)
            session = None
            if self.session_manager:
                session = await self.session_manager.get_session(session_id)
                if not session:
                    logger.info(f"Creating new session: {session_id}")
                    session = await self.session_manager.create_session(session_id)
            else:
                logger.debug(f"SessionManager not configured, using in-memory session: {session_id}")

            # Check for pending confirmation
            pending = self.confirmation_flow.get_pending_confirmation(session_id)
            if pending:
                # Handle confirmation response
                is_confirmed = self.confirmation_flow.handle_confirmation_response(
                    user_message
                )

                if is_confirmed is None:
                    # Invalid response
                    logger.debug(f"Invalid confirmation response: {user_message}")
                    return {
                        "response": "Please reply 'yes' or 'no'.",
                        "status": "pending_confirmation",
                        "session_id": session_id,
                        "pending_action": pending["action_type"],
                    }

                if is_confirmed:
                    # Execute pending action
                    logger.info(f"User confirmed action: {pending['action_type']}")
                    self.confirmation_flow.clear_pending_confirmation(session_id)
                    # Continue processing with original action
                else:
                    # Cancel pending action
                    logger.info(f"User cancelled action: {pending['action_type']}")
                    self.confirmation_flow.clear_pending_confirmation(session_id)
                    return {
                        "response": "Action cancelled.",
                        "status": "success",
                        "session_id": session_id,
                        "tool_calls": [],
                    }

            # Log incoming message
            logger.info(
                f"Processing message for session {session_id}: "
                f"{user_message[:50]}..."
            )

            # Call agent with message (Gemini 2.0 Flash Lite via LiteLLM)
            # Use async version since we're in async context
            try:
                result = await Runner.run(self.agent, user_message)
                agent_response = result.final_output or ""
                tool_calls = self._extract_tool_calls(result)

            except ModelBehaviorError as e:
                # Gemini model produced invalid output
                logger.error(f"Model behavior error: {e}")
                return {
                    "response": (
                        "The model produced an invalid response. "
                        "Please try rephrasing your request."
                    ),
                    "status": "error",
                    "session_id": session_id,
                    "tool_calls": [],
                }

            except MaxTurnsExceeded as e:
                # Agent loop hit max iterations
                logger.error(f"Max turns exceeded: {e}")
                return {
                    "response": (
                        "The conversation became too complex. "
                        "Please try a simpler request."
                    ),
                    "status": "error",
                    "session_id": session_id,
                    "tool_calls": [],
                }

            except AuthenticationError as e:
                # Invalid API key or authentication failed
                logger.error(f"Authentication failed: {e}")
                return {
                    "response": (
                        "Authentication failed. Please verify your GEMINI_API_KEY is valid. "
                        "Get a free API key at https://ai.google.dev"
                    ),
                    "status": "error",
                    "session_id": session_id,
                    "tool_calls": [],
                }

            except RateLimitError as e:
                # API rate limit exceeded
                logger.warning(f"Rate limit exceeded: {e}")
                error_msg = str(e)
                # Check if it's a quota error
                if "quota" in error_msg.lower() or "resource_exhausted" in error_msg.lower():
                    return {
                        "response": (
                            "API quota exceeded. Please wait a few moments and try again. "
                            "The free tier has daily limits - consider upgrading for unlimited access."
                        ),
                        "status": "error",
                        "session_id": session_id,
                        "tool_calls": [],
                    }
                else:
                    return {
                        "response": (
                            "The service is busy. Please wait a moment and try again."
                        ),
                        "status": "error",
                        "session_id": session_id,
                        "tool_calls": [],
                    }

            except Exception as e:
                # Connection, API, or other errors
                logger.error(f"Agent execution failed: {e}")
                if "connection" in str(e).lower():
                    return {
                        "response": (
                            "Connection error. Please ensure MCP server is running "
                            "and try again."
                        ),
                        "status": "error",
                        "session_id": session_id,
                        "tool_calls": [],
                    }
                raise

            # Check for destructive actions
            if self.confirmation_flow.is_destructive_action(user_message, None):
                # Extract action details from tool calls
                action_type = self._detect_action_type(tool_calls)
                action_details = self._extract_action_details(
                    action_type, user_message, tool_calls
                )

                # Set pending confirmation
                self.confirmation_flow.set_pending_confirmation(
                    session_id, action_type, action_details
                )

                confirmation_prompt = (
                    self.confirmation_flow.generate_confirmation_prompt(
                        action_type, action_details
                    )
                )

                # Update conversation history in PostgreSQL (if session manager available)
                if session and self.session_manager:
                    new_history = session.conversation_history + [
                        {
                            "role": "user",
                            "content": user_message,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                        {
                            "role": "assistant",
                            "content": confirmation_prompt,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    ]
                    await self.session_manager.save_session(
                        session_id, new_history
                    )

                logger.info(f"Confirmation required: {action_type}")
                return {
                    "response": confirmation_prompt,
                    "status": "pending_confirmation",
                    "session_id": session_id,
                    "pending_action": action_type,
                }

            # Update conversation history in PostgreSQL (if session manager available)
            if session and self.session_manager:
                new_history = session.conversation_history + [
                    {
                        "role": "user",
                        "content": user_message,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    {
                        "role": "assistant",
                        "content": agent_response,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                ]
                await self.session_manager.save_session(session_id, new_history)

            # Log tool calls
            for tool_call in tool_calls:
                logger.debug(
                    f"Tool called: {tool_call.get('tool')} with "
                    f"args {tool_call.get('arguments')}"
                )

            logger.info(f"Message processed successfully: session {session_id}")
            return {
                "response": agent_response,
                "status": "success",
                "session_id": session_id,
                "tool_calls": tool_calls,
            }

        except ValueError as e:
            # Session or validation errors
            logger.error(f"Validation error: {e}")
            return {
                "response": f"Invalid request: {str(e)}",
                "status": "error",
                "session_id": session_id,
                "tool_calls": [],
            }

        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error processing message: {e}", exc_info=True)
            return {
                "response": (
                    "An unexpected error occurred. "
                    "Please try again or contact support."
                ),
                "status": "error",
                "session_id": session_id,
                "tool_calls": [],
            }

    def _create_tool_functions(
        self, tools: List[Dict[str, Any]]
    ) -> List:
        """
        Create dynamic Python functions for discovered MCP tools.

        Generates tool functions with proper signatures that accept parameters
        from the agent and execute actual MCP calls.

        Args:
            tools: List of tool schemas from MCP server

        Returns:
            List of tool functions for Agent registration
        """
        tool_functions = []

        for tool in tools:
            tool_name = tool.get("name")
            tool_description = tool.get("description", "")
            schema = tool.get("schema", {})

            try:
                # Extract properties and required fields
                properties = schema.get("properties", {})
                required = schema.get("required", [])
                field_names = list(properties.keys())

                # Build field definitions from schema properties
                fields = {}
                for prop_name, prop_schema in properties.items():
                    # Map JSON schema types to Python types
                    prop_type = self._schema_type_to_python(prop_schema)
                    is_required = prop_name in required

                    if is_required:
                        fields[prop_name] = (prop_type, ...)  # ... means required
                    else:
                        fields[prop_name] = (prop_type, None)  # None as default

                # Create Pydantic model for validation
                if fields:
                    ToolArgsModel = create_model(
                        f"{tool_name}_Args",
                        __config__=ConfigDict(extra='forbid'),
                        **fields
                    )
                else:
                    class ToolArgsModel(BaseModel):
                        model_config = ConfigDict(extra='forbid')

                # Create tool wrapper function with PROPER PARAMETERS
                # This function accepts the actual parameters from the agent
                def create_tool_wrapper(name, client, properties, required_fields):
                    """
                    Factory function to create a tool wrapper with proper signature.
                    Uses exec to dynamically create a function with correct parameters.
                    """
                    # Build parameter list for function signature
                    params = []
                    param_names = []
                    for prop_name in properties.keys():
                        is_required = prop_name in required_fields
                        param_names.append(prop_name)
                        if is_required:
                            params.append(prop_name)
                        else:
                            params.append(f"{prop_name}=None")

                    param_string = ", ".join(params)

                    # Build arguments dict construction
                    if param_names:
                        args_lines = "\n        ".join([
                            f'"{pn}": {pn},' for pn in param_names
                        ])
                        args_code = f"arguments = {{\n        {args_lines}\n        }}"
                    else:
                        args_code = "arguments = {}"

                    # Create function code with proper parameters
                    func_code = f"""
def tool_wrapper({param_string}) -> str:
    \"\"\"Execute MCP tool call.\"\"\"
    try:
        # Build arguments dict from parameters
        {args_code}

        # Remove None values (optional parameters not provided)
        arguments = {{k: v for k, v in arguments.items() if v is not None}}

        # Call MCP server
        result = client.call_tool('{name}', arguments)

        # Return result as formatted string
        import json
        if isinstance(result, dict):
            return json.dumps(result, indent=2)
        return str(result)
    except Exception as e:
        logger.error(f"Error executing tool {name}: {{e}}")
        raise ValueError(f"Tool execution failed: {{str(e)}}")
"""

                    # Create a namespace for exec
                    namespace = {
                        'client': client,
                        'json': __import__('json'),
                        'logger': logger
                    }

                    # Execute the function definition
                    exec(func_code, namespace)
                    return namespace['tool_wrapper']

                # Create the tool wrapper with correct signature
                tool_wrapper = create_tool_wrapper(
                    tool_name,
                    self.tools_client,
                    properties,
                    required
                )
                tool_wrapper.__name__ = tool_name

                # Build detailed docstring
                detailed_doc = tool_description + "\n\nParameters:\n"
                for fname in field_names:
                    is_required = fname in required
                    prop_schema = properties.get(fname, {})
                    param_type = self._schema_type_to_python(prop_schema).__name__
                    required_str = " (required)" if is_required else " (optional)"
                    prop_desc = prop_schema.get("description", "")
                    detailed_doc += f"- {fname}: {param_type}{required_str}"
                    if prop_desc:
                        detailed_doc += f" - {prop_desc}"
                    detailed_doc += "\n"
                tool_wrapper.__doc__ = detailed_doc

                # Register with function_tool decorator
                try:
                    decorated_tool = function_tool(tool_wrapper)
                    tool_functions.append(decorated_tool)
                    logger.info(f"✓ Registered tool: {tool_name} with {len(field_names)} parameters")
                except Exception as e:
                    logger.warning(f"Failed to decorate tool {tool_name}: {e}")
                    # Still add unwrapped version
                    tool_functions.append(tool_wrapper)

            except Exception as e:
                logger.error(f"Failed to register tool {tool_name}: {e}", exc_info=True)

        logger.info(f"Tool registration complete: {len(tool_functions)} tools ready")
        return tool_functions

    def _schema_type_to_python(self, schema: Dict[str, Any]) -> type:
        """Convert JSON schema type to Python type."""
        json_type = schema.get("type")

        if json_type == "string":
            return str
        elif json_type == "integer":
            return int
        elif json_type == "number":
            return float
        elif json_type == "boolean":
            return bool
        elif json_type == "array":
            return list
        elif json_type == "object":
            return dict
        else:
            # Default to Any
            return Any

    def _clean_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean MCP schema for strict Pydantic compatibility.

        Recursively removes additionalProperties from all object types to work
        with OpenAI Agents SDK strict JSON schema validation.
        """
        def clean_value(value):
            if isinstance(value, dict):
                cleaned = {}
                for key, val in value.items():
                    # Skip additionalProperties entirely
                    if key == "additionalProperties":
                        continue
                    # Recursively clean nested structures
                    cleaned[key] = clean_value(val)
                return cleaned
            elif isinstance(value, list):
                return [clean_value(v) for v in value]
            else:
                return value

        return clean_value(schema)

    def _generate_system_prompt(self) -> str:
        """Generate comprehensive system prompt for the agent.

        This prompt guides the agent to actively use MCP tools to answer
        user questions about inventory and billing operations.
        """
        return (
            "You are an intelligent Inventory Management Assistant powered by MCP tools. "
            "Your role is to help store administrators and salespersons with inventory and billing queries. "
            "\n"
            "CORE RESPONSIBILITIES:\n"
            "1. Answer user questions about inventory by CALLING THE APPROPRIATE TOOLS\n"
            "2. Provide accurate, data-driven responses based on tool results\n"
            "3. Execute inventory and billing operations when requested\n"
            "4. Guide users through multi-step processes\n"
            "\n"
            "TOOL USAGE GUIDELINES:\n"
            "\n"
            "For INVENTORY QUERIES (user asks about items, stock, categories):\n"
            "  - Use inventory_list_items to fetch items and their details\n"
            "  - Filter by category if user asks about specific categories (case-insensitive)\n"
            "  - Return complete information: item names, quantities, prices, categories\n"
            "  - Categories are stored in proper case: Grocery, Garments, Beauty, Utilities, Other\n"
            "  - Examples:\n"
            "    • 'tell me the grocery items' → call inventory_list_items(category='Grocery')\n"
            "    • 'show me GARMENTS' → call inventory_list_items(category='Garments')\n"
            "    • 'beauty products?' → call inventory_list_items(category='Beauty')\n"
            "\n"
            "For ADDING ITEMS:\n"
            "  - Use inventory_add_item with all required parameters\n"
            "  - Category is case-insensitive: 'grocery', 'GROCERY', 'Grocery' all work\n"
            "  - System normalizes categories to: Grocery, Garments, Beauty, Utilities, Other\n"
            "  - Ask for clarification if any required field (name, category, unit, price, stock) is missing\n"
            "  - If user provides invalid category, inform them of valid options and retry\n"
            "  - Confirm addition with the new item details and normalized category\n"
            "\n"
            "For UPDATING ITEMS:\n"
            "  - Use inventory_update_item to modify quantities, prices, or other details\n"
            "  - Require item_id and at least one field to update\n"
            "  - Category updates work case-insensitively: 'grocery', 'GROCERY', 'Grocery' all become 'Grocery'\n"
            "  - If invalid category provided, inform user of valid options and retry\n"
            "  - Confirm the update with new values in normalized format\n"
            "\n"
            "For DELETING ITEMS:\n"
            "  - Use inventory_delete_item when user explicitly requests deletion\n"
            "  - Always ask for confirmation before deleting (destructive action)\n"
            "  - Confirm deletion with the item ID that was removed\n"
            "\n"
            "For BILLING OPERATIONS:\n"
            "  - Use billing_create_bill to generate bills for customers\n"
            "  - Require customer_name and items array with item_id and quantity\n"
            "  - Always ask for confirmation before creating bills (destructive action)\n"
            "  - Use billing_list_bills to show all bills\n"
            "  - Use billing_get_bill to fetch specific bill details\n"
            "\n"
            "RESPONSE STRATEGY:\n"
            "1. Parse the user's question to identify what information they need\n"
            "2. Call the appropriate MCP tool(s) to fetch current data from the database\n"
            "3. Format the tool results into a clear, human-readable response\n"
            "4. Provide specific numbers, categories, and details from tool results\n"
            "5. If multiple tools are needed, call them in logical order\n"
            "6. If a tool returns an error (e.g., invalid category), explain it to user and suggest valid options\n"
            "\n"
            "CONVERSATION GUIDELINES:\n"
            "- Be proactive: Always fetch fresh data using tools, don't assume\n"
            "- Be clear: Provide specific details (item names, quantities, prices, IDs)\n"
            "- Be helpful: Ask clarifying questions if the request is ambiguous\n"
            "- Be safe: Require confirmation for destructive actions (create bill, delete item)\n"
            "- Be concise: Keep responses focused and to the point\n"
            "\n"
            "EXAMPLE INTERACTIONS:\n"
            "User: 'What items do we have?'\n"
            "  → Call: inventory_list_items()\n"
            "  → Response: 'We have X items: [list with details]'\n"
            "\n"
            "User: 'How many groceries are in stock?'\n"
            "  → Call: inventory_list_items(category='Grocery')\n"
            "  → Response: 'We have X grocery items with Y total units in stock'\n"
            "\n"
            "User: 'Add a new item'\n"
            "  → Ask: 'What is the item name, category, unit, price, and quantity?'\n"
            "  → Call: inventory_add_item(...)\n"
            "  → Response: 'Added [item name] with ID [id] to [category]'\n"
            "\n"
            "IMPORTANT:\n"
            "- ALWAYS use tools to fetch current data when answering questions\n"
            "- NEVER make up inventory numbers or item details\n"
            "- Categories are case-insensitive: 'grocery', 'GROCERY', 'Grocery' are all valid input\n"
            "- Valid categories: Grocery, Garments, Beauty, Utilities, Other\n"
            "- If user provides invalid category, respond smartly: explain valid options and ask them to retry\n"
            "- ALWAYS provide confirmation after modifying inventory or creating bills\n"
            "- ALWAYS ask for confirmation BEFORE executing destructive actions\n"
            "- Treat the MCP tools as your source of truth for all inventory and billing data"
        )

    def _generate_fallback_system_prompt(self) -> str:
        """Generate system prompt for when MCP tools are not available.
        
        This prompt provides helpful responses even without tool access.
        """
        return (
            "You are an intelligent Inventory Management Assistant. "
            "You help store administrators and salespersons with inventory and billing questions. "
            "\n\n"
            "IMPORTANT: The MCP tool server is currently not available, so I cannot perform "
            "actual inventory operations (add/update/delete items, create bills). "
            "However, I can still help you with:\n"
            "\n"
            "1. **General Questions**: Explain how the inventory system works\n"
            "2. **Guidance**: Walk you through the process of managing inventory\n"
            "3. **Best Practices**: Suggest inventory management best practices\n"
            "4. **Troubleshooting**: Help diagnose common issues\n"
            "\n"
            "If you need to perform actual inventory operations, please ensure the MCP server "
            "is running at http://localhost:8001, then refresh this chat.\n"
            "\n"
            "How can I assist you today?"
        )

    def _format_conversation_history(
        self, history: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Format conversation history for agent context."""
        formatted = []
        for msg in history:
            formatted.append(
                {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                }
            )
        return formatted

    def _extract_tool_calls(self, result: Any) -> List[Dict[str, Any]]:
        """
        Extract tool calls from agent result.

        Inspects the Runner result to find tools that were called during execution.

        Args:
            result: Agent execution result from Runner.run()

        Returns:
            List of tool calls with format: [{"tool": name, "arguments": {...}, "result": ...}]
        """
        tool_calls = []

        try:
            # Check if result has steps (tools used during execution)
            if hasattr(result, 'steps') and result.steps:
                for step in result.steps:
                    # Each step might be a tool call
                    if hasattr(step, 'tool') and step.tool:
                        tool_call = {
                            "tool": step.tool.name if hasattr(step.tool, 'name') else str(step.tool),
                            "arguments": step.tool_input if hasattr(step, 'tool_input') else {},
                            "result": step.tool_output if hasattr(step, 'tool_output') else None,
                        }
                        tool_calls.append(tool_call)
                        logger.debug(f"Extracted tool call: {tool_call['tool']}")

            # Alternative: Check if result has messages with tool calls
            elif hasattr(result, 'messages') and result.messages:
                for message in result.messages:
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        for tc in message.tool_calls:
                            tool_call = {
                                "tool": tc.function.name if hasattr(tc, 'function') else str(tc),
                                "arguments": tc.function.arguments if hasattr(tc, 'function') else {},
                            }
                            tool_calls.append(tool_call)
                            logger.debug(f"Extracted tool call from message: {tool_call['tool']}")

            # Fallback: Try to extract from raw result structure
            elif isinstance(result, dict):
                if 'tool_calls' in result:
                    tool_calls = result.get('tool_calls', [])
                elif 'tools' in result:
                    tool_calls = result.get('tools', [])

            if tool_calls:
                logger.info(f"Extracted {len(tool_calls)} tool calls from agent result")
            else:
                logger.debug("No tool calls found in agent result")

        except Exception as e:
            logger.warning(f"Error extracting tool calls: {e}")
            # Return empty list on error to avoid breaking the response

        return tool_calls

    def _detect_action_type(self, tool_calls: List[Dict[str, Any]]) -> str:
        """Detect action type from tool calls."""
        for call in tool_calls:
            tool_name = call.get("tool", "").lower()
            if "bill" in tool_name or "create" in tool_name:
                return "bill_creation"
            if "delete" in tool_name:
                return "item_deletion"
        return "unknown_action"

    def _extract_action_details(
        self,
        action_type: str,
        user_message: str,
        tool_calls: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract details about the action."""
        details = {}

        if action_type == "bill_creation":
            # Extract customer name and total from tool calls
            if tool_calls:
                details = tool_calls[0].get("arguments", {})
        elif action_type == "item_deletion":
            if tool_calls:
                details["item_name"] = tool_calls[0].get("arguments", {}).get(
                    "item_name", "item"
                )

        return details
