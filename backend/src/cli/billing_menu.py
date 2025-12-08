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
from src.services.validation import ValidationService
from src.cli.error_handler import (
    ItemNotFoundError,
    InsufficientStockError,
    ValidationError,
    DatabaseError,
)


def billing_menu(db_session):
    """
    Display billing menu for creating invoices with full cart management

    Args:
        db_session: SQLAlchemy session for database operations
    """
    display_header("CREATE INVOICE")

    try:
        inventory_service = InventoryService(db_session)
        billing_service = BillingService(db_session)

        # Get customer and store info
        customer_name = input("Customer Name (optional, press Enter to skip): ").strip() or None
        store_name = input("Store Name (optional, press Enter to skip): ").strip() or None

        # Create bill draft (empty cart)
        billing_service.create_bill_draft()

        display_header("BILL - ADD ITEMS TO CART")

        # Add items to bill
        while True:
            cart = billing_service.get_cart()
            cart_count = len(cart)

            print(f"\n  Cart Items: {cart_count}")
            if cart_count > 0:
                total = billing_service.calculate_bill_total()
                print(f"  Cart Total: {total}")

            print("\n  1. Add Item")
            print("  2. View Cart")
            print("  3. Update Item Quantity")
            print("  4. Remove Item from Cart")
            print("  5. Confirm & Finalize Bill")
            print("  6. Cancel Bill")

            choice_str = get_numeric_input(
                prompt="Select option (1-6): ",
                min_val=1,
                max_val=6
            )

            choice = int(choice_str)
        if choice == 1:
                # Add item to cart
                _add_item_to_cart(inventory_service, billing_service)

            elchoice = int(choice_str)
        if choice == 2:
                # View cart
                _view_cart(billing_service)

            elchoice = int(choice_str)
        if choice == 3:
                # Update item quantity
                _update_cart_quantity(billing_service)

            elchoice = int(choice_str)
        if choice == 4:
                # Remove item from cart
                _remove_from_cart(billing_service)

            elchoice = int(choice_str)
        if choice == 5:
                # Confirm bill
                cart = billing_service.get_cart()
                if not cart:
                    display_error("Cannot create bill without items")
                    continue

                if not confirm("Confirm and finalize bill?"):
                    display_error("Bill not finalized")
                    continue

                # Confirm bill (deduct stock and save)
                final_bill = billing_service.confirm_bill(
                    customer_name=customer_name,
                    store_name=store_name
                )
                display_header("BILL FINALIZED")
                print(f"\n  Bill ID: {final_bill.id}")
                print(f"  Customer: {final_bill.customer_name or 'N/A'}")
                print(f"  Store: {final_bill.store_name or 'N/A'}")
                print(f"  Total: {final_bill.total_amount}")
                print(f"  Items: {len(final_bill.bill_items)}")
                display_success("Bill created successfully!")
                return final_bill

            elchoice = int(choice_str)
        if choice == 6:
                # Cancel bill
                if confirm("Cancel this bill?"):
                    billing_service.clear_cart()
                    display_message("Bill cancelled")
                    return None

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


def _add_item_to_cart(inventory_service, billing_service):
    """Add an item to the cart"""
    try:
        item_id = get_numeric_input(
            prompt="Enter Item ID: ",
            min_val=1,
            max_val=999999
        )

        item = inventory_service.get_item(item_id)

        quantity = get_numeric_input(
            prompt=f"Quantity (available: {item.stock_qty}): ",
            min_val=Decimal("0.01"),
            max_val=item.stock_qty,
            error_message=f"Quantity must be between 0.01 and {item.stock_qty}"
        )

        cart_item = billing_service.add_to_cart(item_id, quantity)
        display_success(f"Added {quantity} x {item.name} to cart")

    except ItemNotFoundError as e:
        display_error(f"Item not found: {str(e)}")
    except ValidationError as e:
        display_error(f"Error: {str(e)}")
    except Exception as e:
        display_error(f"Error adding item: {str(e)}")


def _view_cart(billing_service):
    """Display cart contents"""
    cart = billing_service.get_cart()
    if not cart:
        display_message("Cart is empty")
        return

    display_header("CURRENT CART")
    print("\n  Item Name           Unit Price  Qty    Total")
    print("  " + "-" * 50)
    total = Decimal("0")
    for item in cart:
        print(f"  {item['item_name']:<17} {item['unit_price']:>10}  "
              f"{item['quantity']:>6}  {item['line_total']:>10}")
        total += item['line_total']

    print("  " + "-" * 50)
    print(f"  {'TOTAL':<17} {' ':>10}  {' ':>6}  {total:>10}\n")


def _update_cart_quantity(billing_service):
    """Update quantity of item in cart"""
    try:
        cart = billing_service.get_cart()
        if not cart:
            display_message("Cart is empty")
            return

        item_id = get_numeric_input(
            prompt="Enter Item ID to update: ",
            min_val=1,
            max_val=999999
        )

        new_quantity = get_numeric_input(
            prompt="New Quantity: ",
            min_val=Decimal("0.01"),
            max_val=Decimal("999999")
        )

        updated_item = billing_service.update_cart_item_quantity(item_id, new_quantity)
        display_success(f"Updated {updated_item['item_name']} to {new_quantity} units")

    except ValidationError as e:
        display_error(f"Error: {str(e)}")
    except Exception as e:
        display_error(f"Error updating item: {str(e)}")


def _remove_from_cart(billing_service):
    """Remove item from cart"""
    try:
        cart = billing_service.get_cart()
        if not cart:
            display_message("Cart is empty")
            return

        item_id = get_numeric_input(
            prompt="Enter Item ID to remove: ",
            min_val=1,
            max_val=999999
        )

        if confirm(f"Remove item {item_id} from cart?"):
            billing_service.remove_from_cart(item_id)
            display_success(f"Item {item_id} removed from cart")

    except ValidationError as e:
        display_error(f"Error: {str(e)}")
    except Exception as e:
        display_error(f"Error removing item: {str(e)}")
