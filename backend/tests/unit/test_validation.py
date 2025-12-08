"""
Unit tests for ValidationService
Tests validation logic for categories, units, prices, and quantities
"""

import pytest
from decimal import Decimal
from src.services.validation import ValidationService


class TestCategoryValidation:
    """Test category validation"""

    def test_valid_categories(self):
        """Test that all valid categories pass validation"""
        valid_categories = ["Grocery", "Garments", "Beauty", "Utilities", "Other"]
        for category in valid_categories:
            is_valid, error_msg = ValidationService.validate_category(category)
            assert is_valid, f"Category '{category}' should be valid"
            assert error_msg == ""

    def test_invalid_categories(self):
        """Test that invalid categories fail validation"""
        invalid_categories = ["Food", "Clothing", "Invalid", ""]
        for category in invalid_categories:
            is_valid, error_msg = ValidationService.validate_category(category)
            assert not is_valid, f"Category '{category}' should be invalid"
            assert len(error_msg) > 0

    def test_category_case_sensitive(self):
        """Test that category validation is case-sensitive"""
        is_valid, _ = ValidationService.validate_category("grocery")  # lowercase
        assert not is_valid, "Category validation should be case-sensitive"

    def test_category_none(self):
        """Test that None category fails validation"""
        is_valid, error_msg = ValidationService.validate_category(None)
        assert not is_valid


class TestUnitValidation:
    """Test unit validation"""

    def test_valid_units(self):
        """Test that all valid units pass validation"""
        valid_units = ["kg", "g", "liter", "ml", "piece", "box", "pack", "other"]
        for unit in valid_units:
            is_valid, error_msg = ValidationService.validate_unit(unit)
            assert is_valid, f"Unit '{unit}' should be valid"
            assert error_msg == ""

    def test_invalid_units(self):
        """Test that invalid units fail validation"""
        invalid_units = ["kilometer", "meter", "invalid", ""]
        for unit in invalid_units:
            is_valid, error_msg = ValidationService.validate_unit(unit)
            assert not is_valid, f"Unit '{unit}' should be invalid"
            assert len(error_msg) > 0

    def test_unit_case_sensitive(self):
        """Test that unit validation is case-sensitive"""
        is_valid, _ = ValidationService.validate_unit("KG")  # uppercase
        assert not is_valid, "Unit validation should be case-sensitive"

    def test_unit_none(self):
        """Test that None unit fails validation"""
        is_valid, error_msg = ValidationService.validate_unit(None)
        assert not is_valid


class TestPriceValidation:
    """Test price validation"""

    def test_valid_prices(self):
        """Test that valid prices pass validation"""
        valid_prices = [0, "0", "100.50", 100.50, Decimal("99.99")]
        for price in valid_prices:
            is_valid, error_msg = ValidationService.validate_price(price)
            assert is_valid, f"Price '{price}' should be valid"
            assert error_msg == ""

    def test_negative_price(self):
        """Test that negative prices fail validation"""
        negative_prices = [-1, "-10.50", Decimal("-100")]
        for price in negative_prices:
            is_valid, _ = ValidationService.validate_price(price)
            assert not is_valid, f"Price '{price}' should be invalid (negative)"

    def test_non_numeric_price(self):
        """Test that non-numeric prices fail validation"""
        invalid_prices = ["abc", "10.20.30", None]
        for price in invalid_prices:
            is_valid, _ = ValidationService.validate_price(price)
            assert not is_valid, f"Price '{price}' should be invalid (non-numeric)"

    def test_price_precision(self):
        """Test that decimal prices are accepted"""
        is_valid, _ = ValidationService.validate_price("99.99")
        assert is_valid, "Decimal prices should be valid"

        is_valid, _ = ValidationService.validate_price("100.999")  # 3 decimal places
        assert is_valid, "Prices with more than 2 decimal places should still be valid"


class TestQuantityValidation:
    """Test quantity validation"""

    def test_valid_quantities(self):
        """Test that valid quantities pass validation"""
        valid_quantities = ["1", 10, 50.5, Decimal("100.25")]
        for qty in valid_quantities:
            is_valid, error_msg = ValidationService.validate_quantity(qty)
            assert is_valid, f"Quantity '{qty}' should be valid"
            assert error_msg == ""

    def test_zero_quantity(self):
        """Test that zero quantity fails validation"""
        is_valid, _ = ValidationService.validate_quantity(0)
        assert not is_valid, "Zero quantity should be invalid"

    def test_negative_quantity(self):
        """Test that negative quantities fail validation"""
        negative_quantities = [-1, "-5", Decimal("-10")]
        for qty in negative_quantities:
            is_valid, _ = ValidationService.validate_quantity(qty)
            assert not is_valid, f"Quantity '{qty}' should be invalid"

    def test_non_numeric_quantity(self):
        """Test that non-numeric quantities fail validation"""
        invalid_quantities = ["abc", "10.20.30", None]
        for qty in invalid_quantities:
            is_valid, _ = ValidationService.validate_quantity(qty)
            assert not is_valid, f"Quantity '{qty}' should be invalid"

    def test_very_small_quantity(self):
        """Test that very small positive quantities are valid"""
        is_valid, _ = ValidationService.validate_quantity("0.01")
        assert is_valid, "Very small positive quantities should be valid"


class TestNonNegativeValidation:
    """Test non-negative validation (for stock quantities)"""

    def test_valid_non_negative(self):
        """Test that non-negative values pass validation"""
        valid_values = [0, "0", "100.50", 100.50, Decimal("0.01")]
        for value in valid_values:
            is_valid, error_msg = ValidationService.validate_non_negative(value)
            assert is_valid, f"Value '{value}' should be valid"
            assert error_msg == ""

    def test_negative_value(self):
        """Test that negative values fail validation"""
        is_valid, _ = ValidationService.validate_non_negative("-1")
        assert not is_valid, "Negative values should be invalid"

    def test_non_numeric_value(self):
        """Test that non-numeric values fail validation"""
        is_valid, _ = ValidationService.validate_non_negative("abc")
        assert not is_valid, "Non-numeric values should be invalid"


class TestItemNameValidation:
    """Test item name validation"""

    def test_valid_item_names(self):
        """Test that valid item names pass validation"""
        valid_names = ["Sugar", "Rice 5kg", "Oil - Premium", "ABC123"]
        for name in valid_names:
            is_valid, error_msg = ValidationService.validate_item_name(name)
            assert is_valid, f"Item name '{name}' should be valid"
            assert error_msg == ""

    def test_empty_item_name(self):
        """Test that empty item name fails validation"""
        is_valid, _ = ValidationService.validate_item_name("")
        assert not is_valid, "Empty item name should be invalid"

    def test_whitespace_only_item_name(self):
        """Test that whitespace-only item name fails validation"""
        is_valid, _ = ValidationService.validate_item_name("   ")
        assert not is_valid, "Whitespace-only item name should be invalid"

    def test_none_item_name(self):
        """Test that None item name fails validation"""
        is_valid, _ = ValidationService.validate_item_name(None)
        assert not is_valid, "None item name should be invalid"

    def test_item_name_max_length(self):
        """Test that item name respects max length"""
        short_name = "A" * 255
        is_valid, _ = ValidationService.validate_item_name(short_name)
        assert is_valid, "Item name at max length should be valid"

        long_name = "A" * 256
        is_valid, _ = ValidationService.validate_item_name(long_name)
        assert not is_valid, "Item name exceeding max length should be invalid"
