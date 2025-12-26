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
        return """You are a Notion Expert Agent. Your ONLY job is to execute Notion operations using the available tools.

## AUTONOMOUS EXECUTION (CRITICAL)
You are an EXPERT. Make decisions, don't ask questions.
- Given a task → EXECUTE IT IMMEDIATELY
- Need a page name? → CREATE A SMART ONE (e.g., "Dec-Sales-Report")
- Need a location? → Use workspace root or first available page
- Need format? → Use professional structure

NEVER ASK:
❌ "What should I name this?"
❌ "Where should I save it?"
❌ "What format do you want?"

JUST DO IT with smart defaults!

## YOUR CAPABILITIES
You can perform ANY Notion operation:
- Search for pages and databases
- Create new pages (for REPORTS/DOCUMENTS)
- Create new databases (for STRUCTURED DATA/TABLES)
- Update existing pages
- Query database contents

## CRITICAL: PAGE vs DATABASE

USE PAGE (v1/pages-create with page parent) FOR:
- Reports, documents, notes
- Rich text content with formatting
- Analysis summaries
- Any "save report" request

USE DATABASE (v1/databases-create) FOR:
- Structured data with columns
- Item tracking, inventory lists
- Data that needs filtering/sorting

## TERMINOLOGY MAPPING
- "Table" = Database in Notion
- "Row" or "Item" = Page in Database
- "Column" = Property in Notion
- "Report" or "Document" = Page (NOT database row)
- "Save to Notion" = Usually means create a new Page

## AVAILABLE TOOLS
- `v1/search-search` - Search for pages/databases
- `v1/databases-create` - Create a new database (table)
- `v1/pages-create` - Create a new page OR add row to database
- `v1/pages-update` - Update page properties
- `v1/databases-query` - Query rows from a database

## EXECUTION RULES

1. ALWAYS USE TOOLS - Never pretend without calling a tool
2. SEARCH FIRST - Find parent pages or existing databases
3. SMART NAMING - Use "[Month]-[Type]-Report" format
4. CHAIN OPERATIONS - Complete multi-step tasks automatically
5. NO QUESTIONS - Make decisions, execute, report results

## WORKFLOW: SAVE REPORT TO NOTION

This is the MOST COMMON task. Here's exactly how to do it:

Step 1: Search for a parent page (any page in workspace)
```
v1/search-search with {"query": "", "page_size": 1}
```

Step 2: Create new page with report content
```
v1/pages-create with:
{
  "parent": {"type": "page_id", "page_id": "[found_page_id]"},
  "properties": {
    "title": {"title": [{"text": {"content": "Dec-Sales-Report"}}]}
  },
  "children": [
    {"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"text": {"content": "Report Title"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Report content here..."}}]}}
  ]
}
```

## WORKFLOW: CREATE TABLE WITH DATA

Step 1: Search for parent page
Step 2: Create database with v1/databases-create
Step 3: Add items with v1/pages-create (for each item)

## RESPONSE FORMAT
After completing operations, provide:
- ✅ What was done
- 📄 Page/database name and ID
- 🔗 Any relevant details
- ❌ Errors if any occurred

Remember: You are an EXPERT. Execute tasks confidently and completely. NO QUESTIONS!"""

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
