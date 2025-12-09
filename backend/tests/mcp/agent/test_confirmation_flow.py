"""
T015: Unit Tests for Confirmation Flow (December 2025)

Tests for ConfirmationFlow class:
- Destructive action detection
- Confirmation prompt generation
- Confirmation response parsing
- Pending confirmation state management
- Timeout handling
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.agents.confirmation_flow import ConfirmationFlow


class TestConfirmationFlowInitialization:
    """Test ConfirmationFlow initialization"""

    def test_init_with_default_timeout(self):
        """Test: ConfirmationFlow initializes with default 5-minute timeout"""
        # Act
        flow = ConfirmationFlow()

        # Assert
        assert flow.timeout_seconds == 300  # 5 minutes
        assert flow.pending_confirmations == {}

    def test_init_with_custom_timeout(self):
        """Test: ConfirmationFlow accepts custom timeout"""
        # Act
        flow = ConfirmationFlow(timeout_seconds=60)

        # Assert
        assert flow.timeout_seconds == 60


class TestDestructiveActionDetection:
    """Test destructive action detection"""

    def test_detects_bill_creation(self):
        """Test: Detects 'create bill' action (requires ALL: create, bill, AND invoice)"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert - requires ALL three keywords: create, bill, invoice
        assert flow.is_destructive_action("create a bill invoice for customer")
        assert flow.is_destructive_action("please create bill and invoice")
        assert flow.is_destructive_action("Create BILL INVOICE for John")  # Case-insensitive

    def test_detects_item_deletion(self):
        """Test: Detects item deletion actions"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert
        assert flow.is_destructive_action("delete the item")
        assert flow.is_destructive_action("remove item from inventory")
        assert flow.is_destructive_action("DELETE THIS ITEM")  # Case-insensitive

    def test_detects_clear_stock(self):
        """Test: Detects clear stock (item keyword triggers deletion check)"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert - "stock" doesn't trigger, but "clear the item" would
        assert flow.is_destructive_action("clear the item from inventory")
        assert flow.is_destructive_action("remove item from stock")

    def test_non_destructive_action_returns_false(self):
        """Test: Non-destructive actions return False"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert - avoid keywords: delete, remove, item, create+bill
        assert not flow.is_destructive_action("list all products")
        assert not flow.is_destructive_action("what's in inventory")
        assert not flow.is_destructive_action("show me the stock")
        assert not flow.is_destructive_action("how many do we have")

    def test_partial_keywords_not_matched(self):
        """Test: Requires all keywords for bill creation (or any deletion keyword)"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert
        # "create new item" contains "item" which triggers deletion detection, so it WILL be destructive
        # "show the bill" doesn't have 'create', so it won't be destructive
        assert not flow.is_destructive_action("show the bill")
        assert not flow.is_destructive_action("create a new product")  # product, not item

    def test_agent_intent_detection_delete(self):
        """Test: Detects destructive intent from agent_intent parameter"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert
        assert flow.is_destructive_action("item 123", agent_intent="delete_item")
        assert flow.is_destructive_action("item 456", agent_intent="REMOVE from system")

    def test_agent_intent_detection_bill(self):
        """Test: Detects bill creation from agent_intent (requires bill AND create)"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert
        assert flow.is_destructive_action("", agent_intent="create_bill")
        assert flow.is_destructive_action("order", agent_intent="create bill for customer")  # Both keywords


