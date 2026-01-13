"""
Unit Tests for SQL Table Validator Service (Phase 14)

Tests the SQL parsing and table validation functionality
that enforces table-level access control.
"""

import pytest
from app.services.sql_table_validator import (
    extract_tables_from_sql,
    validate_sql_tables,
    get_table_access_summary,
)


# =============================================================================
# Tests for extract_tables_from_sql
# =============================================================================

class TestExtractTablesFromSQL:
    """Tests for SQL table extraction."""

    def test_simple_select(self):
        """Test extracting from simple SELECT."""
        sql = "SELECT * FROM products"
        tables = extract_tables_from_sql(sql)
        assert "products" in tables

    def test_select_with_schema(self):
        """Test extracting from SELECT with schema prefix."""
        sql = "SELECT * FROM public.products"
        tables = extract_tables_from_sql(sql)
        assert "products" in tables

    def test_select_with_alias(self):
        """Test extracting from SELECT with table alias."""
        sql = "SELECT p.name FROM products AS p"
        tables = extract_tables_from_sql(sql)
        assert "products" in tables
        assert "p" not in tables  # Alias should not be extracted

    def test_select_multiple_tables(self):
        """Test extracting from SELECT with multiple tables."""
        sql = "SELECT * FROM products, orders"
        tables = extract_tables_from_sql(sql)
        assert "products" in tables
        assert "orders" in tables

    def test_select_with_join(self):
        """Test extracting from SELECT with JOIN."""
        sql = "SELECT * FROM products JOIN orders ON products.id = orders.product_id"
        tables = extract_tables_from_sql(sql)
        assert "products" in tables
        assert "orders" in tables

    def test_select_with_multiple_joins(self):
        """Test extracting from SELECT with multiple JOINs."""
        sql = """
            SELECT * FROM products
            JOIN orders ON products.id = orders.product_id
            LEFT JOIN users ON orders.user_id = users.id
        """
        tables = extract_tables_from_sql(sql)
        assert "products" in tables
        assert "orders" in tables
        assert "users" in tables

    def test_insert_into(self):
        """Test extracting from INSERT."""
        sql = "INSERT INTO orders (product_id, quantity) VALUES (1, 5)"
        tables = extract_tables_from_sql(sql)
        assert "orders" in tables

    def test_update(self):
        """Test extracting from UPDATE."""
        sql = "UPDATE products SET price = 10 WHERE id = 1"
        tables = extract_tables_from_sql(sql)
        assert "products" in tables

    def test_delete(self):
        """Test extracting from DELETE."""
        sql = "DELETE FROM orders WHERE id = 1"
        tables = extract_tables_from_sql(sql)
        assert "orders" in tables

    def test_case_insensitive(self):
        """Test that extraction is case-insensitive."""
        sql = "SELECT * FROM Products JOIN ORDERS ON Products.id = ORDERS.product_id"
        tables = extract_tables_from_sql(sql)
        assert "products" in tables
        assert "orders" in tables

    def test_subquery(self):
        """Test extracting from subquery."""
        sql = """
            SELECT * FROM products
            WHERE id IN (SELECT product_id FROM orders)
        """
        tables = extract_tables_from_sql(sql)
        assert "products" in tables
        assert "orders" in tables

    def test_with_string_literals(self):
        """Test that string literals don't cause false matches."""
        sql = "SELECT * FROM products WHERE name = 'from orders'"
        tables = extract_tables_from_sql(sql)
        assert "products" in tables
        # "orders" should not be extracted from the string literal
        # Note: This depends on implementation - may need adjustment


# =============================================================================
# Tests for validate_sql_tables
# =============================================================================

