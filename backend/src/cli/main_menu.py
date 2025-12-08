"""
Main CLI menu for IMS system (T028)
Routes all sub-menus for inventory and billing operations
Enhanced with statistics and better navigation (Phase 6)
"""

import sys
from src.cli.ui_utils import display_header, display_error, display_message, get_numeric_input
from src.cli.add_item import add_item_menu
from src.cli.list_items import list_items_menu
from src.cli.search_items import search_items_menu
from src.cli.update_item import update_item_menu
from src.cli.billing_menu import billing_menu
from src.cli.error_handler import IMSException
from src.services.inventory_service import InventoryService


def main_menu(db_session):
    """
    Display main menu with statistics and route to sub-menus
    Phase 6: Main menu integration with all workflows

    Args:
        db_session: SQLAlchemy session for database operations
    """
    while True:
        # Get inventory statistics
        inventory_service = InventoryService(db_session)
        try:
            all_items = inventory_service.list_items()
            item_count = len(all_items)
            active_items = len([i for i in all_items if i.is_active])
        except:
            item_count = 0
            active_items = 0

        display_header("INVENTORY MANAGEMENT SYSTEM")

        # Display system statistics
        print(f"\n  System Status: {active_items}/{item_count} Active Items\n")

        print("  INVENTORY OPERATIONS:")
        print("  ─────────────────────")
        print("  1. [I] Add New Item")
        print("  2. [L] List All Items")
        print("  3. [S] Search Items")
        print("  4. [U] Update Item")
        print("\n  BILLING OPERATIONS:")
        print("  ─────────────────────")
        print("  5. [B] Create Invoice")
        print("\n  SYSTEM:")
        print("  ─────────────────────")
        print("  6. [X] Exit")

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
