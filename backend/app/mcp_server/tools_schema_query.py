"""
MCP Tools for Schema Query Agent (Phase 9)

These tools allow the AI agent to query user's existing database
without creating any new tables. Read-only operations only.
"""

import asyncpg
import asyncio
from datetime import datetime
from typing import Optional, Any
import json

from app.services.query_validator import (
    validate_select_query,
    QueryValidationError,
    sanitize_identifier
)
from app.services.schema_discovery import (
    discover_schema,
    get_table_sample,
    get_table_stats,
    format_schema_for_prompt,
    SchemaDiscoveryError,
    TooManyTablesError
)


# Query execution limits
MAX_ROWS = 10000
QUERY_TIMEOUT = 30  # seconds


class SchemaQueryToolError(Exception):
    """Custom exception for schema query tool errors"""
    pass


async def schema_list_tables(
    database_uri: str,
    schema_name: str = "public"
) -> dict:
    """
    List all tables in the specified schema.

    Args:
        database_uri: PostgreSQL connection string
        schema_name: Schema name to list tables from (default: public)

    Returns:
        dict with list of tables and their basic info
    """
    try:
        conn = await asyncpg.connect(database_uri, timeout=10)
        try:
            query = """
                SELECT
                    table_name,
                    table_type,
                    (SELECT COUNT(*) FROM information_schema.columns c
                     WHERE c.table_name = t.table_name
                     AND c.table_schema = t.table_schema) as column_count
                FROM information_schema.tables t
                WHERE table_schema = $1
                AND table_type IN ('BASE TABLE', 'VIEW')
                ORDER BY table_name
            """
            rows = await conn.fetch(query, schema_name)

            tables = [
                {
                    "name": row["table_name"],
                    "type": "view" if row["table_type"] == "VIEW" else "table",
                    "column_count": row["column_count"]
                }
                for row in rows
            ]

            return {
                "success": True,
                "schema": schema_name,
                "table_count": len(tables),
                "tables": tables
            }

        finally:
            await conn.close()

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def schema_describe_table(
    database_uri: str,
    table_name: str,
    schema_name: str = "public"
) -> dict:
    """
    Get detailed structure of a specific table.

    Args:
        database_uri: PostgreSQL connection string
        table_name: Name of the table to describe
        schema_name: Schema name (default: public)

    Returns:
        dict with table structure including columns, types, and constraints
    """
    try:
        # Sanitize inputs
        safe_table = sanitize_identifier(table_name)
        safe_schema = sanitize_identifier(schema_name)

        conn = await asyncpg.connect(database_uri, timeout=10)
        try:
            # Get columns
            columns_query = """
                SELECT
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    c.character_maximum_length,
                    CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
                    CASE WHEN fk.column_name IS NOT NULL THEN fk.foreign_table || '.' || fk.foreign_column ELSE NULL END as foreign_key
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_name = $1 AND tc.table_schema = $2
                ) pk ON c.column_name = pk.column_name
                LEFT JOIN (
                    SELECT
                        kcu.column_name,
                        ccu.table_name as foreign_table,
                        ccu.column_name as foreign_column
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = $1 AND tc.table_schema = $2
                ) fk ON c.column_name = fk.column_name
                WHERE c.table_name = $1 AND c.table_schema = $2
                ORDER BY c.ordinal_position
            """
            column_rows = await conn.fetch(columns_query, safe_table, safe_schema)

            # Get row count estimate
            count_query = """
                SELECT reltuples::bigint as estimate
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = $1 AND n.nspname = $2
            """
            row_count = await conn.fetchval(count_query, safe_table, safe_schema)

            columns = []
            for row in column_rows:
                col = {
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                    "primary_key": row["is_primary_key"]
                }
                if row["character_maximum_length"]:
                    col["type"] = f"{row['data_type']}({row['character_maximum_length']})"
                if row["column_default"]:
                    col["default"] = row["column_default"]
                if row["foreign_key"]:
                    col["foreign_key"] = row["foreign_key"]
                columns.append(col)

            return {
                "success": True,
                "table_name": safe_table,
                "schema": safe_schema,
                "estimated_rows": max(0, row_count or 0),
                "column_count": len(columns),
                "columns": columns
            }

        finally:
            await conn.close()

    except QueryValidationError as e:
        return {"success": False, "error": e.message}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def schema_execute_query(
    database_uri: str,
    query: str,
    max_rows: int = 100
) -> dict:
    """
    Execute a SELECT query and return results.

    CRITICAL: Only SELECT queries are allowed. This is enforced at multiple levels.

    Args:
        database_uri: PostgreSQL connection string
        query: SQL SELECT query to execute
        max_rows: Maximum rows to return (default: 100, max: 10000)

    Returns:
        dict with query results or error
    """
    # Validate query is SELECT only
    is_valid, error_msg = validate_select_query(query)
    if not is_valid:
        return {
            "success": False,
            "error": error_msg,
            "query": query
        }

    # Enforce row limit
    effective_max_rows = min(max_rows, MAX_ROWS)

    try:
        conn = await asyncpg.connect(database_uri, timeout=10)
        try:
            # Add LIMIT if not present (basic check)
            query_upper = query.upper()
            if "LIMIT" not in query_upper:
                # Append LIMIT to query
                query = f"{query.rstrip().rstrip(';')} LIMIT {effective_max_rows}"

            # Execute with timeout
            try:
                rows = await asyncio.wait_for(
                    conn.fetch(query),
                    timeout=QUERY_TIMEOUT
                )
            except asyncio.TimeoutError:
                return {
                    "success": False,
                    "error": f"Query timed out after {QUERY_TIMEOUT} seconds. Please simplify your query.",
                    "query": query
                }

            # Convert rows to list of dicts
            results = []
            for row in rows[:effective_max_rows]:
                row_dict = {}
                for key, value in dict(row).items():
                    # Handle special types
                    if isinstance(value, datetime):
                        row_dict[key] = value.isoformat()
                    elif isinstance(value, (bytes, bytearray)):
                        row_dict[key] = "<binary data>"
                    else:
                        row_dict[key] = value
                results.append(row_dict)

            # Get column names from first row
            columns = list(results[0].keys()) if results else []

            return {
                "success": True,
                "query": query,
                "row_count": len(results),
                "columns": columns,
                "data": results,
                "truncated": len(rows) > effective_max_rows
            }

        finally:
            await conn.close()

    except asyncpg.PostgresSyntaxError as e:
        return {
            "success": False,
            "error": f"SQL syntax error: {str(e)}",
            "query": query
        }
    except asyncpg.UndefinedTableError as e:
        return {
            "success": False,
            "error": f"Table not found: {str(e)}",
            "query": query
        }
    except asyncpg.UndefinedColumnError as e:
        return {
            "success": False,
            "error": f"Column not found: {str(e)}",
            "query": query
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Query execution failed: {str(e)}",
            "query": query
        }


