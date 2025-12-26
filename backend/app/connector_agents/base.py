"""
Base Connector Agent Class.

Provides the foundation for all connector sub-agents.
Each connector (Notion, Slack, etc.) extends this base class.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from agents import Agent
from agents.tool import FunctionTool
from agents.extensions.models.litellm_model import LitellmModel

logger = logging.getLogger(__name__)


class BaseConnectorAgent(ABC):
    """
    Abstract base class for connector sub-agents.

    Each connector implements this class to create a specialized agent
    that handles all operations for that external service.

    Attributes:
        connector_id: Database ID of the user's connector
        connector_name: Human-readable name (e.g., "Notion", "Slack")
        server_url: MCP server URL for the connector
        auth_config: Decrypted authentication configuration
        tools: List of MCP tools available from this connector
    """

    # Connector type identifier (override in subclass)
    CONNECTOR_TYPE: str = "base"

    # Tool name when used as sub-agent tool (override in subclass)
    TOOL_NAME: str = "connector"

    # Tool description for main agent (override in subclass)
    TOOL_DESCRIPTION: str = "Handle operations with external connector"

    def __init__(
        self,
        connector_id: int,
        connector_name: str,
        server_url: str,
        auth_config: Dict[str, Any],
        user_id: int,
    ):
        """
        Initialize connector agent.

        Args:
            connector_id: Database ID of the connector
            connector_name: Display name of the connector
            server_url: MCP server endpoint URL
            auth_config: Decrypted auth configuration (tokens, etc.)
            user_id: Owner user ID
        """
        self.connector_id = connector_id
        self.connector_name = connector_name
        self.server_url = server_url
        self.auth_config = auth_config
        self.user_id = user_id
        self._agent: Optional[Agent] = None
        self._tools: List[FunctionTool] = []
        self._is_initialized = False

        logger.info(
            f"[{self.CONNECTOR_TYPE}Agent] Created for user {user_id}, "
            f"connector {connector_id}: {connector_name}"
        )

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this connector agent.

        Override in subclass to provide connector-specific instructions.

        Returns:
            System prompt string with connector-specific knowledge
        """
        pass

    @abstractmethod
    async def load_tools(self) -> List[FunctionTool]:
        """
        Load MCP tools for this connector.

        Override in subclass to load tools from the MCP server.

        Returns:
            List of FunctionTool objects
        """
        pass

    def get_model(self):
        """
        Get the LLM model for this agent.

        Uses Gemini via LiteLLM if available, otherwise OpenAI.
        """
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            model = os.getenv("GEMINI_MODEL", "gemini/gemini-2.5-flash")
            logger.info(f"[{self.CONNECTOR_TYPE}Agent] Using model: {model}")
            return LitellmModel(model=model, api_key=gemini_key)
        else:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            logger.info(f"[{self.CONNECTOR_TYPE}Agent] Using OpenAI model: {model}")
            return model

    async def initialize(self) -> bool:
        """
        Initialize the connector agent.

        Loads tools and creates the agent instance.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._is_initialized:
            return True

        try:
            logger.info(f"[{self.CONNECTOR_TYPE}Agent] Initializing...")

            # Load MCP tools
            self._tools = await self.load_tools()

            if not self._tools:
                logger.warning(f"[{self.CONNECTOR_TYPE}Agent] No tools loaded!")
                return False

            logger.info(
                f"[{self.CONNECTOR_TYPE}Agent] Loaded {len(self._tools)} tools: "
                f"{[t.name for t in self._tools]}"
            )

            # Create the agent
            self._agent = Agent(
                name=f"{self.connector_name} Agent",
                instructions=self.get_system_prompt(),
                model=self.get_model(),
                tools=self._tools,
            )

            self._is_initialized = True
            logger.info(f"[{self.CONNECTOR_TYPE}Agent] Initialized successfully")
            return True

        except Exception as e:
            logger.error(f"[{self.CONNECTOR_TYPE}Agent] Initialization failed: {e}")
            return False

    def get_agent(self) -> Optional[Agent]:
        """
        Get the underlying Agent instance.

        Returns:
            Agent instance if initialized, None otherwise
        """
        return self._agent

    def as_tool(self, is_enabled: bool = True) -> Optional[Any]:
        """
        Convert this connector agent to a tool for the main agent.

        Args:
            is_enabled: Whether the tool should be enabled

        Returns:
            Tool definition for use with main agent
        """
        if not self._agent:
            logger.warning(f"[{self.CONNECTOR_TYPE}Agent] Cannot create tool - not initialized")
            return None

        return self._agent.as_tool(
            tool_name=self.TOOL_NAME,
            tool_description=self.TOOL_DESCRIPTION,
            is_enabled=is_enabled,
        )

    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._is_initialized

    @property
    def tool_count(self) -> int:
        """Get number of loaded tools."""
        return len(self._tools)
