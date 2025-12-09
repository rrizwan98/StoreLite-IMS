"""
Confirmation Flow for destructive actions.

Detects actions that require user confirmation (bill creation, item deletion)
and manages the confirmation state machine.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Destructive action keywords
DESTRUCTIVE_KEYWORDS = {
    "create bill": ["create", "bill", "invoice"],
    "delete item": ["delete", "remove", "item"],
    "clear stock": ["clear", "zero", "stock"],
}

CONFIRMATION_KEYWORDS = {
    "yes": ["yes", "yeah", "yep", "sure", "ok", "okay", "confirm"],
    "no": ["no", "nope", "cancel", "don't", "dont", "never"],
}


class ConfirmationFlow:
    """Manages confirmation flow for destructive actions."""

    def __init__(self, timeout_seconds: int = 300):
        """
        Initialize ConfirmationFlow.

        Args:
            timeout_seconds: Time before pending confirmation expires
        """
        self.timeout_seconds = timeout_seconds
        self.pending_confirmations: Dict[str, Dict[str, Any]] = {}

    def is_destructive_action(
        self, user_message: str, agent_intent: Optional[str] = None
    ) -> bool:
        """
        Detect if a user message represents a destructive action.

        Args:
            user_message: User's natural language message
            agent_intent: Optional extracted intent from agent

        Returns:
            True if action requires confirmation
        """
        lower_msg = user_message.lower()

        # Check for bill creation keywords
        bill_keywords = DESTRUCTIVE_KEYWORDS["create bill"]
        if all(keyword in lower_msg for keyword in bill_keywords):
            logger.debug(f"Detected destructive action: create bill")
            return True

        # Check for delete/remove keywords
        delete_keywords = DESTRUCTIVE_KEYWORDS["delete item"]
        if any(keyword in lower_msg for keyword in delete_keywords):
            logger.debug(f"Detected destructive action: delete item")
            return True

        # Check agent intent if available
        if agent_intent:
            agent_intent_lower = agent_intent.lower()
            if "delete" in agent_intent_lower or "remove" in agent_intent_lower:
                return True
            if "bill" in agent_intent_lower and "create" in agent_intent_lower:
                return True

        return False

    def generate_confirmation_prompt(
        self, action_type: str, action_details: Dict[str, Any]
    ) -> str:
        """
        Generate a user-friendly confirmation prompt.

        Args:
            action_type: Type of action (e.g., 'bill_creation', 'item_deletion')
            action_details: Details about the action

        Returns:
            Confirmation prompt string
        """
        if action_type == "bill_creation":
            customer = action_details.get("customer_name", "the customer")
            total = action_details.get("total_amount", "?")
            items_summary = action_details.get("items_summary", "items")

            prompt = (
                f"Are you sure you want to create a bill for {customer}: {items_summary} "
                f"(Total: ${total})? Reply 'yes' to confirm."
            )

        elif action_type == "item_deletion":
            item_name = action_details.get("item_name", "this item")
            prompt = f"Are you sure you want to delete {item_name}? Reply 'yes' to confirm."

        else:
            prompt = "Are you sure you want to proceed? Reply 'yes' to confirm."

        return prompt

    def handle_confirmation_response(self, response: str) -> Optional[bool]:
        """
        Parse user response to confirmation question.

        Args:
            response: User's response (e.g., 'yes', 'no', 'maybe')

        Returns:
            True if confirmed, False if denied, None if invalid response
        """
        lower_response = response.lower().strip()

        # Check for yes
        for yes_keyword in CONFIRMATION_KEYWORDS["yes"]:
            if yes_keyword in lower_response:
                logger.debug("Confirmation response: YES")
                return True

        # Check for no
        for no_keyword in CONFIRMATION_KEYWORDS["no"]:
            if no_keyword in lower_response:
                logger.debug("Confirmation response: NO")
                return False

        # Invalid response
        logger.debug(f"Invalid confirmation response: {response}")
        return None

    def set_pending_confirmation(
        self,
        session_id: str,
        action_type: str,
        action_details: Dict[str, Any],
    ) -> None:
        """
        Mark an action as pending confirmation.

        Args:
            session_id: Session ID
            action_type: Type of action
            action_details: Action details
        """
        self.pending_confirmations[session_id] = {
            "action_type": action_type,
            "action_details": action_details,
            "timestamp": datetime.utcnow(),
        }
        logger.debug(
            f"Pending confirmation set for {session_id}: {action_type}"
        )

    def get_pending_confirmation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get pending confirmation for session."""
        pending = self.pending_confirmations.get(session_id)

        if not pending:
            return None

        # Check if pending confirmation expired
        age = datetime.utcnow() - pending["timestamp"]
        if age > timedelta(seconds=self.timeout_seconds):
            logger.debug(f"Pending confirmation expired for {session_id}")
            self.pending_confirmations.pop(session_id, None)
            return None

        return pending

    def clear_pending_confirmation(self, session_id: str) -> None:
        """Clear pending confirmation for session."""
        self.pending_confirmations.pop(session_id, None)
        logger.debug(f"Pending confirmation cleared for {session_id}")
