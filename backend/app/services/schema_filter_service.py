"""
Schema Filter Service for Developer Tools (Phase 14)

This is the CORE service that enables table-level access control for published agents.
It filters the organization's full schema_metadata to only include allowed tables.

Key Principle:
- Same SchemaQueryAgent code is reused
- Only the schema_metadata input is filtered
- Agent literally cannot see or query tables not in the filtered view

Security Design:
- Filter happens at data layer (not query layer)
- Agent's prompt only contains allowed table schemas
- Agent cannot reference tables it doesn't know exist
- Relationships between non-allowed tables are also filtered

Example:
    Full schema: {tables: [products, orders, users, admin_logs, payments]}
    Allowed: ["products", "orders"]
    Filtered: {tables: [products, orders]}  # Agent only sees these!
"""

import logging
from typing import Dict, List, Any, Optional, Set
from copy import deepcopy

logger = logging.getLogger(__name__)


def filter_schema_for_published_agent(
    full_schema: Dict[str, Any],
    allowed_tables: List[str],
    access_mode: str = "read_only"
) -> Dict[str, Any]:
    """
    Filter schema metadata to only include allowed tables.

    This is the KEY function that enables table-level access control
    WITHOUT modifying the existing SchemaQueryAgent.

    Args:
        full_schema: Complete schema_metadata from owner's UserConnection
                    Structure: {
                        database: str,
                        schemas: [str],
                        tables: [{name, schema, columns, ...}],
                        relationships: [{from_table, to_table, ...}],
                        discovered_at: str,
                        table_count: int
                    }
        allowed_tables: List of table names organization has allowed
                       (e.g., ["products", "orders"])
        access_mode: "read_only" or "read_write" - added to schema for prompt

    Returns:
        Filtered schema dict with same structure as original,
        but only containing allowed tables and their relationships.

    Security:
        - Tables not in allowed_tables are completely removed
        - Relationships between removed tables are also removed
        - Agent prompt will only show allowed tables
        - Agent cannot query what it doesn't know exists
    """
    if not full_schema:
        logger.warning("[Schema Filter] Empty schema provided")
        return {
            "database": None,
            "schemas": [],
            "tables": [],
            "relationships": [],
            "table_count": 0,
            "discovered_at": None,
            "access_mode": access_mode,
            "is_filtered": True,
            "original_table_count": 0,
        }

    if not allowed_tables:
        logger.warning("[Schema Filter] No allowed tables specified - returning empty schema")
        return {
            "database": full_schema.get("database"),
            "schemas": full_schema.get("schemas", []),
            "tables": [],
            "relationships": [],
            "table_count": 0,
            "discovered_at": full_schema.get("discovered_at"),
            "access_mode": access_mode,
            "is_filtered": True,
            "original_table_count": len(full_schema.get("tables", [])),
        }

    # Create case-insensitive set for matching
    allowed_set: Set[str] = {t.lower().strip() for t in allowed_tables}

    # Deep copy to avoid modifying original
    filtered = deepcopy(full_schema)

    # Track original count for logging
    original_table_count = len(filtered.get("tables", []))

    # Filter tables
    filtered_tables = []
    for table in filtered.get("tables", []):
        table_name = table.get("name", "").lower().strip()
        if table_name in allowed_set:
            filtered_tables.append(table)

    filtered["tables"] = filtered_tables

    # Filter relationships - only keep those between allowed tables
    filtered_relationships = []
    for rel in filtered.get("relationships", []):
        from_table = rel.get("from_table", "").lower().strip()
        to_table = rel.get("to_table", "").lower().strip()

        # Both tables must be in allowed set
        if from_table in allowed_set and to_table in allowed_set:
            filtered_relationships.append(rel)

    filtered["relationships"] = filtered_relationships

    # Update metadata
    filtered["table_count"] = len(filtered_tables)
    filtered["access_mode"] = access_mode
    filtered["is_filtered"] = True
    filtered["original_table_count"] = original_table_count
    filtered["allowed_tables"] = list(allowed_tables)  # For reference

    logger.info(
        f"[Schema Filter] Filtered schema: "
        f"{original_table_count} → {len(filtered_tables)} tables, "
        f"{len(full_schema.get('relationships', []))} → {len(filtered_relationships)} relationships, "
        f"access_mode={access_mode}"
    )

    return filtered