async def schema_get_sample_data(
    database_uri: str,
    table_name: str,
    schema_name: str = "public",
    limit: int = 10
) -> dict:
    """
    Get sample rows from a table for preview.

    Args:
        database_uri: PostgreSQL connection string
        table_name: Name of the table
        schema_name: Schema name (default: public)
        limit: Number of rows to return (default: 10, max: 100)

    Returns:
        dict with sample data
    """
    try:
        # Sanitize inputs
        safe_table = sanitize_identifier(table_name)
        safe_schema = sanitize_identifier(schema_name)
        effective_limit = min(limit, 100)

        conn = await asyncpg.connect(database_uri, timeout=10)
        try:
            query = f'SELECT * FROM "{safe_schema}"."{safe_table}" LIMIT $1'
            rows = await conn.fetch(query, effective_limit)

            # Convert to list of dicts
            results = []
            for row in rows:
                row_dict = {}
                for key, value in dict(row).items():
                    if isinstance(value, datetime):
                        row_dict[key] = value.isoformat()
                    elif isinstance(value, (bytes, bytearray)):
                        row_dict[key] = "<binary data>"
                    else:
                        row_dict[key] = value
                results.append(row_dict)

            columns = list(results[0].keys()) if results else []

            return {
                "success": True,
                "table_name": safe_table,
                "schema": safe_schema,
                "row_count": len(results),
                "columns": columns,
                "data": results
            }

        finally:
            await conn.close()

    except QueryValidationError as e:
        return {"success": False, "error": e.message}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def schema_get_table_stats(
    database_uri: str,
    table_name: str,
    schema_name: str = "public"
) -> dict:
    """
    Get statistics for a specific table.

    Args:
        database_uri: PostgreSQL connection string
        table_name: Name of the table
        schema_name: Schema name (default: public)

    Returns:
        dict with table statistics
    """
    try:
        result = await get_table_stats(database_uri, table_name, schema_name)
        return {"success": True, **result}
    except SchemaDiscoveryError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def schema_discover_full(
    database_uri: str,
    allowed_schemas: list[str] = None
) -> dict:
    """
    Discover complete database schema.

    Args:
        database_uri: PostgreSQL connection string
        allowed_schemas: List of schema names to include (default: ['public'])

    Returns:
        dict with complete schema metadata
    """
    try:
        schema_metadata = await discover_schema(database_uri, allowed_schemas)
        return {
            "success": True,
            "schema_metadata": schema_metadata
        }
    except TooManyTablesError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "too_many_tables"
        }
    except SchemaDiscoveryError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "discovery_error"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "unknown_error"
        }


async def schema_refresh(
    database_uri: str,
    allowed_schemas: list[str] = None
) -> dict:
    """
    Refresh schema cache by re-discovering the database schema.

    Args:
        database_uri: PostgreSQL connection string
        allowed_schemas: List of schema names to include (default: ['public'])

    Returns:
        dict with updated schema metadata
    """
    return await schema_discover_full(database_uri, allowed_schemas)


# Helper function to format results for agent consumption
def format_query_results_for_agent(results: dict) -> str:
    """
    Format query results as a readable string for the agent to present.

    Args:
        results: Query results dict from schema_execute_query

    Returns:
        Formatted string representation
    """
    if not results.get("success"):
        return f"Error: {results.get('error', 'Unknown error')}"

    data = results.get("data", [])
    if not data:
        return "Query returned no results."

    columns = results.get("columns", [])
    row_count = results.get("row_count", 0)

    lines = [f"Query returned {row_count} row(s):"]
    lines.append("")

    # Format as simple table
    if row_count <= 20:
        # Show all rows for small result sets
        for i, row in enumerate(data, 1):
            lines.append(f"Row {i}:")
            for col in columns:
                lines.append(f"  {col}: {row.get(col)}")
            lines.append("")
    else:
        # Show summary for large result sets
        lines.append(f"Columns: {', '.join(columns)}")
        lines.append("")
        lines.append("First 5 rows:")
        for row in data[:5]:
            row_str = ", ".join(f"{col}={row.get(col)}" for col in columns[:5])
            if len(columns) > 5:
                row_str += ", ..."
            lines.append(f"  {row_str}")

        if row_count > 5:
            lines.append(f"  ... and {row_count - 5} more rows")

    if results.get("truncated"):
        lines.append("")
        lines.append("Note: Results were truncated due to row limit.")

    return "\n".join(lines)
