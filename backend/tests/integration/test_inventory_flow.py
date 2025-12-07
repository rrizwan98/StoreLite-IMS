"""
Integration tests for inventory operations (User Story 1)
Tests the complete flow of adding and listing items with database persistence
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from src.services.inventory_service import InventoryService
from src.models.item import Item
from src.cli.error_handler import ValidationError, ItemNotFoundError


class TestAddItemFlow:
    """Test adding items to inventory"""

    def test_add_item_with_valid_data(self, test_session: Session):
        """Test adding an item with valid data persists to database"""
        service = InventoryService(test_session)

        item = service.add_item(
            name="Sugar",
            category="Grocery",
            unit="kg",
            unit_price="50.00",
            stock_qty="100",
        )
        test_session.commit()

        # Verify item was stored in database
        stored_item = test_session.query(Item).filter(Item.id == item.id).first()
        assert stored_item is not None
        assert stored_item.name == "Sugar"
        assert stored_item.category == "Grocery"
        assert stored_item.unit == "kg"
        assert stored_item.unit_price == Decimal("50.00")
        assert stored_item.stock_qty == Decimal("100")
        assert stored_item.is_active is True

    def test_add_item_with_invalid_category(self, test_session: Session):
        """Test that adding item with invalid category raises ValidationError"""
        service = InventoryService(test_session)

        with pytest.raises(ValidationError):
            service.add_item(
                name="Rice",
                category="InvalidCategory",
                unit="kg",
                unit_price="40.00",
                stock_qty="50",
            )
        test_session.commit()

        # Verify item was NOT stored
        item_count = test_session.query(Item).filter(Item.name == "Rice").count()
        assert item_count == 0

    def test_add_item_with_invalid_unit(self, test_session: Session):
        """Test that adding item with invalid unit raises ValidationError"""
        service = InventoryService(test_session)

        with pytest.raises(ValidationError):
            service.add_item(
                name="Oil",
                category="Grocery",
                unit="InvalidUnit",
                unit_price="200.00",
                stock_qty="20",
            )
        test_session.commit()

        # Verify item was NOT stored
        item_count = test_session.query(Item).filter(Item.name == "Oil").count()
        assert item_count == 0

    def test_add_item_with_negative_price(self, test_session: Session):
        """Test that adding item with negative price raises ValidationError"""
        service = InventoryService(test_session)

        with pytest.raises(ValidationError):
            service.add_item(
                name="Flour",
                category="Grocery",
                unit="kg",
                unit_price="-25.00",
                stock_qty="30",
            )
        test_session.commit()

        # Verify item was NOT stored
        item_count = test_session.query(Item).filter(Item.name == "Flour").count()
        assert item_count == 0

    def test_add_item_with_negative_stock(self, test_session: Session):
        """Test that adding item with negative stock raises ValidationError"""
        service = InventoryService(test_session)

        with pytest.raises(ValidationError):
            service.add_item(
                name="Salt",
                category="Grocery",
                unit="kg",
                unit_price="15.00",
                stock_qty="-10",
            )
        test_session.commit()

        # Verify item was NOT stored
        item_count = test_session.query(Item).filter(Item.name == "Salt").count()
        assert item_count == 0

    def test_add_multiple_items(self, test_session: Session):
        """Test adding multiple items"""
        service = InventoryService(test_session)

        items_data = [
            ("Sugar", "Grocery", "kg", "50.00", "100"),
            ("Rice", "Grocery", "kg", "40.00", "150"),
            ("Oil", "Grocery", "liter", "200.00", "25"),
        ]

        added_items = []
        for name, category, unit, price, stock in items_data:
            item = service.add_item(name, category, unit, price, stock)
            added_items.append(item)

        test_session.commit()

        # Verify all items were stored
        stored_items = test_session.query(Item).filter(Item.is_active == True).all()
        assert len(stored_items) == 3
        assert all(item.is_active for item in stored_items)


class TestListItemsFlow:
    """Test listing items from inventory"""

    def test_list_items_returns_empty_for_empty_inventory(self, test_session: Session):
        """Test that listing items returns empty list for empty inventory"""
        service = InventoryService(test_session)

        items = service.list_items()
        assert items == []

    def test_list_items_returns_all_active_items(self, test_session: Session):
        """Test that listing items returns all active items"""
        service = InventoryService(test_session)

        # Add items
        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        service.add_item("Oil", "Grocery", "liter", "200.00", "25")
        test_session.commit()

        # List items
        items = service.list_items()
        assert len(items) == 3
        assert all(item.is_active for item in items)

    def test_list_items_sorted_by_name(self, test_session: Session):
        """Test that listed items are sorted by name"""
        service = InventoryService(test_session)

        # Add items in random order
        service.add_item("Zebra Rice", "Grocery", "kg", "40.00", "150")
        service.add_item("Apple Sugar", "Grocery", "kg", "50.00", "100")
        service.add_item("Mango Oil", "Grocery", "liter", "200.00", "25")
        test_session.commit()

        # List items
        items = service.list_items()
        assert len(items) == 3
        assert items[0].name == "Apple Sugar"
        assert items[1].name == "Mango Oil"
        assert items[2].name == "Zebra Rice"

    def test_list_items_excludes_inactive_items(self, test_session: Session):
        """Test that listing items excludes inactive (deleted) items"""
        service = InventoryService(test_session)

        # Add items
        item1 = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        item2 = service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        test_session.commit()

        # Mark one as inactive
        item2.is_active = False
        test_session.commit()

        # List items
        items = service.list_items()
        assert len(items) == 1
        assert items[0].name == "Sugar"


class TestSearchItemsFlow:
    """Test searching items in inventory"""

    def test_search_items_by_exact_name(self, test_session: Session):
        """Test searching items by exact name"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        service.add_item("Sugarless", "Grocery", "kg", "45.00", "80")
        test_session.commit()

        items = service.search_items("Sugar")
        assert len(items) >= 1
        assert any(item.name == "Sugar" for item in items)

    def test_search_items_by_partial_name(self, test_session: Session):
        """Test searching items by partial name"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        service.add_item("Rice", "Grocery", "kg", "40.00", "150")
        test_session.commit()

        items = service.search_items("Sug")
        assert len(items) >= 1
        assert any(item.name == "Sugar" for item in items)

    def test_search_items_case_insensitive(self, test_session: Session):
        """Test that search is case-insensitive"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        items = service.search_items("sugar")
        assert len(items) >= 1
        assert any(item.name == "Sugar" for item in items)

    def test_search_items_returns_empty_for_no_match(self, test_session: Session):
        """Test that search returns empty list for no matches"""
        service = InventoryService(test_session)

        service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        items = service.search_items("NonExistent")
        assert len(items) == 0


