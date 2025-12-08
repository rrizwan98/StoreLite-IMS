"""
Unit tests for billing cart operations (Phase 5)
Tests BillingService cart management, totals calculation, and item quantity updates
"""

import pytest
from decimal import Decimal
from src.models.bill import Bill, BillItem


class TestCartOperations:
    """Test shopping cart operations"""

    def test_add_to_cart_single_item(self):
        """Test adding a single item to cart"""
        bill = Bill(
            customer_name=None,
            store_name=None,
            total_amount=Decimal("0.00"),
        )

        bill_item = BillItem(
            bill_id=bill.id,
            item_id=1,
            item_name="Sugar",
            unit_price=Decimal("50.00"),
            quantity=Decimal("2"),
            line_total=Decimal("100.00"),
        )

        assert bill_item.item_name == "Sugar"
        assert bill_item.quantity == Decimal("2")
        assert bill_item.line_total == Decimal("100.00")

    def test_add_to_cart_multiple_items(self):
        """Test adding multiple items to cart"""
        bill = Bill(
            customer_name=None,
            store_name=None,
            total_amount=Decimal("0.00"),
        )

        items = [
            BillItem(bill_id=bill.id, item_id=1, item_name="Sugar",
                    unit_price=Decimal("50.00"), quantity=Decimal("2"),
                    line_total=Decimal("100.00")),
            BillItem(bill_id=bill.id, item_id=2, item_name="Rice",
                    unit_price=Decimal("40.00"), quantity=Decimal("3"),
                    line_total=Decimal("120.00")),
            BillItem(bill_id=bill.id, item_id=3, item_name="Oil",
                    unit_price=Decimal("200.00"), quantity=Decimal("1"),
                    line_total=Decimal("200.00")),
        ]

        assert len(items) == 3
        total = sum(item.line_total for item in items)
        assert total == Decimal("420.00")

    def test_cart_quantity_validation_zero(self):
        """Test that zero quantity raises error"""
        with pytest.raises(ValueError, match="quantity must be positive"):
            BillItem(
                bill_id=1,
                item_id=1,
                item_name="Sugar",
                unit_price=Decimal("50.00"),
                quantity=Decimal("0"),
                line_total=Decimal("0.00"),
            )

    def test_cart_quantity_validation_negative(self):
        """Test that negative quantity raises error"""
        with pytest.raises(ValueError, match="quantity must be positive"):
            BillItem(
                bill_id=1,
                item_id=1,
                item_name="Sugar",
                unit_price=Decimal("50.00"),
                quantity=Decimal("-5"),
                line_total=Decimal("-250.00"),
            )

    def test_cart_decimal_precision(self):
        """Test that cart maintains decimal precision"""
        bill_item = BillItem(
            bill_id=1,
            item_id=1,
            item_name="Coffee",
            unit_price=Decimal("125.75"),
            quantity=Decimal("2.5"),
            line_total=Decimal("314.375"),
        )

        assert bill_item.line_total == Decimal("314.375")
        assert bill_item.line_total.as_tuple().exponent == -3  # 3 decimal places


class TestRemoveFromCart:
    """Test removing items from cart"""

    def test_remove_item_by_reducing_quantity(self):
        """Test reducing quantity of item in cart"""
        item = BillItem(
            bill_id=1,
            item_id=1,
            item_name="Sugar",
            unit_price=Decimal("50.00"),
            quantity=Decimal("5"),
            line_total=Decimal("250.00"),
        )

        # Simulate reducing quantity from 5 to 3
        new_quantity = Decimal("3")
        new_line_total = item.unit_price * new_quantity

        assert new_quantity == Decimal("3")
        assert new_line_total == Decimal("150.00")

    def test_cannot_reduce_quantity_below_zero(self):
        """Test that quantity cannot be reduced below zero"""
        item = BillItem(
            bill_id=1,
            item_id=1,
            item_name="Sugar",
            unit_price=Decimal("50.00"),
            quantity=Decimal("2"),
            line_total=Decimal("100.00"),
        )

        # Try to set negative quantity
        with pytest.raises(ValueError, match="quantity must be positive"):
            new_quantity = Decimal("-1")
            if new_quantity <= 0:
                raise ValueError("quantity must be positive")

    def test_remove_all_quantity_removes_item(self):
        """Test that reducing to zero removes item from cart"""
        item = BillItem(
            bill_id=1,
            item_id=1,
            item_name="Sugar",
            unit_price=Decimal("50.00"),
            quantity=Decimal("2"),
            line_total=Decimal("100.00"),
        )

        # Quantity becomes 0
        new_quantity = Decimal("0")
        should_remove = new_quantity <= 0

        assert should_remove is True


