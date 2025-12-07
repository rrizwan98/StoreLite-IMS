"""
CLI menu for updating item details (T026)
"""

from decimal import Decimal
from src.services.inventory_service import InventoryService
from src.cli.ui_utils import (
    display_header,
    display_error,
    display_success,
    format_single_item,
    get_numeric_input,
    confirm,
)
from src.cli.error_handler import ItemNotFoundError, ValidationError, DatabaseError


def update_item_menu(db_session):
    """
    Display menu for updating an existing item

    Args:
        db_session: SQLAlchemy session for database operations
    """
    display_header("UPDATE ITEM")

    try:
        # Get item ID
        item_id = get_numeric_input(
            prompt="Enter Item ID to update: ",
            min_val=1,
            max_val=999999,
            error_message="Please enter a valid Item ID"
        )

        inventory_service = InventoryService(db_session)

        # Get current item
        item = inventory_service.get_item(item_id)
        if not item:
            display_error(f"Item with ID {item_id} not found")
            return

        # Display current item details
        display_header("CURRENT ITEM DETAILS")
        print(format_single_item(item))

        # Ask what to update
        display_header("UPDATE OPTIONS")
        print("  1. Update Price")
        print("  2. Update Stock Quantity")
        print("  3. Update Both")
        print("  4. Cancel")

        choice = get_numeric_input(
            prompt="Select option (1-4): ",
            min_val=1,
            max_val=4,
            error_message="Please select a valid option (1-4)"
        )

        if choice == 4:
            display_error("Update cancelled.")
            return

        new_price = None
        new_stock = None

        # Get new price if needed
        if choice in [1, 3]:
            new_price = get_numeric_input(
                prompt="New Unit Price: ",
                min_val=Decimal("0.01"),
                max_val=Decimal("999999.99"),
                error_message="Price must be between 0.01 and 999999.99"
            )

        # Get new stock if needed
        if choice in [2, 3]:
            new_stock = get_numeric_input(
                prompt="New Stock Quantity: ",
                min_val=Decimal("0"),
                max_val=Decimal("999999.99"),
                error_message="Stock quantity must be between 0 and 999999.99"
            )

        # Display update summary
        display_header("UPDATE SUMMARY")
        if new_price:
            print(f"  Price: {item.unit_price} → {new_price}")
        if new_stock:
            print(f"  Stock: {item.stock_qty} → {new_stock}")

        # Confirm before updating
        if not confirm("Apply these changes?"):
            display_error("Update cancelled.")
            return

        # Update item
        updated_item = inventory_service.update_item(
            item_id=item_id,
            unit_price=new_price,
            stock_qty=new_stock
        )

        display_header("UPDATED ITEM DETAILS")
        print(format_single_item(updated_item))
        display_success(f"Item {item_id} updated successfully!")

        return updated_item

    except ItemNotFoundError as e:
        display_error(f"Item not found: {str(e)}")
    except ValidationError as e:
        display_error(f"Validation Error: {str(e)}")
    except DatabaseError as e:
        display_error(f"Database Error: {str(e)}")
    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
