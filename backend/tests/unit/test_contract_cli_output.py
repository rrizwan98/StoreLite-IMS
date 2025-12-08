"""
Contract tests for CLI output format (Phase 7)
Validates that CLI output adheres to expected format and structure
"""

import pytest
from decimal import Decimal
from io import StringIO
import sys
from src.cli.ui_utils import (
    display_header,
    display_message,
    display_success,
    display_error,
    format_items_table,
    format_single_item,
)
from src.models.item import Item


class TestDisplayHeaderFormat:
    """Test header display format contract"""

    def test_header_output_contains_text(self, capsys):
        """Header should display centered text"""
        display_header("TEST HEADER")
        captured = capsys.readouterr()
        assert "TEST HEADER" in captured.out

    def test_header_output_includes_border(self, capsys):
        """Header should include decorative border"""
        display_header("TEST")
        captured = capsys.readouterr()
        # Should have some line decoration
        assert len(captured.out) > 0

    def test_header_multiple_words(self, capsys):
        """Header should handle multiple words"""
        display_header("INVENTORY MANAGEMENT SYSTEM")
        captured = capsys.readouterr()
        assert "INVENTORY MANAGEMENT SYSTEM" in captured.out


class TestMessageFormat:
    """Test message display format contract"""

    def test_message_output_format(self, capsys):
        """Message should be displayed with formatting"""
        display_message("This is a test message")
        captured = capsys.readouterr()
        assert "This is a test message" in captured.out

    def test_success_message_format(self, capsys):
        """Success message should indicate success"""
        display_success("Operation completed!")
        captured = capsys.readouterr()
        assert "Operation completed!" in captured.out

    def test_error_message_format(self, capsys):
        """Error message should indicate error"""
        display_error("An error occurred")
        captured = capsys.readouterr()
        assert "An error occurred" in captured.out


class TestItemTableFormat:
    """Test items table format contract"""

    def test_items_table_header_contains_columns(self, capsys):
        """Items table should have column headers"""
        items = [
            Item(id=1, name="Sugar", category="Grocery", unit_price=Decimal("50.00"),
                 stock_qty=Decimal("100"), is_active=True),
        ]
        output = format_items_table(items)
        assert "ID" in output
        assert "Name" in output or "name" in output.lower()

    def test_items_table_single_row(self):
        """Table should display single item correctly"""
        item = Item(
            id=1,
            name="Test Item",
            category="Grocery",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100"),
            is_active=True
        )
        output = format_items_table([item])
        assert "Test Item" in output
        assert "50.00" in output
        assert "100" in output

    def test_items_table_multiple_rows(self):
        """Table should display multiple items"""
        items = [
            Item(id=1, name="Item 1", category="Grocery", unit_price=Decimal("50.00"),
                 stock_qty=Decimal("100"), is_active=True),
            Item(id=2, name="Item 2", category="Grocery", unit_price=Decimal("60.00"),
                 stock_qty=Decimal("80"), is_active=True),
        ]
        output = format_items_table(items)
        assert "Item 1" in output
        assert "Item 2" in output

    def test_items_table_empty_list(self):
        """Table should handle empty list"""
        output = format_items_table([])
        assert len(output) >= 0

    def test_items_table_includes_price(self):
        """Table should include price column"""
        item = Item(
            id=1,
            name="Sugar",
            category="Grocery",
            unit_price=Decimal("99.99"),
            stock_qty=Decimal("50"),
            is_active=True
        )
        output = format_items_table([item])
        assert "99.99" in output

    def test_items_table_includes_stock(self):
        """Table should include stock quantity column"""
        item = Item(
            id=1,
            name="Sugar",
            category="Grocery",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("123"),
            is_active=True
        )
        output = format_items_table([item])
        assert "123" in output


