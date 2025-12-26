"""
Notion Connector Sub-Agent.

Specialized agent for handling all Notion operations.
This agent understands Notion's terminology, API structure, and workflows.
"""

import json
import logging
from typing import List, Dict, Any

from agents.tool import FunctionTool

from .base import BaseConnectorAgent
from app.connectors.mcp_client import UserMCPClient

logger = logging.getLogger(__name__)


class NotionConnectorAgent(BaseConnectorAgent):
    """
    Specialized agent for Notion operations.

    Handles:
    - Creating pages (rows in tables)
    - Creating databases (tables)
    - Searching pages and databases
    - Updating page properties
    - Querying database contents

    This agent knows:
    - Notion terminology (Database = Table, Page = Row, Property = Column)
    - Notion API structure and required formats
    - Common workflows (search → create → update)
    """

    CONNECTOR_TYPE = "Notion"
    TOOL_NAME = "notion_connector"
    TOOL_DESCRIPTION = (
        "Handle ALL Notion operations including: "
        "creating pages/rows, creating databases/tables, "
        "searching content, updating pages, and querying data. "
        "Use this for ANY Notion-related task."
    )

    def get_system_prompt(self) -> str:
        """Get Notion-specific system prompt."""
        return """You are a Notion Expert Agent. Your job is to execute Notion operations using the available tools.

## AUTONOMOUS EXECUTION
Execute tasks immediately. Make intelligent decisions based on the content and context.
- Need a name? → Generate from content + current date
- Need a location? → Use workspace root or first available page
- Need format? → Use professional structure appropriate to content

Execute, don't ask unnecessary questions.

## YOUR CAPABILITIES
- Search for pages and databases
- Create new pages (for documents, reports, notes)
- Create new databases (for structured/tabular data)
- Update existing pages
- Query database contents

## PAGE vs DATABASE

USE PAGE FOR:
- Documents, reports, notes
- Rich text content with formatting
- Any "save content" request

USE DATABASE FOR:
- Structured data with columns
- Data that needs filtering/sorting
- Tabular information

## TERMINOLOGY
- "Table" = Database in Notion
- "Row" or "Item" = Page in Database
- "Column" = Property
- "Report" or "Document" = Page

## AVAILABLE TOOLS (from Notion MCP)
The actual tool names from Notion MCP server:
- `notion-search` - Search for pages/databases (query MUST be non-empty, at least 1 character)
- `notion-create-page` - Create a new page
- `notion-update-page` - Update page properties
- `notion-get-page` - Get page details
- `notion-list-databases` - List available databases
- `notion-query-database` - Query rows from a database
- `notion-create-database` - Create a new database

## CRITICAL: SEARCH TOOL REQUIREMENTS
The `notion-search` tool REQUIRES a non-empty query string (minimum 1 character).
- ✅ CORRECT: {"query": "page", "page_size": 10}
- ✅ CORRECT: {"query": "report", "page_size": 5}
- ❌ WRONG: {"query": "", "page_size": 1} - This will FAIL!

If you need to find any page, search for common terms like "page", "home", or a word from the content you want to save.

## EXECUTION RULES

1. ALWAYS USE TOOLS - Never pretend without calling a tool
2. NON-EMPTY SEARCH - Always use a search term (never empty query)
3. SMART NAMING - Generate contextually appropriate names
4. CHAIN OPERATIONS - Complete multi-step tasks automatically
5. REPORT RESULTS - Confirm what was done

## WORKFLOW: SAVE CONTENT TO NOTION

Step 1: Search for a parent page (use a keyword, never empty)
```
notion-search with {"query": "page", "page_size": 5}
```
Or search for something related to the content topic.

Step 2: Create new page with content
```
notion-create-page with parent, title, and content
```

## WORKFLOW: CREATE DATABASE

Step 1: Search for parent page (with a keyword)
Step 2: Create database with notion-create-database
Step 3: Add items with notion-create-page (for each item)

## ERROR HANDLING
If search returns no results:
- Try a different search term
- Or create the page at workspace root level

## RESPONSE FORMAT
After completing operations, provide:
- ✅ What was done
- 📄 Page/database name
- ❌ Errors if any occurred

Execute tasks completely using tools."""

    async def load_tools(self) -> List[FunctionTool]:
        """Load Notion MCP tools."""
        logger.info(f"[NotionAgent] Loading tools from {self.server_url}")

        try:
            client = UserMCPClient(
                self.server_url,
                timeout=60.0,
                auth_type="oauth",
                auth_config=self.auth_config,
            )

            # Discover tools from Notion MCP server
            mcp_tools = await client.discover_tools()
            logger.info(f"[NotionAgent] Discovered {len(mcp_tools)} MCP tools")

            # Convert MCP tools to FunctionTool format
            function_tools = []
            for tool_def in mcp_tools:
                func_tool = self._create_function_tool(tool_def)
                if func_tool:
                    function_tools.append(func_tool)

            logger.info(f"[NotionAgent] Created {len(function_tools)} function tools")
            return function_tools

        except Exception as e:
            logger.error(f"[NotionAgent] Failed to load tools: {e}")
            return []

    def _create_function_tool(self, tool_def: Dict[str, Any]) -> FunctionTool:
        """
        Create a FunctionTool from MCP tool definition.

        Args:
            tool_def: Tool definition from MCP server

        Returns:
            FunctionTool instance
        """
        tool_name = tool_def.get("name", "unknown_tool")
        tool_description = tool_def.get("description", f"Notion tool: {tool_name}")
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
        tool_func = self._create_tool_caller(tool_name)

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

    def _create_tool_caller(self, tool_name: str):
        """
        Create a callable function for invoking an MCP tool.

        Args:
            tool_name: Name of the tool to call

        Returns:
            Async function that calls the MCP tool
        """
        server_url = self.server_url
        auth_config = self.auth_config

        async def mcp_tool_caller(ctx, args: str) -> str:
            """Call Notion MCP tool with given arguments."""
            try:
                kwargs = json.loads(args) if args else {}
                logger.info(f"[NotionAgent] ═══════════════════════════════════════")
                logger.info(f"[NotionAgent] Calling tool: {tool_name}")
                logger.info(f"[NotionAgent] Args: {str(kwargs)[:500]}...")

                client = UserMCPClient(
                    server_url,
                    timeout=60.0,
                    auth_type="oauth",
                    auth_config=auth_config,
                )
                result = await client.call_tool(tool_name, kwargs)

                logger.info(f"[NotionAgent] Result type: {type(result).__name__}")
                logger.info(f"[NotionAgent] Result: {str(result)[:500]}...")

                # Format result
                if isinstance(result, dict):
                    if "content" in result:
                        contents = result["content"]
                        if isinstance(contents, list):
                            texts = []
                            for c in contents:
                                if isinstance(c, dict) and c.get("type") == "text":
                                    texts.append(c.get("text", ""))
                            if texts:
                                logger.info(f"[NotionAgent] ✓ {tool_name} completed")
                                return "\n".join(texts)
                    logger.info(f"[NotionAgent] ✓ {tool_name} completed")
                    return json.dumps(result, indent=2)

                logger.info(f"[NotionAgent] ✓ {tool_name} completed")
                return str(result)

            except json.JSONDecodeError as e:
                logger.error(f"[NotionAgent] Invalid JSON args for {tool_name}: {e}")
                return f"Error: Invalid arguments format - {e}"
            except Exception as e:
                logger.error(f"[NotionAgent] Error calling {tool_name}: {e}")
                return f"Error calling {tool_name}: {str(e)}"

        return mcp_tool_caller

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