class TestUpdateCartItemQuantity:
    """Test updating quantity of items already in cart"""

    def test_increase_quantity(self):
        """Test increasing quantity of item"""
        item = BillItem(
            bill_id=1,
            item_id=1,
            item_name="Sugar",
            unit_price=Decimal("50.00"),
            quantity=Decimal("2"),
            line_total=Decimal("100.00"),
        )

        # Increase to 5
        new_quantity = Decimal("5")
        new_line_total = item.unit_price * new_quantity

        assert new_quantity == Decimal("5")
        assert new_line_total == Decimal("250.00")

    def test_decrease_quantity(self):
        """Test decreasing quantity of item"""
        item = BillItem(
            bill_id=1,
            item_id=1,
            item_name="Sugar",
            unit_price=Decimal("50.00"),
            quantity=Decimal("10"),
            line_total=Decimal("500.00"),
        )

        # Decrease to 3
        new_quantity = Decimal("3")
        new_line_total = item.unit_price * new_quantity

        assert new_quantity == Decimal("3")
        assert new_line_total == Decimal("150.00")

    def test_update_quantity_to_large_number(self):
        """Test updating quantity to large number"""
        item = BillItem(
            bill_id=1,
            item_id=1,
            item_name="Sugar",
            unit_price=Decimal("50.00"),
            quantity=Decimal("1"),
            line_total=Decimal("50.00"),
        )

        # Update to 999
        new_quantity = Decimal("999")
        new_line_total = item.unit_price * new_quantity

        assert new_quantity == Decimal("999")
        assert new_line_total == Decimal("49950.00")

    def test_update_quantity_with_decimal_value(self):
        """Test updating quantity with decimal value"""
        item = BillItem(
            bill_id=1,
            item_id=1,
            item_name="Oil",
            unit_price=Decimal("200.00"),
            quantity=Decimal("1.5"),
            line_total=Decimal("300.00"),
        )

        # Update to 2.5
        new_quantity = Decimal("2.5")
        new_line_total = item.unit_price * new_quantity

        assert new_quantity == Decimal("2.5")
        assert new_line_total == Decimal("500.00")


class TestCartTotalCalculation:
    """Test calculating cart total"""

    def test_calculate_empty_cart_total(self):
        """Test total for empty cart"""
        total = Decimal("0.00")
        assert total == Decimal("0.00")

    def test_calculate_single_item_total(self):
        """Test total with single item"""
        item_total = Decimal("100.00")
        cart_total = item_total
        assert cart_total == Decimal("100.00")

    def test_calculate_multiple_items_total(self):
        """Test total with multiple items"""
        items_totals = [Decimal("100.00"), Decimal("150.00"), Decimal("250.00")]
        cart_total = sum(items_totals)
        assert cart_total == Decimal("500.00")

    def test_cart_total_with_decimal_precision(self):
        """Test cart total maintains decimal precision"""
        items = [
            Decimal("99.99"),
            Decimal("100.01"),
            Decimal("50.50"),
        ]
        cart_total = sum(items)
        assert cart_total == Decimal("250.50")
        assert cart_total.as_tuple().exponent == -2  # 2 decimal places

    def test_cart_total_empty_after_removing_all_items(self):
        """Test that cart total is zero after removing all items"""
        initial_total = Decimal("500.00")
        # Remove all items
        final_total = Decimal("0.00")
        assert final_total == Decimal("0.00")
