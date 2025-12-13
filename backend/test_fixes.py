"""Test that both fixes work correctly."""
import pytest
from app.agents.confirmation_flow import ConfirmationFlow


def test_confirmation_flow_no_longer_triggers_on_readonly():
    """Test that read-only queries don't trigger confirmation."""
    flow = ConfirmationFlow()
    
    # These should NOT trigger confirmation
    readonly_queries = [
        "tell me the grocery items in db",
        "what items do we have in inventory",
        "show me all items",
        "list the items",
        "how many items are in stock",
    ]
    
    for query in readonly_queries:
        is_destructive = flow.is_destructive_action(query)
        assert not is_destructive, f"Query '{query}' incorrectly marked as destructive"
        print(f"✓ Read-only query OK: '{query}'")


def test_confirmation_flow_triggers_on_destructive():
    """Test that destructive operations still trigger confirmation."""
    flow = ConfirmationFlow()
    
    # These SHOULD trigger confirmation
    destructive_actions = [
        "delete item widget",
        "remove item from stock",
        "create a bill for customer",
        "clear the stock",
    ]
    
    for action in destructive_actions:
        is_destructive = flow.is_destructive_action(action)
        assert is_destructive, f"Action '{action}' should be marked as destructive"
        print(f"✓ Destructive action caught: '{action}'")


def test_confirmation_flow_requires_multiple_keywords():
    """Test that single keywords don't trigger false positives."""
    flow = ConfirmationFlow()
    
    # These should NOT trigger (single keywords only)
    false_positives = [
        "tell me about items",  # has "item" but not "delete" or "remove"
        "remove from list",     # has "remove" but not "item"
        "delete the file",      # has "delete" but not "item"
        "create a new entry",   # has "create" but not "bill"
        "clear the screen",     # has "clear" but not "stock"
    ]
    
    for query in false_positives:
        is_destructive = flow.is_destructive_action(query)
        assert not is_destructive, f"Query '{query}' incorrectly marked as destructive"
        print(f"✓ False positive avoided: '{query}'")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
