"""
CLI menu for searching items in inventory (T025)
"""

from src.services.inventory_service import InventoryService
from src.cli.ui_utils import (
    display_header,
    display_error,
    display_message,
    format_items_table,
    get_input_with_validation,
)
from src.services.validation_service import ValidationService
from src.cli.error_handler import DatabaseError


def search_items_menu(db_session):
    """
    Display search menu for finding items in inventory

    Args:
        db_session: SQLAlchemy session for database operations
    """
    display_header("SEARCH ITEMS")

    try:
        search_term = get_input_with_validation(
            prompt="Enter item name to search: ",
            validator=ValidationService.validate_item_name,
            error_message="Search term is required"
        )

        inventory_service = InventoryService(db_session)

        # Search items
        results = inventory_service.search_items(search_term)

        if not results:
            display_message(f"No items found matching '{search_term}'")
            return

        # Format and display results
        display_header("SEARCH RESULTS")
        table = format_items_table(results)
        print(table)

        # Display summary
        display_message(f"Found {len(results)} item(s)")

        return results

    except DatabaseError as e:
        display_error(f"Database Error: {str(e)}")
    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
