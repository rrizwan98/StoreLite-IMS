"""
CLI menu for searching items in inventory (T025)
Enhanced with category and price range search in Phase 4
"""

from decimal import Decimal
from src.services.inventory_service import InventoryService
from src.cli.ui_utils import (
    display_header,
    display_error,
    display_message,
    format_items_table,
    get_input_with_validation,
)
from src.services.validation import ValidationService
from src.cli.error_handler import DatabaseError


def search_items_menu(db_session):
    """
    Display search menu for finding items in inventory
    Offers multiple search options: name, category, price range

    Args:
        db_session: SQLAlchemy session for database operations
    """
    display_header("SEARCH ITEMS")

    try:
        print("\nSearch Options:")
        print("1. Search by item name")
        print("2. Search by category")
        print("3. Search by price range")

        choice = input("\nSelect search type (1-3): ").strip()

        inventory_service = InventoryService(db_session)
        results = []

        if choice == "1":
            results = _search_by_name(inventory_service)
        elif choice == "2":
            results = _search_by_category(inventory_service)
        elif choice == "3":
            results = _search_by_price_range(inventory_service)
        else:
            display_error("Invalid choice. Please select 1, 2, or 3.")
            return

        if not results:
            display_message("No items found matching your criteria")
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


def _search_by_name(inventory_service):
    """Search items by name"""
    search_term = get_input_with_validation(
        prompt="Enter item name to search: ",
        validator_func=ValidationService.validate_item_name
    )
    return inventory_service.search_items(search_term)


def _search_by_category(inventory_service):
    """Search items by category"""
    print("\nValid categories: Grocery, Garments, Beauty, Utilities, Other")
    category = get_input_with_validation(
        prompt="Enter category: ",
        validator_func=lambda x: x.strip() if x.strip() else None
    )
    results = inventory_service.search_by_category(category)
    return results


def _search_by_price_range(inventory_service):
    """Search items by price range"""
    try:
        min_price_str = get_input_with_validation(
            prompt="Enter minimum price: ",
            validator_func=lambda x: x.strip() if x.strip() else None
        )
        min_price = Decimal(min_price_str)

        max_price_str = get_input_with_validation(
            prompt="Enter maximum price: ",
            validator_func=lambda x: x.strip() if x.strip() else None
        )
        max_price = Decimal(max_price_str)

        if min_price > max_price:
            display_error("Minimum price cannot be greater than maximum price")
            return []

        results = inventory_service.search_by_price_range(min_price, max_price)
        return results
    except (ValueError, Decimal) as e:
        display_error(f"Invalid price format. Please enter valid decimal numbers.")
        return []
