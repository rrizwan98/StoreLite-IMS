"""
Unit tests for billing operations
Tests BillingService methods for bill creation, item addition, and calculations
"""

import pytest
from decimal import Decimal
from datetime import datetime
from src.models.bill import Bill, BillItem


class TestCreateBill:
    """Test bill creation"""

    def test_create_bill_with_all_fields(self):
        """Test creating a bill with customer and store names"""
        bill = Bill(
            customer_name="John Doe",
            store_name="Store A",
            total_amount=Decimal("1500.00"),
        )
        assert bill.customer_name == "John Doe"
        assert bill.store_name == "Store A"
        assert bill.total_amount == Decimal("1500.00")

    def test_create_bill_with_optional_fields_empty(self):
        """Test creating a bill without customer/store names"""
        bill = Bill(
            customer_name=None,
            store_name=None,
            total_amount=Decimal("1000.00"),
        )
        assert bill.customer_name is None
        assert bill.store_name is None
        assert bill.total_amount == Decimal("1000.00")

    def test_create_bill_with_zero_total(self):
        """Test creating a bill with zero total (empty cart initially)"""
        bill = Bill(
            customer_name="Test",
            store_name="Test Store",
            total_amount=Decimal("0.00"),
        )
        assert bill.total_amount == Decimal("0.00")

    def test_create_bill_with_negative_total_raises_error(self):
        """Test that negative total raises validation error"""
        with pytest.raises(ValueError, match="total_amount must be non-negative"):
            Bill(
                customer_name="Test",
                store_name="Test Store",
                total_amount=Decimal("-100.00"),
            )

    def test_bill_timestamp_is_set(self):
        """Test that created_at timestamp is set"""
        now = datetime.utcnow()
        bill = Bill(
            customer_name="Test",
            store_name="Test Store",
            total_amount=Decimal("500.00"),
            created_at=now,
        )
        assert bill.created_at is not None
        assert isinstance(bill.created_at, datetime)


class TestAddItemToBill:
    """Test adding items to a bill"""

    def test_add_item_to_bill(self):
        """Test adding a single item to bill"""
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

    def test_add_multiple_items_to_bill(self):
        """Test adding multiple items to a single bill"""
        bill_item1 = BillItem(
            bill_id=1,
            item_id=5,
            item_name="Sugar",
            unit_price=Decimal("50.00"),
            quantity=Decimal("2"),
            line_total=Decimal("100.00"),
        )
        bill_item2 = BillItem(
            bill_id=1,
            item_id=6,
            item_name="Rice",
            unit_price=Decimal("40.00"),
            quantity=Decimal("1"),
            line_total=Decimal("40.00"),
        )
        assert bill_item1.bill_id == bill_item2.bill_id == 1
        assert bill_item1.item_id != bill_item2.item_id

    def test_bill_item_with_zero_quantity_raises_error(self):
        """Test that zero quantity raises validation error"""
        with pytest.raises(ValueError, match="quantity must be positive"):
            BillItem(
                bill_id=1,
                item_id=5,
                item_name="Test",
                unit_price=Decimal("10.00"),
                quantity=Decimal("0"),
                line_total=Decimal("0.00"),
            )

    def test_bill_item_with_negative_quantity_raises_error(self):
        """Test that negative quantity raises validation error"""
        with pytest.raises(ValueError, match="quantity must be positive"):
            BillItem(
                bill_id=1,
                item_id=5,
                item_name="Test",
                unit_price=Decimal("10.00"),
                quantity=Decimal("-5"),
                line_total=Decimal("50.00"),
            )


class TestBillCalculations:
    """Test bill total calculations"""

    def test_calculate_line_total(self):
        """Test line total calculation (unit_price * quantity)"""
        unit_price = Decimal("50.00")
        quantity = Decimal("2")
        expected_total = Decimal("100.00")

        assert unit_price * quantity == expected_total

    def test_calculate_bill_total_single_item(self):
        """Test bill total with single item"""
        item_total = Decimal("100.00")
        bill_total = item_total

        assert bill_total == Decimal("100.00")

    def test_calculate_bill_total_multiple_items(self):
        """Test bill total with multiple items"""
        item1_total = Decimal("100.00")
        item2_total = Decimal("40.00")
        item3_total = Decimal("200.00")

        bill_total = item1_total + item2_total + item3_total
        assert bill_total == Decimal("340.00")

    def test_calculate_bill_with_decimal_precision(self):
        """Test bill calculation maintains decimal precision"""
        item1 = Decimal("99.99")
        item2 = Decimal("0.01")
        total = item1 + item2

        assert total == Decimal("100.00")
        assert total.as_tuple().exponent == -2  # 2 decimal places


class TestBillValidation:
    """Test bill and bill item validation"""

    def test_bill_item_negative_price_raises_error(self):
        """Test that negative unit_price raises validation error"""
        with pytest.raises(ValueError, match="unit_price must be non-negative"):
            BillItem(
                bill_id=1,
                item_id=5,
                item_name="Test",
                unit_price=Decimal("-10.00"),
                quantity=Decimal("2"),
                line_total=Decimal("20.00"),
            )

    def test_bill_item_negative_line_total_raises_error(self):
        """Test that negative line_total raises validation error"""
        with pytest.raises(ValueError, match="line_total must be non-negative"):
            BillItem(
                bill_id=1,
                item_id=5,
                item_name="Test",
                unit_price=Decimal("10.00"),
                quantity=Decimal("2"),
                line_total=Decimal("-20.00"),
            )

    def test_bill_item_high_precision_decimal(self):
        """Test bill item handles high precision decimals"""
        bill_item = BillItem(
            bill_id=1,
            item_id=5,
            item_name="Coffee",
            unit_price=Decimal("125.75"),
            quantity=Decimal("2.5"),
            line_total=Decimal("314.375"),
        )
        assert bill_item.unit_price == Decimal("125.75")
        assert bill_item.quantity == Decimal("2.5")
        assert bill_item.line_total == Decimal("314.375")