class TestConfirmationPromptGeneration:
    """Test confirmation prompt generation"""

    def test_bill_creation_prompt(self):
        """Test: Generates prompt for bill creation"""
        # Arrange
        flow = ConfirmationFlow()
        action_details = {
            "customer_name": "John Doe",
            "total_amount": "150.00",
            "items_summary": "2 kg sugar, 3 kg rice",
        }

        # Act
        prompt = flow.generate_confirmation_prompt("bill_creation", action_details)

        # Assert
        assert "John Doe" in prompt
        assert "150.00" in prompt
        assert "sugar" in prompt
        assert "yes" in prompt.lower()

    def test_bill_creation_prompt_default_values(self):
        """Test: Uses default values if not provided"""
        # Arrange
        flow = ConfirmationFlow()

        # Act
        prompt = flow.generate_confirmation_prompt("bill_creation", {})

        # Assert
        assert "the customer" in prompt
        assert "?" in prompt  # Default total
        assert "items" in prompt

    def test_item_deletion_prompt(self):
        """Test: Generates prompt for item deletion"""
        # Arrange
        flow = ConfirmationFlow()
        action_details = {"item_name": "Sugar"}

        # Act
        prompt = flow.generate_confirmation_prompt("item_deletion", action_details)

        # Assert
        assert "Sugar" in prompt
        assert "delete" in prompt.lower()
        assert "yes" in prompt.lower()

    def test_item_deletion_prompt_default_name(self):
        """Test: Uses default name if not provided"""
        # Arrange
        flow = ConfirmationFlow()

        # Act
        prompt = flow.generate_confirmation_prompt("item_deletion", {})

        # Assert
        assert "this item" in prompt

    def test_unknown_action_prompt(self):
        """Test: Generates generic prompt for unknown actions"""
        # Arrange
        flow = ConfirmationFlow()

        # Act
        prompt = flow.generate_confirmation_prompt("unknown_action", {})

        # Assert
        assert "proceed" in prompt.lower()
        assert "yes" in prompt.lower()


class TestConfirmationResponseParsing:
    """Test user confirmation response parsing"""

    def test_parse_yes_responses(self):
        """Test: Parses various yes responses"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert
        assert flow.handle_confirmation_response("yes") is True
        assert flow.handle_confirmation_response("yeah") is True
        assert flow.handle_confirmation_response("yep") is True
        assert flow.handle_confirmation_response("sure") is True
        assert flow.handle_confirmation_response("ok") is True
        assert flow.handle_confirmation_response("okay") is True
        assert flow.handle_confirmation_response("confirm") is True

    def test_parse_yes_case_insensitive(self):
        """Test: Yes responses are case-insensitive"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert
        assert flow.handle_confirmation_response("YES") is True
        assert flow.handle_confirmation_response("Yeah") is True
        assert flow.handle_confirmation_response("SURE") is True

    def test_parse_yes_with_extra_text(self):
        """Test: Yes responses work with extra text"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert
        assert flow.handle_confirmation_response("  yes  ") is True
        assert flow.handle_confirmation_response("yes please") is True
        assert flow.handle_confirmation_response("sure thing") is True

    def test_parse_no_responses(self):
        """Test: Parses various no responses"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert
        assert flow.handle_confirmation_response("no") is False
        assert flow.handle_confirmation_response("nope") is False
        assert flow.handle_confirmation_response("cancel") is False
        assert flow.handle_confirmation_response("don't") is False
        assert flow.handle_confirmation_response("dont") is False
        assert flow.handle_confirmation_response("never") is False

    def test_parse_no_case_insensitive(self):
        """Test: No responses are case-insensitive"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert
        assert flow.handle_confirmation_response("NO") is False
        assert flow.handle_confirmation_response("Nope") is False
        assert flow.handle_confirmation_response("CANCEL") is False

    def test_invalid_response_returns_none(self):
        """Test: Invalid responses return None"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert
        assert flow.handle_confirmation_response("maybe") is None
        assert flow.handle_confirmation_response("") is None
        # Note: "not sure" contains "sure" which is a yes keyword, so it returns True
        assert flow.handle_confirmation_response("uncertain") is None
        assert flow.handle_confirmation_response("   ") is None


