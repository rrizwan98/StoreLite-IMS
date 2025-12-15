"""
Query Validator Service for Schema Query Agent (Phase 9)

Ensures only SELECT queries are executed against user's database.
Multi-layer validation for security.
"""

import re
from typing import Tuple


# Dangerous SQL keywords that should never be in a query
DANGEROUS_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
    "TRUNCATE", "GRANT", "REVOKE", "EXECUTE", "CALL",
    "COPY", "VACUUM", "REINDEX", "CLUSTER", "COMMENT",
    "LOCK", "UNLISTEN", "NOTIFY", "LISTEN", "LOAD",
    "SECURITY", "OWNER", "SET ROLE", "RESET ROLE"
]

# Pattern to detect potential SQL injection attempts
INJECTION_PATTERNS = [
    r";\s*(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)",  # Chained dangerous commands
    r"--\s*$",  # SQL comment at end (potential injection)
    r"/\*.*\*/",  # Block comments (potential injection)
    r"'\s*OR\s+'",  # Classic OR injection
    r"'\s*OR\s+1\s*=\s*1",  # OR 1=1 injection
    r"UNION\s+ALL\s+SELECT.*FROM\s+pg_",  # Union injection to system tables
]


class QueryValidationError(Exception):
    """Raised when query validation fails"""
    def __init__(self, message: str, reason: str = "validation_failed"):
        self.message = message
        self.reason = reason
        super().__init__(message)


def validate_select_query(query: str) -> Tuple[bool, str]:
    """
    Validate that a query is a safe SELECT statement.

    Multi-layer validation:
    1. Quick check: Must start with SELECT
    2. Dangerous keyword scan
    3. Injection pattern detection

    Args:
        query: SQL query string

    Returns:
        Tuple of (is_valid, error_message)
        If valid: (True, "")
        If invalid: (False, "reason for rejection")
    """
    if not query or not query.strip():
        return False, "Query cannot be empty"

    # Normalize query for checking
    normalized = query.strip().upper()

    # Layer 1: Must start with SELECT or WITH (for CTEs)
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        return False, "Only SELECT queries are allowed. Query must start with SELECT or WITH."

    # Layer 2: Check for dangerous keywords
    for keyword in DANGEROUS_KEYWORDS:
        # Use word boundary to avoid false positives (e.g., "UPDATED_AT" column)
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, normalized):
            return False, f"Query contains forbidden keyword: {keyword}. Only SELECT queries are allowed."

    # Layer 3: Check for injection patterns
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return False, "Query contains potentially unsafe pattern. Please simplify your query."

    # Layer 4: Check for multiple statements (semicolon not at end)
    # Remove string literals first to avoid false positives
    query_without_strings = re.sub(r"'[^']*'", "", query)
    semicolons = query_without_strings.count(";")
    if semicolons > 1 or (semicolons == 1 and not query_without_strings.strip().endswith(";")):
        return False, "Multiple SQL statements are not allowed. Please use a single SELECT query."

    # Layer 5: Check for system catalog access (optional - can be relaxed)
    # if re.search(r"\bpg_catalog\b|\binformation_schema\b", normalized):
    #     return False, "Direct access to system catalogs is not allowed."

    return True, ""


def sanitize_identifier(identifier: str) -> str:
    """
    Sanitize a SQL identifier (table name, column name, schema name).

    Args:
        identifier: Raw identifier string

    Returns:
        Sanitized identifier safe for use in queries
    """
    # Remove any quotes first
    clean = identifier.strip().strip('"').strip("'")

    # Only allow alphanumeric, underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', clean):
        raise QueryValidationError(
            f"Invalid identifier: {identifier}. Only alphanumeric characters and underscores allowed.",
            reason="invalid_identifier"
        )

    return clean


def build_safe_select(
    table_name: str,
    schema_name: str = "public",
    columns: list[str] = None,
    limit: int = 100
) -> str:
    """
    Build a safe SELECT query with sanitized identifiers.

    Args:
        table_name: Table name
        schema_name: Schema name (default: public)
        columns: List of column names (default: *)
        limit: Row limit (default: 100)

    Returns:
        Safe SQL query string
    """
    safe_schema = sanitize_identifier(schema_name)
    safe_table = sanitize_identifier(table_name)

    if columns:
        safe_columns = ", ".join(f'"{sanitize_identifier(c)}"' for c in columns)
    else:
        safe_columns = "*"

    return f'SELECT {safe_columns} FROM "{safe_schema}"."{safe_table}" LIMIT {min(limit, 10000)}'


def extract_tables_from_query(query: str) -> list[str]:
    """
    Extract table names from a SELECT query.
    Used for access control validation.

    Args:
        query: SQL query string

    Returns:
        List of table names found in the query
    """
    # Simple regex to find table names after FROM and JOIN
    # This is a basic implementation - production should use SQL parser
    pattern = r'\b(?:FROM|JOIN)\s+(?:"?(\w+)"?\.)?\"?(\w+)\"?'
    matches = re.findall(pattern, query, re.IGNORECASE)

    tables = []
    for schema, table in matches:
        if table.upper() not in ["SELECT", "WHERE", "AND", "OR", "ON"]:
            full_name = f"{schema}.{table}" if schema else table
            tables.append(full_name)

    return list(set(tables))


def check_table_access(
    query: str,
    allowed_tables: list[str],
    allowed_schemas: list[str] = None
) -> Tuple[bool, str]:
    """
    Check if query only accesses allowed tables.

    Args:
        query: SQL query string
        allowed_tables: List of allowed table names
        allowed_schemas: List of allowed schema names

    Returns:
        Tuple of (is_allowed, error_message)
    """
    if allowed_schemas is None:
        allowed_schemas = ["public"]

    tables_in_query = extract_tables_from_query(query)

    # Normalize allowed tables to include schema
    normalized_allowed = set()
    for table in allowed_tables:
        if "." in table:
            normalized_allowed.add(table.lower())
        else:
            for schema in allowed_schemas:
                normalized_allowed.add(f"{schema}.{table}".lower())
                normalized_allowed.add(table.lower())

    for table in tables_in_query:
        table_lower = table.lower()
        # Check if table is in allowed list
        if table_lower not in normalized_allowed:
            # Also check without schema prefix
            table_only = table_lower.split(".")[-1] if "." in table_lower else table_lower
            if table_only not in normalized_allowed:
                return False, f"Access to table '{table}' is not allowed."

    return True, ""
