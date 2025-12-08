"""
Integration tests for search and update operations (Phase 4)
Tests the complete flow of searching items by various criteria and updating items
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from src.services.inventory_service import InventoryService
from src.models.item import Item
from src.cli.error_handler import ValidationError, ItemNotFoundError


class TestSearchByCategoryFlow:
    """Test searching items by category"""

    def test_search_by_category_returns_matching_items(self, test_session: Session):
        """Test that search by category returns all items in that category"""
        service = InventoryService(test_session)

        # Add items in different categories
        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        service.add_item("Shirt", "Garments", "piece", "200.00", "50")
        test_session.commit()

        # Search for Grocery items
        items = service.search_by_category("Grocery")
        assert len(items) == 2
        assert all(item.category == "Grocery" for item in items)

    def test_search_by_category_case_insensitive(self, test_session: Session):
        """Test that category search is case-insensitive"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        test_session.commit()

        # Search with different case
        items = service.search_by_category("grocery")
        assert len(items) == 2

        items = service.search_by_category("GROCERY")
        assert len(items) == 2

    def test_search_by_category_returns_empty_for_invalid_category(self, test_session: Session):
        """Test that search returns empty for invalid category"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        items = service.search_by_category("InvalidCategory")
        assert len(items) == 0

    def test_search_by_category_excludes_inactive_items(self, test_session: Session):
        """Test that search excludes inactive items"""
        service = InventoryService(test_session)

        item1 = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        item2 = service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        test_session.commit()

        # Mark one as inactive
        item2.is_active = False
        test_session.commit()

        items = service.search_by_category("Grocery")
        assert len(items) == 1
        assert items[0].name == "Sugar"

    def test_search_by_category_returns_empty_for_no_matches(self, test_session: Session):
        """Test that search returns empty list when no items in category"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        items = service.search_by_category("Beauty")
        assert len(items) == 0


class TestSearchByPriceRangeFlow:
    """Test searching items by price range"""

    def test_search_by_price_range_returns_matching_items(self, test_session: Session):
        """Test that search by price range returns items within range"""
        service = InventoryService(test_session)

        # Add items with different prices
        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        service.add_item("Oil", "Grocery", "liter", "200.00", "25")
        test_session.commit()

        # Search for items between 30 and 100
        items = service.search_by_price_range(Decimal("30.00"), Decimal("100.00"))
        assert len(items) == 2
        names = {item.name for item in items}
        assert names == {"Sugar", "Rice"}

    def test_search_by_price_range_includes_boundaries(self, test_session: Session):
        """Test that price range search includes boundary values"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        service.add_item("Oil", "Grocery", "liter", "200.00", "25")
        test_session.commit()

        # Search for exactly 50.00 and 40.00
        items = service.search_by_price_range(Decimal("40.00"), Decimal("50.00"))
        assert len(items) == 2
        prices = {item.unit_price for item in items}
        assert prices == {Decimal("40.00"), Decimal("50.00")}

    def test_search_by_price_range_with_single_item(self, test_session: Session):
        """Test search that matches only one item"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        test_session.commit()

        items = service.search_by_price_range(Decimal("45.00"), Decimal("55.00"))
        assert len(items) == 1
        assert items[0].name == "Sugar"

    def test_search_by_price_range_raises_error_for_invalid_range(self, test_session: Session):
        """Test that invalid price range (min > max) raises error"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        with pytest.raises(ValueError, match="min_price must be less than or equal to max_price"):
            service.search_by_price_range(Decimal("100.00"), Decimal("50.00"))

    def test_search_by_price_range_returns_empty_for_no_matches(self, test_session: Session):
        """Test that search returns empty list when no items in range"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        items = service.search_by_price_range(Decimal("100.00"), Decimal("200.00"))
        assert len(items) == 0

    def test_search_by_price_range_excludes_inactive_items(self, test_session: Session):
        """Test that search excludes inactive items"""
        service = InventoryService(test_session)

        item1 = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        item2 = service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        test_session.commit()

        # Mark one as inactive
        item2.is_active = False
        test_session.commit()

        items = service.search_by_price_range(Decimal("30.00"), Decimal("100.00"))
        assert len(items) == 1
        assert items[0].name == "Sugar"


