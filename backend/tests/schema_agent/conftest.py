"""
Pytest configuration for Schema Agent tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_database_uri():
    """Mock PostgreSQL database URI"""
    return "postgresql://test_user:test_pass@localhost:5432/test_db"


@pytest.fixture
def mock_schema_metadata():
    """Mock schema metadata for testing"""
    return {
        "tables": [
            {
                "name": "users",
                "type": "table",
                "column_count": 4,
                "columns": [
                    {"name": "id", "type": "integer", "primary_key": True, "nullable": False},
                    {"name": "name", "type": "varchar(255)", "nullable": False},
                    {"name": "email", "type": "varchar(255)", "nullable": True},
                    {"name": "created_at", "type": "timestamp", "nullable": False},
                ]
            },
            {
                "name": "orders",
                "type": "table",
                "column_count": 5,
                "columns": [
                    {"name": "id", "type": "integer", "primary_key": True, "nullable": False},
                    {"name": "user_id", "type": "integer", "foreign_key": "users.id", "nullable": False},
                    {"name": "total", "type": "decimal(10,2)", "nullable": False},
                    {"name": "status", "type": "varchar(50)", "nullable": False},
                    {"name": "created_at", "type": "timestamp", "nullable": False},
                ]
            },
        ],
        "table_count": 2,
        "discovered_at": "2024-01-15T10:30:00Z",
    }


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    user.connection_type = "schema_query_only"
    user.database_uri = "postgresql://test:test@localhost/testdb"
    return user


@pytest.fixture
def mock_connection_status():
    """Mock connection status"""
    return {
        "connected": True,
        "connection_type": "schema_query_only",
        "schema_status": "ready",
        "table_count": 5,
    }


@pytest.fixture
def sample_queries():
    """Sample queries for testing"""
    return {
        "valid": [
            "SELECT * FROM users",
            "SELECT id, name FROM users WHERE active = true",
            "SELECT COUNT(*) FROM orders GROUP BY status",
            "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id",
        ],
        "invalid": [
            "INSERT INTO users (name) VALUES ('test')",
            "UPDATE users SET name = 'hacked'",
            "DELETE FROM users WHERE id = 1",
            "DROP TABLE users",
            "TRUNCATE TABLE orders",
        ],
    }


# Test markers
def pytest_configure(config):
    """Register pytest markers for schema agent tests"""
    config.addinivalue_line("markers", "schema_agent: mark test as schema agent test")
    config.addinivalue_line("markers", "query_validation: mark test as query validation test")
    config.addinivalue_line("markers", "schema_discovery: mark test as schema discovery test")
