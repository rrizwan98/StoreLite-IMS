"""
CLI menu for listing items in inventory (T024)
"""

from src.services.inventory_service import InventoryService
from src.cli.ui_utils import (
    display_header,
    display_error,
    display_message,
    format_items_table,
)
from src.cli.error_handler import DatabaseError


def list_items_menu(db_session, sort_by: str = "name", active_only: bool = True):
    """
    Display all items in inventory as formatted table

    Args:
        db_session: SQLAlchemy session for database operations
        sort_by: Column to sort by ('name', 'category', 'price', 'stock')
        active_only: If True, only show active items
    """
    display_header("INVENTORY LIST")

    try:
        inventory_service = InventoryService(db_session)

        # Get items from inventory
        items = inventory_service.list_items(
            sort_by=sort_by,
            active_only=active_only
        )

        if not items:
            display_message(
                "No items in inventory." if active_only
                else "No items found."
            )
            return

        # Format and display as table
        table = format_items_table(items)
        print(table)

        # Display summary
        total_items = len(items)
        display_message(f"Total items: {total_items}")

        return items

    except DatabaseError as e:
        display_error(f"Database Error: {str(e)}")
    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
