"""
Unit tests for Schema Discovery Service (Phase 9)

Tests the database schema discovery functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.schema_discovery import (
    test_connection as check_connection,  # Renamed to avoid pytest collection
    discover_schema,
    get_table_sample,
    get_table_stats,
    format_schema_for_prompt,
    SchemaDiscoveryError,
    TooManyTablesError,
    MAX_TABLES_LIMIT,
)


class TestTestConnection:
    """Tests for test_connection function"""

    @pytest.mark.asyncio
    async def test_valid_connection(self):
        """Valid connection should return success"""
        with patch('app.services.schema_discovery.asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(side_effect=[
                "PostgreSQL 15.2",  # version
                "testdb",            # database name
                "testuser"           # current user
            ])
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await check_connection("postgresql://user:pass@localhost/db")

            assert result["status"] == "success"
            assert "successful" in result.get("message", "").lower()
            mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_connection_string(self):
        """Invalid connection string should return failure"""
        with patch('app.services.schema_discovery.asyncpg.connect') as mock_connect:
            mock_connect.side_effect = Exception("Connection refused")

            result = await check_connection("invalid://string")

            assert result["status"] == "error"
            assert "message" in result

    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Connection timeout should return failure"""
        with patch('app.services.schema_discovery.asyncpg.connect') as mock_connect:
            import asyncio
            mock_connect.side_effect = asyncio.TimeoutError()

            result = await check_connection("postgresql://user:pass@localhost/db")

            assert result["status"] == "error"


