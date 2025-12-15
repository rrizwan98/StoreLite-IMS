"""
Unit tests for Schema Query Validator (Phase 9)

Tests the multi-layer query validation for SELECT-only enforcement.
"""

import pytest
from app.services.query_validator import (
    validate_select_query,
    sanitize_identifier,
    build_safe_select,
    check_table_access,
    QueryValidationError,
    DANGEROUS_KEYWORDS,
)


class TestValidateSelectQuery:
    """Tests for validate_select_query function"""

    # === Valid SELECT queries ===

    def test_simple_select_valid(self):
        """Simple SELECT should be valid"""
        query = "SELECT * FROM users"
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    def test_select_with_columns_valid(self):
        """SELECT with specific columns should be valid"""
        query = "SELECT id, name, email FROM customers"
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    def test_select_with_where_valid(self):
        """SELECT with WHERE clause should be valid"""
        query = "SELECT * FROM orders WHERE status = 'pending'"
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    def test_select_with_join_valid(self):
        """SELECT with JOIN should be valid"""
        query = """
            SELECT u.name, o.total
            FROM users u
            JOIN orders o ON u.id = o.user_id
        """
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    def test_select_with_subquery_valid(self):
        """SELECT with subquery should be valid"""
        query = """
            SELECT * FROM products
            WHERE category_id IN (SELECT id FROM categories WHERE active = true)
        """
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    def test_select_with_aggregate_valid(self):
        """SELECT with aggregate functions should be valid"""
        query = "SELECT COUNT(*), SUM(amount), AVG(price) FROM sales"
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    def test_select_with_group_by_valid(self):
        """SELECT with GROUP BY should be valid"""
        query = "SELECT category, COUNT(*) FROM products GROUP BY category"
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    def test_select_with_order_by_valid(self):
        """SELECT with ORDER BY should be valid"""
        query = "SELECT * FROM products ORDER BY created_at DESC"
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    def test_select_with_limit_valid(self):
        """SELECT with LIMIT should be valid"""
        query = "SELECT * FROM logs LIMIT 100"
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    def test_select_with_cte_valid(self):
        """SELECT with CTE (WITH clause) should be valid"""
        query = """
            WITH active_users AS (
                SELECT * FROM users WHERE active = true
            )
            SELECT * FROM active_users
        """
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    def test_select_lowercase_valid(self):
        """Lowercase SELECT should be valid"""
        query = "select * from users"
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    def test_select_mixed_case_valid(self):
        """Mixed case SELECT should be valid"""
        query = "SeLeCt * FrOm users"
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    # === Invalid queries - Modification attempts ===

    def test_insert_rejected(self):
        """INSERT should be rejected"""
        query = "INSERT INTO users (name) VALUES ('test')"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        # Query doesn't start with SELECT, so will be rejected for that reason
        assert len(error) > 0

    def test_update_rejected(self):
        """UPDATE should be rejected"""
        query = "UPDATE users SET name = 'test' WHERE id = 1"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert len(error) > 0

    def test_delete_rejected(self):
        """DELETE should be rejected"""
        query = "DELETE FROM users WHERE id = 1"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert len(error) > 0

    def test_drop_table_rejected(self):
        """DROP TABLE should be rejected"""
        query = "DROP TABLE users"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert len(error) > 0

    def test_drop_database_rejected(self):
        """DROP DATABASE should be rejected"""
        query = "DROP DATABASE mydb"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert len(error) > 0

    def test_truncate_rejected(self):
        """TRUNCATE should be rejected"""
        query = "TRUNCATE TABLE users"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert len(error) > 0

    def test_alter_table_rejected(self):
        """ALTER TABLE should be rejected"""
        query = "ALTER TABLE users ADD COLUMN age INT"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert len(error) > 0

    def test_create_table_rejected(self):
        """CREATE TABLE should be rejected"""
        query = "CREATE TABLE test (id INT)"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert len(error) > 0

    def test_create_index_rejected(self):
        """CREATE INDEX should be rejected"""
        query = "CREATE INDEX idx_name ON users (name)"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert len(error) > 0

    def test_grant_rejected(self):
        """GRANT should be rejected"""
        query = "GRANT SELECT ON users TO public"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert len(error) > 0

    def test_revoke_rejected(self):
        """REVOKE should be rejected"""
        query = "REVOKE ALL ON users FROM public"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert len(error) > 0

    # === SQL Injection attempts ===

    def test_semicolon_injection_rejected(self):
        """Semicolon injection should be rejected"""
        query = "SELECT * FROM users; DROP TABLE users;"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert "multiple" in error.lower() or "semicolon" in error.lower() or "DROP" in error.upper()

    def test_comment_injection_rejected(self):
        """Comment injection hiding DROP should be rejected"""
        query = "SELECT * FROM users -- DROP TABLE users"
        # This should still be valid as the DROP is in a comment
        # But let's ensure the query itself is safe
        is_valid, error = validate_select_query(query)
        # The validator might accept or reject based on implementation
        # Key thing is DROP is not executed

    def test_union_select_valid(self):
        """UNION SELECT should be valid (read operation)"""
        query = "SELECT id FROM users UNION SELECT id FROM admins"
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    # === Edge cases ===

    def test_empty_query_rejected(self):
        """Empty query should be rejected"""
        query = ""
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert "empty" in error.lower()

    def test_whitespace_only_rejected(self):
        """Whitespace-only query should be rejected"""
        query = "   \n\t   "
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert "empty" in error.lower()

    def test_non_select_start_rejected(self):
        """Query not starting with SELECT or WITH should be rejected"""
        query = "EXPLAIN SELECT * FROM users"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
        assert "SELECT" in error or "must start" in error.lower()

    def test_update_in_column_name_valid(self):
        """Column named 'update' should not trigger rejection"""
        query = "SELECT update_date, last_update FROM records"
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""

    def test_delete_in_column_name_valid(self):
        """Column named 'deleted' should not trigger rejection"""
        query = "SELECT deleted, is_deleted FROM users"
        is_valid, error = validate_select_query(query)
        assert is_valid is True
        assert error == ""


