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
from typing import Optional, Dict, Any, List, AsyncIterator
from datetime import datetime

from agents import Agent, Runner, ItemHelpers
from agents.run import RunConfig
from agents.mcp import MCPServerStdio
from agents.extensions.models.litellm_model import LitellmModel
from agents.extensions.memory import SQLAlchemySession
from agents.model_settings import ModelSettings

from app.services.schema_discovery import format_schema_for_prompt
from app.services.agent_session_service import create_user_session, AgentSessionManager

logger = logging.getLogger(__name__)

# Version marker for debugging
SCHEMA_AGENT_VERSION = "2.4.0-gmail-connector-subagent"
logger.info(f"[Schema Agent] Module loaded - Version {SCHEMA_AGENT_VERSION} (MCP + User Connectors + Gmail as Sub-Agent)")


# ============================================================================
# Configuration
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Use Gemini 2.0 Flash which supports function calling well
# gemini-2.0-flash-exp has better tool calling than lite version
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
URGENT: CHECK FOR MESSAGE PREFIX FIRST
############################################
BEFORE doing anything else, check if the user's message starts with a prefix:

1. [FILE:uuid] - User has attached a file for analysis
   If YES: Extract the file_id from the prefix (e.g., [FILE:abc-123-def] → file_id="abc-123-def")

   **For PDF files:** Call `pdf_read_text(file_id)` to read the ENTIRE document first
   **For CSV/Excel:** Call `data_read(file_id)` to see columns and data
   **For Images:** Call `image_get_info(file_id)` for dimensions

   IMPORTANT: For PDFs, ALWAYS read the full document with pdf_read_text - NEVER ask for page numbers!

2. [TOOL:GMAIL] - User wants to send results via email
   If YES: You MUST call the gmail_connector tool after getting query results. This is NON-NEGOTIABLE.

3. [TOOL:GOOGLE_SEARCH] - User wants to search the web
   If YES: You MUST call the google_search tool. This is NON-NEGOTIABLE.
   The response MUST include Sources section with clickable links.

Failure to use the selected tool is a critical error.

############################################
CORE MISSION
############################################
Answer the user's data questions fully and helpfully with concrete results they can trust. Never invent data. Default to detailed and useful. Go one step further: after answering, add high-value insights supporting the user's underlying goal.

############################################
AUTONOMOUS DECISION MAKING (CRITICAL)
############################################
You are an INTELLIGENT ASSISTANT. Understand user intent and execute autonomously.

<autonomous_behavior>
RULE 1: UNDERSTAND USER INTENT FROM CONTEXT
- Analyze what the user is asking for based on their query
- Infer the domain (medical, ecommerce, education, finance, etc.) from their data/query
- Make intelligent decisions based on the context - don't need explicit instructions

RULE 2: SMART DEFAULTS (CONTEXT-AWARE)
- Title/Name: Generate based on content type and current date
- Format: Professional structure appropriate to the content
- Location: Use sensible defaults (workspace root for new content)
- Date: Use current date/time when relevant

RULE 3: EXECUTE, DON'T ASK
NEVER ask about things you can decide:
❌ "What should I name this?" → Generate appropriate name from content
❌ "Where should I save it?" → Use default location
❌ "What format do you want?" → Use professional format
❌ "Should I include analysis?" → Include relevant insights

ONLY ask when genuinely ambiguous:
✓ Multiple tables with similar names - which one?
✓ Ambiguous date range with multiple years of data
✓ Conflicting instructions that need clarification

RULE 4: COMPLETE MULTI-STEP REQUESTS
When user gives a compound request:
1. Break it down into required steps
2. Execute ALL steps in sequence
3. Use appropriate tools for each step
4. Report complete results