class TestGetItemFlow:
    """Test getting a single item"""

    def test_get_item_by_id(self, test_session: Session):
        """Test getting an item by ID"""
        service = InventoryService(test_session)

        added_item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        retrieved_item = service.get_item(added_item.id)
        assert retrieved_item.id == added_item.id
        assert retrieved_item.name == "Sugar"

    def test_get_nonexistent_item_raises_error(self, test_session: Session):
        """Test that getting nonexistent item raises ItemNotFoundError"""
        service = InventoryService(test_session)

        with pytest.raises(ItemNotFoundError):
            service.get_item(9999)

    def test_get_inactive_item_raises_error(self, test_session: Session):
        """Test that getting inactive item raises ItemNotFoundError"""
        service = InventoryService(test_session)

        item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        # Mark as inactive
        item.is_active = False
        test_session.commit()

        with pytest.raises(ItemNotFoundError):
            service.get_item(item.id)


class TestUpdateItemFlow:
    """Test updating items"""

    def test_update_item_price(self, test_session: Session):
        """Test updating item price"""
        service = InventoryService(test_session)

        item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        updated_item = service.update_item(item.id, unit_price="55.00")
        test_session.commit()

        assert updated_item.unit_price == Decimal("55.00")

    def test_update_item_stock(self, test_session: Session):
        """Test updating item stock"""
        service = InventoryService(test_session)

        item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        updated_item = service.update_item(item.id, stock_qty="120")
        test_session.commit()

        assert updated_item.stock_qty == Decimal("120")

    def test_update_item_price_and_stock(self, test_session: Session):
        """Test updating both price and stock"""
        service = InventoryService(test_session)

        item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        updated_item = service.update_item(item.id, unit_price="60.00", stock_qty="150")
        test_session.commit()

        assert updated_item.unit_price == Decimal("60.00")
        assert updated_item.stock_qty == Decimal("150")

    def test_update_item_with_negative_price_raises_error(self, test_session: Session):
        """Test that updating with negative price raises ValidationError"""
        service = InventoryService(test_session)

        item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        with pytest.raises(ValidationError):
            service.update_item(item.id, unit_price="-10.00")

    def test_update_item_with_negative_stock_raises_error(self, test_session: Session):
        """Test that updating with negative stock raises ValidationError"""
        service = InventoryService(test_session)

        item = service.add_item("Sugar", "Grocery", "kg", "50.00", "100")
        test_session.commit()

        with pytest.raises(ValidationError):
            service.update_item(item.id, stock_qty="-50")
