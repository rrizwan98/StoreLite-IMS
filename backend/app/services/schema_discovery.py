"""
Schema Discovery Service for Schema Query Agent (Phase 9)

Discovers and caches database schema from user's PostgreSQL database.
Used to provide context to the AI agent for natural language queries.
"""

import asyncpg
from datetime import datetime
from typing import Optional
import json


# Maximum tables allowed per connection (as per spec clarification)
MAX_TABLES_LIMIT = 100


class SchemaDiscoveryError(Exception):
    """Custom exception for schema discovery errors"""
    pass


class TooManyTablesError(SchemaDiscoveryError):
    """Raised when table count exceeds MAX_TABLES_LIMIT"""
    pass


async def test_connection(database_uri: str, timeout: float = 10.0) -> dict:
    """
    Test PostgreSQL connection and return basic info.

    Args:
        database_uri: PostgreSQL connection string
        timeout: Connection timeout in seconds

    Returns:
        dict with status and connection info
    """
    try:
        conn = await asyncpg.connect(database_uri, timeout=timeout)
        try:
            # Get PostgreSQL version
            version = await conn.fetchval("SELECT version()")
            # Get current database name
            db_name = await conn.fetchval("SELECT current_database()")
            # Get current user
            db_user = await conn.fetchval("SELECT current_user")

            return {
                "status": "success",
                "database": db_name,
                "user": db_user,
                "version": version,
                "message": "Connection successful"
            }
        finally:
            await conn.close()
    except asyncpg.InvalidPasswordError:
        return {"status": "error", "message": "Invalid password"}
    except asyncpg.InvalidCatalogNameError:
        return {"status": "error", "message": "Database does not exist"}
    except asyncpg.PostgresConnectionError as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


async def discover_schema(
    database_uri: str,
    allowed_schemas: list[str] = None,
    timeout: float = 30.0
) -> dict:
    """
    Discover complete database schema including tables, columns, and relationships.

    Args:
        database_uri: PostgreSQL connection string
        allowed_schemas: List of schema names to include (default: ['public'])
        timeout: Connection timeout in seconds

    Returns:
        dict with complete schema metadata

    Raises:
        TooManyTablesError: If table count exceeds MAX_TABLES_LIMIT
        SchemaDiscoveryError: If discovery fails
    """
    if allowed_schemas is None:
        allowed_schemas = ["public"]

    try:
        conn = await asyncpg.connect(database_uri, timeout=timeout)
        try:
            # Step 1: Get all tables
            tables = await _get_tables(conn, allowed_schemas)

            # Check table limit
            if len(tables) > MAX_TABLES_LIMIT:
                raise TooManyTablesError(
                    f"Database has {len(tables)} tables, exceeding limit of {MAX_TABLES_LIMIT}. "
                    f"Please specify allowed_schemas to filter tables."
                )

            # Step 2: Get columns for each table
            for table in tables:
                table["columns"] = await _get_columns(
                    conn, table["name"], table["schema"]
                )
                table["estimated_rows"] = await _get_row_count_estimate(
                    conn, table["name"], table["schema"]
                )

            # Step 3: Get foreign key relationships
            relationships = await _get_foreign_keys(conn, allowed_schemas)

            # Step 4: Add relationships to tables
            for table in tables:
                table["relationships"] = [
                    rel for rel in relationships
                    if rel["from_table"] == table["name"] and rel["from_schema"] == table["schema"]
                ]

            # Build schema metadata
            schema_metadata = {
                "tables": tables,
                "relationships": relationships,
                "discovered_at": datetime.utcnow().isoformat() + "Z",
                "total_tables": len(tables),
                "total_columns": sum(len(t["columns"]) for t in tables),
                "schemas": allowed_schemas,
                "version": "1.0"
            }

            return schema_metadata

        finally:
            await conn.close()

    except TooManyTablesError:
        raise
    except asyncpg.PostgresError as e:
        raise SchemaDiscoveryError(f"Database error during schema discovery: {str(e)}")
    except Exception as e:
        raise SchemaDiscoveryError(f"Schema discovery failed: {str(e)}")


async def _get_tables(conn: asyncpg.Connection, schemas: list[str]) -> list[dict]:
    """Get all tables in specified schemas."""
    query = """
        SELECT
            table_schema,
            table_name,
            table_type
        FROM information_schema.tables
        WHERE table_schema = ANY($1)
        AND table_type IN ('BASE TABLE', 'VIEW')
        ORDER BY table_schema, table_name
    """
    rows = await conn.fetch(query, schemas)

    return [
        {
            "name": row["table_name"],
            "schema": row["table_schema"],
            "type": "view" if row["table_type"] == "VIEW" else "table",
            "columns": [],
            "relationships": []
        }
        for row in rows
    ]


async def _get_columns(
    conn: asyncpg.Connection,
    table_name: str,
    schema_name: str
) -> list[dict]:
    """Get columns for a specific table."""
    query = """
        SELECT
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key
        FROM information_schema.columns c
        LEFT JOIN (
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_name = $1
            AND tc.table_schema = $2
        ) pk ON c.column_name = pk.column_name
        WHERE c.table_name = $1
        AND c.table_schema = $2
        ORDER BY c.ordinal_position
    """
    rows = await conn.fetch(query, table_name, schema_name)

    columns = []
    for row in rows:
        col = {
            "name": row["column_name"],
            "type": _format_data_type(row),
            "nullable": row["is_nullable"] == "YES",
            "primary_key": row["is_primary_key"],
        }
        if row["column_default"]:
            col["default"] = row["column_default"]
        columns.append(col)

    return columns


