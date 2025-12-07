"""
Validation service for inventory and billing operations
"""

from decimal import Decimal, InvalidOperation


class ValidationService:
    """Service for validating user input"""

    VALID_CATEGORIES = ["Grocery", "Garments", "Beauty", "Utilities", "Other"]
    VALID_UNITS = ["kg", "g", "liter", "ml", "piece", "box", "pack", "other"]

    @classmethod
    def validate_category(cls, category: str) -> tuple[bool, str]:
        """
        Validate category

        Args:
            category: Category name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not category or not isinstance(category, str):
            return False, "Category must be a non-empty string"
        if category not in cls.VALID_CATEGORIES:
            return False, f"Invalid category. Must be one of: {', '.join(cls.VALID_CATEGORIES)}"
        return True, ""

    @classmethod
    def validate_unit(cls, unit: str) -> tuple[bool, str]:
        """
        Validate unit

        Args:
            unit: Unit name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not unit or not isinstance(unit, str):
            return False, "Unit must be a non-empty string"
        if unit not in cls.VALID_UNITS:
            return False, f"Invalid unit. Must be one of: {', '.join(cls.VALID_UNITS)}"
        return True, ""

    @classmethod
    def validate_price(cls, price: str | float | Decimal) -> tuple[bool, str]:
        """
        Validate price (must be non-negative number)

        Args:
            price: Price to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            price_decimal = Decimal(str(price))
            if price_decimal < 0:
                return False, "Price must be non-negative"
            return True, ""
        except (InvalidOperation, ValueError, TypeError):
            return False, "Price must be a valid number"

    @classmethod
    def validate_quantity(cls, qty: str | float | Decimal) -> tuple[bool, str]:
        """
        Validate quantity (must be positive number)

        Args:
            qty: Quantity to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            qty_decimal = Decimal(str(qty))
            if qty_decimal <= 0:
                return False, "Quantity must be greater than 0"
            return True, ""
        except (InvalidOperation, ValueError, TypeError):
            return False, "Quantity must be a valid number"

    @classmethod
    def validate_non_negative(cls, value: str | float | Decimal) -> tuple[bool, str]:
        """
        Validate non-negative number (for stock quantity)

        Args:
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            value_decimal = Decimal(str(value))
            if value_decimal < 0:
                return False, "Value must be non-negative"
            return True, ""
        except (InvalidOperation, ValueError, TypeError):
            return False, "Value must be a valid number"

    @classmethod
    def validate_item_name(cls, name: str) -> tuple[bool, str]:
        """
        Validate item name

        Args:
            name: Item name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name or not isinstance(name, str):
            return False, "Item name must be a non-empty string"
        if len(name.strip()) == 0:
            return False, "Item name cannot be empty or whitespace"
        if len(name) > 255:
            return False, "Item name must be 255 characters or less"
        return True, ""
