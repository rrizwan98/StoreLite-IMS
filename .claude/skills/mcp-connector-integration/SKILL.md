---
name: mcp-connector-integration
description: Create new MCP connector integrations with OAuth browser authentication, sub-agent creation, and schema_agent integration. Use when adding new external service connectors like Slack, Google Drive, Airtable, Linear, GitHub, or any MCP-compatible service. Triggers on requests to add connectors, integrate external services, or create new MCP sub-agents.
---

# MCP Connector Integration Skill

This skill guides you through creating a complete MCP connector integration for external services. Each connector follows the same pattern: OAuth browser authentication, sub-agent creation with OpenAI Agents SDK, and integration with the main schema_agent.

## Overview

When integrating a new MCP connector, you will create:
1. **Frontend**: Predefined connector config, OAuth flow, UI components
2. **Backend**: Connector sub-agent, registry entry, MCP client integration
3. **Database**: User connection storage with encrypted credentials

## Before You Start

Before implementing any connector:
1. **Research the service's MCP server** using Context7 or web search
2. **Find the OAuth configuration** (client ID, authorization URL, scopes)
3. **Identify the MCP server URL** for the service
4. **Check available MCP tools** the service provides

## Implementation Checklist

### Phase 1: Frontend Configuration

#### 1.1 Add Predefined Connector

File: `frontend/lib/predefined-connectors.ts`

Add a new connector configuration following this template:

```typescript
const NEW_CONNECTOR: PredefinedConnector = {
  id: 'connector_id',           // lowercase, unique identifier
  name: 'Connector Name',       // Display name
  description: 'Brief description of what this connector does',
  logo: '/connectors/connector-logo.svg',  // Add logo to public/connectors/
  category: 'Category',         // e.g., 'Productivity', 'Development', 'Communication'
  capabilities: ['Capability 1', 'Capability 2', 'Capability 3'],
  developer: 'Developer/Company Name',
  website: 'https://service-website.com',
  privacyPolicy: 'https://service-website.com/privacy',
  authType: 'oauth',
  oauthConfig: {
    clientId: process.env.NEXT_PUBLIC_CONNECTOR_OAUTH_CLIENT_ID || '',
    authorizationUrl: 'https://service.com/oauth/authorize',
    redirectUri: typeof window !== 'undefined'
      ? `${window.location.origin}/connectors/callback/connector_id`
      : '',
    scopes: ['scope1', 'scope2'],  // OAuth scopes required
  },
  mcpServerUrl: 'https://mcp.service.com/mcp',  // MCP server endpoint
  isAvailable: true,
};

// Add to PREDEFINED_CONNECTORS array
export const PREDEFINED_CONNECTORS: PredefinedConnector[] = [
  NOTION_CONNECTOR,
  NEW_CONNECTOR,  // Add here
];
```

#### 1.2 Add Logo

Place the connector logo at: `frontend/public/connectors/connector-logo.svg`

#### 1.3 Add Environment Variable

File: `frontend/.env.local`
```
NEXT_PUBLIC_CONNECTOR_OAUTH_CLIENT_ID=your_client_id_here
```

### Phase 2: OAuth Callback Handler

File: `frontend/app/connectors/callback/page.tsx`

The callback page handles OAuth responses. For new connectors with different OAuth flows, update the token exchange logic in `handleNotionCallback` or create a new handler.

Key steps:
1. Extract authorization code from URL
2. Exchange code for tokens via backend API
3. Store connection in database
4. Redirect to success page

### Phase 3: Backend Sub-Agent

#### 3.1 Create Connector Agent

File: `backend/app/connector_agents/new_connector_agent.py`

