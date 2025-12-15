"""
Schema Query Agent (Phase 9)

AI agent for querying user's existing database schema.
Uses natural language to generate and execute SQL queries.
Read-only operations only - no table modifications.
"""

import logging
import os
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel

from app.services.schema_discovery import format_schema_for_prompt
from app.services.query_validator import validate_select_query
from app.mcp_server.tools_schema_query import (
    schema_list_tables,
    schema_describe_table,
    schema_execute_query,
    schema_get_sample_data,
    schema_get_table_stats,
    format_query_results_for_agent
)

logger = logging.getLogger(__name__)


class SchemaQueryAgent:
    """
    AI Agent for natural language queries against user's existing database.

    Key Features:
    - Schema-aware: Understands user's database structure
    - Read-only: Only executes SELECT queries
    - Natural language: Converts questions to SQL
    - Visualization hints: Suggests charts for results

    Usage:
        agent = SchemaQueryAgent(
            database_uri="postgresql://...",
            schema_metadata={"tables": [...], ...}
        )
        result = await agent.query("Show me top 10 customers")
    """

    def __init__(
        self,
        database_uri: str,
        schema_metadata: dict,
        gemini_api_key: Optional[str] = None,
        temperature: float = 0.3,  # Lower temperature for more deterministic SQL
        max_tokens: int = 4096,
    ):
        """
        Initialize Schema Query Agent.

        Args:
            database_uri: PostgreSQL connection string for user's database
            schema_metadata: Discovered schema metadata dict
            gemini_api_key: Google Gemini API key
            temperature: Model temperature (lower = more deterministic)
            max_tokens: Max output tokens
        """
        self.database_uri = database_uri
        self.schema_metadata = schema_metadata

        # Validate Gemini API Key
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY must be provided or set in environment")

        # Model configuration
        self.model_name = os.getenv("GEMINI_MODEL", "gemini/gemini-robotics-er-1.5-preview")
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Agent instance
        self._agent: Optional[Agent] = None
        self._model: Optional[LitellmModel] = None

        # Conversation history for context
        self._conversation_history: List[Dict[str, str]] = []

        logger.info(
            f"Initializing Schema Query Agent "
            f"(model={self.model_name}, temp={temperature})"
        )

    def _generate_system_prompt(self) -> str:
        """
        Generate system prompt with schema context.

        Returns:
            System prompt string with database schema information
        """
        schema_description = format_schema_for_prompt(self.schema_metadata)

        return f"""You are a database query assistant that helps users explore and analyze their data.

## Your Capabilities
1. Convert natural language questions to SQL queries
2. Execute SELECT queries against the database
3. Present results in a clear, readable format
4. Suggest visualizations for data when appropriate

## Database Schema
{schema_description}

## Rules (CRITICAL - You MUST follow these)
1. **READ-ONLY**: You can ONLY execute SELECT queries. Never use INSERT, UPDATE, DELETE, DROP, CREATE, or ALTER.
2. **EXPLAIN FIRST**: Before executing a query, briefly explain what SQL you will run.
3. **VALIDATE DATA**: Check if the query makes sense given the schema.
4. **FORMAT RESULTS**: Present results clearly. For large results, summarize key findings.
5. **SUGGEST CHARTS**: When appropriate, suggest chart types (bar, line, pie) for visualization.
6. **HANDLE ERRORS**: If a query fails, explain why and suggest alternatives.
7. **BE HELPFUL**: If the user's question is ambiguous, ask for clarification.

## Available Tools
- `execute_query(query)`: Execute a SELECT query and return results
- `list_tables(schema)`: List all tables in a schema
- `describe_table(table_name)`: Get table structure
- `get_sample_data(table_name, limit)`: Preview table data
- `get_table_stats(table_name)`: Get table statistics

## Response Format
When presenting query results:
1. Briefly state what you found
2. Show the key data points
3. If applicable, suggest a visualization
4. Offer follow-up questions the user might want to ask

Remember: You are analyzing the user's OWN data. Be helpful, accurate, and never modify anything."""

    async def initialize(self) -> None:
        """
        Initialize the agent with model and tools.
        """
        # Initialize LiteLLM model
        try:
            self._model = LitellmModel(
                model=self.model_name,
                api_key=self.gemini_api_key,
            )
            logger.info(f"LiteLLMModel initialized: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize LiteLLMModel: {e}")
            raise ValueError(f"Model initialization failed: {e}") from e

        # Create function tools that capture database_uri
        database_uri = self.database_uri

        @function_tool
        async def execute_query(query: str, max_rows: int = 100) -> str:
            """
            Execute a SQL SELECT query and return results.
            Only SELECT queries are allowed - no INSERT, UPDATE, DELETE, etc.

            Args:
                query: SQL SELECT query to execute
                max_rows: Maximum rows to return (default: 100, max: 10000)

            Returns:
                Query results as formatted string
            """
            # Validate query first
            is_valid, error_msg = validate_select_query(query)
            if not is_valid:
                return f"Query rejected: {error_msg}"

            result = await schema_execute_query(database_uri, query, max_rows)
            return format_query_results_for_agent(result)

        @function_tool
        async def list_tables(schema_name: str = "public") -> str:
            """
            List all tables in the specified schema.

            Args:
                schema_name: PostgreSQL schema name (default: public)

            Returns:
                List of tables with basic info
            """
            result = await schema_list_tables(database_uri, schema_name)
            if not result.get("success"):
                return f"Error: {result.get('error')}"

            tables = result.get("tables", [])
            lines = [f"Tables in schema '{schema_name}':"]
            for t in tables:
                lines.append(f"  - {t['name']} ({t['type']}, {t['column_count']} columns)")
            return "\n".join(lines)

        @function_tool
        async def describe_table(table_name: str, schema_name: str = "public") -> str:
            """
            Get detailed structure of a table including columns and their types.

            Args:
                table_name: Name of the table to describe
                schema_name: Schema name (default: public)

            Returns:
                Table structure with columns, types, and constraints
            """
            result = await schema_describe_table(database_uri, table_name, schema_name)
            if not result.get("success"):
                return f"Error: {result.get('error')}"

            lines = [
                f"Table: {result['schema']}.{result['table_name']}",
                f"Estimated rows: ~{result['estimated_rows']:,}",
                "",
                "Columns:"
            ]
            for col in result.get("columns", []):
                pk = " [PK]" if col.get("primary_key") else ""
                fk = f" -> {col['foreign_key']}" if col.get("foreign_key") else ""
                nullable = " (nullable)" if col.get("nullable") else ""
                lines.append(f"  - {col['name']}: {col['type']}{pk}{fk}{nullable}")

            return "\n".join(lines)

        @function_tool
        async def get_sample_data(table_name: str, schema_name: str = "public", limit: int = 5) -> str:
            """
            Get sample rows from a table to preview its data.

            Args:
                table_name: Name of the table
                schema_name: Schema name (default: public)
                limit: Number of sample rows (default: 5, max: 20)

            Returns:
                Sample data rows
            """
            result = await schema_get_sample_data(
                database_uri, table_name, schema_name, min(limit, 20)
            )
            if not result.get("success"):
                return f"Error: {result.get('error')}"

            data = result.get("data", [])
            if not data:
                return f"Table '{table_name}' is empty."

            lines = [f"Sample data from {table_name} ({len(data)} rows):"]
            for i, row in enumerate(data, 1):
                row_str = ", ".join(f"{k}={v}" for k, v in list(row.items())[:5])
                if len(row) > 5:
                    row_str += ", ..."
                lines.append(f"  {i}. {row_str}")

            return "\n".join(lines)

        @function_tool
        async def get_table_stats(table_name: str, schema_name: str = "public") -> str:
            """
            Get statistics for a table (row count, size, indexes).

            Args:
                table_name: Name of the table
                schema_name: Schema name (default: public)

            Returns:
                Table statistics
            """
            result = await schema_get_table_stats(database_uri, table_name, schema_name)
            if not result.get("success"):
                return f"Error: {result.get('error')}"

            return (
                f"Statistics for {table_name}:\n"
                f"  - Estimated rows: ~{result.get('estimated_rows', 0):,}\n"
                f"  - Table size: {result.get('size', 'unknown')}\n"
                f"  - Columns: {result.get('column_count', 0)}\n"
                f"  - Indexes: {result.get('index_count', 0)}"
            )

        # Create the agent
        self._agent = Agent(
            name="Schema Query Agent",
            instructions=self._generate_system_prompt(),
            model=self._model,
            tools=[
                execute_query,
                list_tables,
                describe_table,
                get_sample_data,
                get_table_stats
            ],
        )

        logger.info("Schema Query Agent initialized with 5 tools")

    async def query(
        self,
        natural_query: str,
        include_sql: bool = True
    ) -> Dict[str, Any]:
        """
        Process a natural language query.

        Args:
            natural_query: User's question in natural language
            include_sql: Whether to include generated SQL in response

        Returns:
            dict with response, data, and optional visualization hint
        """
        if not self._agent:
            await self.initialize()

        try:
            # Run the agent
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

            return {
                "success": True,
                "response": response_text,
                "visualization_hint": visualization_hint
            }

        except Exception as e:
            logger.error(f"Agent query failed: {e}")
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

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self._conversation_history.copy()


# Factory function for creating agent instances
async def create_schema_query_agent(
    database_uri: str,
    schema_metadata: dict,
    auto_initialize: bool = True
) -> SchemaQueryAgent:
    """
    Factory function to create and initialize a Schema Query Agent.

    Args:
        database_uri: PostgreSQL connection string
        schema_metadata: Discovered schema metadata
        auto_initialize: Whether to initialize immediately

    Returns:
        Initialized SchemaQueryAgent instance
    """
    agent = SchemaQueryAgent(
        database_uri=database_uri,
        schema_metadata=schema_metadata
    )

    if auto_initialize:
        await agent.initialize()

    return agent
