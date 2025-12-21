"""
Schema Query Agent (Phase 9/10) - MCP Version with Gmail Integration

AI agent for querying user's existing database schema using postgres-mcp.
Uses natural language to generate and execute SQL queries via MCP tools.
Read-only operations only - no table modifications.

Key Features:
- Connects to postgres-mcp server for database operations
- Uses MCP tools (execute_sql, list_tables, etc.) for all DB operations
- Read-only mode enforced at MCP server level
- Schema-aware prompts for intelligent querying
- Gmail integration for sending query results via email (Phase 10)
"""

import logging
import os
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from agents.extensions.models.litellm_model import LitellmModel
from agents.extensions.memory import SQLAlchemySession
from agents.model_settings import ModelSettings

from app.services.schema_discovery import format_schema_for_prompt
from app.services.agent_session_service import create_user_session, AgentSessionManager

logger = logging.getLogger(__name__)

# Version marker for debugging
SCHEMA_AGENT_VERSION = "2.2.0-mcp-gmail-session"
logger.info(f"[Schema Agent] Module loaded - Version {SCHEMA_AGENT_VERSION} (MCP-enabled with Gmail + PostgreSQL Sessions)")


# ============================================================================
# Configuration
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Use Gemini 2.0 Flash which supports function calling well
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini/gemini-2.5-flash")


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

    return f"""You are a world-class database analyst and query assistant. Your job is to deeply understand user questions, execute precise SQL queries, and provide comprehensive, well-structured answers grounded in actual data.

############################################
URGENT: CHECK FOR TOOL PREFIX FIRST
############################################
BEFORE doing anything else, check if the user's message starts with [TOOL:GMAIL].
If YES: You MUST call the send_email tool after getting query results. This is NON-NEGOTIABLE.
If the message contains [TOOL:GMAIL], failure to call send_email is a critical error.

############################################
CORE MISSION
############################################
Answer the user's data questions fully and helpfully with concrete results they can trust. Never invent data. Default to detailed and useful. Go one step further: after answering, add high-value insights supporting the user's underlying goal.

############################################
DATABASE SCHEMA
############################################
{schema_description}

############################################
AVAILABLE MCP TOOLS
############################################
- `execute_sql`: Execute SQL queries and return results
- `list_schemas`: List all database schemas
- `list_objects`: List tables, views, and objects
- `get_object_details`: Get column info for a table/view
- `explain_query`: Get query execution plan
- `get_top_queries`: Find slow queries for optimization

############################################
AVAILABLE FUNCTION TOOLS
############################################
- `send_email`: Send query results or any content via user's connected Gmail
- `check_email_status`: Check if user's Gmail is connected and ready

<tool_usage_rules>
- Prefer tools for all data queries - never guess or fabricate results
- Parallelize independent reads to reduce latency
- After executing queries, present:
  * What was found (data first!)
  * Key insights or patterns
  * Relevant context or implications
- Use send_email when user explicitly asks to email/send results
- If email fails due to not connected, inform user to connect Gmail in settings
</tool_usage_rules>

############################################
GMAIL TOOL ACTIVATION (IMPORTANT)
############################################
<gmail_tool_rules>
When message starts with [TOOL:GMAIL], the user has selected the Gmail tool:
1. Execute the query to get the requested data
2. ALWAYS call send_email tool with the results - this is MANDATORY
3. Format email body PROFESSIONALLY with:
   - Greeting: "Hello,"
   - Brief description of the data
   - Data formatted in clean, readable tables (use ASCII tables, not markdown)
   - Summary/insights section
   - Sign-off: "Best regards,\nAI Data Assistant\nIMS Inventory System"
4. Use descriptive email subject based on the query

EMAIL FORMAT TEMPLATE:
```
Hello,

Here is the data you requested:

[QUERY DESCRIPTION]

[DATA IN READABLE TABLE FORMAT]
Example:
+--------+------------+-----------+
| Column | Column     | Column    |
+--------+------------+-----------+
| Value  | Value      | Value     |
+--------+------------+-----------+

Summary:
- [Key insight 1]
- [Key insight 2]

Best regards,
AI Data Assistant
IMS Inventory System
```

CRITICAL: When [TOOL:GMAIL] is present, sending email is NOT optional - always send!
</gmail_tool_rules>

############################################
EXECUTION BEHAVIOR (NON-NEGOTIABLE)
############################################
<execution_spec>
- IMMEDIATELY execute queries when user asks a question
- DO NOT ask for confirmation before running queries
- DO NOT show SQL and wait for approval
- DO NOT say "I will execute..." - just execute and show results
- The user asked, so they want the answer - deliver it directly
- READ-ONLY mode: Only SELECT queries are allowed
</execution_spec>

############################################
OUTPUT VERBOSITY & FORMATTING
############################################
<output_verbosity_spec>
- For simple counts/lookups: 1-2 sentences with the answer
- For data listings: formatted table or numbered list
- For complex analysis: 1 short overview + key data points + insights
- Avoid long narrative paragraphs; prefer compact bullets and tables
- Do not rephrase user requests unless semantics change
</output_verbosity_spec>

<formatting_rules>
- Use Markdown tables for tabular data
- Use numbered lists for rankings/top-N queries
- Use bullets for insights and observations
- Bold key numbers and findings
- Include data visualization suggestions when appropriate (bar, line, pie)
</formatting_rules>

############################################
HANDLING AMBIGUITY
############################################
<uncertainty_and_ambiguity>
- If query is ambiguous, state best-guess interpretation plainly
- Then comprehensively answer the most likely intent
- If multiple interpretations exist, answer the most common one
- DO NOT ask clarifying questions - just answer intelligently
- For schema mismatches: suggest closest matching columns/tables
</uncertainty_and_ambiguity>

############################################
ERROR HANDLING
############################################
<error_handling_spec>
- If a query fails, explain why clearly
- Suggest corrected query or alternative approach
- Check column names against schema before reporting "not found"
- For permission errors: explain read-only limitations
</error_handling_spec>

############################################
VALUE-ADD BEHAVIOR
############################################
<value_add_spec>
- Provide concrete data with specific numbers, counts, percentages
- Include relevant context (trends, comparisons, notable patterns)
- Suggest follow-up analyses the user might find valuable
- For time-series data: mention trends or changes over time
- For aggregations: break down by relevant dimensions if useful
</value_add_spec>

############################################
EXAMPLE BEHAVIORS
############################################
User: "How many users are there?"
→ Execute COUNT query immediately
→ Response: "There are **150 users** in the database."

User: "Show top 5 products by price"
→ Execute ORDER BY query immediately
→ Response:
"**Top 5 Products by Price:**
| Rank | Product | Price |
|------|---------|-------|
| 1 | Product A | $999 |
| 2 | Product B | $850 |
..."

User: "What's our best selling item?"
→ Execute aggregation query on sales/orders
→ Response: "**Best Seller:** Product X with 1,234 units sold.
This represents 23% of total sales volume."

############################################
FINAL CHECKLIST (INTERNAL)
############################################
Before responding, verify:
✓ Did I execute the query (not just describe it)?
✓ Did I present actual data from the database?
✓ Is the answer formatted clearly and concisely?
✓ Did I add useful context or insights?

You are analyzing the user's OWN data. Be helpful, accurate, and action-oriented."""


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
        user_id: Optional[int] = None,
        enable_gmail: bool = True,
        thread_id: Optional[str] = None,
    ):
        """
        Initialize Schema Query Agent.

        Args:
            database_uri: PostgreSQL connection string for user's database
            schema_metadata: Discovered schema metadata dict
            read_only: Whether to use read-only mode (default: True)
            user_id: User ID for tool context (needed for Gmail integration)
            enable_gmail: Whether to enable Gmail tools (default: True)
            thread_id: Thread ID for ChatKit session (for persistent conversation)
        """
        self.database_uri = database_uri
        self.schema_metadata = schema_metadata
        self.read_only = read_only
        self.user_id = user_id
        self.enable_gmail = enable_gmail
        self.thread_id = thread_id

        # MCP server and agent instances
        self._mcp_server: Optional[MCPServerStdio] = None
        self._agent: Optional[Agent] = None

        # Session manager for PostgreSQL-backed conversation history
        self._session_manager: Optional[AgentSessionManager] = None
        self._persistent_session: Optional[SQLAlchemySession] = None

        # Fallback in-memory history (used if session fails)
        self._conversation_history: List[Dict[str, str]] = []

        # Session info
        self._session_id = f"schema-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self._mcp_tools: List[str] = []
        self._function_tools: List[str] = []
        self._is_initialized = False

        # Initialize session manager if user_id is provided
        if user_id:
            self._session_manager = AgentSessionManager(user_id)

        logger.info(
            f"[Schema Agent] Created agent instance "
            f"(read_only={read_only}, user_id={user_id}, gmail={enable_gmail}, "
            f"thread={thread_id}, session={self._session_id})"
        )

    async def initialize(self) -> Dict[str, Any]:
        """
        Test connection to postgres-mcp and verify it works.

        Note: We create fresh MCP connections per query to avoid stale connection issues.
        This method just validates the setup.

        Returns:
            Dict with initialization status and available tools
        """
        if self._is_initialized:
            return {
                "success": True,
                "message": "Already initialized",
                "tools": self._mcp_tools
            }

        mcp_server = None
        try:
            # Determine access mode (postgres-mcp uses "restricted" for read-only)
            access_mode = "restricted" if self.read_only else "unrestricted"

            # Log sanitized URI (hide password)
            sanitized_uri = self.database_uri
            if "@" in sanitized_uri:
                # Hide password: postgresql://user:pass@host -> postgresql://user:***@host
                prefix, rest = sanitized_uri.split("@", 1)
                if ":" in prefix:
                    proto_user = prefix.rsplit(":", 1)[0]
                    sanitized_uri = f"{proto_user}:***@{rest}"

            logger.info(f"[Schema Agent] Testing postgres-mcp connection (mode={access_mode}, db={sanitized_uri[:60]}...)")

            # Create test MCP server to verify setup
            mcp_server = MCPServerStdio(
                name=f"postgres-mcp-init-{self._session_id}",
                params={
                    "command": "postgres-mcp",
                    "args": [self.database_uri, f"--access-mode={access_mode}"],
                },
                cache_tools_list=True,
                client_session_timeout_seconds=30.0,  # 30 seconds for init test
            )

            # Start the MCP server (enters async context)
            await mcp_server.__aenter__()

            # Get available tools from the MCP server
            tools = await mcp_server.list_tools()
            self._mcp_tools = [t.name for t in tools]

            logger.info(f"[Schema Agent] postgres-mcp verified with tools: {self._mcp_tools}")

            self._is_initialized = True

            return {
                "success": True,
                "message": f"postgres-mcp verified (mode={access_mode})",
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
            error_msg = str(e)
            # Better error messages for common issues
            if "Connection closed" in error_msg:
                logger.error(f"[Schema Agent] postgres-mcp connection failed - likely database connection issue")
                return {
                    "success": False,
                    "error": "Database connection failed. Please verify your database URI is correct and the database is accessible.",
                    "details": error_msg,
                }
            elif "timeout" in error_msg.lower():
                logger.error(f"[Schema Agent] postgres-mcp connection timeout")
                return {
                    "success": False,
                    "error": "Database connection timed out. The database may be slow or unreachable.",
                    "details": error_msg,
                }
            else:
                logger.error(f"[Schema Agent] Failed to initialize: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": error_msg,
                }
        finally:
            # Clean up test MCP server
            if mcp_server:
                try:
                    await mcp_server.__aexit__(None, None, None)
                except Exception:
                    pass

    async def query(
        self,
        natural_query: str,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a natural language query using the MCP-connected agent.

        Creates a fresh MCP connection for each query to avoid stale connection issues.
        Uses PostgreSQL-backed session for persistent conversation history.

        Args:
            natural_query: User's question in natural language
            thread_id: Optional thread ID for ChatKit (for persistent conversation)

        Returns:
            dict with response, and optional visualization hint
        """
        mcp_server = None

        try:
            logger.info(f"[Schema Agent] Processing query: {natural_query[:50]}...")

            # Use provided thread_id or instance thread_id
            effective_thread_id = thread_id or self.thread_id

            # Get or create persistent session for conversation history
            session = None
            if self._session_manager:
                try:
                    session = self._session_manager.get_session(effective_thread_id)  # Sync call
                    logger.info(f"[Schema Agent] Using PostgreSQL session for user {self.user_id}, thread {effective_thread_id}")
                except Exception as e:
                    logger.warning(f"[Schema Agent] Failed to get session, using fallback: {e}")
                    session = None

            # Determine access mode
            access_mode = "restricted" if self.read_only else "unrestricted"

            # Create fresh MCP server for this query
            # This avoids stale connection issues on Windows
            mcp_server = MCPServerStdio(
                name=f"postgres-mcp-query-{datetime.now().strftime('%H%M%S%f')}",
                params={
                    "command": "postgres-mcp",
                    "args": [self.database_uri, f"--access-mode={access_mode}"],
                },
                cache_tools_list=True,
                client_session_timeout_seconds=120.0,  # 2 minutes for query execution
            )

            # Start MCP server
            logger.info(f"[Schema Agent] Starting postgres-mcp for query...")
            await mcp_server.__aenter__()

            # Get tools (for logging)
            tools = await mcp_server.list_tools()
            tool_names = [t.name for t in tools]
            logger.info(f"[Schema Agent] MCP connected with tools: {tool_names}")

            # Generate system prompt with schema context
            system_prompt = generate_schema_agent_prompt(self.schema_metadata)

            # Prepare function tools list (Gmail tools if enabled)
            function_tools = []
            if self.enable_gmail and self.user_id:
                try:
                    from app.mcp_server.tools_gmail import GMAIL_TOOLS
                    function_tools = GMAIL_TOOLS
                    self._function_tools = ["send_email", "check_email_status"]
                    logger.info(f"[Schema Agent] Gmail tools enabled for user {self.user_id}")
                except ImportError as e:
                    logger.warning(f"[Schema Agent] Gmail tools not available: {e}")

            # Create agent with fresh MCP server and function tools
            agent = Agent(
                name="Schema Query Agent",
                instructions=system_prompt,
                model=get_llm_model(),
                mcp_servers=[mcp_server],
                tools=function_tools if function_tools else None,
                model_settings=ModelSettings(tool_choice="auto"),
            )

            # Build context for tools (needed for Gmail to access user_id)
            run_context = {"user_id": self.user_id} if self.user_id else {}

            # Log final query being sent to agent
            logger.info(f"[Schema Agent] Sending query to agent: {natural_query[:150]}...")
            logger.info(f"[Schema Agent] Function tools available: {[t.name if hasattr(t, 'name') else str(t) for t in function_tools]}")
            logger.info(f"[Schema Agent] Session persistence: {'PostgreSQL' if session else 'In-memory'}")

            # Run the agent with session for persistent conversation history
            result = await Runner.run(
                agent,
                input=natural_query,
                max_turns=10,  # Limit iterations
                context=run_context,
                session=session,  # Use PostgreSQL-backed session for conversation memory
            )

            # Log detailed result info
            logger.info(f"[Schema Agent] Run completed. Checking tool calls...")
            if hasattr(result, 'new_items'):
                for item in result.new_items:
                    item_type = type(item).__name__
                    logger.info(f"[Schema Agent] Result item: {item_type}")
                    if hasattr(item, 'raw_item'):
                        logger.info(f"[Schema Agent] Raw item: {item.raw_item}")

            # Extract response
            response_text = str(result.final_output) if result.final_output else ""
            logger.info(f"[Schema Agent] Final output (first 200 chars): {response_text[:200]}...")

            # Also add to in-memory history as fallback
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

            logger.info(f"[Schema Agent] Query completed successfully (session: {'persistent' if session else 'memory'})")

            return {
                "success": True,
                "response": response_text,
                "visualization_hint": visualization_hint,
                "session_type": "postgresql" if session else "memory",
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[Schema Agent] Query failed: {e}", exc_info=True)

            # Provide better error messages
            if "ClosedResourceError" in error_msg or "Connection closed" in error_msg:
                return {
                    "success": False,
                    "error": "Database connection was interrupted. Please try again.",
                    "response": "The database connection was interrupted. Please try your query again."
                }

            return {
                "success": False,
                "error": error_msg,
                "response": f"I encountered an error processing your request: {error_msg}"
            }
        finally:
            # Always clean up MCP server
            if mcp_server:
                try:
                    await mcp_server.__aexit__(None, None, None)
                    logger.info(f"[Schema Agent] MCP server closed")
                except Exception as e:
                    logger.warning(f"[Schema Agent] Error closing MCP server: {e}")

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
        Close the agent and reset state.

        Note: MCP connections are created per-query and cleaned up automatically.
        This method resets the agent state and clears session manager.
        """
        logger.info(f"[Schema Agent] Closing agent for session {self._session_id}")
        self._is_initialized = False
        self._mcp_tools = []
        self._conversation_history = []

        # Clear session manager
        if self._session_manager:
            await self._session_manager.clear_session()
            self._session_manager = None

    def clear_history(self) -> None:
        """Clear conversation history (in-memory only)."""
        self._conversation_history = []

    async def clear_persistent_history(self) -> None:
        """Clear PostgreSQL-backed conversation history."""
        if self._session_manager:
            await self._session_manager.clear_session()
        self._conversation_history = []
        logger.info(f"[Schema Agent] Cleared persistent history for user {self.user_id}")

    def get_history(self) -> List[Dict[str, str]]:
        """Get in-memory conversation history."""
        return self._conversation_history.copy()

    async def get_persistent_history(self, limit: int = 50) -> list:
        """Get PostgreSQL-backed conversation history."""
        if self._session_manager:
            return await self._session_manager.get_history(limit)
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
    user_id: Optional[int] = None,
    enable_gmail: bool = True,
    thread_id: Optional[str] = None,
) -> SchemaQueryAgent:
    """
    Factory function to create and initialize a Schema Query Agent.

    Args:
        database_uri: PostgreSQL connection string
        schema_metadata: Discovered schema metadata
        auto_initialize: Whether to initialize immediately
        read_only: Whether to use read-only mode
        user_id: User ID for tool context (needed for Gmail integration)
        enable_gmail: Whether to enable Gmail tools (default: True)
        thread_id: Thread ID for ChatKit session (for persistent conversation)

    Returns:
        Initialized SchemaQueryAgent instance with PostgreSQL session support
    """
    agent = SchemaQueryAgent(
        database_uri=database_uri,
        schema_metadata=schema_metadata,
        read_only=read_only,
        user_id=user_id,
        enable_gmail=enable_gmail,
        thread_id=thread_id,
    )

    if auto_initialize:
        result = await agent.initialize()
        if not result.get("success"):
            raise RuntimeError(f"Failed to initialize agent: {result.get('error')}")

    return agent
