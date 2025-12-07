"""
CLI menu for billing operations (T027)
"""

from decimal import Decimal
from src.services.inventory_service import InventoryService
from src.services.billing_service import BillingService
from src.cli.ui_utils import (
    display_header,
    display_error,
    display_success,
    display_message,
    format_items_table,
    get_numeric_input,
    get_input_with_validation,
    confirm,
)
from src.services.validation_service import ValidationService
from src.cli.error_handler import (
    ItemNotFoundError,
    InsufficientStockError,
    ValidationError,
    DatabaseError,
)


def billing_menu(db_session):
    """
    Display billing menu for creating invoices

    Args:
        db_session: SQLAlchemy session for database operations
    """
    display_header("CREATE INVOICE")

    try:
        inventory_service = InventoryService(db_session)
        billing_service = BillingService(db_session)

        # Get customer and store info
        customer_name = get_input_with_validation(
            prompt="Customer Name (optional, press Enter to skip): ",
            validator=lambda x: (True, "") if not x or len(x) <= 255 else (False, "Name too long"),
            error_message="Invalid customer name"
        ) or None

        store_name = get_input_with_validation(
            prompt="Store Name (optional, press Enter to skip): ",
            validator=lambda x: (True, "") if not x or len(x) <= 255 else (False, "Name too long"),
            error_message="Invalid store name"
        ) or None

        # Create bill draft
        bill = billing_service.create_bill_draft(
            customer_name=customer_name,
            store_name=store_name
        )

        display_header(f"BILL #{bill.id} - ADD ITEMS")

        # Add items to bill
        while True:
            print("\n  1. Add Item")
            print("  2. View Cart")
            print("  3. Confirm & Pay")
            print("  4. Cancel Bill")

            choice = get_numeric_input(
                prompt="Select option (1-4): ",
                min_val=1,
                max_val=4,
                error_message="Please select a valid option (1-4)"
            )

            if choice == 1:
                # Add item to bill
                _add_item_to_bill(bill, inventory_service, billing_service, db_session)

            elif choice == 2:
                # View cart
                cart = billing_service.get_cart(bill.id)
                if not cart:
                    display_message("Cart is empty")
                else:
                    display_header("CURRENT CART")
                    _display_bill_items(cart)

            elif choice == 3:
                # Confirm bill
                cart = billing_service.get_cart(bill.id)
                if not cart:
                    display_error("Cannot create bill without items")
                    continue

                if not confirm("Confirm and finalize bill?"):
                    display_error("Bill not finalized")
                    continue

                # Confirm bill (deduct stock and save)
                final_bill = billing_service.confirm_bill(bill.id)
                display_header("BILL FINALIZED")
                _display_bill_items(final_bill.bill_items)
                print(f"\n  Total: {final_bill.total_amount}")
                display_success("Bill created successfully!")
                return final_bill

            elif choice == 4:
                # Cancel bill
                if confirm("Cancel this bill?"):
                    db_session.delete(bill)
                    db_session.commit()
                    display_error("Bill cancelled")
                    return None
                break

    except InsufficientStockError as e:
        display_error(f"Insufficient Stock: {str(e)}")
    except ItemNotFoundError as e:
        display_error(f"Item not found: {str(e)}")
    except ValidationError as e:
        display_error(f"Validation Error: {str(e)}")
    except DatabaseError as e:
        display_error(f"Database Error: {str(e)}")
    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")


def _add_item_to_bill(bill, inventory_service, billing_service, db_session):
    """Helper function to add an item to bill"""
    try:
        # Get item ID
        item_id = get_numeric_input(
            prompt="Enter Item ID: ",
            min_val=1,
            max_val=999999,
            error_message="Please enter a valid Item ID"
        )

        item = inventory_service.get_item(item_id)
        if not item:
            display_error(f"Item {item_id} not found")
            return

        # Get quantity
        quantity = get_numeric_input(
            prompt=f"Quantity (available: {item.stock_qty}): ",
            min_val=Decimal("0.01"),
            max_val=item.stock_qty,
            error_message=f"Quantity must be between 0.01 and {item.stock_qty}"
        )

        # Add to cart
        bill_item = billing_service.add_to_cart(
            bill_id=bill.id,
            item_id=item_id,
            quantity=quantity
        )

        display_success(f"Added {quantity} x {item.name} to cart")

    except InsufficientStockError as e:
        display_error(f"Insufficient Stock: {str(e)}")
    except ItemNotFoundError as e:
        display_error(f"Item not found: {str(e)}")
    except Exception as e:
        display_error(f"Error adding item: {str(e)}")


def _display_bill_items(bill_items):
    """Helper function to display bill items"""
    if not bill_items:
        display_message("No items in bill")
        return

    print("\n  ID  Item Name           Unit Price  Qty    Total")
    print("  " + "-" * 55)
    for item in bill_items:
        print(f"  {item.item_id:<3} {item.item_name:<17} {item.unit_price:>10}  "
              f"{item.quantity:>6}  {item.line_total:>10}")
