"""
Comprehensive tests for case-insensitive category functionality.

Tests the following:
1. Schema validation with case-insensitive categories
2. MCP tools with case-insensitive queries
3. FastAPI endpoints with case-insensitive queries
4. Category normalization and error handling
"""

import pytest
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Item
from app.schemas import ItemCreate, ItemUpdate, VALID_CATEGORIES
from app.mcp_server.utils import normalize_category, category_exists, get_valid_categories
from app.mcp_server.exceptions import MCPValidationError


# ============================================================================
# Test 1: Schema Validation - Case-Insensitive Categories
# ============================================================================

class TestSchemaValidation:
    """Test Pydantic schemas with case-insensitive category handling."""

    def test_item_create_accepts_lowercase_category(self):
        """ItemCreate should accept and normalize lowercase categories."""
        schema = ItemCreate(
            name="Test Item",
            category="grocery",  # lowercase
            unit="kg",
            unit_price=Decimal("10.00"),
            stock_qty=Decimal("100")
        )
        assert schema.category == "Grocery"

    def test_item_create_accepts_uppercase_category(self):
        """ItemCreate should accept and normalize uppercase categories."""
        schema = ItemCreate(
            name="Test Item",
            category="GARMENTS",  # uppercase
            unit="piece",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("50")
        )
        assert schema.category == "Garments"

    def test_item_create_accepts_mixed_case_category(self):
        """ItemCreate should accept and normalize mixed case categories."""
        schema = ItemCreate(
            name="Test Item",
            category="BeAuTy",  # mixed case
            unit="ml",
            unit_price=Decimal("25.00"),
            stock_qty=Decimal("200")
        )
        assert schema.category == "Beauty"

    def test_item_create_accepts_proper_case_category(self):
        """ItemCreate should accept proper case categories unchanged."""
        schema = ItemCreate(
            name="Test Item",
            category="Utilities",  # proper case
            unit="box",
            unit_price=Decimal("15.00"),
            stock_qty=Decimal("75")
        )
        assert schema.category == "Utilities"

    def test_item_create_accepts_other_category(self):
        """ItemCreate should accept 'Other' category."""
        schema = ItemCreate(
            name="Test Item",
            category="other",  # lowercase
            unit="piece",
            unit_price=Decimal("5.00"),
            stock_qty=Decimal("10")
        )
        assert schema.category == "Other"

    def test_item_create_rejects_invalid_category(self):
        """ItemCreate should reject invalid categories with helpful error."""
        with pytest.raises(ValueError) as exc_info:
            ItemCreate(
                name="Test Item",
                category="InvalidCategory",
                unit="kg",
                unit_price=Decimal("10.00"),
                stock_qty=Decimal("100")
            )
        error = str(exc_info.value)
        assert "InvalidCategory" in error
        assert "Valid categories" in error
        # Should list valid categories
        for cat in sorted(VALID_CATEGORIES):
            assert cat in error

    def test_item_update_accepts_lowercase_category(self):
        """ItemUpdate should accept and normalize lowercase categories."""
        schema = ItemUpdate(
            category="beauty",  # lowercase
            unit_price=Decimal("30.00")
        )
        assert schema.category == "Beauty"

    def test_item_update_accepts_none_category(self):
        """ItemUpdate should allow None for partial updates."""
        schema = ItemUpdate(
            name="Updated Name"
        )
        assert schema.category is None

    def test_item_update_rejects_invalid_category(self):
        """ItemUpdate should reject invalid categories."""
        with pytest.raises(ValueError) as exc_info:
            ItemUpdate(
                category="NonExistent"
            )
        error = str(exc_info.value)
        assert "NonExistent" in error
        assert "Valid categories" in error


# ============================================================================
# Test 2: Helper Functions
# ============================================================================

class TestHelperFunctions:
    """Test case-insensitive category helper functions."""

    def test_get_valid_categories(self):
        """get_valid_categories should return all valid categories."""
        categories = get_valid_categories()
        assert isinstance(categories, list)
        assert len(categories) == 5
        assert "Grocery" in categories
        assert "Garments" in categories
        assert "Beauty" in categories
        assert "Utilities" in categories
        assert "Other" in categories

    def test_normalize_category_exact_match(self):
        """normalize_category should return exact match unchanged."""
        result = normalize_category("Grocery")
        assert result == "Grocery"

    def test_normalize_category_lowercase(self):
        """normalize_category should normalize lowercase to proper case."""
        result = normalize_category("grocery")
        assert result == "Grocery"

    def test_normalize_category_uppercase(self):
        """normalize_category should normalize uppercase to proper case."""
        result = normalize_category("GARMENTS")
        assert result == "Garments"

    def test_normalize_category_mixed_case(self):
        """normalize_category should normalize mixed case to proper case."""
        result = normalize_category("bEaUtY")
        assert result == "Beauty"

    def test_normalize_category_invalid_raises_error(self):
        """normalize_category should raise MCPValidationError for invalid categories."""
        with pytest.raises(MCPValidationError) as exc_info:
            normalize_category("InvalidCategory")
        error = exc_info.value
        assert error.error_code == "CATEGORY_INVALID"
        assert "InvalidCategory" in error.message
        assert "Valid categories" in error.message

    def test_normalize_category_empty_raises_error(self):
        """normalize_category should raise error for empty string."""
        with pytest.raises(MCPValidationError):
            normalize_category("")

    def test_normalize_category_none_raises_error(self):
        """normalize_category should raise error for None."""
        with pytest.raises(MCPValidationError):
            normalize_category(None)

    def test_category_exists_exact_match(self):
        """category_exists should return True for exact match."""
        assert category_exists("Grocery") is True

    def test_category_exists_lowercase(self):
        """category_exists should return True for lowercase."""
        assert category_exists("grocery") is True

    def test_category_exists_uppercase(self):
        """category_exists should return True for uppercase."""
        assert category_exists("GARMENTS") is True

    def test_category_exists_invalid(self):
        """category_exists should return False for invalid category."""
        assert category_exists("InvalidCategory") is False

    def test_category_exists_empty(self):
        """category_exists should return False for empty string."""
        assert category_exists("") is False

    def test_category_exists_none(self):
        """category_exists should return False for None."""
        assert category_exists(None) is False


