"""
Unit tests for inventory MCP tools
"""
import pytest
from decimal import Decimal


class TestInventoryAddItem:
    """Tests for inventory_add_item tool."""

    @pytest.mark.asyncio
    async def test_inventory_add_item_success(self, test_session):
        """Test successful item creation."""
        from app.mcp_server.tools_inventory import inventory_add_item

        result = await inventory_add_item(
            name="Sugar",
            category="Grocery",
            unit="kg",
            unit_price=50.0,
            stock_qty=100.0,
            session=test_session
        )

        assert result["name"] == "Sugar"
        assert result["category"] == "Grocery"
        assert result["is_active"] is True
        assert "id" in result
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_inventory_add_item_validates_category(self, test_session):
        """Test validation error for invalid category."""
        from app.mcp_server.tools_inventory import inventory_add_item
        from app.mcp_server.exceptions import MCPValidationError

        with pytest.raises(MCPValidationError) as exc_info:
            await inventory_add_item(
                name="Sugar",
                category="InvalidCategory",
                unit="kg",
                unit_price=50.0,
                stock_qty=100.0,
                session=test_session
            )
        assert exc_info.value.error_code == "CATEGORY_INVALID"

    @pytest.mark.asyncio
    async def test_inventory_add_item_validates_price(self, test_session):
        """Test validation error for negative price."""
        from app.mcp_server.tools_inventory import inventory_add_item
        from app.mcp_server.exceptions import MCPValidationError

        with pytest.raises(MCPValidationError):
            await inventory_add_item(
                name="Sugar",
                category="Grocery",
                unit="kg",
                unit_price=-50.0,
                stock_qty=100.0,
                session=test_session
            )


class TestInventoryUpdateItem:
    """Tests for inventory_update_item tool."""

    @pytest.mark.asyncio
    async def test_inventory_update_item_success(self, sample_items, test_session):
        """Test successful item update."""
        from app.mcp_server.tools_inventory import inventory_update_item

        item_id = sample_items[0].id

        result = await inventory_update_item(
            item_id=item_id,
            name="White Sugar",
            unit_price=55.0,
            session=test_session
        )

        assert result["id"] == item_id
        assert result["name"] == "White Sugar"
        assert float(result["unit_price"]) == 55.0

    @pytest.mark.asyncio
    async def test_inventory_update_item_not_found(self, test_session):
        """Test update non-existent item."""
        from app.mcp_server.tools_inventory import inventory_update_item
        from app.mcp_server.exceptions import MCPNotFoundError

        with pytest.raises(MCPNotFoundError):
            await inventory_update_item(
                item_id=9999,
                name="Sugar",
                session=test_session
            )

    @pytest.mark.asyncio
    async def test_inventory_update_item_partial(self, sample_items, test_session):
        """Test partial update (only name)."""
        from app.mcp_server.tools_inventory import inventory_update_item

        item_id = sample_items[0].id
        original_price = float(sample_items[0].unit_price)

        result = await inventory_update_item(
            item_id=item_id,
            name="Updated Sugar",
            session=test_session
        )

        assert result["name"] == "Updated Sugar"
        assert float(result["unit_price"]) == original_price


class TestInventoryDeleteItem:
    """Tests for inventory_delete_item tool."""

    @pytest.mark.asyncio
    async def test_inventory_delete_item_success(self, sample_items, test_session):
        """Test soft delete sets is_active = FALSE."""
        from app.mcp_server.tools_inventory import inventory_delete_item
        from app.models import Item
        from sqlalchemy import select

        item_id = sample_items[0].id

        result = await inventory_delete_item(item_id=item_id, session=test_session)

        assert result["id"] == item_id
        assert result["success"] is True

        # Verify is_active is now False
        stmt = select(Item).where(Item.id == item_id)
        result = await test_session.execute(stmt)
        item = result.scalar_one()
        assert item.is_active is False

    @pytest.mark.asyncio
    async def test_inventory_delete_item_not_found(self, test_session):
        """Test delete non-existent item."""
        from app.mcp_server.tools_inventory import inventory_delete_item
        from app.mcp_server.exceptions import MCPNotFoundError

        with pytest.raises(MCPNotFoundError):
            await inventory_delete_item(item_id=9999, session=test_session)


class TestInventoryListItems:
    """Tests for inventory_list_items tool."""

    @pytest.mark.asyncio
    async def test_inventory_list_items_success(self, sample_items, test_session):
        """Test list all items."""
        from app.mcp_server.tools_inventory import inventory_list_items

        result = await inventory_list_items(session=test_session)

        assert "items" in result
        assert "pagination" in result
        assert len(result["items"]) == len(sample_items)
        assert result["pagination"]["total"] == len(sample_items)

    @pytest.mark.asyncio
    async def test_inventory_list_items_filter_by_name(self, sample_items, test_session):
        """Test filter by name."""
        from app.mcp_server.tools_inventory import inventory_list_items

        result = await inventory_list_items(
            name="Sugar",
            session=test_session
        )

        assert all(item["name"] == "Sugar" for item in result["items"])

    @pytest.mark.asyncio
    async def test_inventory_list_items_pagination_defaults(self, sample_items, test_session):
        """Test pagination defaults (20 items, max 100)."""
        from app.mcp_server.tools_inventory import inventory_list_items

        result = await inventory_list_items(session=test_session)

        assert result["pagination"]["limit"] == 20  # Default
        assert result["pagination"]["page"] == 1  # Default

    @pytest.mark.asyncio
    async def test_inventory_list_items_excludes_inactive(self, sample_items, test_session):
        """Test inactive items excluded from list."""
        from app.mcp_server.tools_inventory import (
            inventory_delete_item,
            inventory_list_items
        )

        # Delete an item
        await inventory_delete_item(item_id=sample_items[0].id, session=test_session)

        # List should not include deleted item
        result = await inventory_list_items(session=test_session)
        assert all(item["is_active"] is True for item in result["items"])
        assert len(result["items"]) == 1  # Only Rice remains
