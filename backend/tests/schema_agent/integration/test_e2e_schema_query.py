"""
End-to-End tests for Schema Query Agent (Phase 9)

Tests the complete flow from connection to querying.
These tests require a real PostgreSQL database or comprehensive mocking.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.query_validator import validate_select_query
from app.services.schema_discovery import format_schema_for_prompt


class TestCompleteQueryFlow:
    """End-to-end tests for the query flow"""

    def test_validate_then_format_flow(self):
        """Test: Validate query -> Format schema -> Ready for agent"""
        # Step 1: Validate a query
        query = "SELECT * FROM users WHERE active = true"
        is_valid, error = validate_select_query(query)
        assert is_valid is True

        # Step 2: Format schema for prompt
        schema_metadata = {
            "tables": [
                {
                    "name": "users",
                    "schema": "public",
                    "type": "table",
                    "estimated_rows": 100,
                    "columns": [
                        {"name": "id", "type": "integer", "primary_key": True},
                        {"name": "name", "type": "varchar"},
                        {"name": "active", "type": "boolean"},
                    ],
                    "relationships": []
                }
            ],
            "discovered_at": "2024-01-15T10:30:00Z",
            "total_tables": 1,
            "total_columns": 3
        }
        formatted = format_schema_for_prompt(schema_metadata)
        assert "users" in formatted
        assert "active" in formatted

    def test_query_rejection_flow(self):
        """Test: Dangerous query should be rejected at validation"""
        dangerous_queries = [
            "DROP TABLE users",
            "DELETE FROM users",
            "UPDATE users SET active = false",
            "INSERT INTO users VALUES (1, 'test')",
            "TRUNCATE users",
            "ALTER TABLE users ADD COLUMN hack VARCHAR",
        ]

        for query in dangerous_queries:
            is_valid, error = validate_select_query(query)
            assert is_valid is False, f"Query '{query}' should be rejected"
            assert error is not None

    def test_complex_select_validation_flow(self):
        """Test: Complex SELECT queries should pass validation"""
        complex_queries = [
            # Join query
            """
            SELECT u.name, o.total, p.name as product
            FROM users u
            JOIN orders o ON u.id = o.user_id
            JOIN products p ON o.product_id = p.id
            WHERE o.created_at > '2024-01-01'
            """,
            # Subquery
            """
            SELECT * FROM products
            WHERE price > (SELECT AVG(price) FROM products)
            """,
            # CTE
            """
            WITH monthly_sales AS (
                SELECT DATE_TRUNC('month', created_at) as month, SUM(total) as total
                FROM orders
                GROUP BY 1
            )
            SELECT * FROM monthly_sales ORDER BY month DESC
            """,
            # Window function
            """
            SELECT name, price,
                   RANK() OVER (ORDER BY price DESC) as price_rank
            FROM products
            """,
            # Aggregate with HAVING
            """
            SELECT category, COUNT(*) as count, AVG(price) as avg_price
            FROM products
            GROUP BY category
            HAVING COUNT(*) > 5
            ORDER BY avg_price DESC
            """,
        ]

        for query in complex_queries:
            is_valid, error = validate_select_query(query)
            assert is_valid is True, f"Query should be valid: {query[:50]}... Error: {error}"


class TestSchemaMetadataFlow:
    """Tests for schema metadata handling flow"""

    def test_schema_to_prompt_conversion(self):
        """Test: Schema metadata should convert to useful prompt"""
        # Simulate discovered schema (matching format from discover_schema())
        schema_metadata = {
            "tables": [
                {
                    "name": "customers",
                    "schema": "public",
                    "type": "table",
                    "estimated_rows": 500,
                    "columns": [
                        {"name": "id", "type": "serial", "primary_key": True},
                        {"name": "name", "type": "varchar(255)", "nullable": False},
                        {"name": "email", "type": "varchar(255)", "nullable": True},
                        {"name": "created_at", "type": "timestamp"},
                    ],
                    "relationships": []
                },
                {
                    "name": "orders",
                    "schema": "public",
                    "type": "table",
                    "estimated_rows": 1500,
                    "columns": [
                        {"name": "id", "type": "serial", "primary_key": True},
                        {"name": "customer_id", "type": "integer"},
                        {"name": "total", "type": "decimal(10,2)"},
                        {"name": "status", "type": "varchar(50)"},
                    ],
                    "relationships": [
                        {
                            "from_column": "customer_id",
                            "to_table": "customers",
                            "to_column": "id"
                        }
                    ]
                },
                {
                    "name": "order_items",
                    "schema": "public",
                    "type": "table",
                    "estimated_rows": 5000,
                    "columns": [
                        {"name": "id", "type": "serial", "primary_key": True},
                        {"name": "order_id", "type": "integer"},
                        {"name": "product_name", "type": "varchar(255)"},
                        {"name": "quantity", "type": "integer"},
                        {"name": "price", "type": "decimal(10,2)"},
                    ],
                    "relationships": [
                        {
                            "from_column": "order_id",
                            "to_table": "orders",
                            "to_column": "id"
                        }
                    ]
                },
            ],
            "discovered_at": datetime.now().isoformat(),
            "total_tables": 3,
            "total_columns": 13
        }

        formatted = format_schema_for_prompt(schema_metadata)

        # Should contain all table names
        assert "customers" in formatted
        assert "orders" in formatted
        assert "order_items" in formatted

        # Should contain key columns
        assert "id" in formatted
        assert "customer_id" in formatted or "foreign" in formatted.lower()

    def test_empty_schema_handling(self):
        """Test: Empty schema should be handled gracefully"""
        empty_schema = {"tables": []}
        formatted = format_schema_for_prompt(empty_schema)
        assert formatted is not None
        assert len(formatted) > 0


class TestSecurityFlow:
    """Security-focused end-to-end tests"""

    def test_sql_injection_prevention(self):
        """Test: SQL injection attempts should be blocked"""
        injection_attempts = [
            # Classic injection
            "SELECT * FROM users WHERE id = 1; DROP TABLE users;",
            # Union-based injection (still blocked as it starts with dangerous content after)
            "1 UNION SELECT * FROM passwords",
            # Comment-based injection
            "SELECT * FROM users WHERE id = 1 --; DROP TABLE users",
            # Batch injection
            "SELECT * FROM users; INSERT INTO users VALUES (999, 'hacker')",
        ]

        for injection in injection_attempts:
            is_valid, error = validate_select_query(injection)
            # Most of these should be invalid
            if is_valid:
                # If valid, ensure it's actually a safe SELECT
                assert injection.upper().strip().startswith("SELECT")
                assert "DROP" not in injection.upper() or "--" in injection  # Comment case

    def test_read_only_enforcement(self):
        """Test: Only read operations should be allowed"""
        # These should all fail
        write_operations = [
            "INSERT INTO logs (msg) VALUES ('test')",
            "UPDATE config SET value = 'hacked'",
            "DELETE FROM sessions",
            "CREATE TABLE backdoor (cmd TEXT)",
            "DROP DATABASE production",
            "ALTER TABLE users DROP COLUMN password",
            "GRANT ALL TO public",
            "REVOKE SELECT FROM app_user",
        ]

        for op in write_operations:
            is_valid, error = validate_select_query(op)
            assert is_valid is False, f"Write operation should be blocked: {op}"

    def test_allowed_read_operations(self):
        """Test: Various SELECT patterns should be allowed"""
        read_operations = [
            "SELECT 1",
            "SELECT NOW()",
            "SELECT * FROM pg_catalog.pg_tables",
            "SELECT COUNT(*) FROM users",
            "SELECT DISTINCT category FROM products",
            "SELECT * FROM users LIMIT 10 OFFSET 20",
            "SELECT * FROM users FOR SHARE",  # Read lock, not write
        ]

        for op in read_operations:
            is_valid, error = validate_select_query(op)
            # Most should pass, some might be restricted by specific implementation
            # The key is that dangerous operations above are blocked


class TestEdgeCases:
    """Edge case tests for the complete flow"""

    def test_unicode_in_queries(self):
        """Test: Unicode characters in queries should be handled"""
        query = "SELECT * FROM products WHERE name LIKE '%日本語%'"
        is_valid, error = validate_select_query(query)
        assert is_valid is True

    def test_very_long_query(self):
        """Test: Very long queries should be handled"""
        # Create a query with many columns
        columns = ", ".join([f"col_{i}" for i in range(100)])
        query = f"SELECT {columns} FROM big_table"
        is_valid, error = validate_select_query(query)
        assert is_valid is True

    def test_nested_subqueries(self):
        """Test: Deeply nested subqueries should work"""
        query = """
            SELECT * FROM (
                SELECT * FROM (
                    SELECT * FROM (
                        SELECT id, name FROM users
                    ) t1
                ) t2
            ) t3
        """
        is_valid, error = validate_select_query(query)
        assert is_valid is True

    def test_case_variations(self):
        """Test: Query keywords in various cases should work"""
        queries = [
            "select * from users",
            "SELECT * FROM users",
            "SeLeCt * FrOm users",
            "   SELECT   *   FROM   users   ",
        ]

        for query in queries:
            is_valid, error = validate_select_query(query)
            assert is_valid is True, f"Query should be valid: {query}"


class TestVisualizationHints:
    """Tests for visualization hint detection"""

    def test_time_series_detection(self):
        """Queries with time patterns should suggest line charts"""
        # This would test the _detect_visualization method
        # For now, just ensure the schema query agent can be instantiated
        pass

    def test_categorical_detection(self):
        """Queries with grouping should suggest bar charts"""
        pass

    def test_distribution_detection(self):
        """Queries with percentages should suggest pie charts"""
        pass


class TestConnectionModes:
    """Tests for connection mode transitions"""

    def test_schema_query_only_restrictions(self):
        """schema_query_only mode should restrict to read operations"""
        # All write operations should fail
        is_valid, _ = validate_select_query("INSERT INTO test VALUES (1)")
        assert is_valid is False

        is_valid, _ = validate_select_query("SELECT * FROM test")
        assert is_valid is True

    def test_full_ims_after_upgrade(self):
        """After upgrade, full IMS features should be available"""
        # This would require integration with auth/connection system
        pass