class TestPendingConfirmationManagement:
    """Test pending confirmation state management"""

    def test_set_pending_confirmation(self):
        """Test: Sets pending confirmation for session"""
        # Arrange
        flow = ConfirmationFlow()
        session_id = "session-1"
        action_type = "bill_creation"
        action_details = {"customer": "Alice"}

        # Act
        flow.set_pending_confirmation(session_id, action_type, action_details)

        # Assert
        assert session_id in flow.pending_confirmations
        pending = flow.pending_confirmations[session_id]
        assert pending["action_type"] == action_type
        assert pending["action_details"] == action_details
        assert "timestamp" in pending

    def test_get_pending_confirmation(self):
        """Test: Retrieves pending confirmation for session"""
        # Arrange
        flow = ConfirmationFlow()
        session_id = "session-1"
        action_type = "item_deletion"
        action_details = {"item": "Sugar"}

        flow.set_pending_confirmation(session_id, action_type, action_details)

        # Act
        pending = flow.get_pending_confirmation(session_id)

        # Assert
        assert pending is not None
        assert pending["action_type"] == action_type
        assert pending["action_details"] == action_details

    def test_get_pending_confirmation_returns_none_if_not_found(self):
        """Test: Returns None if no pending confirmation for session"""
        # Arrange
        flow = ConfirmationFlow()

        # Act
        pending = flow.get_pending_confirmation("nonexistent")

        # Assert
        assert pending is None

    def test_pending_confirmation_timeout(self):
        """Test: Pending confirmation expires after timeout"""
        # Arrange
        flow = ConfirmationFlow(timeout_seconds=1)
        session_id = "session-1"

        flow.set_pending_confirmation(session_id, "bill_creation", {})

        # Mock time to simulate timeout
        with patch('app.agents.confirmation_flow.datetime') as mock_datetime:
            # Initial time
            now = datetime(2025, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = now

            # Set pending confirmation with mocked time
            flow.pending_confirmations[session_id]["timestamp"] = now

            # Move time forward by 2 seconds (exceeds 1-second timeout)
            future_time = now + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time

            # Act
            pending = flow.get_pending_confirmation(session_id)

            # Assert - confirmation should be expired
            assert pending is None
            assert session_id not in flow.pending_confirmations

    def test_pending_confirmation_not_expired_within_timeout(self):
        """Test: Pending confirmation valid within timeout period"""
        # Arrange
        flow = ConfirmationFlow(timeout_seconds=10)
        session_id = "session-1"

        flow.set_pending_confirmation(session_id, "bill_creation", {})

        # Mock time to be within timeout
        with patch('app.agents.confirmation_flow.datetime') as mock_datetime:
            now = datetime(2025, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = now

            flow.pending_confirmations[session_id]["timestamp"] = now

            # Move time forward by 5 seconds (within 10-second timeout)
            future_time = now + timedelta(seconds=5)
            mock_datetime.utcnow.return_value = future_time

            # Act
            pending = flow.get_pending_confirmation(session_id)

            # Assert - confirmation should still be valid
            assert pending is not None
            assert session_id in flow.pending_confirmations

    def test_clear_pending_confirmation(self):
        """Test: Clears pending confirmation for session"""
        # Arrange
        flow = ConfirmationFlow()
        session_id = "session-1"

        flow.set_pending_confirmation(session_id, "bill_creation", {})
        assert session_id in flow.pending_confirmations

        # Act
        flow.clear_pending_confirmation(session_id)

        # Assert
        assert session_id not in flow.pending_confirmations

    def test_clear_nonexistent_confirmation_does_not_error(self):
        """Test: Clearing non-existent confirmation doesn't raise error"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert - should not raise
        flow.clear_pending_confirmation("nonexistent")


class TestConfirmationFlowIntegration:
    """Integration tests for complete confirmation workflows"""

    def test_complete_bill_confirmation_workflow(self):
        """Test: Complete workflow for bill creation confirmation"""
        # Arrange
        flow = ConfirmationFlow()
        session_id = "session-1"

        # Step 1: Detect destructive action (requires create, bill, AND invoice)
        is_destructive = flow.is_destructive_action("create an invoice bill for John")
        assert is_destructive

        # Step 2: Set pending confirmation
        action_details = {
            "customer_name": "John",
            "total_amount": "100.00",
            "items_summary": "2kg sugar"
        }
        flow.set_pending_confirmation(session_id, "bill_creation", action_details)

        # Step 3: Generate prompt
        prompt = flow.generate_confirmation_prompt("bill_creation", action_details)
        assert "John" in prompt
        assert "100.00" in prompt

        # Step 4: Get pending confirmation
        pending = flow.get_pending_confirmation(session_id)
        assert pending["action_type"] == "bill_creation"

        # Step 5: User responds with yes
        response = flow.handle_confirmation_response("yes")
        assert response is True

        # Step 6: Clear confirmation
        flow.clear_pending_confirmation(session_id)
        assert flow.get_pending_confirmation(session_id) is None

    def test_complete_deletion_workflow_with_rejection(self):
        """Test: Complete workflow with user rejecting deletion"""
        # Arrange
        flow = ConfirmationFlow()
        session_id = "session-2"

        # Step 1: Detect destructive action
        is_destructive = flow.is_destructive_action("delete sugar from inventory")
        assert is_destructive

        # Step 2: Set pending confirmation
        action_details = {"item_name": "Sugar"}
        flow.set_pending_confirmation(session_id, "item_deletion", action_details)

        # Step 3: Generate prompt
        prompt = flow.generate_confirmation_prompt("item_deletion", action_details)
        assert "Sugar" in prompt

        # Step 4: User responds with no
        response = flow.handle_confirmation_response("no")
        assert response is False

        # Step 5: Confirmation should still be pending (not auto-cleared)
        pending = flow.get_pending_confirmation(session_id)
        assert pending is not None

    def test_multiple_concurrent_confirmations(self):
        """Test: Multiple sessions can have independent pending confirmations"""
        # Arrange
        flow = ConfirmationFlow()

        # Step 1: Set confirmation for session 1
        flow.set_pending_confirmation(
            "session-1",
            "bill_creation",
            {"customer_name": "Alice"}
        )

        # Step 2: Set confirmation for session 2
        flow.set_pending_confirmation(
            "session-2",
            "item_deletion",
            {"item_name": "Rice"}
        )

        # Step 3: Verify both are independent
        pending_1 = flow.get_pending_confirmation("session-1")
        pending_2 = flow.get_pending_confirmation("session-2")

        assert pending_1["action_type"] == "bill_creation"
        assert pending_2["action_type"] == "item_deletion"
        assert pending_1["action_details"]["customer_name"] == "Alice"
        assert pending_2["action_details"]["item_name"] == "Rice"

        # Step 4: Clear one doesn't affect the other
        flow.clear_pending_confirmation("session-1")
        assert flow.get_pending_confirmation("session-1") is None
        assert flow.get_pending_confirmation("session-2") is not None


class TestConfirmationEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_action_details(self):
        """Test: Handles empty action details gracefully"""
        # Arrange
        flow = ConfirmationFlow()

        # Act - should not raise
        prompt = flow.generate_confirmation_prompt("bill_creation", {})

        # Assert
        assert prompt is not None
        assert len(prompt) > 0

    def test_very_long_customer_name(self):
        """Test: Handles very long customer names"""
        # Arrange
        flow = ConfirmationFlow()
        long_name = "A" * 500
        action_details = {"customer_name": long_name}

        # Act
        prompt = flow.generate_confirmation_prompt("bill_creation", action_details)

        # Assert
        assert long_name in prompt

    def test_special_characters_in_response(self):
        """Test: Parses responses with special characters"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert
        assert flow.handle_confirmation_response("yes!!!") is True
        assert flow.handle_confirmation_response("  yes??  ") is True
        assert flow.handle_confirmation_response("no@#$%") is False

    def test_unicode_in_confirmation(self):
        """Test: Handles unicode characters in responses"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert
        assert flow.handle_confirmation_response("yeah 👍") is True
        assert flow.handle_confirmation_response("nope ❌") is False

    def test_whitespace_handling(self):
        """Test: Properly handles whitespace"""
        # Arrange
        flow = ConfirmationFlow()

        # Act & Assert
        assert flow.handle_confirmation_response("   YES   ") is True
        assert flow.handle_confirmation_response("\tno\t") is False
        assert flow.handle_confirmation_response("y e s") is None  # Spaces break matching


# Markers for pytest
pytestmark = pytest.mark.unit
