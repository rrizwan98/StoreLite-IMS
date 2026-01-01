"""
Connector Agent Registry.

Factory for creating and managing connector sub-agents.
Loads user's active connectors and creates appropriate agent instances.
"""

import logging
from typing import Dict, List, Any, Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import UserMCPConnection
from app.connectors.encryption import decrypt_credentials
from .base import BaseConnectorAgent
from .notion_agent import NotionConnectorAgent
from .gdrive_agent import GoogleDriveConnectorAgent
from .gmail_agent import GmailConnectorAgent

logger = logging.getLogger(__name__)


class ConnectorAgentRegistry:
    """
    Registry for connector sub-agents.

    Maps connector types to their specialized agent classes.
    Handles creation and initialization of connector agents.
    """

    # Map connector types to agent classes
    AGENT_CLASSES: Dict[str, Type[BaseConnectorAgent]] = {
        "notion": NotionConnectorAgent,
        "google_drive": GoogleDriveConnectorAgent,
        "gdrive": GoogleDriveConnectorAgent,  # Alias
        "gmail": GmailConnectorAgent,
        # Future connectors:
        # "slack": SlackConnectorAgent,
        # "airtable": AirtableConnectorAgent,
    }

    # URL patterns to detect connector type
    URL_PATTERNS: Dict[str, str] = {
        "notion": "notion",
        "gdrive": "google_drive",
        "google-drive": "google_drive",
        "google_drive": "google_drive",
        "gmail": "gmail",
        "mail": "gmail",
        "slack": "slack",
        "airtable": "airtable",
    }

    def __init__(self):
        """Initialize the registry."""
        self._agents: Dict[int, BaseConnectorAgent] = {}
        logger.info("[ConnectorRegistry] Initialized")

    def detect_connector_type(self, connector: UserMCPConnection) -> Optional[str]:
        """
        Detect the connector type from URL or name.

        Args:
            connector: UserMCPConnection model

        Returns:
            Detected connector type (e.g., "notion") or None
        """
        # Check URL first
        url_lower = connector.server_url.lower()
        for pattern, conn_type in self.URL_PATTERNS.items():
            if pattern in url_lower:
                logger.info(f"[ConnectorRegistry] Detected type '{conn_type}' from URL: {connector.server_url}")
                return conn_type

        # Check name as fallback
        name_lower = connector.name.lower()
        for pattern, conn_type in self.URL_PATTERNS.items():
            if pattern in name_lower:
                logger.info(f"[ConnectorRegistry] Detected type '{conn_type}' from name: {connector.name}")
                return conn_type

        logger.info(f"[ConnectorRegistry] Could not detect type for: {connector.name} ({connector.server_url})")
        return None

    def get_agent_class(self, connector_type: str) -> Optional[Type[BaseConnectorAgent]]:
        """
        Get the agent class for a connector type.

        Args:
            connector_type: Type of connector (e.g., "notion", "slack")

        Returns:
            Agent class if supported, None otherwise
        """
        normalized_type = connector_type.lower().strip()
        return self.AGENT_CLASSES.get(normalized_type)

    def is_supported(self, connector_type: str) -> bool:
        """
        Check if a connector type has a specialized agent.

        Args:
            connector_type: Type of connector

        Returns:
            True if supported, False otherwise
        """
        return self.get_agent_class(connector_type) is not None

    async def create_agent(
        self,
        connector: UserMCPConnection,
        connector_type: str,
        decrypted_config: Dict[str, Any],
    ) -> Optional[BaseConnectorAgent]:
        """
        Create a connector agent instance.

        Args:
            connector: UserMCPConnection database model
            connector_type: Detected connector type (e.g., "notion")
            decrypted_config: Decrypted authentication configuration

        Returns:
            Initialized connector agent, or None if failed
        """
        agent_class = self.get_agent_class(connector_type)

        if not agent_class:
            logger.warning(
                f"[ConnectorRegistry] No agent class for type: {connector_type}"
            )
            return None

        try:
            # Create agent instance
            agent = agent_class(
                connector_id=connector.id,
                connector_name=connector.name,
                server_url=connector.server_url,
                auth_config=decrypted_config,
                user_id=connector.user_id,
            )

            # Initialize (loads tools and creates internal agent)
            success = await agent.initialize()

            if success:
                self._agents[connector.id] = agent
                logger.info(
                    f"[ConnectorRegistry] Created {connector_type} agent "
                    f"for connector {connector.id} with {agent.tool_count} tools"
                )
                return agent
            else:
                logger.error(
                    f"[ConnectorRegistry] Failed to initialize {connector_type} agent"
                )
                return None

        except Exception as e:
            logger.error(
                f"[ConnectorRegistry] Error creating agent for {connector_type}: {e}"
            )
            return None

    def get_cached_agent(self, connector_id: int) -> Optional[BaseConnectorAgent]:
        """
        Get a cached agent by connector ID.

        Args:
            connector_id: Database ID of the connector

        Returns:
            Cached agent if exists, None otherwise
        """
        return self._agents.get(connector_id)

    def clear_cache(self, connector_id: Optional[int] = None):
        """
        Clear cached agents.

        Args:
            connector_id: If provided, only clear this connector's agent.
                         If None, clear all cached agents.
        """
        if connector_id:
            if connector_id in self._agents:
                del self._agents[connector_id]
                logger.info(f"[ConnectorRegistry] Cleared agent cache for connector {connector_id}")
        else:
            self._agents.clear()
            logger.info("[ConnectorRegistry] Cleared all agent caches")


