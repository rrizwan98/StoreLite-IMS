"""
Main CLI menu for IMS system (T028)
Routes all sub-menus for inventory and billing operations
"""

import sys
from src.cli.ui_utils import display_header, display_error, display_message, get_numeric_input
from src.cli.add_item import add_item_menu
from src.cli.list_items import list_items_menu
from src.cli.search_items import search_items_menu
from src.cli.update_item import update_item_menu
from src.cli.billing_menu import billing_menu
from src.cli.error_handler import IMSException


def main_menu(db_session):
    """
    Display main menu and route to sub-menus

    Args:
        db_session: SQLAlchemy session for database operations
    """
    while True:
        display_header("INVENTORY MANAGEMENT SYSTEM")

        print("  1. Add New Item")
        print("  2. List All Items")
        print("  3. Search Items")
        print("  4. Update Item")
        print("  5. Create Invoice")
        print("  6. Exit")

        try:
            choice = get_numeric_input(
                prompt="Select option (1-6): ",
                min_val=1,
                max_val=6,
                error_message="Please select a valid option (1-6)"
            )

            if choice == 1:
                add_item_menu(db_session)

            elif choice == 2:
                list_items_menu(db_session)

            elif choice == 3:
                search_items_menu(db_session)

            elif choice == 4:
                update_item_menu(db_session)

            elif choice == 5:
                billing_menu(db_session)

            elif choice == 6:
                display_message("Thank you for using IMS. Goodbye!")
                sys.exit(0)

            # Pause before returning to main menu
            input("\nPress Enter to continue...")

        except IMSException as e:
            display_error(f"Error: {str(e)}")
        except KeyboardInterrupt:
            display_message("\nExiting...")
            sys.exit(0)
        except Exception as e:
            display_error(f"Unexpected error: {str(e)}")