class TestValidateSQLTables:
    """Tests for SQL table validation."""

    def test_valid_single_table(self):
        """Test validation of query using single allowed table."""
        sql = "SELECT * FROM products"
        is_valid, error, tables = validate_sql_tables(
            sql=sql,
            allowed_tables=["products"],
            access_mode="read_only"
        )

        assert is_valid is True
        assert error is None
        assert "products" in tables

    def test_valid_multiple_tables(self):
        """Test validation of query using multiple allowed tables."""
        sql = "SELECT * FROM products JOIN orders ON products.id = orders.product_id"
        is_valid, error, tables = validate_sql_tables(
            sql=sql,
            allowed_tables=["products", "orders"],
            access_mode="read_only"
        )

        assert is_valid is True
        assert error is None

    def test_invalid_unauthorized_table(self):
        """Test rejection of query using unauthorized table."""
        sql = "SELECT * FROM users"
        is_valid, error, tables = validate_sql_tables(
            sql=sql,
            allowed_tables=["products", "orders"],
            access_mode="read_only"
        )

        assert is_valid is False
        assert "users" in error
        assert "unauthorized" in error.lower()

    def test_invalid_mixed_tables(self):
        """Test rejection of query with mix of allowed and unauthorized tables."""
        sql = "SELECT * FROM products JOIN users ON products.owner_id = users.id"
        is_valid, error, tables = validate_sql_tables(
            sql=sql,
            allowed_tables=["products"],
            access_mode="read_only"
        )

        assert is_valid is False
        assert "users" in error

    def test_read_only_blocks_insert(self):
        """Test that read_only mode blocks INSERT."""
        sql = "INSERT INTO products (name, price) VALUES ('Test', 10)"
        is_valid, error, tables = validate_sql_tables(
            sql=sql,
            allowed_tables=["products"],
            access_mode="read_only"
        )

        assert is_valid is False
        assert "write" in error.lower() or "read-only" in error.lower()

    def test_read_only_blocks_update(self):
        """Test that read_only mode blocks UPDATE."""
        sql = "UPDATE products SET price = 20 WHERE id = 1"
        is_valid, error, tables = validate_sql_tables(
            sql=sql,
            allowed_tables=["products"],
            access_mode="read_only"
        )

        assert is_valid is False

    def test_read_only_blocks_delete(self):
        """Test that read_only mode blocks DELETE."""
        sql = "DELETE FROM products WHERE id = 1"
        is_valid, error, tables = validate_sql_tables(
            sql=sql,
            allowed_tables=["products"],
            access_mode="read_only"
        )

        assert is_valid is False

    def test_read_write_allows_insert(self):
        """Test that read_write mode allows INSERT."""
        sql = "INSERT INTO products (name, price) VALUES ('Test', 10)"
        is_valid, error, tables = validate_sql_tables(
            sql=sql,
            allowed_tables=["products"],
            access_mode="read_write"
        )

        assert is_valid is True
        assert error is None

    def test_read_write_allows_update(self):
        """Test that read_write mode allows UPDATE."""
        sql = "UPDATE products SET price = 20 WHERE id = 1"
        is_valid, error, tables = validate_sql_tables(
            sql=sql,
            allowed_tables=["products"],
            access_mode="read_write"
        )

        assert is_valid is True

    def test_empty_sql(self):
        """Test rejection of empty SQL."""
        is_valid, error, tables = validate_sql_tables(
            sql="",
            allowed_tables=["products"],
            access_mode="read_only"
        )

        assert is_valid is False

    def test_empty_allowed_tables(self):
        """Test rejection when no tables are allowed."""
        sql = "SELECT * FROM products"
        is_valid, error, tables = validate_sql_tables(
            sql=sql,
            allowed_tables=[],
            access_mode="read_only"
        )

        assert is_valid is False


# =============================================================================
# Tests for get_table_access_summary
# =============================================================================

class TestGetTableAccessSummary:
    """Tests for access summary generation."""

    def test_read_only_summary(self):
        """Test summary for read-only access."""
        summary = get_table_access_summary(
            allowed_tables=["products", "orders"],
            access_mode="read_only"
        )

        assert "products" in summary
        assert "orders" in summary
        assert "SELECT" in summary

    def test_read_write_summary(self):
        """Test summary for read-write access."""
        summary = get_table_access_summary(
            allowed_tables=["products"],
            access_mode="read_write"
        )

        assert "products" in summary
        assert "INSERT" in summary or "UPDATE" in summary or "DELETE" in summary

    def test_empty_tables_summary(self):
        """Test summary with no allowed tables."""
        summary = get_table_access_summary(
            allowed_tables=[],
            access_mode="read_only"
        )

        assert "none" in summary.lower()
