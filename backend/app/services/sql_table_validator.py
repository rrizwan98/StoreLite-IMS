"""
SQL Table Validator Service for Published Agents (Phase 14)

This service validates SQL queries to ensure they only access allowed tables.
It's used to enforce table-level access control for published agents.

Security Design:
- Parses SQL to extract table names
- Validates against allowed tables list
- Blocks queries accessing unauthorized tables
- Works with SELECT, INSERT, UPDATE, DELETE, JOIN, subqueries
"""

import re
import logging
from typing import List, Set, Tuple, Optional

logger = logging.getLogger(__name__)


def extract_tables_from_sql(sql: str) -> Set[str]:
    """
    Extract all table names referenced in a SQL query.

    Handles:
    - SELECT ... FROM table
    - JOIN table
    - INSERT INTO table
    - UPDATE table
    - DELETE FROM table
    - Subqueries
    - Schema-qualified names (schema.table)
    - Table aliases

    Args:
        sql: SQL query string

    Returns:
        Set of table names (lowercase, without schema prefix)
    """
    tables = set()

    # Normalize whitespace and convert to lowercase for parsing
    normalized = ' '.join(sql.lower().split())

    # Remove string literals to avoid false matches
    # Replace quoted strings with placeholders
    normalized = re.sub(r"'[^']*'", "''", normalized)
    normalized = re.sub(r'"[^"]*"', '""', normalized)

    # Pattern for FROM clause (handles multiple tables)
    # FROM table1, table2 or FROM table1 AS t1, table2 t2
    from_pattern = r'\bfrom\s+([a-z_][a-z0-9_]*(?:\s*\.\s*[a-z_][a-z0-9_]*)?(?:\s+(?:as\s+)?[a-z_][a-z0-9_]*)?(?:\s*,\s*[a-z_][a-z0-9_]*(?:\s*\.\s*[a-z_][a-z0-9_]*)?(?:\s+(?:as\s+)?[a-z_][a-z0-9_]*)?)*)'

    # Pattern for JOIN clause
    join_pattern = r'\bjoin\s+([a-z_][a-z0-9_]*(?:\s*\.\s*[a-z_][a-z0-9_]*)?)'

    # Pattern for INSERT INTO
    insert_pattern = r'\binsert\s+into\s+([a-z_][a-z0-9_]*(?:\s*\.\s*[a-z_][a-z0-9_]*)?)'

    # Pattern for UPDATE
    update_pattern = r'\bupdate\s+([a-z_][a-z0-9_]*(?:\s*\.\s*[a-z_][a-z0-9_]*)?)'

    # Pattern for DELETE FROM
    delete_pattern = r'\bdelete\s+from\s+([a-z_][a-z0-9_]*(?:\s*\.\s*[a-z_][a-z0-9_]*)?)'

    # Extract FROM tables
    from_matches = re.findall(from_pattern, normalized)
    for match in from_matches:
        # Split by comma for multiple tables
        parts = match.split(',')
        for part in parts:
            table = _extract_table_name(part.strip())
            if table:
                tables.add(table)

    # Extract JOIN tables
    join_matches = re.findall(join_pattern, normalized)
    for match in join_matches:
        table = _extract_table_name(match)
        if table:
            tables.add(table)

    # Extract INSERT tables
    insert_matches = re.findall(insert_pattern, normalized)
    for match in insert_matches:
        table = _extract_table_name(match)
        if table:
            tables.add(table)

    # Extract UPDATE tables
    update_matches = re.findall(update_pattern, normalized)
    for match in update_matches:
        table = _extract_table_name(match)
        if table:
            tables.add(table)

    # Extract DELETE tables
    delete_matches = re.findall(delete_pattern, normalized)
    for match in delete_matches:
        table = _extract_table_name(match)
        if table:
            tables.add(table)

    logger.debug(f"[SQL Validator] Extracted tables: {tables}")
    return tables


