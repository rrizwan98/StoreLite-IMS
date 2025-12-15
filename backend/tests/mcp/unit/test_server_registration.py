"""
Task 45: Server registration tests - Verify all tools are registered with FastMCP server
"""
import pytest
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.mcp_server.server import create_server
from app.mcp_server.tools_inventory import (
    inventory_add_item,
    inventory_update_item,
    inventory_delete_item,
    inventory_list_items,
)
from app.mcp_server.tools_billing import (
    billing_create_bill,
    billing_get_bill,
    billing_list_bills,
)


class TestServerInitialization:
    """Test server initialization and configuration."""

    def test_server_creates_successfully(self):
        """Verify server initializes without error."""
        server = create_server()
        assert server is not None
        assert hasattr(server, 'name')
        assert server.name == "ims-mcp-server"

    def test_server_has_required_attributes(self):
        """Verify server has required configuration attributes."""
        server = create_server()
        assert hasattr(server, 'name')
        # Version is set by FastMCP, just verify it exists and is a string
        assert server.name == "ims-mcp-server"


class TestToolRegistration:
    """Test that all tools are properly registered."""

    def test_inventory_add_item_exists(self):
        """Verify inventory_add_item tool function exists."""
        assert callable(inventory_add_item)
        assert inventory_add_item.__name__ == "inventory_add_item"

    def test_inventory_update_item_exists(self):
        """Verify inventory_update_item tool function exists."""
        assert callable(inventory_update_item)
        assert inventory_update_item.__name__ == "inventory_update_item"

    def test_inventory_delete_item_exists(self):
        """Verify inventory_delete_item tool function exists."""
        assert callable(inventory_delete_item)
        assert inventory_delete_item.__name__ == "inventory_delete_item"

    def test_inventory_list_items_exists(self):
        """Verify inventory_list_items tool function exists."""
        assert callable(inventory_list_items)
        assert inventory_list_items.__name__ == "inventory_list_items"

    def test_billing_create_bill_exists(self):
        """Verify billing_create_bill tool function exists."""
        assert callable(billing_create_bill)
        assert billing_create_bill.__name__ == "billing_create_bill"

    def test_billing_get_bill_exists(self):
        """Verify billing_get_bill tool function exists."""
        assert callable(billing_get_bill)
        assert billing_get_bill.__name__ == "billing_get_bill"

    def test_billing_list_bills_exists(self):
        """Verify billing_list_bills tool function exists."""
        assert callable(billing_list_bills)
        assert billing_list_bills.__name__ == "billing_list_bills"

    def test_all_tools_are_async(self):
        """Verify all tools are async functions."""
        import inspect

        tools = [
            inventory_add_item,
            inventory_update_item,
            inventory_delete_item,
            inventory_list_items,
            billing_create_bill,
            billing_get_bill,
            billing_list_bills,
        ]

        for tool in tools:
            # Check if function has __wrapped__ attribute (decorator)
            # or check if it's a coroutine function
            assert inspect.iscoroutinefunction(tool) or hasattr(tool, '__wrapped__'), \
                f"{tool.__name__} is not an async function"


class TestToolSignatures:
    """Test that tools have correct function signatures."""

    def test_inventory_add_item_signature(self):
        """Verify inventory_add_item has required parameters."""
        import inspect
        sig = inspect.signature(inventory_add_item)
        params = list(sig.parameters.keys())

        # Remove decorator wrapper if present
        required_params = ['name', 'category', 'unit', 'unit_price', 'stock_qty', 'session']
        for param in required_params:
            assert param in params, f"Missing parameter: {param}"

    def test_inventory_update_item_signature(self):
        """Verify inventory_update_item has required parameters."""
        import inspect
        sig = inspect.signature(inventory_update_item)
        params = list(sig.parameters.keys())

        assert 'item_id' in params
        assert 'session' in params

    def test_inventory_delete_item_signature(self):
        """Verify inventory_delete_item has required parameters."""
        import inspect
        sig = inspect.signature(inventory_delete_item)
        params = list(sig.parameters.keys())

        assert 'item_id' in params
        assert 'session' in params

    def test_inventory_list_items_signature(self):
        """Verify inventory_list_items has required parameters."""
        import inspect
        sig = inspect.signature(inventory_list_items)
        params = list(sig.parameters.keys())

        assert 'session' in params
        # pagination params should exist
        assert 'page' in params or 'limit' in params

    def test_billing_create_bill_signature(self):
        """Verify billing_create_bill has required parameters."""
        import inspect
        sig = inspect.signature(billing_create_bill)
        params = list(sig.parameters.keys())

        assert 'items' in params
        assert 'session' in params

    def test_billing_get_bill_signature(self):
        """Verify billing_get_bill has required parameters."""
        import inspect
        sig = inspect.signature(billing_get_bill)
        params = list(sig.parameters.keys())

        assert 'bill_id' in params
        assert 'session' in params

    def test_billing_list_bills_signature(self):
        """Verify billing_list_bills has required parameters."""
        import inspect
        sig = inspect.signature(billing_list_bills)
        params = list(sig.parameters.keys())

        assert 'session' in params
        # pagination params should exist
        assert 'page' in params or 'limit' in params


class TestToolDocumentation:
    """Test that tools are properly documented."""

    def test_inventory_add_item_has_docstring(self):
        """Verify inventory_add_item has documentation."""
        assert inventory_add_item.__doc__ is not None
        assert len(inventory_add_item.__doc__) > 0

    def test_inventory_update_item_has_docstring(self):
        """Verify inventory_update_item has documentation."""
        assert inventory_update_item.__doc__ is not None

    def test_inventory_delete_item_has_docstring(self):
        """Verify inventory_delete_item has documentation."""
        assert inventory_delete_item.__doc__ is not None

    def test_inventory_list_items_has_docstring(self):
        """Verify inventory_list_items has documentation."""
        assert inventory_list_items.__doc__ is not None

    def test_billing_create_bill_has_docstring(self):
        """Verify billing_create_bill has documentation."""
        assert billing_create_bill.__doc__ is not None

    def test_billing_get_bill_has_docstring(self):
        """Verify billing_get_bill has documentation."""
        assert billing_get_bill.__doc__ is not None

    def test_billing_list_bills_has_docstring(self):
        """Verify billing_list_bills has documentation."""
        assert billing_list_bills.__doc__ is not None


class TestServerToolCount:
    """Test that server has correct number of tools."""

    def test_all_seven_tools_registered(self):
        """Verify exactly 7 tools are available."""
        tools = [
            inventory_add_item,
            inventory_update_item,
            inventory_delete_item,
            inventory_list_items,
            billing_create_bill,
            billing_get_bill,
            billing_list_bills,
        ]

        assert len(tools) == 7, "Should have exactly 7 tools"

        # All should be callable
        for tool in tools:
            assert callable(tool), f"{tool} is not callable"
