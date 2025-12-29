"""
Connector Sub-Agents Module.

This module contains specialized sub-agents for external service connectors.
Each connector (Notion, Gmail, Google Drive, etc.) has its own dedicated agent
that handles all operations for that service.

These sub-agents are used as tools by the main Schema Agent, providing:
- Focused expertise for each connector
- Clean separation of concerns
- Easier maintenance and scaling
- Better LLM performance (fewer tools visible to main agent)

Architecture:
    Schema Agent (Main)
    ├── Database tools (postgres-mcp)
    ├── Google Search tool
    └── Connector Sub-Agents (as tools)
        ├── NotionConnectorAgent
        ├── GoogleDriveConnectorAgent
        ├── GmailConnectorAgent
        ├── SlackConnectorAgent (future)
        └── AirtableConnectorAgent (future)
"""

from .base import BaseConnectorAgent
from .notion_agent import NotionConnectorAgent
from .gdrive_agent import GoogleDriveConnectorAgent
from .gmail_agent import GmailConnectorAgent
from .registry import ConnectorAgentRegistry, get_connector_agent_tools

__all__ = [
    "BaseConnectorAgent",
    "NotionConnectorAgent",
    "GoogleDriveConnectorAgent",
    "GmailConnectorAgent",
    "ConnectorAgentRegistry",
    "get_connector_agent_tools",
]
