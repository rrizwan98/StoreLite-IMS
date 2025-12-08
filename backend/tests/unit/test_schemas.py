"""
Unit tests for Pydantic schemas
"""

import pytest
from decimal import Decimal
from app.schemas import ItemCreate, ItemUpdate, ItemResponse, BillCreate, BillItemCreate, BillItemResponse, BillResponse


class TestItemCreateSchema:
    """Test ItemCreate request schema validation"""

    def test_valid_item_creation(self):
        """Test valid item creation payload passes validation"""
        data = {
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "100.000",
        }
        item = ItemCreate(**data)
        assert item.name == "Sugar"
        assert item.category == "Grocery"
        assert item.unit == "kg"
        assert item.unit_price == Decimal("10.50")
        assert item.stock_qty == Decimal("100.000")

    def test_negative_unit_price_rejected(self):
        """Test negative unit_price is rejected"""
        data = {
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "-10.50",
            "stock_qty": "100.000",
        }
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ItemCreate(**data)

    def test_negative_stock_qty_rejected(self):
        """Test negative stock_qty is rejected"""
        data = {
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "10.50",
            "stock_qty": "-100.000",
        }
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ItemCreate(**data)

    def test_missing_required_fields_rejected(self):
        """Test missing required fields are rejected"""
        with pytest.raises(ValueError):
            ItemCreate(name="Sugar", category="Grocery")  # Missing unit, unit_price, stock_qty

    def test_zero_price_accepted(self):
        """Test zero price is accepted"""
        data = {
            "name": "Free Item",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "0.00",
            "stock_qty": "100.000",
        }
        item = ItemCreate(**data)
        assert item.unit_price == Decimal("0.00")

    def test_decimal_quantities_accepted(self):
        """Test decimal quantities are accepted (e.g., 100.5 for 100.5kg)"""
        data = {
            "name": "Flour",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": "5.50",
            "stock_qty": "100.500",
        }
        item = ItemCreate(**data)
        assert item.stock_qty == Decimal("100.500")


class TestItemUpdateSchema:
    """Test ItemUpdate request schema validation"""

    def test_all_fields_optional(self):
        """Test all fields in update are optional"""
        item = ItemUpdate()
        assert item.name is None
        assert item.category is None
        assert item.unit is None
        assert item.unit_price is None
        assert item.stock_qty is None

    def test_partial_update(self):
        """Test partial update with some fields"""
        data = {"unit_price": "15.00"}
        item = ItemUpdate(**data)
        assert item.unit_price == Decimal("15.00")
        assert item.name is None
        assert item.category is None

    def test_negative_price_rejected(self):
        """Test negative price is rejected"""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ItemUpdate(unit_price="-10.00")

    def test_negative_stock_rejected(self):
        """Test negative stock is rejected"""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ItemUpdate(stock_qty="-50.000")


class TestBillItemCreateSchema:
    """Test BillItemCreate request schema validation"""

    def test_valid_bill_item(self):
        """Test valid bill item creation"""
        data = {"item_id": 1, "quantity": "10.000"}
        bill_item = BillItemCreate(**data)
        assert bill_item.item_id == 1
        assert bill_item.quantity == Decimal("10.000")

    def test_zero_quantity_rejected(self):
        """Test zero quantity is rejected"""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            BillItemCreate(item_id=1, quantity="0")

    def test_negative_quantity_rejected(self):
        """Test negative quantity is rejected"""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            BillItemCreate(item_id=1, quantity="-5.000")

    def test_decimal_quantity_accepted(self):
        """Test decimal quantity is accepted"""
        data = {"item_id": 1, "quantity": "2.500"}
        bill_item = BillItemCreate(**data)
        assert bill_item.quantity == Decimal("2.500")


class TestBillCreateSchema:
    """Test BillCreate request schema validation"""

    def test_valid_bill_creation(self):
        """Test valid bill creation"""
        data = {
            "items": [{"item_id": 1, "quantity": "10.000"}],
            "customer_name": "John Doe",
            "store_name": "Store 1",
        }
        bill = BillCreate(**data)
        assert len(bill.items) == 1
        assert bill.customer_name == "John Doe"

    def test_empty_items_array_rejected(self):
        """Test empty items array is rejected"""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            BillCreate(items=[], customer_name="John")

    def test_optional_customer_and_store_names(self):
        """Test optional customer and store names"""
        data = {"items": [{"item_id": 1, "quantity": "10.000"}]}
        bill = BillCreate(**data)
        assert bill.customer_name is None
        assert bill.store_name is None

    def test_multiple_items(self):
        """Test bill with multiple items"""
        data = {
            "items": [
                {"item_id": 1, "quantity": "5.000"},
                {"item_id": 2, "quantity": "10.000"},
            ],
        }
        bill = BillCreate(**data)
        assert len(bill.items) == 2