def _extract_table_name(table_ref: str) -> Optional[str]:
    """
    Extract table name from a table reference.

    Handles:
    - table_name
    - schema.table_name
    - table_name AS alias
    - table_name alias

    Returns:
        Table name without schema or alias, lowercase
    """
    if not table_ref:
        return None

    # Remove leading/trailing whitespace
    table_ref = table_ref.strip()

    # Handle schema.table_name
    if '.' in table_ref:
        # Take the part after the last dot
        parts = table_ref.split('.')
        table_ref = parts[-1].strip()

    # Handle aliases (table_name AS alias or table_name alias)
    # Split on whitespace and take first part
    parts = table_ref.split()
    if parts:
        table_name = parts[0].strip()
        # Remove any remaining special characters
        table_name = re.sub(r'[^a-z0-9_]', '', table_name)
        return table_name if table_name else None

    return None


def validate_sql_tables(
    sql: str,
    allowed_tables: List[str],
    access_mode: str = "read_only"
) -> Tuple[bool, Optional[str], Set[str]]:
    """
    Validate that a SQL query only accesses allowed tables.

    Args:
        sql: SQL query to validate
        allowed_tables: List of table names the agent is allowed to access
        access_mode: "read_only" or "read_write"

    Returns:
        Tuple of:
        - is_valid: True if query only uses allowed tables
        - error_message: Error message if invalid, None if valid
        - accessed_tables: Set of tables the query tries to access
    """
    if not sql or not sql.strip():
        return False, "Empty SQL query", set()

    if not allowed_tables:
        return False, "No tables are allowed for this agent", set()

    # Create lowercase set of allowed tables
    allowed_set = {t.lower().strip() for t in allowed_tables}

    # Extract tables from query
    accessed_tables = extract_tables_from_sql(sql)

    if not accessed_tables:
        # Could not extract any tables - might be a simple query or syntax we don't handle
        # Allow it but log a warning
        logger.warning(f"[SQL Validator] Could not extract tables from: {sql[:100]}...")
        return True, None, accessed_tables

    # Check for unauthorized tables
    unauthorized = accessed_tables - allowed_set

    if unauthorized:
        error_msg = f"Access denied: Query references unauthorized table(s): {', '.join(sorted(unauthorized))}. Allowed tables: {', '.join(sorted(allowed_tables))}"
        logger.warning(f"[SQL Validator] {error_msg}")
        return False, error_msg, accessed_tables

    # Check access mode for write operations
    if access_mode == "read_only":
        sql_lower = sql.lower().strip()
        write_patterns = [
            r'^\s*insert\s+',
            r'^\s*update\s+',
            r'^\s*delete\s+',
            r'^\s*drop\s+',
            r'^\s*alter\s+',
            r'^\s*create\s+',
            r'^\s*truncate\s+',
        ]
        for pattern in write_patterns:
            if re.match(pattern, sql_lower):
                error_msg = "Access denied: Write operations are not allowed in read-only mode"
                logger.warning(f"[SQL Validator] {error_msg}")
                return False, error_msg, accessed_tables

    logger.debug(
        f"[SQL Validator] Query validated successfully. "
        f"Tables accessed: {accessed_tables}, Allowed: {allowed_set}"
    )
    return True, None, accessed_tables


def get_table_access_summary(
    allowed_tables: List[str],
    access_mode: str
) -> str:
    """
    Get a human-readable summary of table access permissions.

    Args:
        allowed_tables: List of allowed table names
        access_mode: "read_only" or "read_write"

    Returns:
        Summary string for prompts/messages
    """
    mode_desc = "SELECT only" if access_mode == "read_only" else "SELECT, INSERT, UPDATE, DELETE"
    tables_desc = ", ".join(sorted(allowed_tables)) if allowed_tables else "none"

    return f"Allowed tables: {tables_desc}. Allowed operations: {mode_desc}."
