"""
Schema Query Agent (Phase 9) - MCP Version

AI agent for querying user's existing database schema using postgres-mcp.
Uses natural language to generate and execute SQL queries via MCP tools.
Read-only operations only - no table modifications.

Key Features:
- Connects to postgres-mcp server for database operations
- Uses MCP tools (execute_sql, list_tables, etc.) for all DB operations
- Read-only mode enforced at MCP server level
- Schema-aware prompts for intelligent querying
"""

import logging
import os
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from agents.extensions.models.litellm_model import LitellmModel
from agents.model_settings import ModelSettings

from app.services.schema_discovery import format_schema_for_prompt

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini/gemini-2.0-flash")


def get_llm_model():
    """
    Get the LLM model instance.
    Uses Gemini via LiteLLM if GEMINI_API_KEY is set, otherwise falls back to OpenAI.
    """
    if GEMINI_API_KEY:
        logger.info(f"[Schema Agent] Using Gemini model: {GEMINI_MODEL}")
        return LitellmModel(
            model=GEMINI_MODEL,
            api_key=GEMINI_API_KEY,
        )
    else:
        # Fallback to OpenAI if no Gemini key
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(f"[Schema Agent] Using OpenAI model: {openai_model}")
        return openai_model


# ============================================================================
# System Prompt Generator
# ============================================================================

def generate_schema_agent_prompt(schema_metadata: dict) -> str:
    """
    Generate system prompt with schema context for the agent.

    Args:
        schema_metadata: Discovered schema metadata dict

    Returns:
        System prompt string with database schema information
    """
    schema_description = format_schema_for_prompt(schema_metadata)

    return f"""You are a database query assistant that helps users explore and analyze their data.

## Your Capabilities
1. Convert natural language questions to SQL queries
2. Execute SELECT queries against the database using MCP tools
3. Present results in a clear, readable format
4. Suggest visualizations for data when appropriate

## Database Schema
{schema_description}

## Rules (CRITICAL - You MUST follow these)
1. **READ-ONLY**: You can ONLY execute SELECT queries. The database is in read-only mode.
2. **USE MCP TOOLS**: Always use the available MCP tools to interact with the database.
3. **EXPLAIN FIRST**: Before executing a query, briefly explain what you will do.
4. **VALIDATE DATA**: Check if the query makes sense given the schema.
5. **FORMAT RESULTS**: Present results clearly. For large results, summarize key findings.
6. **SUGGEST CHARTS**: When appropriate, suggest chart types (bar, line, pie) for visualization.
7. **HANDLE ERRORS**: If a query fails, explain why and suggest alternatives.
8. **BE HELPFUL**: If the user's question is ambiguous, ask for clarification.

## Available MCP Tools (from postgres-mcp)
- `execute_sql`: Execute a SQL query and return results
- `list_tables`: List all tables in the database
- `describe_table`: Get table structure with columns and types
- `get_table_stats`: Get statistics about a table
- `list_schemas`: List all schemas in the database

## Response Format
When presenting query results:
1. Briefly state what you found
2. Show the key data points
3. If applicable, suggest a visualization type
4. Offer follow-up questions the user might want to ask

Remember: You are analyzing the user's OWN data. Be helpful, accurate, and never attempt to modify anything."""


# ============================================================================
# Schema Query Agent with MCP
# ============================================================================

