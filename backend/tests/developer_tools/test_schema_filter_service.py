"""
Unit Tests for Schema Filter Service (Phase 14)

Tests the core schema filtering functionality that enables
table-level access control for published agents.
"""

import pytest
from app.services.schema_filter_service import (
    filter_schema_for_published_agent,
    validate_allowed_tables,
    get_table_names_from_schema,
    get_table_info,
    build_table_summary,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_schema():
    """Sample schema metadata for testing."""
    return {
        "database": "test_db",
        "schemas": ["public"],
        "discovered_at": "2025-01-13T10:00:00Z",
        "tables": [
            {
                "name": "products",
                "schema": "public",
                "columns": [
                    {"name": "id", "type": "integer", "is_primary_key": True},
                    {"name": "name", "type": "varchar"},
                    {"name": "price", "type": "decimal"},
                ],
            },
            {
                "name": "orders",
                "schema": "public",
                "columns": [
                    {"name": "id", "type": "integer", "is_primary_key": True},
                    {"name": "product_id", "type": "integer"},
                    {"name": "quantity", "type": "integer"},
                ],
            },
            {
                "name": "users",
                "schema": "public",
                "columns": [
                    {"name": "id", "type": "integer", "is_primary_key": True},
                    {"name": "email", "type": "varchar"},
                    {"name": "password_hash", "type": "varchar"},
                ],
            },
            {
                "name": "admin_logs",
                "schema": "public",
                "columns": [
                    {"name": "id", "type": "integer", "is_primary_key": True},
                    {"name": "action", "type": "varchar"},
                    {"name": "user_id", "type": "integer"},
                ],
            },
        ],
        "relationships": [
            {"from_table": "orders", "to_table": "products", "from_column": "product_id", "to_column": "id"},
            {"from_table": "orders", "to_table": "users", "from_column": "user_id", "to_column": "id"},
            {"from_table": "admin_logs", "to_table": "users", "from_column": "user_id", "to_column": "id"},
        ],
        "table_count": 4,
    }


# =============================================================================
# Tests for filter_schema_for_published_agent
# =============================================================================

class TestFilterSchemaForPublishedAgent:
    """Tests for the main schema filtering function."""

    def test_filter_single_table(self, sample_schema):
        """Test filtering to a single table."""
        result = filter_schema_for_published_agent(
            full_schema=sample_schema,
            allowed_tables=["products"],
            access_mode="read_only"
        )

        assert result["table_count"] == 1
        assert len(result["tables"]) == 1
        assert result["tables"][0]["name"] == "products"
        assert result["access_mode"] == "read_only"
        assert result["is_filtered"] is True

    def test_filter_multiple_tables(self, sample_schema):
        """Test filtering to multiple tables."""
        result = filter_schema_for_published_agent(
            full_schema=sample_schema,
            allowed_tables=["products", "orders"],
            access_mode="read_write"
        )

        assert result["table_count"] == 2
        table_names = [t["name"] for t in result["tables"]]
        assert "products" in table_names
        assert "orders" in table_names
        assert "users" not in table_names
        assert result["access_mode"] == "read_write"

    def test_filter_preserves_relationships_between_allowed_tables(self, sample_schema):
        """Test that relationships between allowed tables are preserved."""
        result = filter_schema_for_published_agent(
            full_schema=sample_schema,
            allowed_tables=["products", "orders"],
            access_mode="read_only"
        )

        # Should keep orders -> products relationship
        assert len(result["relationships"]) == 1
        rel = result["relationships"][0]
        assert rel["from_table"] == "orders"
        assert rel["to_table"] == "products"

    def test_filter_removes_relationships_to_non_allowed_tables(self, sample_schema):
        """Test that relationships to non-allowed tables are removed."""
        result = filter_schema_for_published_agent(
            full_schema=sample_schema,
            allowed_tables=["orders"],  # Only orders, not products or users
            access_mode="read_only"
        )

        # Should remove all relationships since neither products nor users are allowed
        assert len(result["relationships"]) == 0

    def test_filter_case_insensitive(self, sample_schema):
        """Test that table name matching is case-insensitive."""
        result = filter_schema_for_published_agent(
            full_schema=sample_schema,
            allowed_tables=["PRODUCTS", "Orders"],
            access_mode="read_only"
        )

        assert result["table_count"] == 2
        table_names = [t["name"] for t in result["tables"]]
        assert "products" in table_names
        assert "orders" in table_names

    def test_filter_empty_allowed_tables(self, sample_schema):
        """Test filtering with empty allowed tables list."""
        result = filter_schema_for_published_agent(
            full_schema=sample_schema,
            allowed_tables=[],
            access_mode="read_only"
        )

        assert result["table_count"] == 0
        assert len(result["tables"]) == 0
        assert result["is_filtered"] is True

    def test_filter_empty_schema(self):
        """Test filtering with empty schema."""
        result = filter_schema_for_published_agent(
            full_schema={},
            allowed_tables=["products"],
            access_mode="read_only"
        )

        assert result["table_count"] == 0
        assert result["is_filtered"] is True

    def test_filter_none_schema(self):
        """Test filtering with None schema."""
        result = filter_schema_for_published_agent(
            full_schema=None,
            allowed_tables=["products"],
            access_mode="read_only"
        )

        assert result["table_count"] == 0
        assert result["is_filtered"] is True

    def test_filter_adds_metadata(self, sample_schema):
        """Test that filter adds required metadata fields."""
        result = filter_schema_for_published_agent(
            full_schema=sample_schema,
            allowed_tables=["products"],
            access_mode="read_only"
        )

        assert "access_mode" in result
        assert "is_filtered" in result
        assert "original_table_count" in result
        assert "allowed_tables" in result
        assert result["original_table_count"] == 4


# =============================================================================
# Tests for validate_allowed_tables
# =============================================================================

class TestValidateAllowedTables:
    """Tests for table validation function."""

    def test_validate_existing_tables(self, sample_schema):
        """Test validation of tables that exist."""
        valid, invalid = validate_allowed_tables(
            allowed_tables=["products", "orders"],
            full_schema=sample_schema
        )

        assert valid == ["products", "orders"]
        assert invalid == []

    def test_validate_mixed_tables(self, sample_schema):
        """Test validation with mix of existing and non-existing tables."""
        valid, invalid = validate_allowed_tables(
            allowed_tables=["products", "nonexistent", "orders", "fake_table"],
            full_schema=sample_schema
        )

        assert "products" in valid
        assert "orders" in valid
        assert "nonexistent" in invalid
        assert "fake_table" in invalid

    def test_validate_case_insensitive(self, sample_schema):
        """Test case-insensitive validation."""
        valid, invalid = validate_allowed_tables(
            allowed_tables=["PRODUCTS", "Orders"],
            full_schema=sample_schema
        )

        assert len(valid) == 2
        assert len(invalid) == 0

    def test_validate_empty_schema(self):
        """Test validation with empty schema."""
        valid, invalid = validate_allowed_tables(
            allowed_tables=["products"],
            full_schema={}
        )

        assert valid == []
        assert invalid == ["products"]


# =============================================================================
# Tests for get_table_names_from_schema
# =============================================================================

class TestGetTableNamesFromSchema:
    """Tests for extracting table names."""

    def test_get_table_names(self, sample_schema):
        """Test extracting table names from schema."""
        names = get_table_names_from_schema(sample_schema)

        assert len(names) == 4
        assert "products" in names
        assert "orders" in names
        assert "users" in names
        assert "admin_logs" in names

    def test_get_table_names_empty_schema(self):
        """Test with empty schema."""
        names = get_table_names_from_schema({})
        assert names == []

    def test_get_table_names_none_schema(self):
        """Test with None schema."""
        names = get_table_names_from_schema(None)
        assert names == []


# =============================================================================
# Tests for get_table_info
# =============================================================================

class TestGetTableInfo:
    """Tests for getting specific table info."""

    def test_get_existing_table(self, sample_schema):
        """Test getting info for existing table."""
        info = get_table_info(sample_schema, "products")

        assert info is not None
        assert info["name"] == "products"
        assert len(info["columns"]) == 3

    def test_get_table_case_insensitive(self, sample_schema):
        """Test case-insensitive table lookup."""
        info = get_table_info(sample_schema, "PRODUCTS")

        assert info is not None
        assert info["name"] == "products"

    def test_get_nonexistent_table(self, sample_schema):
        """Test getting info for non-existent table."""
        info = get_table_info(sample_schema, "nonexistent")
        assert info is None


# =============================================================================
# Tests for build_table_summary
# =============================================================================

class TestBuildTableSummary:
    """Tests for building table summaries."""

    def test_build_summary(self, sample_schema):
        """Test building table summary."""
        summaries = build_table_summary(sample_schema)

        assert len(summaries) == 4

        # Find products summary
        products = next(s for s in summaries if s["name"] == "products")
        assert products["column_count"] == 3
        assert products["has_primary_key"] is True

    def test_build_summary_sorted(self, sample_schema):
        """Test that summaries are sorted by name."""
        summaries = build_table_summary(sample_schema)

        names = [s["name"] for s in summaries]
        assert names == sorted(names)

    def test_build_summary_empty_schema(self):
        """Test with empty schema."""
        summaries = build_table_summary({})
        assert summaries == []
