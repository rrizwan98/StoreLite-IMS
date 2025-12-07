"""
Unit tests for search operations in InventoryService (Phase 4 - RED phase).

These tests are written FIRST and will FAIL until the implementation is complete.
Tests cover:
- T032: search_by_category() method
- T033: search_by_price_range() method
- T034: soft_delete_item() functionality (using update_item)
"""

import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.base import Base
from src.models.item import Item
from src.models.bill import Bill, BillItem
from src.services.inventory_service import InventoryService
from src.services.billing_service import BillingService


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def inventory_service(test_db):
    """Create an InventoryService instance with test database."""
    return InventoryService(session=test_db)


@pytest.fixture
def billing_service(test_db):
    """Create a BillingService instance with test database."""
    return BillingService(session=test_db)


# ============================================================================
# T032: Unit tests for search_by_category()
# ============================================================================

def test_search_by_category_returns_only_matching_items(inventory_service):
    """Test that search_by_category returns only items matching the category."""
    # Create 3 items: 2 Grocery, 1 Garments
    inventory_service.add_item(
        name="Rice",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("50.00"),
        stock_qty=Decimal("100")
    )
    inventory_service.add_item(
        name="Sugar",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("45.00"),
        stock_qty=Decimal("50")
    )
    inventory_service.add_item(
        name="T-Shirt",
        category="Garments",
        unit="piece",
        unit_price=Decimal("150.00"),
        stock_qty=Decimal("20")
    )

    # Call search_by_category("Grocery")
    results = inventory_service.search_by_category("Grocery")

    # Assert returns exactly 2 items
    assert len(results) == 2
    assert all(item.category == "Grocery" for item in results)
    assert set(item.name for item in results) == {"Rice", "Sugar"}


def test_search_by_category_case_insensitive(inventory_service):
    """Test that search_by_category is case-insensitive."""
    # Create item with category "Grocery"
    inventory_service.add_item(
        name="Milk",
        category="Grocery",
        unit="liter",
        unit_price=Decimal("60.00"),
        stock_qty=Decimal("30")
    )

    # Call search_by_category("grocery") with lowercase
    results = inventory_service.search_by_category("grocery")

    # Assert returns the item
    assert len(results) == 1
    assert results[0].name == "Milk"
    assert results[0].category == "Grocery"


def test_search_by_category_invalid_category(inventory_service):
    """Test that search_by_category returns empty list for invalid category."""
    # Create some items
    inventory_service.add_item(
        name="Soap",
        category="Beauty",
        unit="piece",
        unit_price=Decimal("25.00"),
        stock_qty=Decimal("40")
    )

    # Call search_by_category("Invalid")
    results = inventory_service.search_by_category("InvalidCategory")

    # Assert returns empty list (no error)
    assert results == []


def test_search_by_category_returns_only_active_items(inventory_service):
    """Test that search_by_category returns only active items (is_active=True)."""
    # Create 1 active Grocery item, 1 inactive Grocery item
    item1 = inventory_service.add_item(
        name="Active Rice",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("50.00"),
        stock_qty=Decimal("100")
    )

    item2 = inventory_service.add_item(
        name="Inactive Rice",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("55.00"),
        stock_qty=Decimal("50")
    )

    # Soft-delete item2 (set is_active=False)
    inventory_service.update_item(item2.id, is_active=False)

    # Call search_by_category("Grocery")
    results = inventory_service.search_by_category("Grocery")

    # Assert returns only the active item
    assert len(results) == 1
    assert results[0].name == "Active Rice"
    assert results[0].is_active is True


# ============================================================================
# T033: Unit tests for search_by_price_range()
# ============================================================================

def test_search_by_price_range_returns_items_within_range(inventory_service):
    """Test that search_by_price_range returns items within the specified range."""
    # Create items with prices: 10, 50, 100, 200
    inventory_service.add_item(
        name="Item A",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("10.00"),
        stock_qty=Decimal("10")
    )
    inventory_service.add_item(
        name="Item B",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("50.00"),
        stock_qty=Decimal("10")
    )
    inventory_service.add_item(
        name="Item C",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("100.00"),
        stock_qty=Decimal("10")
    )
    inventory_service.add_item(
        name="Item D",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("200.00"),
        stock_qty=Decimal("10")
    )

    # Call search_by_price_range(min_price=40, max_price=150)
    results = inventory_service.search_by_price_range(
        min_price=Decimal("40"),
        max_price=Decimal("150")
    )

    # Assert returns items with prices 50 and 100
    assert len(results) == 2
    prices = {item.unit_price for item in results}
    assert prices == {Decimal("50.00"), Decimal("100.00")}


def test_search_by_price_range_inclusive_boundaries(inventory_service):
    """Test that search_by_price_range includes boundary values."""
    # Create items with prices: 50, 100, 150
    inventory_service.add_item(
        name="Item A",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("50.00"),
        stock_qty=Decimal("10")
    )
    inventory_service.add_item(
        name="Item B",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("100.00"),
        stock_qty=Decimal("10")
    )
    inventory_service.add_item(
        name="Item C",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("150.00"),
        stock_qty=Decimal("10")
    )

    # Call search_by_price_range(min_price=100, max_price=100)
    results = inventory_service.search_by_price_range(
        min_price=Decimal("100"),
        max_price=Decimal("100")
    )

    # Assert returns item with price 100
    assert len(results) == 1
    assert results[0].unit_price == Decimal("100.00")


