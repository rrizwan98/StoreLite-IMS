"""
System Tools Registry.

This module defines the developer-managed system tools (Gmail, Analytics, etc.)
that are available to all users. Tool availability is controlled by the
is_enabled flag.

This is a code-based registry - not stored in database.
User's connection status is stored in user_tool_status table.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class SystemTool:
    """
    System tool definition.

    Attributes:
        id: Unique tool identifier (e.g., 'gmail', 'analytics')
        name: Display name for UI
        description: What the tool does
        icon: Icon identifier for UI
        category: Tool category (communication, insights, utilities)
        auth_type: Authentication type ('none', 'oauth')
        is_enabled: Whether tool is available for use
        is_beta: Whether tool is marked as "coming soon"
    """
    id: str
    name: str
    description: str
    icon: str
    category: str
    auth_type: str
    is_enabled: bool = True
    is_beta: bool = False


# ============================================================================
# System Tools Registry (Developer-Managed)
# ============================================================================

SYSTEM_TOOLS: Dict[str, SystemTool] = {
    "gmail": SystemTool(
        id="gmail",
        name="Gmail",
        description="Send emails via Gmail",
        icon="mail",
        category="communication",
        auth_type="oauth",
        is_enabled=True,
        is_beta=False,
    ),
    "analytics": SystemTool(
        id="analytics",
        name="Analytics",
        description="View sales and inventory analytics",
        icon="chart",
        category="insights",
        auth_type="none",
        is_enabled=True,
        is_beta=False,
    ),
    "export": SystemTool(
        id="export",
        name="Export",
        description="Export data to various formats (CSV, PDF)",
        icon="download",
        category="utilities",
        auth_type="none",
        is_enabled=False,  # Coming soon
        is_beta=True,
    ),
    "google_search": SystemTool(
        id="google_search",
        name="Google Search",
        description="Search the web for real-time information, documentation, news, and current events",
        icon="search",
        category="utilities",
        auth_type="none",  # No user auth needed - uses server's GEMINI_API_KEY
        is_enabled=True,
        is_beta=False,
    ),
    "file_search": SystemTool(
        id="file_search",
        name="File Search",
        description="Search through your uploaded files (PDFs, documents, spreadsheets) using semantic search with citations",
        icon="document",
        category="utilities",
        auth_type="none",  # Uses user's Gemini FileSearchStore
        is_enabled=True,
        is_beta=False,
    ),
}


# ============================================================================
# Registry Functions
# ============================================================================

def get_all_system_tools() -> List[Dict]:
    """
    Get all system tools as list of dicts.

    Returns:
        List of tool dictionaries
    """
    return [asdict(tool) for tool in SYSTEM_TOOLS.values()]


def get_system_tool(tool_id: str) -> Optional[SystemTool]:
    """
    Get a specific system tool by ID.

    Args:
        tool_id: Tool identifier (e.g., 'gmail')

    Returns:
        SystemTool if found, None otherwise
    """
    return SYSTEM_TOOLS.get(tool_id)


def get_enabled_tools() -> List[Dict]:
    """
    Get only enabled (non-beta) system tools.

    Returns:
        List of enabled tool dictionaries
    """
    return [
        asdict(tool)
        for tool in SYSTEM_TOOLS.values()
        if tool.is_enabled and not tool.is_beta
    ]


def get_tools_by_category(category: str) -> List[Dict]:
    """
    Get system tools by category.

    Args:
        category: Category name (communication, insights, utilities)

    Returns:
        List of matching tool dictionaries
    """
    return [
        asdict(tool)
        for tool in SYSTEM_TOOLS.values()
        if tool.category == category
    ]