class TestSoftDeleteFlow:
    """Test soft-delete functionality via update_item with is_active=False"""

    def test_soft_delete_item_via_update(self, test_session: Session):
        """Test marking item as inactive (soft delete)"""
        service = InventoryService(test_session)

        item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        # Mark as inactive
        updated_item = service.update_item(item.id, is_active=False)
        test_session.commit()

        assert updated_item.is_active is False

    def test_soft_deleted_item_not_listed(self, test_session: Session):
        """Test that soft-deleted items don't appear in list"""
        service = InventoryService(test_session)

        item1 = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        item2 = service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        test_session.commit()

        # Soft delete one item
        service.update_item(item1.id, is_active=False)
        test_session.commit()

        # List should only show active items
        items = service.list_items()
        assert len(items) == 1
        assert items[0].name == "Rice"

    def test_soft_deleted_item_not_searchable(self, test_session: Session):
        """Test that soft-deleted items don't appear in search results"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        test_session.commit()

        # Soft delete the first item
        items = service.search_items("Sugar")
        assert len(items) == 1
        service.update_item(items[0].id, is_active=False)
        test_session.commit()

        # Search should not return soft-deleted items
        results = service.search_items("Sugar")
        assert len(results) == 0

    def test_soft_deleted_item_still_in_database(self, test_session: Session):
        """Test that soft-deleted items are still in database (not physically deleted)"""
        service = InventoryService(test_session)

        item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()
        item_id = item.id

        # Soft delete
        service.update_item(item_id, is_active=False)
        test_session.commit()

        # Query directly - should still exist
        stored_item = test_session.query(Item).filter(Item.id == item_id).first()
        assert stored_item is not None
        assert stored_item.is_active is False

    def test_get_item_fails_for_soft_deleted_item(self, test_session: Session):
        """Test that get_item raises error for soft-deleted items"""
        service = InventoryService(test_session)

        item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        # Soft delete
        service.update_item(item.id, is_active=False)
        test_session.commit()

        # get_item should raise ItemNotFoundError
        with pytest.raises(ItemNotFoundError):
            service.get_item(item.id)

    def test_soft_delete_preserves_historical_data_for_bills(self, test_session: Session):
        """Test that soft-deleting item doesn't affect historical bill data"""
        service = InventoryService(test_session)

        item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()
        original_price = item.unit_price

        # Soft delete item
        service.update_item(item.id, is_active=False)
        test_session.commit()

        # Query directly - price should still be there
        stored_item = test_session.query(Item).filter(Item.id == item.id).first()
        assert stored_item.unit_price == original_price
        # This is important for historical reference in bills


class TestUpdateItemWithPartialFields:
    """Test updating items with various field combinations"""

    def test_update_only_is_active_field(self, test_session: Session):
        """Test updating only the is_active field"""
        service = InventoryService(test_session)

        item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        original_price = item.unit_price
        test_session.commit()

        updated_item = service.update_item(item.id, is_active=False)
        test_session.commit()

        assert updated_item.is_active is False
        assert updated_item.unit_price == original_price  # Unchanged

    def test_update_price_and_is_active(self, test_session: Session):
        """Test updating both price and is_active"""
        service = InventoryService(test_session)

        item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        updated_item = service.update_item(item.id, unit_price="60.00", is_active=False)
        test_session.commit()

        assert updated_item.unit_price == Decimal("60.00")
        assert updated_item.is_active is False

    def test_update_multiple_fields_except_is_active(self, test_session: Session):
        """Test updating multiple fields while leaving is_active unchanged"""
        service = InventoryService(test_session)

        item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        updated_item = service.update_item(item.id, unit_price="55.00", stock_qty="120")
        test_session.commit()

        assert updated_item.unit_price == Decimal("55.00")
        assert updated_item.stock_qty == Decimal("120")
        assert updated_item.is_active is True  # Still active


class TestSearchAndUpdateIntegration:
    """Test combined search and update operations"""

    def test_search_then_update_category(self, test_session: Session):
        """Test searching for items then updating a found item"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        service.add_item("Wheat", "Grocery", "kg", "30.00", "80")
        test_session.commit()

        # Search for "Sug"
        results = service.search_items("Sug")
        assert len(results) >= 1

        # Update the first result
        item_to_update = results[0]
        updated_item = service.update_item(item_to_update.id, unit_price="55.00")
        test_session.commit()

        assert updated_item.unit_price == Decimal("55.00")

    def test_search_by_category_then_soft_delete(self, test_session: Session):
        """Test searching by category then soft-deleting found items"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        test_session.commit()

        # Search by category
        items = service.search_by_category("Grocery")
        assert len(items) == 2

        # Soft delete the first one
        service.update_item(items[0].id, is_active=False)
        test_session.commit()

        # Search again should return only 1
        items = service.search_by_category("Grocery")
        assert len(items) == 1

    def test_search_by_price_range_then_update(self, test_session: Session):
        """Test searching by price range then updating found items"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        service.add_item("Oil", "Grocery", "liter", "200.00", "25")
        test_session.commit()

        # Search for items between 30 and 100
        items = service.search_by_price_range(Decimal("30.00"), Decimal("100.00"))
        assert len(items) == 2

        # Increase stock for all found items
        for item in items:
            service.update_item(item.id, stock_qty=str(int(item.stock_qty) + 10))
        test_session.commit()

        # Verify the updates
        updated_items = service.search_by_price_range(Decimal("30.00"), Decimal("100.00"))
        for item in updated_items:
            assert item.stock_qty >= 110