def validate_allowed_tables(
    allowed_tables: List[str],
    full_schema: Dict[str, Any]
) -> tuple[List[str], List[str]]:
    """
    Validate that requested tables exist in the full schema.

    Args:
        allowed_tables: List of table names to validate
        full_schema: Complete schema_metadata

    Returns:
        Tuple of (valid_tables, invalid_tables)

    Use Case:
        When organization creates a published agent, validate that
        the requested tables actually exist in their database.
    """
    if not full_schema or not full_schema.get("tables"):
        return [], list(allowed_tables)

    # Get all table names from schema (lowercase for comparison)
    available_tables: Set[str] = {
        table.get("name", "").lower().strip()
        for table in full_schema.get("tables", [])
    }

    valid_tables = []
    invalid_tables = []

    for table in allowed_tables:
        if table.lower().strip() in available_tables:
            valid_tables.append(table)
        else:
            invalid_tables.append(table)

    return valid_tables, invalid_tables


def get_table_names_from_schema(schema: Dict[str, Any]) -> List[str]:
    """
    Extract all table names from a schema.

    Args:
        schema: Schema metadata dict

    Returns:
        List of table names
    """
    if not schema or not schema.get("tables"):
        return []

    return [
        table.get("name", "")
        for table in schema.get("tables", [])
        if table.get("name")
    ]


def get_table_info(
    schema: Dict[str, Any],
    table_name: str
) -> Optional[Dict[str, Any]]:
    """
    Get detailed info for a specific table.

    Args:
        schema: Schema metadata dict
        table_name: Name of table to find

    Returns:
        Table dict with columns, etc. or None if not found
    """
    if not schema or not schema.get("tables"):
        return None

    table_lower = table_name.lower().strip()

    for table in schema.get("tables", []):
        if table.get("name", "").lower().strip() == table_lower:
            return table

    return None


def count_columns_in_tables(
    schema: Dict[str, Any],
    table_names: Optional[List[str]] = None
) -> Dict[str, int]:
    """
    Count columns for each table (or specified tables).

    Args:
        schema: Schema metadata dict
        table_names: Optional list of tables to count (None = all)

    Returns:
        Dict mapping table name to column count
    """
    if not schema or not schema.get("tables"):
        return {}

    result = {}

    for table in schema.get("tables", []):
        name = table.get("name", "")
        if table_names is None or name.lower() in {t.lower() for t in table_names}:
            columns = table.get("columns", [])
            result[name] = len(columns)

    return result


def build_table_summary(
    schema: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Build a summary of tables for frontend display.

    Args:
        schema: Schema metadata dict

    Returns:
        List of dicts: [{name, column_count, primary_key, ...}]
    """
    if not schema or not schema.get("tables"):
        return []

    summaries = []

    for table in schema.get("tables", []):
        columns = table.get("columns", [])

        # Find primary key column(s)
        pk_columns = [
            col.get("name")
            for col in columns
            if col.get("is_primary_key") or col.get("constraint_type") == "PRIMARY KEY"
        ]

        summary = {
            "name": table.get("name", ""),
            "schema": table.get("schema", "public"),
            "column_count": len(columns),
            "primary_key": pk_columns[0] if pk_columns else None,
            "has_primary_key": len(pk_columns) > 0,
            "columns": [col.get("name") for col in columns[:5]],  # First 5 for preview
            "column_preview": ", ".join([col.get("name", "") for col in columns[:3]]) + (
                "..." if len(columns) > 3 else ""
            ),
        }

        summaries.append(summary)

    # Sort by table name
    summaries.sort(key=lambda x: x["name"].lower())

    return summaries


def get_access_mode_description(access_mode: str) -> str:
    """
    Get human-readable description of access mode.

    Args:
        access_mode: "read_only" or "read_write"

    Returns:
        Description string for UI/prompts
    """
    if access_mode == "read_only":
        return "Read-only access (SELECT queries only)"
    elif access_mode == "read_write":
        return "Full access (SELECT, INSERT, UPDATE, DELETE)"
    else:
        return f"Unknown access mode: {access_mode}"