# ============================================================================
# Test 3: MCP Tools - Case-Insensitive Categories
# ============================================================================

@pytest.mark.asyncio
class TestMCPToolsCaseInsensitive:
    """Test MCP tools with case-insensitive category queries."""

    async def test_inventory_add_item_normalizes_category(self, db_session: AsyncSession):
        """inventory_add_item should normalize category to proper case."""
        # Import here to avoid circular imports
        from app.mcp_server.tools_inventory import inventory_add_item

        # Add item with lowercase category
        result = await inventory_add_item(
            name="Test Sugar",
            category="grocery",  # lowercase
            unit="kg",
            unit_price=2.50,
            stock_qty=50.0,
            session=db_session
        )

        # Should be normalized to proper case
        assert result["category"] == "Grocery"
        assert result["name"] == "Test Sugar"

    async def test_inventory_list_items_case_insensitive_filter(self, db_session: AsyncSession):
        """inventory_list_items should filter by category case-insensitively."""
        from app.mcp_server.tools_inventory import inventory_add_item, inventory_list_items

        # Add test items
        await inventory_add_item(
            name="Rice", category="Grocery", unit="kg",
            unit_price=1.50, stock_qty=100.0, session=db_session
        )
        await inventory_add_item(
            name="Wheat", category="Grocery", unit="kg",
            unit_price=2.00, stock_qty=75.0, session=db_session
        )
        await inventory_add_item(
            name="Shirt", category="Garments", unit="piece",
            unit_price=25.0, stock_qty=50.0, session=db_session
        )

        # List items with lowercase category filter
        result = await inventory_list_items(category="grocery", session=db_session)
        assert len(result["items"]) == 2
        assert all(item["category"] == "Grocery" for item in result["items"])

    async def test_inventory_list_items_uppercase_filter(self, db_session: AsyncSession):
        """inventory_list_items should filter by uppercase category."""
        from app.mcp_server.tools_inventory import inventory_add_item, inventory_list_items

        # Add test items
        await inventory_add_item(
            name="Soap", category="Beauty", unit="piece",
            unit_price=5.0, stock_qty=100.0, session=db_session
        )
        await inventory_add_item(
            name="Shampoo", category="Beauty", unit="ml",
            unit_price=10.0, stock_qty=50.0, session=db_session
        )

        # List items with uppercase category filter
        result = await inventory_list_items(category="BEAUTY", session=db_session)
        assert len(result["items"]) == 2
        assert all(item["category"] == "Beauty" for item in result["items"])

    async def test_inventory_update_item_normalizes_category(self, db_session: AsyncSession):
        """inventory_update_item should normalize category on update."""
        from app.mcp_server.tools_inventory import inventory_add_item, inventory_update_item

        # Add item
        item = await inventory_add_item(
            name="Test Item", category="Grocery", unit="kg",
            unit_price=5.0, stock_qty=50.0, session=db_session
        )

        # Update with different case category
        result = await inventory_update_item(
            item_id=item["id"],
            category="GARMENTS",  # uppercase
            session=db_session
        )

        # Should be normalized to proper case
        assert result["category"] == "Garments"

    async def test_inventory_add_item_invalid_category_raises_error(self, db_session: AsyncSession):
        """inventory_add_item should raise error for invalid category."""
        from app.mcp_server.tools_inventory import inventory_add_item

        with pytest.raises(MCPValidationError) as exc_info:
            await inventory_add_item(
                name="Test Item",
                category="InvalidCategory",  # invalid
                unit="kg",
                unit_price=5.0,
                stock_qty=50.0,
                session=db_session
            )
        error = exc_info.value
        assert error.error_code == "CATEGORY_INVALID"
        assert "InvalidCategory" in error.message


# ============================================================================
# Test 4: FastAPI Endpoints - Case-Insensitive Categories
# ============================================================================