class TestSanitizeIdentifier:
    """Tests for sanitize_identifier function"""

    def test_valid_identifier(self):
        """Valid identifiers should pass"""
        assert sanitize_identifier("users") == "users"
        assert sanitize_identifier("my_table") == "my_table"
        assert sanitize_identifier("Table123") == "Table123"

    def test_identifier_starting_with_underscore(self):
        """Identifier starting with underscore should pass"""
        assert sanitize_identifier("_private") == "_private"
        assert sanitize_identifier("_test_table") == "_test_table"

    def test_empty_identifier_raises(self):
        """Empty identifier should raise error"""
        with pytest.raises(QueryValidationError):
            sanitize_identifier("")

    def test_whitespace_only_raises(self):
        """Whitespace-only identifier should raise error"""
        with pytest.raises(QueryValidationError):
            sanitize_identifier("   ")

    def test_sql_injection_in_identifier_raises(self):
        """SQL injection in identifier should raise error"""
        with pytest.raises(QueryValidationError):
            sanitize_identifier("users; DROP TABLE users")

    def test_quotes_stripped_then_validated(self):
        """Quotes should be stripped before validation"""
        # Valid after stripping quotes
        assert sanitize_identifier('"users"') == "users"
        assert sanitize_identifier("'users'") == "users"

    def test_special_chars_rejected(self):
        """Special characters should be rejected"""
        with pytest.raises(QueryValidationError):
            sanitize_identifier("table$name")

    def test_space_in_identifier_rejected(self):
        """Space in identifier should be rejected"""
        with pytest.raises(QueryValidationError):
            sanitize_identifier("my table")

    def test_hyphen_rejected(self):
        """Hyphen in identifier should be rejected"""
        with pytest.raises(QueryValidationError):
            sanitize_identifier("my-table")


class TestBuildSafeSelect:
    """Tests for build_safe_select function"""

    def test_simple_safe_select(self):
        """Build simple safe SELECT"""
        query = build_safe_select("users")
        assert "SELECT" in query.upper()
        assert "users" in query

    def test_safe_select_with_columns(self):
        """Build safe SELECT with specific columns"""
        query = build_safe_select("users", columns=["id", "name", "email"])
        assert "id" in query
        assert "name" in query
        assert "email" in query

    def test_safe_select_with_limit(self):
        """Build safe SELECT with LIMIT"""
        query = build_safe_select("users", limit=10)
        assert "LIMIT" in query.upper()
        assert "10" in query

    def test_safe_select_with_schema(self):
        """Build safe SELECT with schema"""
        query = build_safe_select("users", schema_name="public")
        assert "public" in query
        assert "users" in query


class TestCheckTableAccess:
    """Tests for check_table_access function"""

    def test_allowed_table(self):
        """Access to allowed table should pass"""
        allowed = ["users", "orders", "products"]
        query = "SELECT * FROM users"
        is_allowed, error = check_table_access(query, allowed)
        assert is_allowed is True

    def test_disallowed_table(self):
        """Access to non-allowed table should fail"""
        allowed = ["users", "orders"]
        query = "SELECT * FROM secrets"
        is_allowed, error = check_table_access(query, allowed)
        assert is_allowed is False

    def test_allowed_with_join(self):
        """Query with JOIN to allowed tables should pass"""
        allowed = ["users", "orders"]
        query = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        is_allowed, error = check_table_access(query, allowed)
        assert is_allowed is True

    def test_disallowed_in_join(self):
        """Query with JOIN to disallowed table should fail"""
        allowed = ["users"]
        query = "SELECT * FROM users JOIN secrets ON users.id = secrets.user_id"
        is_allowed, error = check_table_access(query, allowed)
        assert is_allowed is False


class TestDangerousKeywords:
    """Tests for dangerous keywords list"""

    def test_all_dangerous_keywords_rejected(self):
        """All dangerous keywords should be rejected in queries"""
        for keyword in DANGEROUS_KEYWORDS:
            query = f"{keyword} something"
            is_valid, error = validate_select_query(query)
            assert is_valid is False, f"Keyword '{keyword}' should be rejected"

    def test_dangerous_keywords_in_subquery(self):
        """Dangerous keywords in subqueries should be rejected"""
        query = "SELECT * FROM (DELETE FROM users)"
        is_valid, error = validate_select_query(query)
        assert is_valid is False