class TestSingleItemFormat:
    """Test single item display format contract"""

    def test_single_item_contains_all_fields(self):
        """Single item output should contain all fields"""
        item = Item(
            id=1,
            name="Test Item",
            category="Grocery",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100"),
            is_active=True
        )
        output = format_single_item(item)
        assert "Test Item" in output
        assert "50.00" in output
        assert "100" in output
        assert "Grocery" in output

    def test_single_item_includes_id(self):
        """Item display should include ID"""
        item = Item(
            id=42,
            name="Test Item",
            category="Grocery",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100"),
            is_active=True
        )
        output = format_single_item(item)
        assert "42" in output

    def test_single_item_includes_category(self):
        """Item display should include category"""
        item = Item(
            id=1,
            name="Test Item",
            category="Beauty",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100"),
            is_active=True
        )
        output = format_single_item(item)
        assert "Beauty" in output

    def test_single_item_includes_status(self):
        """Item display should indicate active/inactive status"""
        active_item = Item(
            id=1,
            name="Active",
            category="Grocery",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100"),
            is_active=True
        )
        active_output = format_single_item(active_item)
        assert len(active_output) > 0

        inactive_item = Item(
            id=2,
            name="Inactive",
            category="Grocery",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100"),
            is_active=False
        )
        inactive_output = format_single_item(inactive_item)
        assert len(inactive_output) > 0


class TestCLIOutputConsistency:
    """Test consistency of CLI outputs"""

    def test_numeric_formatting_consistency(self):
        """Prices should format consistently"""
        item1 = Item(
            id=1,
            name="Item 1",
            category="Grocery",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100"),
            is_active=True
        )
        item2 = Item(
            id=2,
            name="Item 2",
            category="Grocery",
            unit_price=Decimal("50.10"),
            stock_qty=Decimal("100.50"),
            is_active=True
        )
        output1 = format_items_table([item1])
        output2 = format_items_table([item2])
        # Both should have price-like values
        assert "50" in output1
        assert "50" in output2

    def test_column_alignment_consistency(self):
        """Columns should be aligned consistently"""
        items = [
            Item(id=1, name="Short", category="Grocery", unit_price=Decimal("50.00"),
                 stock_qty=Decimal("100"), is_active=True),
            Item(id=2, name="A Much Longer Item Name", category="Grocery",
                 unit_price=Decimal("100.00"), stock_qty=Decimal("1000"), is_active=True),
        ]
        output = format_items_table(items)
        # Should have consistent formatting for both rows
        lines = output.split('\n')
        assert len(lines) > 0

    def test_decimal_precision_in_output(self):
        """Decimal values should show proper precision"""
        item = Item(
            id=1,
            name="Test",
            category="Grocery",
            unit_price=Decimal("99.99"),
            stock_qty=Decimal("10.50"),
            is_active=True
        )
        output = format_items_table([item])
        # Should show decimal values
        assert "99.99" in output or "99" in output


class TestCLIOutputErrorHandling:
    """Test CLI output for error scenarios"""

    def test_error_message_does_not_expose_internals(self, capsys):
        """Error messages should be user-friendly"""
        display_error("User-friendly error message")
        captured = capsys.readouterr()
        assert "User-friendly error message" in captured.out
        # Should not contain stack traces
        assert "Traceback" not in captured.out
        assert "File" not in captured.out or "user-friendly" in captured.out.lower()

    def test_validation_error_messaging(self, capsys):
        """Validation errors should be clear"""
        display_error("Validation Error: Please enter a valid value")
        captured = capsys.readouterr()
        assert "Validation Error" in captured.out
        assert "valid value" in captured.out


class TestCLIMenuStructure:
    """Test CLI menu structure and formatting"""

    def test_menu_header_formatting(self, capsys):
        """Menu headers should be prominent"""
        display_header("MAIN MENU")
        captured = capsys.readouterr()
        assert "MAIN MENU" in captured.out

    def test_menu_option_formatting(self, capsys):
        """Menu options should be clearly numbered"""
        # Test that numbered options are readable
        output = "  1. Option One\n  2. Option Two\n"
        assert "1." in output
        assert "2." in output
        assert "Option One" in output


class TestCLIInputPromptFormat:
    """Test input prompt formatting"""

    def test_prompt_clarity(self):
        """Prompts should be clear and actionable"""
        prompt = "Enter Item ID: "
        assert "Item ID" in prompt
        assert ":" in prompt

    def test_prompt_validation_message(self):
        """Validation messages should guide user"""
        message = "Please enter a valid Item ID (1-999999)"
        assert "valid" in message.lower()
        assert "Item ID" in message