Example patterns (adapt to user's domain):
- "Show me X and save to Notion" → Query data, analyze, save, confirm
- "Analyze Y and email results" → Query, analyze, format email, send
- "Check Z status" → Query relevant data, provide insights

RULE 5: DELIVER COMPLETE RESULTS
- Show full results in chat
- Confirm any external actions (saved to Notion, email sent, etc.)
- Include relevant insights based on the data
</autonomous_behavior>

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
- `google_search`: Search the web for real-time information, documentation, news, and current events

**PDF Document Tools:**
- `pdf_read_text`: Read ENTIRE PDF content (all pages, all text, all tables)
- `pdf_search_text`: Search for specific text in PDF with page locations
- `pdf_get_info`: Get PDF metadata (page count, author, title)

**Data File Tools (CSV/Excel):**
- `data_read`: Read data file with columns, statistics, and sample rows
- `data_filter`: Filter data by column conditions (equals, contains, greater_than, etc.)
- `data_aggregate`: Calculate aggregations (sum, avg, count, min, max)

**Image Tools:**
- `image_get_info`: Get image dimensions, format, and metadata

**General:**
- `get_uploaded_file_info`: Check file status and type before processing

############################################
FILE UPLOAD ANALYSIS (CRITICAL - READ CAREFULLY)
############################################
When a message contains [FILE:uuid] or user mentions an uploaded file:

<pdf_file_rules>
**FOR PDF FILES - ALWAYS DO THIS:**
1. FIRST: Call `pdf_read_text(file_id)` to read the ENTIRE document
   - This extracts ALL text from ALL pages automatically
   - You do NOT need to specify page numbers - it reads everything
   - NEVER ask user for page numbers - just read the whole document

2. THEN: Answer the user's question from the extracted text
   - The text contains everything in the PDF
   - Search through it to find what user is asking about

3. IF user asks to find specific text: Use `pdf_search_text(file_id, "search term")`
   - This searches the ENTIRE PDF and returns all matches with page locations

**CRITICAL PDF RULES:**
- NEVER ask "What page is this on?" - YOU read the document and find it
- NEVER say "Could you specify the page?" - YOU search through all pages
- ALWAYS call pdf_read_text FIRST before answering any PDF question
- The pdf_read_text tool gives you the COMPLETE document text
</pdf_file_rules>

<csv_excel_rules>
**FOR CSV/EXCEL FILES:**
1. Call `data_read(file_id)` to see columns, statistics, and sample data
2. Use `data_filter(file_id, column, operator, value)` to find specific rows
3. Use `data_aggregate(file_id, column, operation)` for calculations
</csv_excel_rules>

<image_rules>
**FOR IMAGE FILES:**
1. Call `image_get_info(file_id)` to get dimensions and format
</image_rules>

<file_analysis_patterns>
PATTERN: User uploads PDF and asks a question
→ Call pdf_read_text(file_id) to get ALL document text
→ Analyze the text to find the answer
→ Provide complete answer with relevant quotes/data

PATTERN: User asks to find something in PDF
→ Call pdf_search_text(file_id, "search term") to find all occurrences
→ Show matches with page numbers and context

PATTERN: User uploads CSV/Excel
→ Call data_read(file_id) to understand structure
→ Use data_filter or data_aggregate as needed
→ Provide insights with statistics

PATTERN: Compare file with database
→ Read file content first (appropriate tool for type)
→ Query relevant database tables
→ Compare and provide insights
</file_analysis_patterns>

############################################
CONNECTOR SUB-AGENTS (EXTERNAL INTEGRATIONS)
############################################
You have access to connector sub-agents for external services. Each connector (Notion, Slack, etc.)
is available as a SINGLE TOOL that handles all operations for that service.

<connector_tool_rules>
1. Connector tools are loaded dynamically based on user's connected services
2. Each connector is a SPECIALIZED AGENT - just describe what you want to do
3. The connector agent will handle all the internal API calls and workflows
4. DO NOT worry about API details - the sub-agent is an EXPERT
5. For complex tasks: describe the FULL task in one message to the connector
</connector_tool_rules>

############################################
NOTION CONNECTOR (notion_connector tool)
############################################
If Notion is connected, you have the `notion_connector` tool - a specialized agent for Notion operations.

<how_to_use_notion_connector>
The Notion connector understands:
- Notion terminology (Database = Table, Page = Row, Property = Column)
- All Notion API operations (search, create, update, query)
- Multi-step workflows automatically

For DOCUMENTS/REPORTS:
- Create a PAGE with formatted content
- Use headers, bullets, tables as needed

For STRUCTURED DATA:
- Create a DATABASE with appropriate columns
- Add items as rows

Simply describe your goal - the connector handles the API details.
</how_to_use_notion_connector>

<notion_usage_patterns>
USAGE PATTERNS (adapt to user's context):

PATTERN 1: Save content to Notion
→ Call notion_connector describing what to save and the content

PATTERN 2: Analyze and save
→ First: Query and analyze the user's data
→ Then: Format results appropriately
→ Finally: Call notion_connector to save

PATTERN 3: Track items
→ Call notion_connector to create database with relevant columns
→ Add items as needed

Generate names based on content and current date - be contextually appropriate.
</notion_usage_patterns>

<notion_report_template>
STANDARD REPORT STRUCTURE (adapt sections based on content):

# [Title based on content]
**Generated:** [Current Date]
**Period:** [If applicable]

## Summary
[Key findings relevant to the data]

## Data
[Tables, metrics, or content as appropriate]

## Analysis & Insights
[Observations and recommendations relevant to the context]

---
*Generated by AI Assistant*
</notion_report_template>

<tool_usage_rules>
- Prefer tools for all data queries - never guess or fabricate results
- Parallelize independent reads to reduce latency
- After executing queries, present:
  * What was found (data first!)
  * Key insights or patterns
  * Relevant context or implications
- Use gmail_connector when user explicitly asks to email/send results
- If email fails due to Gmail not connected, inform user to connect Gmail via Connectors
</tool_usage_rules>

############################################
GMAIL CONNECTOR ACTIVATION (IMPORTANT)
############################################
<gmail_connector_rules>
When message starts with [TOOL:GMAIL], the user has selected the Gmail connector:
1. Execute the query to get the requested data
2. ALWAYS call gmail_connector tool with the results - this is MANDATORY
3. The gmail_connector sub-agent handles all email operations:
   - Sending emails (gmail_send)
   - Checking status (gmail_status)
   - Reading inbox (gmail_read_inbox)
   - Searching emails (gmail_search)
4. Format email body PROFESSIONALLY with:
   - Greeting: "Hello,"
   - Brief description of the data
   - Data formatted in clean, readable tables
   - Summary/insights section
   - Sign-off: "Best regards,\nAI Data Assistant"
5. Use descriptive email subject based on the query

CRITICAL: When [TOOL:GMAIL] is present, sending email is NOT optional - always send via gmail_connector!
</gmail_connector_rules>

############################################
GOOGLE SEARCH TOOL (WEB GROUNDING)
############################################
<google_search_rules>
You have access to Google Search for real-time web information.

WHEN TO USE GOOGLE SEARCH (MANDATORY):
1. Message starts with [TOOL:GOOGLE_SEARCH] - ALWAYS use google_search tool
2. User explicitly asks to "search the web" or "Google this"

WHEN TO AUTONOMOUSLY USE GOOGLE SEARCH:
The agent MAY decide to use google_search without user selecting the tool for:
- Current events, news, or today's information
- Latest versions, updates, or recent releases of software/libraries
- External documentation, tutorials, or how-to guides
- Weather, stocks, or real-time data
- Information about topics NOT in the database

WHEN NOT TO USE GOOGLE SEARCH:
- Query is about user's database inventory or sales data
- Query asks about counts, totals, or aggregations from database
- Query can be answered using execute_sql or other database tools
- Query is about internal business data stored in the database

RESPONSE FORMAT WITH SOURCES:
When using google_search, ALWAYS include sources at the end:

[Your response with information from web search]

Sources:
- [Source Title 1](https://example.com/1)
- [Source Title 2](https://example.com/2)
- [Source Title 3](https://example.com/3)

CRITICAL: When [TOOL:GOOGLE_SEARCH] prefix is present, using google_search is MANDATORY!
</google_search_rules>

############################################
MULTI-TASK EXECUTION (CRITICAL)
############################################
<multi_task_spec>
When user gives MULTIPLE tasks in ONE message, you MUST:
1. IDENTIFY all tasks in the request
2. PLAN the execution order (dependencies first)
3. EXECUTE ALL tasks in sequence WITHOUT stopping to ask
4. REPORT results of ALL tasks in a single response

EXECUTION PATTERN:
User: "[Query request] and [Action request]"
→ Step 1: Execute query using appropriate database tools
→ Step 2: Process/analyze the results
→ Step 3: Perform requested action (save, email, etc.)
→ Step 4: Report complete results + confirm action

NEVER:
- Stop after first task and ask "what next?"
- Say "I've done step 1, should I continue?"
- Ask for confirmation between steps
- Ask unnecessary clarifying questions
- Leave tasks incomplete

ALWAYS:
- Complete the ENTIRE request in one go
- Make intelligent decisions based on context
- Chain tools as needed
- Handle errors gracefully and continue with remaining tasks
- Deliver results AND confirm any external actions
</multi_task_spec>

############################################
EXECUTION BEHAVIOR (NON-NEGOTIABLE)
############################################
<execution_spec>
- IMMEDIATELY execute queries when user asks a question
- DO NOT ask for confirmation before running queries
- DO NOT show SQL and wait for approval
- DO NOT say "I will execute..." - just execute and show results
- The user asked, so they want the answer - deliver it directly
- READ-ONLY mode for database: Only SELECT queries are allowed
- READ-WRITE mode for connectors: Use connector tools to create/update/delete
- Complete ALL tasks in the request - never stop halfway
</execution_spec>

############################################
CRITICAL: ALWAYS USE TOOLS (MANDATORY)
############################################
<tool_mandate>
YOU MUST USE TOOLS FOR EVERY TASK. NEVER PRETEND TO DO SOMETHING WITHOUT CALLING A TOOL.

WRONG (DO NOT DO THIS):
- "I have saved your data to Notion" (without calling any tool)
- "I created a page for you" (without v1/pages-create tool call)
- "The report is now in Notion" (without actual tool execution)

CORRECT (ALWAYS DO THIS):
- Call v1/search-search to find pages/databases
- Call v1/pages-create to create a page
- Call v1/databases-create to create a table
- Call execute_sql to query the database
- THEN report what you actually did with tool results

IF A TOOL CALL FAILS:
- Report the actual error from the tool
- Suggest how to fix it
- DO NOT pretend the operation succeeded

REMEMBER: Every action requires a tool call. No exceptions.
</tool_mandate>

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
HANDLING AMBIGUITY (SMART DEFAULTS)
############################################
<uncertainty_and_ambiguity>
PRINCIPLE: Make smart decisions, don't ask dumb questions.

WHEN TO JUST DECIDE (don't ask):
- Page/report name → Use smart naming convention
- Save location → Create new page in workspace
- Report format → Use professional template
- Date range → Default to current month/quarter
- Which columns to show → Include all relevant ones
- Include insights? → ALWAYS yes

WHEN TO BRIEFLY CLARIFY (ask only if critical):
- Multiple tables with similar names and unclear which one
- Genuinely ambiguous date context (multiple years of similar data)
- User's request could mean two completely different things

HOW TO CLARIFY (if you must):
- Ask ONE specific question, not multiple
- Provide the options clearly
- Example: "I found 'sales_2023' and 'sales_2024' tables. Which one? (or 'both' for comparison)"

DEFAULT BEHAVIOR:
- Assume the most common/useful interpretation
- Execute on that assumption
- If wrong, user will correct - that's faster than asking upfront
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
        thread_id: Optional[str] = None,
        connector_tools: Optional[List[Any]] = None,
    ):
        """
        Initialize Schema Query Agent.

        Args:
            database_uri: PostgreSQL connection string for user's database
            schema_metadata: Discovered schema metadata dict
            read_only: Whether to use read-only mode (default: True)
            user_id: User ID for tool context
            thread_id: Thread ID for ChatKit session (for persistent conversation)
            connector_tools: Optional list of tools from user's MCP connectors (Gmail, Notion, GDrive, etc.)
        """
        self.database_uri = database_uri
        self.schema_metadata = schema_metadata
        self.read_only = read_only
        self.user_id = user_id
        self.thread_id = thread_id
        self.connector_tools = connector_tools or []

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
        self._connector_tool_names: List[str] = []
        self._is_initialized = False

        # Initialize session manager if user_id is provided
        if user_id:
            self._session_manager = AgentSessionManager(user_id)

        # Track connector tool names
        if connector_tools:
            self._connector_tool_names = [
                getattr(t, 'name', str(t)) for t in connector_tools
            ]

        logger.info(
            f"[Schema Agent] Created agent instance "
            f"(read_only={read_only}, user_id={user_id}, "
            f"thread={thread_id}, connectors={len(self.connector_tools)}, session={self._session_id})"
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
        natural_query: str | List[Dict[str, Any]],
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a natural language query using the MCP-connected agent.

        Creates a fresh MCP connection for each query to avoid stale connection issues.
        Uses PostgreSQL-backed session for persistent conversation history.

        Args:
            natural_query: User's question - can be:
                - A simple string for text-only queries
                - A list of input items for multi-modal queries (images, files)
            thread_id: Optional thread ID for ChatKit (for persistent conversation)

        Returns:
            dict with response, and optional visualization hint
        """
        mcp_server = None

        try:
            # Log query info
            if isinstance(natural_query, str):
                query_preview = natural_query[:50]
            else:
                query_preview = "[Multi-modal input]"

            logger.info(f"[Schema Agent] Processing query: {query_preview}...")

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
                client_session_timeout_seconds=300.0,  # 5 minutes for complex multi-step operations
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

            # Add connector tools info to system prompt if available
            if self.connector_tools and self._connector_tool_names:
                connector_tools_section = f"""

############################################
CONNECTED EXTERNAL SERVICES (MCP CONNECTORS)
############################################
You have access to the following connector tools from external services:

AVAILABLE CONNECTOR TOOLS:
{chr(10).join(f'- `{name}`: Use for operations with the connected service' for name in self._connector_tool_names)}

IMPORTANT CONNECTOR TOOL RULES:
1. Use the EXACT tool names listed above (e.g., `notion-create-database`, NOT `create_database`)
2. These tools connect to the user's external accounts (Notion, etc.)
3. When user asks to create, update, or fetch data from external services, use these tools
4. Chain tools if needed (e.g., search first, then create)
5. For Notion specifically:
   - `notion-search`: Search pages and databases
   - `notion-create-pages`: Create new pages
   - `notion-create-database`: Create new databases
   - `notion-update-page`: Update existing pages
   - `notion-fetch`: Fetch page content
"""
                system_prompt = system_prompt + connector_tools_section
                logger.info(f"[Schema Agent] Added {len(self._connector_tool_names)} connector tools to system prompt")

            # Prepare function tools list
            function_tools = []

            # Add Google Search tool (always available as System Tool)
            try:
                from app.mcp_server.tools_google_search import GOOGLE_SEARCH_TOOLS
                function_tools.extend(GOOGLE_SEARCH_TOOLS)
                self._function_tools.append("google_search") if hasattr(self, '_function_tools') else None
                logger.info(f"[Schema Agent] Google Search tool enabled")
            except ImportError as e:
                logger.warning(f"[Schema Agent] Google Search tool not available: {e}")

            # Add File Analysis tools (Feature 012 - File Upload Processing)
            try:
                from app.mcp_server.tools_file_analysis import FILE_ANALYSIS_TOOLS, set_file_analysis_context
                function_tools.extend(FILE_ANALYSIS_TOOLS)
                self._function_tools.append("analyze_uploaded_file") if hasattr(self, '_function_tools') else None
                self._function_tools.append("get_uploaded_file_info") if hasattr(self, '_function_tools') else None
                logger.info(f"[Schema Agent] File Analysis tools enabled")
            except ImportError as e:
                logger.warning(f"[Schema Agent] File Analysis tools not available: {e}")

            # Add connector tools if available
            if self.connector_tools:
                function_tools.extend(self.connector_tools)
                logger.info(f"[Schema Agent] ═══════════════════════════════════════")
                logger.info(f"[Schema Agent] CONNECTOR TOOLS ADDED: {len(self.connector_tools)}")
                for i, tool in enumerate(self.connector_tools):
                    tool_name = getattr(tool, 'name', str(tool))
                    tool_desc = getattr(tool, 'description', 'No description')[:100]
                    logger.info(f"[Schema Agent]   {i+1}. {tool_name}: {tool_desc}")
                logger.info(f"[Schema Agent] ═══════════════════════════════════════")

            # Create agent with fresh MCP server and function tools
            # Use "auto" for tool_choice - works with both OpenAI and Gemini
            logger.info(f"[Schema Agent] Tool choice setting: auto")
            logger.info(f"[Schema Agent] Total function tools: {len(function_tools)}")

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

            # If using session memory + list inputs (multi-modal), Agents SDK requires a session_input_callback
            # so it knows how to merge the new list with stored conversation history.
            is_multimodal_input = isinstance(natural_query, list)
            # Multimodal inputs can be very large (base64 images). Disable tracing to avoid 5MB trace payload errors.
            run_config = RunConfig(tracing_disabled=True, trace_include_sensitive_data=False) if is_multimodal_input else None
            if session and is_multimodal_input:
                async def _merge_session_inputs(history_items: list, new_items: list):
                    return history_items + new_items
                run_config = RunConfig(
                    session_input_callback=_merge_session_inputs,
                    tracing_disabled=True,
                    trace_include_sensitive_data=False,
                )
                logger.info("[Schema Agent] Multi-modal input detected - using session_input_callback for session memory")

            # Run the agent with session for persistent conversation history
            # Increased max_turns to 25 for complex multi-step operations (Notion workflows)
            logger.info(f"[Schema Agent] ═══════════════════════════════════════")
            logger.info(f"[Schema Agent] STARTING AGENT RUN")
            logger.info(f"[Schema Agent] Query: {natural_query}")
            logger.info(f"[Schema Agent] Tools count: {len(function_tools)}")
            logger.info(f"[Schema Agent] Max turns: 25")
            logger.info(f"[Schema Agent] Session: {'enabled' if session else 'disabled'} (multimodal={is_multimodal_input})")
            logger.info(f"[Schema Agent] ═══════════════════════════════════════")

            result = await Runner.run(
                agent,
                input=natural_query,
                max_turns=25,  # Allow more iterations for complex multi-tool workflows
                context=run_context,
                run_config=run_config,
                session=session,  # Use PostgreSQL-backed session for conversation memory
            )

            # Log detailed result info
            logger.info(f"[Schema Agent] ═══════════════════════════════════════")
            logger.info(f"[Schema Agent] Run completed. Analyzing result...")
            logger.info(f"[Schema Agent] Result type: {type(result).__name__}")

            if hasattr(result, 'new_items'):
                logger.info(f"[Schema Agent] New items count: {len(result.new_items)}")
                for idx, item in enumerate(result.new_items):
                    item_type = getattr(item, 'type', type(item).__name__)
                    logger.info(f"[Schema Agent] Item {idx}: {item_type}")
                    if hasattr(item, 'raw_item'):
                        raw_str = str(item.raw_item)[:300]
                        logger.info(f"[Schema Agent] Raw item {idx}: {raw_str}...")

            # Extract response with comprehensive fallback handling
            response_text = ""

            # Method 1: Try final_output first (works for most cases)
            if result.final_output:
                response_text = str(result.final_output)
                logger.info(f"[Schema Agent] Got response from final_output: {len(response_text)} chars")

            # Method 2: Use ItemHelpers for message_output_item extraction
            if not response_text and hasattr(result, 'new_items'):
                for item in reversed(result.new_items):  # Check from latest to earliest
                    item_type = getattr(item, 'type', '')

                    # Use ItemHelpers for message_output_item (recommended approach)
                    if item_type == 'message_output_item':
                        extracted = ItemHelpers.text_message_output(item)
                        if extracted:
                            response_text = extracted
                            logger.info(f"[Schema Agent] Got response from ItemHelpers.text_message_output: {len(response_text)} chars")
                            break

                    # Fallback: Try direct content/text attributes
                    if hasattr(item, 'content') and item.content:
                        response_text = str(item.content)
                        logger.info(f"[Schema Agent] Got response from new_items.content: {len(response_text)} chars")
                        break
                    elif hasattr(item, 'text') and item.text:
                        response_text = str(item.text)
                        logger.info(f"[Schema Agent] Got response from new_items.text: {len(response_text)} chars")
                        break

            # Method 3: Deep extraction from raw_item for Gemini/LiteLLM responses
            if not response_text and hasattr(result, 'new_items'):
                for item in reversed(result.new_items):
                    if hasattr(item, 'raw_item'):
                        raw = item.raw_item

                        # Handle dict format
                        if isinstance(raw, dict):
                            # Check for 'content' list (OpenAI format)
                            if 'content' in raw:
                                contents = raw.get('content', [])
                                if isinstance(contents, list):
                                    for c in contents:
                                        if isinstance(c, dict) and c.get('type') == 'text':
                                            response_text = c.get('text', '')
                                            if response_text:
                                                logger.info(f"[Schema Agent] Got response from raw_item.content[].text: {len(response_text)} chars")
                                                break
                                elif isinstance(contents, str) and contents:
                                    response_text = contents
                                    logger.info(f"[Schema Agent] Got response from raw_item.content (str): {len(response_text)} chars")
                            # Check for direct 'text' field
                            elif 'text' in raw and raw['text']:
                                response_text = str(raw['text'])
                                logger.info(f"[Schema Agent] Got response from raw_item.text: {len(response_text)} chars")
                            # Check for 'message' field (some providers)
                            elif 'message' in raw and raw['message']:
                                msg = raw['message']
                                if isinstance(msg, dict) and 'content' in msg:
                                    response_text = str(msg['content'])
                                else:
                                    response_text = str(msg)
                                logger.info(f"[Schema Agent] Got response from raw_item.message: {len(response_text)} chars")

                        # Handle object with attributes
                        elif hasattr(raw, 'content'):
                            content = raw.content
                            if isinstance(content, list):
                                for c in content:
                                    if hasattr(c, 'text') and c.text:
                                        response_text = c.text
                                        logger.info(f"[Schema Agent] Got response from raw_item.content[].text (obj): {len(response_text)} chars")
                                        break
                            elif isinstance(content, str) and content:
                                response_text = content
                                logger.info(f"[Schema Agent] Got response from raw_item.content (obj str): {len(response_text)} chars")
                        elif hasattr(raw, 'text') and raw.text:
                            response_text = raw.text
                            logger.info(f"[Schema Agent] Got response from raw_item.text (obj): {len(response_text)} chars")

                    if response_text:
                        break

            # If still empty, log detailed debug info and provide error message
            if not response_text:
                logger.error(f"[Schema Agent] CRITICAL: No response text found!")
                logger.error(f"[Schema Agent] Result final_output: {result.final_output}")
                if hasattr(result, 'new_items'):
                    for idx, item in enumerate(result.new_items):
                        logger.error(f"[Schema Agent] DEBUG Item {idx}: type={getattr(item, 'type', 'unknown')}, attrs={[a for a in dir(item) if not a.startswith('_')]}")
                        if hasattr(item, 'raw_item'):
                            logger.error(f"[Schema Agent] DEBUG Raw {idx}: {item.raw_item}")
                response_text = "I'm sorry, I couldn't generate a proper response. Please try rephrasing your question or check the database connection."

            logger.info(f"[Schema Agent] Final output (first 300 chars): {response_text[:300]}...")
            logger.info(f"[Schema Agent] ═══════════════════════════════════════")

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

    async def query_streamed(
        self,
        natural_query: str | List[Dict[str, Any]],
        thread_id: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process a natural language query with streaming progress updates.

        Yields progress events for each step (tool calls, outputs, thoughts, etc.)
        for real-time UI feedback in ChatKit.

        Args:
            natural_query: User's question - can be:
                - A simple string for text-only queries
                - A list of input items for multi-modal queries (images, files)
                  Format: [{"role": "user", "content": [{"type": "input_text", "text": "..."}, {"type": "input_image", "image_url": "data:..."}]}]
            thread_id: Optional thread ID for ChatKit

        Yields:
            Dict with type and details for each streaming event
        """
        mcp_server = None

        try:
            # Log query info
            if isinstance(natural_query, str):
                query_preview = natural_query[:50]
                is_multimodal = False
            else:
                # Multi-modal input - extract text preview
                query_preview = "[Multi-modal input]"
                is_multimodal = True
                for item in natural_query:
                    if isinstance(item, dict) and item.get("content"):
                        for content in item["content"]:
                            if isinstance(content, dict) and content.get("type") == "input_text":
                                query_preview = content.get("text", "")[:50]
                                break

            logger.info(f"[Schema Agent] Processing streamed query: {query_preview}... (multimodal={is_multimodal})")

            yield {"type": "progress", "text": "Analyzing your question..."}

            effective_thread_id = thread_id or self.thread_id

            # Get session
            session = None
            if self._session_manager:
                try:
                    session = self._session_manager.get_session(effective_thread_id)
                    logger.info(f"[Schema Agent] Using PostgreSQL session")
                except Exception as e:
                    logger.warning(f"[Schema Agent] Session fallback: {e}")

            access_mode = "restricted" if self.read_only else "unrestricted"

            yield {"type": "progress", "text": "Connecting to database..."}

            # Create fresh MCP server
            mcp_server = MCPServerStdio(
                name=f"postgres-mcp-stream-{datetime.now().strftime('%H%M%S%f')}",
                params={
                    "command": "postgres-mcp",
                    "args": [self.database_uri, f"--access-mode={access_mode}"],
                },
                cache_tools_list=True,
                client_session_timeout_seconds=300.0,
            )

            await mcp_server.__aenter__()

            tools = await mcp_server.list_tools()
            tool_names = [t.name for t in tools]
            logger.info(f"[Schema Agent] MCP connected with tools: {tool_names}")

            yield {"type": "progress", "text": f"Database connected. {len(tool_names)} tools available."}

            # Generate system prompt
            system_prompt = generate_schema_agent_prompt(self.schema_metadata)

            # Add connector tools info
            if self.connector_tools and self._connector_tool_names:
                connector_tools_section = f"""

############################################
CONNECTED EXTERNAL SERVICES (MCP CONNECTORS)
############################################
AVAILABLE CONNECTOR TOOLS:
{chr(10).join(f'- `{name}`' for name in self._connector_tool_names)}
"""
                system_prompt = system_prompt + connector_tools_section

            # Prepare function tools
            function_tools = []

            # Add Google Search tool
            try:
                from app.mcp_server.tools_google_search import GOOGLE_SEARCH_TOOLS
                function_tools.extend(GOOGLE_SEARCH_TOOLS)
            except ImportError:
                pass

            # Add File Analysis tools (Feature 012)
            try:
                from app.mcp_server.tools_file_analysis import FILE_ANALYSIS_TOOLS
                function_tools.extend(FILE_ANALYSIS_TOOLS)
                logger.info(f"[Schema Agent Stream] File Analysis tools enabled")
            except ImportError:
                pass

            if self.connector_tools:
                function_tools.extend(self.connector_tools)
                yield {"type": "progress", "text": f"Loaded {len(self.connector_tools)} connector tools."}

            yield {"type": "progress", "text": "Initializing AI agent..."}

            # Create agent
            agent = Agent(
                name="Schema Query Agent",
                instructions=system_prompt,
                model=get_llm_model(),
                mcp_servers=[mcp_server],
                tools=function_tools if function_tools else None,
                model_settings=ModelSettings(tool_choice="auto"),
            )

            run_context = {"user_id": self.user_id} if self.user_id else {}

            yield {"type": "progress", "text": "Processing your query..."}

            # If using session memory + list inputs (multi-modal), Agents SDK requires a session_input_callback
            # so it knows how to merge the new list with stored conversation history.
            is_multimodal_input = isinstance(natural_query, list)
            # Multimodal inputs can be very large (base64 images). Disable tracing to avoid 5MB trace payload errors.
            run_config = RunConfig(tracing_disabled=True, trace_include_sensitive_data=False) if is_multimodal_input else None
            if session and is_multimodal_input:
                async def _merge_session_inputs(history_items: list, new_items: list):
                    return history_items + new_items
                run_config = RunConfig(
                    session_input_callback=_merge_session_inputs,
                    tracing_disabled=True,
                    trace_include_sensitive_data=False,
                )
                logger.info("[Schema Agent Stream] Multi-modal input detected - using session_input_callback for session memory")
            
            # Run with streaming
            result = Runner.run_streamed(
                agent,
                input=natural_query,
                max_turns=25,
                context=run_context,
                run_config=run_config,
                session=session,
            )

            response_text = ""
            tool_calls_made = []

            # Track last tool name for output matching
            last_tool_name = ""

            # Stream events from agent execution
            async for event in result.stream_events():
                event_type = getattr(event, 'type', 'unknown')
                logger.info(f"[Schema Agent Stream] Event type: {event_type}")

                # Handle run_item_stream_event - contains tool calls, outputs, messages
                if event_type == "run_item_stream_event":
                    item = event.item
                    item_type = getattr(item, 'type', 'unknown')

                    # Tool call started
                    if item_type == "tool_call_item":
                        # Try multiple ways to get tool name
                        tool_name = None

                        # Method 1: Direct 'name' attribute
                        if hasattr(item, 'name') and item.name:
                            tool_name = item.name

                        # Method 2: Check raw_item for function call details
                        if not tool_name and hasattr(item, 'raw_item'):
                            raw = item.raw_item
                            if isinstance(raw, dict):
                                # Check for function name in various locations
                                if 'name' in raw:
                                    tool_name = raw['name']
                                elif 'function' in raw and isinstance(raw['function'], dict):
                                    tool_name = raw['function'].get('name')
                                elif 'tool_call' in raw and isinstance(raw['tool_call'], dict):
                                    tool_name = raw['tool_call'].get('name')
                            elif hasattr(raw, 'name'):
                                tool_name = raw.name
                            elif hasattr(raw, 'function') and hasattr(raw.function, 'name'):
                                tool_name = raw.function.name

                        # Method 3: Check call_id pattern for MCP tools
                        if not tool_name and hasattr(item, 'call_id'):
                            call_id = item.call_id
                            if call_id and '_' in str(call_id):
                                # Sometimes call_id contains tool name
                                tool_name = str(call_id).split('_')[0]

                        # Fallback
                        if not tool_name:
                            tool_name = "database_tool"

                        last_tool_name = tool_name
                        tool_calls_made.append(tool_name)

                        # Get arguments
                        tool_args = getattr(item, 'arguments', '')
                        if not tool_args and hasattr(item, 'raw_item'):
                            raw = item.raw_item
                            if isinstance(raw, dict):
                                tool_args = raw.get('arguments', raw.get('input', ''))

                        # Format tool call info
                        args_preview = str(tool_args)[:100] + "..." if len(str(tool_args)) > 100 else str(tool_args)

                        logger.info(f"[Schema Agent Stream] Tool call: {tool_name}, args: {args_preview}")

                        yield {
                            "type": "tool_call",
                            "text": f"Calling tool: {tool_name}",
                            "tool_name": tool_name,
                            "arguments": args_preview,
                        }

                    # Tool call output received
                    elif item_type == "tool_call_output_item":
                        output = getattr(item, 'output', '')
                        output_preview = str(output)[:200] + "..." if len(str(output)) > 200 else str(output)

                        # Use last tool name if available
                        tool_name = last_tool_name or "tool"

                        yield {
                            "type": "tool_output",
                            "text": f"Response from: {tool_name}",
                            "tool_name": tool_name,
                            "output_preview": output_preview,
                        }

                    # Message output (assistant's text response)
                    elif item_type == "message_output_item":
                        # Use ItemHelpers to extract text
                        text = ItemHelpers.text_message_output(item)
                        if text:
                            response_text = text

                    # Reasoning/thinking item
                    elif item_type == "reasoning_item":
                        reasoning = getattr(item, 'content', '')
                        if reasoning:
                            yield {
                                "type": "thinking",
                                "text": f"Agent thinking: {str(reasoning)[:150]}...",
                            }

                # Handle agent updated event
                elif event_type == "agent_updated_stream_event":
                    new_agent = getattr(event, 'new_agent', None)
                    if new_agent:
                        agent_name = getattr(new_agent, 'name', 'Agent')
                        yield {
                            "type": "progress",
                            "text": f"Switched to: {agent_name}",
                        }

                # Handle raw response streaming (for real-time token output)
                elif event_type == "raw_response_event":
                    # Check for text delta events for streaming text
                    data = getattr(event, 'data', None)
                    if data and hasattr(data, 'delta'):
                        delta = data.delta
                        if delta:
                            yield {"type": "content_delta", "text": str(delta)}

            # After streaming completes, extract final response
            # Method 1: Try final_output first
            if not response_text and result.final_output:
                response_text = str(result.final_output)
                logger.info(f"[Schema Agent Stream] Got response from final_output: {len(response_text)} chars")

            # Method 2: Use ItemHelpers for message_output_item extraction
            if not response_text and hasattr(result, 'new_items'):
                for item in reversed(result.new_items):
                    item_type = getattr(item, 'type', '')

                    if item_type == 'message_output_item':
                        extracted = ItemHelpers.text_message_output(item)
                        if extracted:
                            response_text = extracted
                            logger.info(f"[Schema Agent Stream] Got response from ItemHelpers: {len(response_text)} chars")
                            break

                    if hasattr(item, 'content') and item.content:
                        response_text = str(item.content)
                        logger.info(f"[Schema Agent Stream] Got response from content: {len(response_text)} chars")
                        break

            # Method 3: Deep extraction from raw_item
            if not response_text and hasattr(result, 'new_items'):
                for item in reversed(result.new_items):
                    if hasattr(item, 'raw_item'):
                        raw = item.raw_item

                        if isinstance(raw, dict):
                            if 'content' in raw:
                                contents = raw.get('content', [])
                                if isinstance(contents, list):
                                    for c in contents:
                                        if isinstance(c, dict) and c.get('type') == 'text':
                                            response_text = c.get('text', '')
                                            if response_text:
                                                break
                                elif isinstance(contents, str) and contents:
                                    response_text = contents
                            elif 'text' in raw and raw['text']:
                                response_text = str(raw['text'])
                            elif 'message' in raw:
                                msg = raw['message']
                                if isinstance(msg, dict) and 'content' in msg:
                                    response_text = str(msg['content'])
                                elif msg:
                                    response_text = str(msg)

                        elif hasattr(raw, 'content'):
                            content = raw.content
                            if isinstance(content, list):
                                for c in content:
                                    if hasattr(c, 'text') and c.text:
                                        response_text = c.text
                                        break
                            elif isinstance(content, str) and content:
                                response_text = content
                        elif hasattr(raw, 'text') and raw.text:
                            response_text = raw.text

                    if response_text:
                        break

            if not response_text:
                logger.error(f"[Schema Agent Stream] CRITICAL: No response text found!")
                response_text = "I'm sorry, I couldn't generate a proper response. Please try rephrasing your question."

            # Add to history
            self._conversation_history.append({"role": "user", "content": natural_query})
            self._conversation_history.append({"role": "assistant", "content": response_text})

            # Yield final response
            visualization_hint = self._detect_visualization(response_text, natural_query)

            yield {
                "type": "complete",
                "response": response_text,
                "tools_used": tool_calls_made,
                "visualization_hint": visualization_hint,
            }

        except Exception as e:
            logger.error(f"[Schema Agent] Streamed query failed: {e}", exc_info=True)
            yield {
                "type": "error",
                "text": f"Error: {str(e)}",
                "response": f"I encountered an error: {str(e)}",
            }
        finally:
            if mcp_server:
                try:
                    await mcp_server.__aexit__(None, None, None)
                except Exception:
                    pass

    def _detect_visualization(self, response: Any, query: Any) -> Optional[Dict[str, str]]:
        """
        Detect if response data is suitable for visualization.

        Returns visualization hint dict or None.
        """
        # query can be a string OR multi-modal list payload. Normalize to text.
        query_text = ""
        if isinstance(query, str):
            query_text = query
        elif isinstance(query, list):
            # Possible shapes:
            # - ChatKit/Agent multi-modal: [{"role": "user", "content": [{"type":"input_text","text":"..."}, ...]}]
            # - Other list forms; we try best-effort extraction.
            try:
                for msg in query:
                    if isinstance(msg, dict):
                        content = msg.get("content")
                        if isinstance(content, list):
                            for part in content:
                                if isinstance(part, dict) and part.get("type") == "input_text" and part.get("text"):
                                    query_text = str(part["text"])
                                    break
                        if query_text:
                            break
            except Exception:
                query_text = ""

        query_lower = (query_text or "").lower()
        response_lower = (response if isinstance(response, str) else str(response)).lower()

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
    thread_id: Optional[str] = None,
    connector_tools: Optional[List[Any]] = None,
) -> SchemaQueryAgent:
    """
    Factory function to create and initialize a Schema Query Agent.

    Args:
        database_uri: PostgreSQL connection string
        schema_metadata: Discovered schema metadata
        auto_initialize: Whether to initialize immediately
        read_only: Whether to use read-only mode
        user_id: User ID for tool context
        thread_id: Thread ID for ChatKit session (for persistent conversation)
        connector_tools: Optional list of tools from user's MCP connectors (Gmail, Notion, GDrive, etc.)

    Returns:
        Initialized SchemaQueryAgent instance with PostgreSQL session support
    """
    agent = SchemaQueryAgent(
        database_uri=database_uri,
        schema_metadata=schema_metadata,
        read_only=read_only,
        user_id=user_id,
        thread_id=thread_id,
        connector_tools=connector_tools,
    )

    if auto_initialize:
        result = await agent.initialize()
        if not result.get("success"):
            raise RuntimeError(f"Failed to initialize agent: {result.get('error')}")

    return agent