```python
"""
New Connector Sub-Agent.

Specialized agent for handling all operations with the external service.
"""

import json
import logging
from typing import List, Dict, Any

from agents.tool import FunctionTool

from .base import BaseConnectorAgent
from app.connectors.mcp_client import UserMCPClient

logger = logging.getLogger(__name__)


class NewConnectorAgent(BaseConnectorAgent):
    """
    Specialized agent for New Service operations.
    """

    CONNECTOR_TYPE = "NewService"
    TOOL_NAME = "newservice_connector"
    TOOL_DESCRIPTION = (
        "Handle ALL operations with New Service including: "
        "[list main capabilities]. "
        "Use this for ANY New Service-related task."
    )

    def get_system_prompt(self) -> str:
        """Get connector-specific system prompt."""
        # IMPORTANT: Follow GPT-5.2 prompting guide
        # - Be direct and explicit
        # - Don't mention specific MCP tool names (they can change)
        # - Focus on capabilities, not implementation details
        return """You are an expert agent for [Service Name]. Execute operations using the connected MCP server.

## AUTONOMOUS EXECUTION
Execute tasks immediately. Make intelligent decisions based on content and context.
Do not ask unnecessary questions - use reasonable defaults.

## YOUR CAPABILITIES
- [List capability 1]
- [List capability 2]
- [List capability 3]
- [List capability 4]

## TERMINOLOGY
Understand the service's terminology:
- [Term 1] = [Explanation]
- [Term 2] = [Explanation]

## EXECUTION RULES

1. ALWAYS USE TOOLS - Never pretend to complete operations without calling tools
2. CHAIN OPERATIONS - Complete multi-step tasks automatically
3. SMART DEFAULTS - Generate appropriate names/values when not specified
4. REPORT RESULTS - Confirm what was done with specific details

## COMMON WORKFLOWS

### Workflow 1: [Description]
Step 1: [Action]
Step 2: [Action]

### Workflow 2: [Description]
Step 1: [Action]
Step 2: [Action]

## ERROR HANDLING
If an operation fails:
- Try alternative approaches
- Report specific error to user
- Suggest next steps

## RESPONSE FORMAT
After completing operations:
- What was done (with specifics)
- Any relevant IDs or links
- Errors if any occurred

Execute tasks completely using the available tools."""

    async def load_tools(self) -> List[FunctionTool]:
        """Load MCP tools from the service."""
        logger.info(f"[{self.CONNECTOR_TYPE}Agent] Loading tools from {self.server_url}")

        try:
            client = UserMCPClient(
                self.server_url,
                timeout=60.0,
                auth_type="oauth",
                auth_config=self.auth_config,
            )

            mcp_tools = await client.discover_tools()
            logger.info(f"[{self.CONNECTOR_TYPE}Agent] Discovered {len(mcp_tools)} MCP tools")

            function_tools = []
            for tool_def in mcp_tools:
                func_tool = self._create_function_tool(tool_def)
                if func_tool:
                    function_tools.append(func_tool)

            logger.info(f"[{self.CONNECTOR_TYPE}Agent] Created {len(function_tools)} function tools")
            return function_tools

        except Exception as e:
            logger.error(f"[{self.CONNECTOR_TYPE}Agent] Failed to load tools: {e}")
            return []

    def _create_function_tool(self, tool_def: Dict[str, Any]) -> FunctionTool:
        """Create a FunctionTool from MCP tool definition."""
        tool_name = tool_def.get("name", "unknown_tool")
        tool_description = tool_def.get("description", f"Tool: {tool_name}")
        input_schema = tool_def.get("inputSchema", {})

        cleaned_schema = self._clean_json_schema(input_schema)

        if cleaned_schema.get("type") != "object":
            cleaned_schema = {
                "type": "object",
                "properties": cleaned_schema.get("properties", {}),
                "required": cleaned_schema.get("required", []),
            }

        if "properties" not in cleaned_schema:
            cleaned_schema["properties"] = {}

        tool_func = self._create_tool_caller(tool_name)
        tool_func.__name__ = tool_name
        tool_func.__doc__ = tool_description

        return FunctionTool(
            name=tool_name,
            description=tool_description,
            params_json_schema=cleaned_schema,
            on_invoke_tool=tool_func,
            strict_json_schema=False,
        )

    def _create_tool_caller(self, tool_name: str):
        """Create a callable function for invoking an MCP tool."""
        server_url = self.server_url
        auth_config = self.auth_config
        connector_name = self.connector_name

        async def mcp_tool_caller(ctx, args: str) -> str:
            """Call MCP tool with given arguments."""
            try:
                kwargs = json.loads(args) if args else {}

                logger.info(f"[{connector_name}Agent] Calling tool: {tool_name}")
                logger.info(f"[{connector_name}Agent] Args: {str(kwargs)[:500]}...")

                client = UserMCPClient(
                    server_url,
                    timeout=60.0,
                    auth_type="oauth",
                    auth_config=auth_config,
                )
                result = await client.call_tool(tool_name, kwargs)

                # Format result with connector context for streaming UI
                result_text = ""
                if isinstance(result, dict):
                    if "content" in result:
                        contents = result["content"]
                        if isinstance(contents, list):
                            texts = [c.get("text", "") for c in contents if c.get("type") == "text"]
                            if texts:
                                result_text = "\n".join(texts)
                    if not result_text:
                        result_text = json.dumps(result, indent=2)
                else:
                    result_text = str(result)

                logger.info(f"[{connector_name}Agent] {tool_name} completed successfully")
                return f"[{connector_name}:{tool_name}] {result_text}"

            except json.JSONDecodeError as e:
                error_msg = f"[{connector_name}:{tool_name}] Error: Invalid arguments - {e}"
                logger.error(error_msg)
                return error_msg
            except Exception as e:
                error_msg = f"[{connector_name}:{tool_name}] Error: {str(e)}"
                logger.error(error_msg)
                return error_msg

        return mcp_tool_caller

    def _clean_json_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Clean JSON schema for OpenAI compatibility."""
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
```