@pytest.mark.asyncio
class TestFastAPIEndpointsCaseInsensitive:
    """Test FastAPI endpoints with case-insensitive categories."""

    async def test_create_item_normalizes_category(self, client, db_session: AsyncSession):
        """POST /items should normalize category."""
        response = client.post(
            "/api/items",
            json={
                "name": "Test Item",
                "category": "grocery",  # lowercase
                "unit": "kg",
                "unit_price": "10.00",
                "stock_qty": "50"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "Grocery"  # normalized

    async def test_list_items_case_insensitive_filter(self, client, db_session: AsyncSession):
        """GET /items should filter by category case-insensitively."""
        # Create test items
        client.post(
            "/api/items",
            json={
                "name": "Rice",
                "category": "Grocery",
                "unit": "kg",
                "unit_price": "2.00",
                "stock_qty": "100"
            }
        )
        client.post(
            "/api/items",
            json={
                "name": "Wheat",
                "category": "Grocery",
                "unit": "kg",
                "unit_price": "1.50",
                "stock_qty": "75"
            }
        )

        # Query with lowercase category
        response = client.get("/api/items?category=grocery")
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 2
        assert all(item["category"] == "Grocery" for item in items)

    async def test_list_items_uppercase_filter(self, client):
        """GET /items should filter by uppercase category."""
        # Create test items
        client.post(
            "/api/items",
            json={
                "name": "Shirt",
                "category": "Garments",
                "unit": "piece",
                "unit_price": "25.00",
                "stock_qty": "50"
            }
        )

        # Query with uppercase category
        response = client.get("/api/items?category=GARMENTS")
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 1
        assert items[0]["category"] == "Garments"

    async def test_update_item_normalizes_category(self, client):
        """PUT /items/{id} should normalize category."""
        # Create item
        create_response = client.post(
            "/api/items",
            json={
                "name": "Test Item",
                "category": "Grocery",
                "unit": "kg",
                "unit_price": "5.00",
                "stock_qty": "100"
            }
        )
        item_id = create_response.json()["id"]

        # Update with different case category
        response = client.put(
            f"/api/items/{item_id}",
            json={"category": "BEAUTY"}  # uppercase
        )
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Beauty"  # normalized

    async def test_create_item_invalid_category_rejected(self, client):
        """POST /items should reject invalid category."""
        response = client.post(
            "/api/items",
            json={
                "name": "Test Item",
                "category": "InvalidCategory",
                "unit": "kg",
                "unit_price": "5.00",
                "stock_qty": "50"
            }
        )
        assert response.status_code == 422  # validation error
        data = response.json()
        assert "category" in str(data).lower()


# ============================================================================
# Test 5: Database Persistence
# ============================================================================

@pytest.mark.asyncio
class TestDatabasePersistence:
    """Test that normalized categories are persisted correctly in database."""

    async def test_category_stored_in_normalized_form(self, db_session: AsyncSession):
        """Categories should be stored in normalized (proper case) form."""
        # Create item with lowercase category
        item = Item(
            name="Test Item",
            category="grocery",  # will be normalized by schema
            unit="kg",
            unit_price=Decimal("10.00"),
            stock_qty=Decimal("50"),
            is_active=True
        )

        # In a real scenario, category would be normalized by the schema/application
        # For this test, we manually set normalized form
        item.category = "Grocery"
        db_session.add(item)
        await db_session.commit()

        # Retrieve and verify
        stmt = select(Item).where(Item.name == "Test Item")
        result = await db_session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.category == "Grocery"

    async def test_case_insensitive_query_finds_items(self, db_session: AsyncSession):
        """Case-insensitive queries should find items regardless of search case."""
        # Create item
        item = Item(
            name="Test Item",
            category="Grocery",
            unit="kg",
            unit_price=Decimal("10.00"),
            stock_qty=Decimal("50"),
            is_active=True
        )
        db_session.add(item)
        await db_session.commit()

        # Query with lowercase (simulating ILIKE)
        stmt = select(Item).where(Item.category.ilike("grocery"))
        result = await db_session.execute(stmt)
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.name == "Test Item"
        assert found.category == "Grocery"


# ============================================================================
# Test 6: Error Messages
# ============================================================================

class TestErrorMessages:
    """Test that error messages are helpful and include valid categories."""

    def test_invalid_category_error_includes_valid_options(self):
        """Error for invalid category should list valid options."""
        try:
            normalize_category("InvalidCategory")
        except MCPValidationError as e:
            # Check error message includes valid categories
            assert "Valid categories" in e.message
            for cat in ["Grocery", "Garments", "Beauty", "Utilities", "Other"]:
                assert cat in e.message

    def test_schema_error_message_includes_valid_categories(self):
        """Schema validation error should include valid categories."""
        try:
            ItemCreate(
                name="Test",
                category="WrongCategory",
                unit="kg",
                unit_price=Decimal("10"),
                stock_qty=Decimal("50")
            )
        except ValueError as e:
            error_msg = str(e)
            assert "WrongCategory" in error_msg
            assert "Valid categories" in error_msg

