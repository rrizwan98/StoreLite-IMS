"""
UI utilities for console interface
Handles table formatting, dropdowns, messages, and output
"""

from typing import List, Optional


def display_header(title: str) -> None:
    """Display a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def display_error(message: str) -> None:
    """Display an error message"""
    print(f"\n❌ ERROR: {message}\n")


def display_success(message: str) -> None:
    """Display a success message"""
    print(f"\n✅ SUCCESS: {message}\n")


def display_info(message: str) -> None:
    """Display an info message"""
    print(f"ℹ️  {message}")


def display_message(message: str) -> None:
    """Display a regular message"""
    print(f"\n{message}\n")


def format_items_table(items: List) -> None:
    """
    Display items as a formatted table

    Args:
        items: List of Item objects
    """
    if not items:
        print("No items found.\n")
        return

    # Table headers
    headers = ["ID", "Name", "Category", "Unit", "Price", "Stock"]
    col_widths = [5, 25, 15, 10, 12, 12]

    # Print header
    print("\n" + "-" * (sum(col_widths) + 7))  # 7 for separators
    header_row = "│ " + " │ ".join(
        h.ljust(w) for h, w in zip(headers, col_widths)
    )
    print(header_row + " │")
    print("-" * (sum(col_widths) + 7))

    # Print rows
    for item in items:
        row = [
            str(item.id),
            str(item.name)[:25],
            str(item.category)[:15],
            str(item.unit)[:10],
            f"${float(item.unit_price):.2f}",
            f"{float(item.stock_qty):.2f}",
        ]
        row_str = "│ " + " │ ".join(
            cell.ljust(w) for cell, w in zip(row, col_widths)
        )
        print(row_str + " │")

    print("-" * (sum(col_widths) + 7) + "\n")


def format_single_item(item) -> None:
    """
    Display a single item's details

    Args:
        item: Item object
    """
    print("\n" + "=" * 60)
    print(f"Item ID: {item.id}")
    print(f"Name: {item.name}")
    print(f"Category: {item.category}")
    print(f"Unit: {item.unit}")
    print(f"Unit Price: ${float(item.unit_price):.2f}")
    print(f"Stock Quantity: {float(item.stock_qty):.2f}")
    print(f"Active: {'Yes' if item.is_active else 'No'}")
    print(f"Created: {item.created_at}")
    print(f"Updated: {item.updated_at}")
    print("=" * 60 + "\n")


def searchable_dropdown(options: List[str], prompt: str = "Select an option") -> Optional[str]:
    """
    Display a searchable dropdown menu

    Args:
        options: List of options to choose from
        prompt: Prompt to display to user

    Returns:
        Selected option or None if invalid
    """
    print(f"\n{prompt}")
    print("(Type to search, or press Enter to select from filtered list)\n")

    while True:
        search_term = input("Search: ").strip().lower()

        if not search_term:
            print("Search term cannot be empty. Please try again.\n")
            continue

        # Filter options by search term
        filtered = [opt for opt in options if search_term in opt.lower()]

        if not filtered:
            print(f"No matches found for '{search_term}'. Please try again.\n")
            continue

        # Display filtered options
        print("\nMatches found:")
        for i, opt in enumerate(filtered, 1):
            print(f"  {i}. {opt}")

        # Let user select
        while True:
            try:
                choice = input("\nSelect option (number): ").strip()
                if not choice.isdigit():
                    print("Please enter a valid number.\n")
                    continue

                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(filtered):
                    selected = filtered[choice_idx]
                    print(f"Selected: {selected}\n")
                    return selected
                else:
                    print(f"Please enter a number between 1 and {len(filtered)}.\n")
            except ValueError:
                print("Invalid input. Please try again.\n")


def get_input_with_validation(
    prompt: str,
    validator_func=None,
    allow_empty: bool = False
) -> str:
    """
    Get user input with optional validation

    Args:
        prompt: Prompt to display
        validator_func: Function that returns (is_valid, error_message)
        allow_empty: Whether to allow empty input

    Returns:
        Validated input
    """
    while True:
        user_input = input(f"\n{prompt}: ").strip()

        if not user_input:
            if allow_empty:
                return ""
            print("Input cannot be empty. Please try again.\n")
            continue

        if validator_func:
            is_valid, error_msg = validator_func(user_input)
            if not is_valid:
                print(f"Invalid input: {error_msg}\n")
                continue

        return user_input


def get_numeric_input(prompt: str, allow_decimal: bool = True) -> Optional[str]:
    """
    Get numeric input from user

    Args:
        prompt: Prompt to display
        allow_decimal: Whether to allow decimal numbers

    Returns:
        Numeric string or None if invalid
    """
    while True:
        user_input = input(f"\n{prompt}: ").strip()

        if not user_input:
            print("Input cannot be empty. Please try again.\n")
            continue

        try:
            if allow_decimal:
                float(user_input)
            else:
                int(user_input)
            return user_input
        except ValueError:
            print(
                f"Invalid number. Please enter a valid "
                f"{'decimal' if allow_decimal else 'integer'} number.\n"
            )


def display_bill_preview(cart: List[dict], total: float) -> None:
    """
    Display bill preview with items and total

    Args:
        cart: List of dictionaries with item info
        total: Total amount
    """
    if not cart:
        print("Cart is empty.\n")
        return

    headers = ["Item Name", "Unit", "Qty", "Unit Price", "Line Total"]
    col_widths = [20, 8, 8, 12, 12]

    print("\n" + "=" * 70)
    print("BILL PREVIEW")
    print("=" * 70)
    print("-" * 70)
    header_row = "│ " + " │ ".join(
        h.ljust(w) for h, w in zip(headers, col_widths)
    )
    print(header_row + " │")
    print("-" * 70)

    for item in cart:
        row = [
            str(item["item_name"])[:20],
            str(item.get("unit", ""))[:8],
            f"{float(item['quantity']):.2f}",
            f"${float(item['unit_price']):.2f}",
            f"${float(item['line_total']):.2f}",
        ]
        row_str = "│ " + " │ ".join(
            cell.ljust(w) for cell, w in zip(row, col_widths)
        )
        print(row_str + " │")

    print("-" * 70)
    total_str = f"TOTAL: ${total:.2f}"
    print(total_str.rjust(70))
    print("=" * 70 + "\n")


def display_invoice(bill, bill_items: List) -> None:
    """
    Display formatted invoice

    Args:
        bill: Bill object
        bill_items: List of BillItem objects
    """
    print("\n" + "=" * 70)
    print("INVOICE".center(70))
    print("=" * 70)
    print(f"Bill ID: {bill.id}".ljust(35) + f"Date: {bill.created_at}")
    print(f"Customer: {bill.customer_name or 'N/A'}".ljust(35) + f"Store: {bill.store_name or 'N/A'}")
    print("-" * 70)

    headers = ["Item", "Unit", "Qty", "Unit Price", "Line Total"]
    col_widths = [18, 8, 8, 12, 12]

    header_row = "│ " + " │ ".join(
        h.ljust(w) for h, w in zip(headers, col_widths)
    )
    print(header_row + " │")
    print("-" * 70)

    for item in bill_items:
        row = [
            str(item.item_name)[:18],
            str(item.unit or "")[:8],
            f"{float(item.quantity):.2f}",
            f"${float(item.unit_price):.2f}",
            f"${float(item.line_total):.2f}",
        ]
        row_str = "│ " + " │ ".join(
            cell.ljust(w) for cell, w in zip(row, col_widths)
        )
        print(row_str + " │")

    print("-" * 70)
    total_str = f"TOTAL: ${float(bill.total_amount):.2f}"
    print(total_str.rjust(70))
    print("=" * 70)
    print("\nThank you for your purchase!".center(70))
    print("=" * 70 + "\n")


def confirm(prompt: str = "Are you sure?") -> bool:
    """
    Ask user for confirmation

    Args:
        prompt: Confirmation prompt

    Returns:
        True if user confirms, False otherwise
    """
    while True:
        response = input(f"\n{prompt} (y/n): ").strip().lower()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        else:
            print("Please enter 'y' or 'n'.\n")