# Global registry instance
_registry = ConnectorAgentRegistry()


async def get_connector_agent_tools(
    db: AsyncSession,
    user_id: int,
) -> List[Any]:
    """
    Get all connector agents as tools for the Schema Agent.

    This is the main entry point for integrating connector sub-agents
    with the Schema Agent. It:
    1. Loads all active connectors for the user
    2. Creates specialized sub-agents for each
    3. Returns them as tools that Schema Agent can use

    Args:
        db: Database session
        user_id: User ID to load connectors for

    Returns:
        List of tools (agent.as_tool()) for Schema Agent
    """
    logger.info(f"[ConnectorRegistry] Loading connector agent tools for user {user_id}")

    tools = []
    seen_connector_types = set()  # Track types to avoid duplicate tools

    try:
        # Query active and verified connectors for this user
        # Order by id desc to get most recent first
        query = select(UserMCPConnection).where(
            UserMCPConnection.user_id == user_id,
            UserMCPConnection.is_active == True,
            UserMCPConnection.is_verified == True,
        ).order_by(UserMCPConnection.id.desc())
        result = await db.execute(query)
        connectors = result.scalars().all()

        logger.info(f"[ConnectorRegistry] Found {len(connectors)} active verified connectors")

        for connector in connectors:
            # Detect connector type from URL/name
            connector_type = _registry.detect_connector_type(connector)

            if not connector_type:
                logger.info(
                    f"[ConnectorRegistry] Could not detect type for connector: {connector.name}"
                )
                continue

            # Skip if we already have a tool for this connector type (avoid duplicates)
            if connector_type in seen_connector_types:
                logger.info(
                    f"[ConnectorRegistry] Skipping duplicate {connector_type} connector: {connector.name} (id={connector.id})"
                )
                continue

            # Check if we support this connector type
            if not _registry.is_supported(connector_type):
                logger.info(
                    f"[ConnectorRegistry] No sub-agent for type: {connector_type} ({connector.name})"
                )
                continue

            try:
                # Decrypt auth config
                decrypted_config = {}
                if connector.auth_config:
                    try:
                        decrypted_config = decrypt_credentials(connector.auth_config)
                    except Exception as e:
                        logger.warning(
                            f"[ConnectorRegistry] Failed to decrypt config for connector {connector.id}: {e}"
                        )

                # Create or get cached agent
                agent = _registry.get_cached_agent(connector.id)

                if not agent:
                    agent = await _registry.create_agent(
                        connector, connector_type, decrypted_config
                    )

                if agent and agent.is_initialized:
                    # Convert agent to tool for Schema Agent
                    tool = agent.as_tool(is_enabled=True)
                    if tool:
                        tools.append(tool)
                        seen_connector_types.add(connector_type)  # Mark type as seen
                        logger.info(
                            f"[ConnectorRegistry] Added {connector_type} sub-agent tool: "
                            f"{agent.TOOL_NAME}"
                        )

            except Exception as e:
                logger.error(
                    f"[ConnectorRegistry] Error processing connector {connector.id}: {e}"
                )
                continue

        logger.info(f"[ConnectorRegistry] Returning {len(tools)} connector sub-agent tools")
        return tools

    except Exception as e:
        logger.error(f"[ConnectorRegistry] Error loading connector agent tools: {e}")
        return []


def get_registry() -> ConnectorAgentRegistry:
    """Get the global registry instance."""
    return _registry