#### 3.2 Register in Registry

File: `backend/app/connector_agents/registry.py`

```python
from .new_connector_agent import NewConnectorAgent

class ConnectorAgentRegistry:
    AGENT_CLASSES: Dict[str, Type[BaseConnectorAgent]] = {
        "notion": NotionConnectorAgent,
        "newservice": NewConnectorAgent,  # Add here
    }

    URL_PATTERNS: Dict[str, str] = {
        "notion": "notion",
        "newservice": "newservice",  # Add URL pattern
    }
```

#### 3.3 Export in __init__.py

File: `backend/app/connector_agents/__init__.py`

```python
from .new_connector_agent import NewConnectorAgent
```

### Phase 4: Backend Environment

File: `backend/.env`
```
# New Service OAuth (if backend handles token exchange)
NEWSERVICE_CLIENT_ID=your_client_id
NEWSERVICE_CLIENT_SECRET=your_client_secret
```

### Phase 5: OAuth Token Exchange (if needed)

If the connector requires server-side token exchange, add endpoint:

File: `backend/app/routers/oauth.py` (create if not exists)

```python
@router.post("/oauth/newservice/callback")
async def newservice_oauth_callback(
    request: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exchange authorization code for tokens."""
    # Exchange code for tokens
    # Encrypt and store credentials
    # Create UserMCPConnection record
    pass
```

## Testing the Integration

1. **UI Test**: Click the new connector button in "Manage Tools"
2. **OAuth Test**: Complete the OAuth flow
3. **Connection Test**: Verify connector shows as "Connected"
4. **Agent Test**: Ask the agent to perform an operation with the new service
5. **Streaming Test**: Verify progress messages show correct tool names

## GPT-5.2 Prompting Best Practices

When writing sub-agent prompts:

1. **Be Direct**: "Execute tasks immediately" not "You might want to consider..."
2. **No Tool Names**: Say "use the available tools" not "call notion-search"
3. **Autonomous Execution**: Agent should complete tasks without asking unnecessary questions
4. **Smart Defaults**: Generate appropriate values when not specified
5. **Clear Structure**: Use headers and bullet points for scannability
6. **Error Handling**: Include fallback strategies
7. **Result Reporting**: Always confirm what was done

## File Structure Reference

```
frontend/
  lib/
    predefined-connectors.ts     # Add connector config
  public/
    connectors/
      connector-logo.svg         # Add logo
  app/
    connectors/
      callback/
        page.tsx                 # OAuth callback handler

backend/
  app/
    connector_agents/
      __init__.py                # Export new agent
      registry.py                # Register agent class
      new_connector_agent.py     # New agent implementation
    routers/
      oauth.py                   # Token exchange (if needed)
```

## Common Issues

1. **OAuth Redirect Mismatch**: Ensure redirect URI matches exactly in OAuth app config
2. **Tool Discovery Fails**: Check MCP server URL and authentication
3. **Agent Not Using Tools**: Verify registry mapping and connector type detection
4. **Streaming Shows "unknown_tool"**: Check tool name extraction in streaming handler

## Additional Resources

For detailed implementation, read supporting files:
- [backend-reference.md](backend-reference.md) - Backend code patterns
- [frontend-reference.md](frontend-reference.md) - Frontend UI patterns
- [agent-template.md](agent-template.md) - Agent prompt templates