def _format_data_type(row: dict) -> str:
    """Format data type with precision/length info."""
    data_type = row["data_type"]

    if row["character_maximum_length"]:
        return f"{data_type}({row['character_maximum_length']})"
    elif row["numeric_precision"] and row["numeric_scale"]:
        return f"{data_type}({row['numeric_precision']},{row['numeric_scale']})"
    elif row["numeric_precision"]:
        return f"{data_type}({row['numeric_precision']})"

    return data_type


async def _get_foreign_keys(conn: asyncpg.Connection, schemas: list[str]) -> list[dict]:
    """Get all foreign key relationships in specified schemas."""
    query = """
        SELECT
            tc.table_schema as from_schema,
            tc.table_name as from_table,
            kcu.column_name as from_column,
            ccu.table_schema as to_schema,
            ccu.table_name as to_table,
            ccu.column_name as to_column,
            tc.constraint_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = ANY($1)
        ORDER BY tc.table_name, kcu.column_name
    """
    rows = await conn.fetch(query, schemas)

    return [
        {
            "from_schema": row["from_schema"],
            "from_table": row["from_table"],
            "from_column": row["from_column"],
            "to_schema": row["to_schema"],
            "to_table": row["to_table"],
            "to_column": row["to_column"],
            "constraint_name": row["constraint_name"],
            "type": "many-to-one"  # FK implies many-to-one by default
        }
        for row in rows
    ]


async def _get_row_count_estimate(
    conn: asyncpg.Connection,
    table_name: str,
    schema_name: str
) -> int:
    """Get estimated row count from PostgreSQL statistics."""
    query = """
        SELECT reltuples::bigint AS estimate
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = $1
        AND n.nspname = $2
    """
    result = await conn.fetchval(query, table_name, schema_name)
    return max(0, result or 0)


async def get_table_sample(
    database_uri: str,
    table_name: str,
    schema_name: str = "public",
    limit: int = 10,
    timeout: float = 30.0
) -> list[dict]:
    """
    Get sample rows from a table.

    Args:
        database_uri: PostgreSQL connection string
        table_name: Name of the table
        schema_name: Schema name (default: public)
        limit: Maximum rows to return (default: 10)
        timeout: Query timeout in seconds

    Returns:
        List of row dictionaries
    """
    try:
        conn = await asyncpg.connect(database_uri, timeout=timeout)
        try:
            # Sanitize identifiers (basic protection)
            safe_schema = schema_name.replace('"', '""')
            safe_table = table_name.replace('"', '""')

            query = f'SELECT * FROM "{safe_schema}"."{safe_table}" LIMIT $1'
            rows = await conn.fetch(query, min(limit, 100))

            return [dict(row) for row in rows]

        finally:
            await conn.close()
    except Exception as e:
        raise SchemaDiscoveryError(f"Failed to get sample data: {str(e)}")


async def get_table_stats(
    database_uri: str,
    table_name: str,
    schema_name: str = "public",
    timeout: float = 30.0
) -> dict:
    """
    Get statistics for a specific table.

    Args:
        database_uri: PostgreSQL connection string
        table_name: Name of the table
        schema_name: Schema name (default: public)
        timeout: Query timeout in seconds

    Returns:
        dict with table statistics
    """
    try:
        conn = await asyncpg.connect(database_uri, timeout=timeout)
        try:
            # Get row count estimate
            row_estimate = await _get_row_count_estimate(conn, table_name, schema_name)

            # Get table size
            size_query = """
                SELECT pg_size_pretty(pg_total_relation_size($1::regclass)) as size
            """
            safe_name = f'"{schema_name}"."{table_name}"'
            size_result = await conn.fetchval(size_query, safe_name)

            # Get column count
            column_query = """
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_name = $1 AND table_schema = $2
            """
            column_count = await conn.fetchval(column_query, table_name, schema_name)

            # Get index count
            index_query = """
                SELECT COUNT(*) FROM pg_indexes
                WHERE tablename = $1 AND schemaname = $2
            """
            index_count = await conn.fetchval(index_query, table_name, schema_name)

            return {
                "table_name": table_name,
                "schema": schema_name,
                "estimated_rows": row_estimate,
                "size": size_result,
                "column_count": column_count,
                "index_count": index_count
            }

        finally:
            await conn.close()
    except Exception as e:
        raise SchemaDiscoveryError(f"Failed to get table stats: {str(e)}")


def format_schema_for_prompt(schema_metadata: dict) -> str:
    """
    Format schema metadata as a readable string for AI agent system prompt.

    Args:
        schema_metadata: Schema metadata dict from discover_schema()

    Returns:
        Formatted string describing the database schema
    """
    lines = [
        f"Database Schema (discovered {schema_metadata.get('discovered_at', 'unknown')})",
        f"Total: {schema_metadata.get('total_tables', 0)} tables, {schema_metadata.get('total_columns', 0)} columns",
        ""
    ]

    for table in schema_metadata.get("tables", []):
        # Table header
        table_type = "VIEW" if table.get("type") == "view" else "TABLE"
        rows = table.get("estimated_rows", 0)
        lines.append(f"## {table['schema']}.{table['name']} ({table_type}, ~{rows:,} rows)")

        # Columns
        lines.append("Columns:")
        for col in table.get("columns", []):
            pk_marker = " [PK]" if col.get("primary_key") else ""
            nullable = " (nullable)" if col.get("nullable") else ""
            lines.append(f"  - {col['name']}: {col['type']}{pk_marker}{nullable}")

        # Relationships
        if table.get("relationships"):
            lines.append("Foreign Keys:")
            for rel in table["relationships"]:
                lines.append(
                    f"  - {rel['from_column']} -> {rel['to_table']}.{rel['to_column']}"
                )

        lines.append("")

    return "\n".join(lines)
