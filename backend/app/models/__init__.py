"""
Models Package for IMS Backend

This package contains additional SQLAlchemy models that are kept in separate files
for better organization.

This __init__.py re-exports all models from both:
- app.models_core (the original models: User, UserConnection, etc.)
- app.models.published_agent (new feature models)

This allows imports like:
    from app.models import User, PublishedAgentConfig
"""

# Import from published_agent module (in this package)
from app.models.published_agent import (
    PublishedAgentConfig,
    PublishedAgentUsage,
)

# Re-export core models from parent module to maintain backward compatibility
# We use importlib to avoid circular import issues
def _import_core_models():
    """Import core models from the parent models_core module."""
    import importlib.util
    import os

    # Get the path to models.py (which we'll rename conceptually as models_core)
    models_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models.py")

    spec = importlib.util.spec_from_file_location("models_core", models_py_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_core = _import_core_models()

# Re-export all core models
User = _core.User
UserConnection = _core.UserConnection
UserSettings = _core.UserSettings
Item = _core.Item
Bill = _core.Bill
BillItem = _core.BillItem
UserMCPConnection = _core.UserMCPConnection
UserToolStatus = _core.UserToolStatus
ScheduledTask = _core.ScheduledTask
UploadedFile = _core.UploadedFile
ConnectionType = _core.ConnectionType
ConnectionMode = _core.ConnectionMode
MCPStatus = _core.MCPStatus
AgentSession = _core.AgentSession
ConversationHistory = _core.ConversationHistory
ChatKitThread = _core.ChatKitThread
ChatKitThreadItem = _core.ChatKitThreadItem
UserFileSearchStore = _core.UserFileSearchStore
UserFileDocument = _core.UserFileDocument

__all__ = [
    # Core models
    "User",
    "UserConnection",
    "UserSettings",
    "Item",
    "Bill",
    "BillItem",
    "UserMCPConnection",
    "UserToolStatus",
    "ScheduledTask",
    "UploadedFile",
    "AgentSession",
    "ConversationHistory",
    "ChatKitThread",
    "ChatKitThreadItem",
    "UserFileSearchStore",
    "UserFileDocument",
    # Enums
    "ConnectionType",
    "ConnectionMode",
    "MCPStatus",
    # New feature models
    "PublishedAgentConfig",
    "PublishedAgentUsage",
]
