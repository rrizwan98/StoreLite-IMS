"""
CLI menu for adding items to inventory (T023)
"""

from decimal import Decimal
from src.services.inventory_service import InventoryService
from src.services.validation_service import ValidationService
from src.cli.ui_utils import (
    display_header,
    display_error,
    display_success,
    get_input_with_validation,
    get_numeric_input,
    confirm,
)
from src.cli.error_handler import ValidationError, DatabaseError


def add_item_menu(db_session):
    """
    Display menu for adding a new item to inventory

    Args:
        db_session: SQLAlchemy session for database operations
    """
    display_header("ADD NEW ITEM")

    try:
        # Get item name
        item_name = get_input_with_validation(
            prompt="Item Name: ",
            validator=ValidationService.validate_item_name,
            error_message="Item name is required and must not exceed 255 characters"
        )

        # Get category
        display_header("AVAILABLE CATEGORIES")
        categories = ["Grocery", "Garments", "Beauty", "Utilities", "Other"]
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat}")

        category_choice = get_numeric_input(
            prompt="Select Category (1-5): ",
            min_val=1,
            max_val=5,
            error_message="Please select a valid category (1-5)"
        )
        category = categories[category_choice - 1]

        # Get unit
        display_header("AVAILABLE UNITS")
        units = ["kg", "g", "liter", "ml", "piece", "box", "pack", "other"]
        for i, unit in enumerate(units, 1):
            print(f"  {i}. {unit}")

        unit_choice = get_numeric_input(
            prompt="Select Unit (1-8): ",
            min_val=1,
            max_val=8,
            error_message="Please select a valid unit (1-8)"
        )
        unit = units[unit_choice - 1]

        # Get unit price
        unit_price = get_numeric_input(
            prompt="Unit Price: ",
            min_val=Decimal("0.01"),
            max_val=Decimal("999999.99"),
            error_message="Price must be between 0.01 and 999999.99"
        )

        # Get stock quantity
        stock_qty = get_numeric_input(
            prompt="Initial Stock Quantity: ",
            min_val=Decimal("0"),
            max_val=Decimal("999999.99"),
            error_message="Stock quantity must be between 0 and 999999.99"
        )

        # Display summary
        display_header("ITEM SUMMARY")
        print(f"  Name:     {item_name}")
        print(f"  Category: {category}")
        print(f"  Unit:     {unit}")
        print(f"  Price:    {unit_price}")
        print(f"  Stock:    {stock_qty}")

        # Confirm before adding
        if not confirm("Add this item?"):
            display_error("Item addition cancelled.")
            return

        # Add item to inventory
        inventory_service = InventoryService(db_session)
        item = inventory_service.add_item(
            name=item_name,
            category=category,
            unit=unit,
            unit_price=unit_price,
            stock_qty=stock_qty,
            is_active=True
        )

        display_success(f"Item '{item_name}' (ID: {item.id}) added successfully!")
        return item

    except ValidationError as e:
        display_error(f"Validation Error: {str(e)}")
    except DatabaseError as e:
        display_error(f"Database Error: {str(e)}")
    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