class SchemaQueryAgent:
    """
    AI Agent for natural language queries against user's existing database.
    Uses postgres-mcp for all database operations.

    Key Features:
    - MCP-based: Uses postgres-mcp server for database access
    - Schema-aware: Understands user's database structure
    - Read-only: Only executes SELECT queries (enforced by MCP)
    - Natural language: Converts questions to SQL
    - Visualization hints: Suggests charts for results

    Usage:
        agent = SchemaQueryAgent(
            database_uri="postgresql://...",
            schema_metadata={"tables": [...], ...}
        )
        await agent.initialize()
        result = await agent.query("Show me top 10 customers")
        await agent.close()
    """

    def __init__(
        self,
        database_uri: str,
        schema_metadata: dict,
        read_only: bool = True,
    ):
        """
        Initialize Schema Query Agent.

        Args:
            database_uri: PostgreSQL connection string for user's database
            schema_metadata: Discovered schema metadata dict
            read_only: Whether to use read-only mode (default: True)
        """
        self.database_uri = database_uri
        self.schema_metadata = schema_metadata
        self.read_only = read_only

        # MCP server and agent instances
        self._mcp_server: Optional[MCPServerStdio] = None
        self._agent: Optional[Agent] = None

        # Conversation history for context
        self._conversation_history: List[Dict[str, str]] = []

        # Session info
        self._session_id = f"schema-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self._mcp_tools: List[str] = []
        self._is_initialized = False

        logger.info(
            f"[Schema Agent] Created agent instance "
            f"(read_only={read_only}, session={self._session_id})"
        )

    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize the MCP server and agent.

        Returns:
            Dict with initialization status and available tools
        """
        if self._is_initialized:
            return {
                "success": True,
                "message": "Already initialized",
                "tools": self._mcp_tools
            }

        try:
            # Determine access mode
            access_mode = "read-only" if self.read_only else "unrestricted"

            logger.info(f"[Schema Agent] Starting postgres-mcp (mode={access_mode})...")

            # Create MCP server using postgres-mcp via stdio
            self._mcp_server = MCPServerStdio(
                name=f"postgres-mcp-{self._session_id}",
                params={
                    "command": "postgres-mcp",
                    "args": [self.database_uri, f"--access-mode={access_mode}"],
                },
                cache_tools_list=True,
                client_session_timeout_seconds=60.0,  # 60 seconds for cloud DB connections
            )

            # Start the MCP server (enters async context)
            await self._mcp_server.__aenter__()

            # Get available tools from the MCP server
            tools = await self._mcp_server.list_tools()
            self._mcp_tools = [t.name for t in tools]

            logger.info(f"[Schema Agent] Connected with tools: {self._mcp_tools}")

            # Generate system prompt with schema context
            system_prompt = generate_schema_agent_prompt(self.schema_metadata)

            # Create the agent with MCP server
            self._agent = Agent(
                name="Schema Query Agent",
                instructions=system_prompt,
                model=get_llm_model(),
                mcp_servers=[self._mcp_server],
                model_settings=ModelSettings(tool_choice="auto"),
            )

            self._is_initialized = True

            logger.info(f"[Schema Agent] Initialized successfully")

            return {
                "success": True,
                "message": f"Connected via postgres-mcp (mode={access_mode})",
                "tools": self._mcp_tools,
                "session_id": self._session_id,
            }

        except FileNotFoundError:
            logger.error("[Schema Agent] postgres-mcp not found")
            return {
                "success": False,
                "error": "postgres-mcp not installed",
                "install_instructions": "Install postgres-mcp with: pipx install postgres-mcp",
            }
        except Exception as e:
            logger.error(f"[Schema Agent] Failed to initialize: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }

    async def query(
        self,
        natural_query: str,
    ) -> Dict[str, Any]:
        """
        Process a natural language query using the MCP-connected agent.

        Args:
            natural_query: User's question in natural language

        Returns:
            dict with response, and optional visualization hint
        """
        if not self._is_initialized:
            init_result = await self.initialize()
            if not init_result.get("success"):
                return {
                    "success": False,
                    "error": init_result.get("error", "Failed to initialize"),
                    "response": "I couldn't connect to the database. Please try again."
                }

        try:
            logger.info(f"[Schema Agent] Processing query: {natural_query[:50]}...")

            # Run the agent - it will use MCP tools automatically
            result = await Runner.run(
                self._agent,
                input=natural_query,
                max_turns=10  # Limit iterations
            )

            # Extract response
            response_text = str(result.final_output) if result.final_output else ""

            # Add to conversation history
            self._conversation_history.append({
                "role": "user",
                "content": natural_query
            })
            self._conversation_history.append({
                "role": "assistant",
                "content": response_text
            })

            # Detect if response contains data suitable for visualization
            visualization_hint = self._detect_visualization(response_text, natural_query)

            logger.info(f"[Schema Agent] Query completed successfully")

            return {
                "success": True,
                "response": response_text,
                "visualization_hint": visualization_hint
            }

        except Exception as e:
            logger.error(f"[Schema Agent] Query failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "response": f"I encountered an error processing your request: {str(e)}"
            }

    def _detect_visualization(self, response: str, query: str) -> Optional[Dict[str, str]]:
        """
        Detect if response data is suitable for visualization.

        Returns visualization hint dict or None.
        """
        query_lower = query.lower()
        response_lower = response.lower()

        # Keywords that suggest different chart types
        if any(word in query_lower for word in ["trend", "over time", "monthly", "daily", "weekly"]):
            return {"type": "line_chart", "reason": "Time-series data detected"}

        if any(word in query_lower for word in ["top", "bottom", "ranking", "compare", "by category"]):
            return {"type": "bar_chart", "reason": "Categorical comparison detected"}

        if any(word in query_lower for word in ["distribution", "percentage", "breakdown", "share"]):
            return {"type": "pie_chart", "reason": "Distribution data detected"}

        if "row" in response_lower and any(char.isdigit() for char in response):
            return {"type": "data_table", "reason": "Tabular data detected"}

        return None

    async def close(self) -> None:
        """
        Close the MCP server connection.
        """
        if self._mcp_server:
            try:
                await self._mcp_server.__aexit__(None, None, None)
                logger.info(f"[Schema Agent] MCP server closed for session {self._session_id}")
            except Exception as e:
                logger.error(f"[Schema Agent] Error closing MCP server: {e}")
            finally:
                self._mcp_server = None
                self._agent = None
                self._is_initialized = False

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self._conversation_history.copy()

    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._is_initialized

    @property
    def mcp_tools(self) -> List[str]:
        """Get list of available MCP tools."""
        return self._mcp_tools.copy()


# ============================================================================
# Factory Function
# ============================================================================

async def create_schema_query_agent(
    database_uri: str,
    schema_metadata: dict,
    auto_initialize: bool = True,
    read_only: bool = True,
) -> SchemaQueryAgent:
    """
    Factory function to create and initialize a Schema Query Agent.

    Args:
        database_uri: PostgreSQL connection string
        schema_metadata: Discovered schema metadata
        auto_initialize: Whether to initialize immediately
        read_only: Whether to use read-only mode

    Returns:
        Initialized SchemaQueryAgent instance
    """
    agent = SchemaQueryAgent(
        database_uri=database_uri,
        schema_metadata=schema_metadata,
        read_only=read_only,
    )

    if auto_initialize:
        result = await agent.initialize()
        if not result.get("success"):
            raise RuntimeError(f"Failed to initialize agent: {result.get('error')}")

    return agent
