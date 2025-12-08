"""
Unit tests for ORM models (Item, Bill, BillItem)
Tests model creation, field validation, and constraints
"""

import pytest
from decimal import Decimal
from datetime import datetime
from src.models.item import Item
from src.models.bill import Bill, BillItem


class TestItemModel:
    """Test Item model"""

    def test_create_item_with_valid_data(self):
        """Test creating an item with valid data"""
        item = Item(
            name="Sugar",
            category="Grocery",
            unit="kg",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100"),
            is_active=True,
        )
        assert item.name == "Sugar"
        assert item.category == "Grocery"
        assert item.unit == "kg"
        assert item.unit_price == Decimal("50.00")
        assert item.stock_qty == Decimal("100")
        assert item.is_active is True

    def test_item_default_is_active_explicit(self):
        """Test that is_active can be set to True"""
        item = Item(
            name="Rice",
            category="Grocery",
            unit="kg",
            unit_price=Decimal("40.00"),
            stock_qty=Decimal("50"),
            is_active=True,
        )
        assert item.is_active is True

    def test_item_timestamps_are_set_explicitly(self):
        """Test that created_at and updated_at can be set"""
        now = datetime.utcnow()
        item = Item(
            name="Oil",
            category="Grocery",
            unit="liter",
            unit_price=Decimal("200.00"),
            stock_qty=Decimal("20"),
            created_at=now,
            updated_at=now,
        )
        assert item.created_at is not None
        assert item.updated_at is not None
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)

    def test_item_invalid_category_raises_error(self):
        """Test that invalid category raises validation error"""
        with pytest.raises(ValueError, match="Invalid category"):
            item = Item(
                name="Invalid",
                category="InvalidCategory",
                unit="kg",
                unit_price=Decimal("10.00"),
                stock_qty=Decimal("5"),
            )

    def test_item_invalid_unit_raises_error(self):
        """Test that invalid unit raises validation error"""
        with pytest.raises(ValueError, match="Invalid unit"):
            item = Item(
                name="Invalid",
                category="Grocery",
                unit="InvalidUnit",
                unit_price=Decimal("10.00"),
                stock_qty=Decimal("5"),
            )

    def test_item_negative_price_raises_error(self):
        """Test that negative price raises validation error"""
        with pytest.raises(ValueError, match="unit_price must be non-negative"):
            item = Item(
                name="Test",
                category="Grocery",
                unit="kg",
                unit_price=Decimal("-10.00"),
                stock_qty=Decimal("5"),
            )

    def test_item_negative_stock_raises_error(self):
        """Test that negative stock raises validation error"""
        with pytest.raises(ValueError, match="stock_qty must be non-negative"):
            item = Item(
                name="Test",
                category="Grocery",
                unit="kg",
                unit_price=Decimal("10.00"),
                stock_qty=Decimal("-5"),
            )

    def test_item_to_dict(self):
        """Test converting item to dictionary"""
        now = datetime.utcnow()
        item = Item(
            name="Sugar",
            category="Grocery",
            unit="kg",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100"),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        item.id = 1
        item_dict = item.to_dict()

        assert item_dict["id"] == 1
        assert item_dict["name"] == "Sugar"
        assert item_dict["category"] == "Grocery"
        assert item_dict["unit"] == "kg"
        assert item_dict["unit_price"] == 50.00
        assert item_dict["stock_qty"] == 100.00
        assert item_dict["is_active"] is True

    def test_item_repr(self):
        """Test item string representation"""
        item = Item(
            name="Rice",
            category="Grocery",
            unit="kg",
            unit_price=Decimal("40.00"),
            stock_qty=Decimal("50"),
        )
        item.id = 5
        repr_str = repr(item)
        assert "Rice" in repr_str
        assert "Grocery" in repr_str
        assert "id=5" in repr_str


class TestBillModel:
    """Test Bill model"""

    def test_create_bill_with_valid_data(self):
        """Test creating a bill with valid data"""
        bill = Bill(
            customer_name="John Doe",
            store_name="Store A",
            total_amount=Decimal("1500.00"),
        )
        assert bill.customer_name == "John Doe"
        assert bill.store_name == "Store A"
        assert bill.total_amount == Decimal("1500.00")

    def test_bill_customer_and_store_optional(self):
        """Test that customer and store names are optional"""
        bill = Bill(
            customer_name=None,
            store_name=None,
            total_amount=Decimal("1000.00"),
        )
        assert bill.customer_name is None
        assert bill.store_name is None
        assert bill.total_amount == Decimal("1000.00")

    def test_bill_timestamp_is_set(self):
        """Test that created_at is set"""
        now = datetime.utcnow()
        bill = Bill(
            customer_name="Test",
            store_name="Test Store",
            total_amount=Decimal("500.00"),
            created_at=now,
        )
        assert bill.created_at is not None
        assert isinstance(bill.created_at, datetime)

    def test_bill_negative_total_raises_error(self):
        """Test that negative total_amount raises validation error"""
        with pytest.raises(ValueError, match="total_amount must be non-negative"):
            bill = Bill(
                customer_name="Test",
                store_name="Test Store",
                total_amount=Decimal("-100.00"),
            )

    def test_bill_to_dict(self):
        """Test converting bill to dictionary"""
        bill = Bill(
            customer_name="John",
            store_name="Store",
            total_amount=Decimal("1500.00"),
        )
        bill.id = 10
        bill_dict = bill.to_dict()

        assert bill_dict["id"] == 10
        assert bill_dict["customer_name"] == "John"
        assert bill_dict["store_name"] == "Store"
        assert bill_dict["total_amount"] == 1500.00
        assert isinstance(bill_dict["bill_items"], list)

    def test_bill_repr(self):
        """Test bill string representation"""
        bill = Bill(
            customer_name="Jane",
            store_name="Shop",
            total_amount=Decimal("2000.00"),
        )
        bill.id = 7
        repr_str = repr(bill)
        assert "Jane" in repr_str
        assert "Shop" in repr_str
        assert "id=7" in repr_str


class TestBillItemModel:
    """Test BillItem model"""

    def test_create_bill_item_with_valid_data(self):
        """Test creating a bill item with valid data"""
        bill_item = BillItem(
            bill_id=1,
            item_id=5,
            item_name="Sugar",
            unit_price=Decimal("50.00"),
            quantity=Decimal("2"),
            line_total=Decimal("100.00"),
        )
        assert bill_item.bill_id == 1
        assert bill_item.item_id == 5
        assert bill_item.item_name == "Sugar"
        assert bill_item.unit_price == Decimal("50.00")
        assert bill_item.quantity == Decimal("2")
        assert bill_item.line_total == Decimal("100.00")

    def test_bill_item_timestamp_is_set(self):
        """Test that created_at is set"""
        now = datetime.utcnow()
        bill_item = BillItem(
            bill_id=1,
            item_id=5,
            item_name="Rice",
            unit_price=Decimal("40.00"),
            quantity=Decimal("5"),
            line_total=Decimal("200.00"),
            created_at=now,
        )
        assert bill_item.created_at is not None
        assert isinstance(bill_item.created_at, datetime)

    def test_bill_item_negative_price_raises_error(self):
        """Test that negative unit_price raises validation error"""
        with pytest.raises(ValueError, match="unit_price must be non-negative"):
            bill_item = BillItem(
                bill_id=1,
                item_id=5,
                item_name="Test",
                unit_price=Decimal("-10.00"),
                quantity=Decimal("2"),
                line_total=Decimal("20.00"),
            )

    def test_bill_item_zero_quantity_raises_error(self):
        """Test that zero quantity raises validation error"""
        with pytest.raises(ValueError, match="quantity must be positive"):
            bill_item = BillItem(
                bill_id=1,
                item_id=5,
                item_name="Test",
                unit_price=Decimal("10.00"),
                quantity=Decimal("0"),
                line_total=Decimal("0.00"),
            )

    def test_bill_item_negative_quantity_raises_error(self):
        """Test that negative quantity raises validation error"""
        with pytest.raises(ValueError, match="quantity must be positive"):
            bill_item = BillItem(
                bill_id=1,
                item_id=5,
                item_name="Test",
                unit_price=Decimal("10.00"),
                quantity=Decimal("-5"),
                line_total=Decimal("50.00"),
            )

    def test_bill_item_negative_line_total_raises_error(self):
        """Test that negative line_total raises validation error"""
        with pytest.raises(ValueError, match="line_total must be non-negative"):
            bill_item = BillItem(
                bill_id=1,
                item_id=5,
                item_name="Test",
                unit_price=Decimal("10.00"),
                quantity=Decimal("2"),
                line_total=Decimal("-20.00"),
            )

    def test_bill_item_to_dict(self):
        """Test converting bill item to dictionary"""
        bill_item = BillItem(
            bill_id=1,
            item_id=5,
            item_name="Sugar",
            unit_price=Decimal("50.00"),
            quantity=Decimal("2"),
            line_total=Decimal("100.00"),
        )
        bill_item.id = 15
        item_dict = bill_item.to_dict()

        assert item_dict["id"] == 15
        assert item_dict["bill_id"] == 1
        assert item_dict["item_id"] == 5
        assert item_dict["item_name"] == "Sugar"
        assert item_dict["unit_price"] == 50.00
        assert item_dict["quantity"] == 2.00
        assert item_dict["line_total"] == 100.00

    def test_bill_item_repr(self):
        """Test bill item string representation"""
        bill_item = BillItem(
            bill_id=2,
            item_id=10,
            item_name="Oil",
            unit_price=Decimal("200.00"),
            quantity=Decimal("1"),
            line_total=Decimal("200.00"),
        )
        bill_item.id = 25
        repr_str = repr(bill_item)
        assert "Oil" in repr_str
        assert "bill_id=2" in repr_str
        assert "qty=1" in repr_str