def test_search_by_price_range_empty_range(inventory_service):
    """Test that search_by_price_range returns empty list when no items in range."""
    # Create items with prices: 10, 20, 30
    inventory_service.add_item(
        name="Item A",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("10.00"),
        stock_qty=Decimal("10")
    )
    inventory_service.add_item(
        name="Item B",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("20.00"),
        stock_qty=Decimal("10")
    )
    inventory_service.add_item(
        name="Item C",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("30.00"),
        stock_qty=Decimal("10")
    )

    # Call search_by_price_range(min_price=100, max_price=200)
    results = inventory_service.search_by_price_range(
        min_price=Decimal("100"),
        max_price=Decimal("200")
    )

    # Assert returns empty list
    assert results == []


def test_search_by_price_range_invalid_params(inventory_service):
    """Test that search_by_price_range raises ValueError when min > max."""
    # Call search_by_price_range(min_price=200, max_price=100)
    with pytest.raises(ValueError) as exc_info:
        inventory_service.search_by_price_range(
            min_price=Decimal("200"),
            max_price=Decimal("100")
        )

    # Assert raises ValueError (min > max)
    assert "min_price must be <= max_price" in str(exc_info.value)


def test_search_by_price_range_returns_only_active_items(inventory_service):
    """Test that search_by_price_range returns only active items."""
    # Create 1 active item with price 50, 1 inactive item with price 50
    item1 = inventory_service.add_item(
        name="Active Item",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("50.00"),
        stock_qty=Decimal("10")
    )

    item2 = inventory_service.add_item(
        name="Inactive Item",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("50.00"),
        stock_qty=Decimal("10")
    )

    # Soft-delete item2
    inventory_service.update_item(item2.id, is_active=False)

    # Call search_by_price_range
    results = inventory_service.search_by_price_range(
        min_price=Decimal("40"),
        max_price=Decimal("60")
    )

    # Assert returns only the active item
    assert len(results) == 1
    assert results[0].name == "Active Item"


# ============================================================================
# T034: Unit tests for soft_delete_item() using update_item()
# ============================================================================

def test_soft_delete_marks_item_inactive(inventory_service):
    """Test that soft-deleting an item marks it as inactive."""
    # Create item with is_active=True
    item = inventory_service.add_item(
        name="Test Item",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("50.00"),
        stock_qty=Decimal("10")
    )
    assert item.is_active is True

    # Call update_item(item_id, is_active=False)
    updated_item = inventory_service.update_item(item.id, is_active=False)

    # Assert item.is_active is False
    assert updated_item.is_active is False


def test_soft_deleted_item_not_in_list(inventory_service):
    """Test that soft-deleted items don't appear in list_items()."""
    # Create 2 items: 1 active, 1 deleted (is_active=False)
    item1 = inventory_service.add_item(
        name="Active Item",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("50.00"),
        stock_qty=Decimal("10")
    )

    item2 = inventory_service.add_item(
        name="Deleted Item",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("60.00"),
        stock_qty=Decimal("20")
    )

    # Soft-delete item2
    inventory_service.update_item(item2.id, is_active=False)

    # Call list_items()
    items = inventory_service.list_items()

    # Assert returns only 1 item (the active one)
    assert len(items) == 1
    assert items[0].name == "Active Item"


def test_soft_delete_doesnt_delete_from_db(inventory_service, test_db):
    """Test that soft-delete doesn't physically remove row from database."""
    # Create item
    item = inventory_service.add_item(
        name="Test Item",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("50.00"),
        stock_qty=Decimal("10")
    )
    item_id = item.id

    # Call update_item(item_id, is_active=False)
    inventory_service.update_item(item_id, is_active=False)

    # Query database directly (without is_active filter)
    db_item = test_db.query(Item).filter(Item.id == item_id).first()

    # Assert row still exists with is_active=False
    assert db_item is not None
    assert db_item.is_active is False
    assert db_item.name == "Test Item"


def test_soft_delete_item_still_in_old_bills(inventory_service, billing_service, test_db):
    """Test that soft-deleted items are preserved in historical bills."""
    # Create item
    item = inventory_service.add_item(
        name="Historical Item",
        category="Grocery",
        unit="kg",
        unit_price=Decimal("100.00"),
        stock_qty=Decimal("50")
    )

    # Create bill with item using cart workflow
    billing_service.create_bill_draft()
    billing_service.add_to_cart(item_id=item.id, quantity=Decimal("5"))
    bill = billing_service.confirm_bill(customer_name="Test Customer")

    # Soft-delete item
    inventory_service.update_item(item.id, is_active=False)

    # Query bill_items directly
    bill_items = test_db.query(BillItem).all()

    # Assert bill_items still has reference to deleted item (historical data preserved)
    assert len(bill_items) >= 1
    # Find the bill_item for our specific bill
    our_bill_item = next((bi for bi in bill_items if bi.bill_id == bill.id), None)
    assert our_bill_item is not None
    assert our_bill_item.item_id == item.id
    assert our_bill_item.quantity == Decimal("5")

    # Verify the item itself is soft-deleted
    deleted_item = test_db.query(Item).filter(Item.id == item.id).first()
    assert deleted_item.is_active is False