class TestDiscoverSchema:
    """Tests for discover_schema function"""

    @pytest.mark.asyncio
    async def test_discover_schema_basic(self):
        """Basic schema discovery should work"""
        with patch('app.services.schema_discovery.asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()

            # Mock tables query (includes table_schema)
            mock_conn.fetch = AsyncMock(side_effect=[
                # Tables from information_schema.tables
                [
                    {"table_schema": "public", "table_name": "users", "table_type": "BASE TABLE"},
                    {"table_schema": "public", "table_name": "orders", "table_type": "BASE TABLE"},
                ],
                # Columns for users
                [
                    {"column_name": "id", "data_type": "integer", "is_nullable": "NO",
                     "column_default": None, "character_maximum_length": None,
                     "numeric_precision": None, "numeric_scale": None, "is_primary_key": True},
                    {"column_name": "name", "data_type": "varchar", "is_nullable": "YES",
                     "column_default": None, "character_maximum_length": 255,
                     "numeric_precision": None, "numeric_scale": None, "is_primary_key": False},
                ],
                # Columns for orders
                [
                    {"column_name": "id", "data_type": "integer", "is_nullable": "NO",
                     "column_default": None, "character_maximum_length": None,
                     "numeric_precision": None, "numeric_scale": None, "is_primary_key": True},
                    {"column_name": "user_id", "data_type": "integer", "is_nullable": "NO",
                     "column_default": None, "character_maximum_length": None,
                     "numeric_precision": None, "numeric_scale": None, "is_primary_key": False},
                ],
                # Foreign keys
                []
            ])
            # Mock fetchval for row count estimates
            mock_conn.fetchval = AsyncMock(return_value=100)
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await discover_schema("postgresql://user:pass@localhost/db")

            assert "tables" in result
            assert len(result["tables"]) == 2

    @pytest.mark.asyncio
    async def test_discover_schema_empty_database(self):
        """Empty database should return empty schema"""
        with patch('app.services.schema_discovery.asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[])
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await discover_schema("postgresql://user:pass@localhost/db")

            assert "tables" in result
            assert len(result["tables"]) == 0

    @pytest.mark.asyncio
    async def test_discover_schema_too_many_tables(self):
        """Too many tables should raise TooManyTablesError"""
        with patch('app.services.schema_discovery.asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()

            # Create more tables than limit (include table_schema)
            too_many_tables = [
                {"table_schema": "public", "table_name": f"table_{i}", "table_type": "BASE TABLE"}
                for i in range(MAX_TABLES_LIMIT + 10)
            ]
            mock_conn.fetch = AsyncMock(return_value=too_many_tables)
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            with pytest.raises(TooManyTablesError):
                await discover_schema("postgresql://user:pass@localhost/db")

    @pytest.mark.asyncio
    async def test_discover_schema_with_allowed_schemas(self):
        """Schema discovery should respect allowed_schemas parameter"""
        with patch('app.services.schema_discovery.asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[])
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            await discover_schema(
                "postgresql://user:pass@localhost/db",
                allowed_schemas=["public", "sales"]
            )

            # Verify the query was called
            mock_conn.fetch.assert_called()


class TestGetTableSample:
    """Tests for get_table_sample function"""

    @pytest.mark.asyncio
    async def test_get_sample_data(self):
        """Should return sample data from table"""
        with patch('app.services.schema_discovery.asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[
                {"id": 1, "name": "Test 1"},
                {"id": 2, "name": "Test 2"},
            ])
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await get_table_sample(
                "postgresql://user:pass@localhost/db",
                "users"
            )

            assert len(result) == 2
            assert result[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_get_sample_respects_limit(self):
        """Should respect the limit parameter"""
        with patch('app.services.schema_discovery.asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[{"id": 1}])
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            await get_table_sample(
                "postgresql://user:pass@localhost/db",
                "users",
                limit=5
            )

            # Verify LIMIT was used in query
            call_args = mock_conn.fetch.call_args
            assert "5" in str(call_args) or call_args[0][1] == 5

    @pytest.mark.asyncio
    async def test_get_sample_empty_table(self):
        """Empty table should return empty list"""
        with patch('app.services.schema_discovery.asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[])
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await get_table_sample(
                "postgresql://user:pass@localhost/db",
                "users"
            )

            assert result == []


class TestGetTableStats:
    """Tests for get_table_stats function"""

    @pytest.mark.asyncio
    async def test_get_stats_basic(self):
        """Should return basic table statistics"""
        with patch('app.services.schema_discovery.asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            # Mock _get_row_count_estimate return
            mock_conn.fetchval = AsyncMock(side_effect=[
                1000,      # estimated rows from pg_class
                "100 kB",  # size from pg_size_pretty
                5,         # column count
                2,         # index count
            ])
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            result = await get_table_stats(
                "postgresql://user:pass@localhost/db",
                "users"
            )

            assert "estimated_rows" in result
            assert result["estimated_rows"] == 1000

    @pytest.mark.asyncio
    async def test_get_stats_nonexistent_table(self):
        """Non-existent table should raise error"""
        with patch('app.services.schema_discovery.asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            # Simulate an error when querying nonexistent table
            mock_conn.fetchval = AsyncMock(side_effect=Exception("relation does not exist"))
            mock_conn.close = AsyncMock()
            mock_connect.return_value = mock_conn

            with pytest.raises(SchemaDiscoveryError):
                await get_table_stats(
                    "postgresql://user:pass@localhost/db",
                    "nonexistent_table"
                )


class TestFormatSchemaForPrompt:
    """Tests for format_schema_for_prompt function"""

    def test_format_basic_schema(self):
        """Should format basic schema for AI prompt"""
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
                    ],
                    "relationships": []
                }
            ],
            "total_tables": 1,
            "total_columns": 2
        }

        result = format_schema_for_prompt(schema_metadata)

        assert "users" in result
        assert "id" in result
        assert "name" in result
        assert "integer" in result.lower() or "int" in result.lower()

    def test_format_schema_with_foreign_keys(self):
        """Should include foreign key information"""
        schema_metadata = {
            "tables": [
                {
                    "name": "orders",
                    "schema": "public",
                    "type": "table",
                    "estimated_rows": 50,
                    "columns": [
                        {"name": "id", "type": "integer", "primary_key": True},
                        {"name": "user_id", "type": "integer"},
                    ],
                    "relationships": [
                        {
                            "from_column": "user_id",
                            "to_table": "users",
                            "to_column": "id"
                        }
                    ]
                }
            ],
            "total_tables": 1,
            "total_columns": 2
        }

        result = format_schema_for_prompt(schema_metadata)

        assert "orders" in result
        assert "user_id" in result
        assert "users" in result or "foreign" in result.lower()

    def test_format_empty_schema(self):
        """Empty schema should return meaningful message"""
        schema_metadata = {"tables": []}

        result = format_schema_for_prompt(schema_metadata)

        assert result is not None
        assert len(result) > 0

    def test_format_schema_multiple_tables(self):
        """Should format multiple tables"""
        schema_metadata = {
            "tables": [
                {
                    "name": "users",
                    "schema": "public",
                    "type": "table",
                    "estimated_rows": 100,
                    "columns": [{"name": "id", "type": "integer"}],
                    "relationships": []
                },
                {
                    "name": "orders",
                    "schema": "public",
                    "type": "table",
                    "estimated_rows": 500,
                    "columns": [{"name": "id", "type": "integer"}],
                    "relationships": []
                },
                {
                    "name": "products",
                    "schema": "public",
                    "type": "table",
                    "estimated_rows": 200,
                    "columns": [{"name": "id", "type": "integer"}],
                    "relationships": []
                },
            ],
            "total_tables": 3,
            "total_columns": 3
        }

        result = format_schema_for_prompt(schema_metadata)

        assert "users" in result
        assert "orders" in result
        assert "products" in result


class TestSchemaDiscoveryError:
    """Tests for custom exceptions"""

    def test_schema_discovery_error(self):
        """SchemaDiscoveryError should have message"""
        error = SchemaDiscoveryError("Test error")
        assert str(error) == "Test error"

    def test_too_many_tables_error(self):
        """TooManyTablesError should have informative message"""
        error = TooManyTablesError(
            f"Database has 150 tables, exceeding limit of {MAX_TABLES_LIMIT}."
        )
        assert "150" in str(error)
        assert str(MAX_TABLES_LIMIT) in str(error)


class TestMaxTablesLimit:
    """Tests for MAX_TABLES_LIMIT constant"""

    def test_max_tables_limit_is_100(self):
        """MAX_TABLES_LIMIT should be 100 as per spec"""
        assert MAX_TABLES_LIMIT == 100

    def test_max_tables_limit_is_positive(self):
        """MAX_TABLES_LIMIT should be positive"""
        assert MAX_TABLES_LIMIT > 0
