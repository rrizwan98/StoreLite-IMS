"""
Pydantic Schemas Package for IMS Backend

Contains request/response models for API validation.

This __init__.py re-exports all schemas from both:
- app.schemas_core (the original schemas: ItemCreate, BillCreate, etc.)
- app.schemas.developer_portal (new feature schemas)

This allows imports like:
    from app.schemas import ItemCreate, CreateAgentRequest
"""

# Import from developer_portal module (in this package)
from app.schemas.developer_portal import (
    # Request models
    CreateAgentRequest,
    UpdateAgentRequest,
    PublicChatRequest,
    # Response models
    AgentResponse,
    AgentCreatedResponse,
    AgentListResponse,
    PublicChatResponse,
    UsageStatsResponse,
    EmbedCodeResponse,
    RegenerateKeyResponse,
    RateLimitErrorResponse,
    TableSummary,
)

# Re-export core schemas from parent module to maintain backward compatibility
def _import_core_schemas():
    """Import core schemas from the parent schemas_core module."""
    import importlib.util
    import os

    schemas_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas.py")
    spec = importlib.util.spec_from_file_location("schemas_core", schemas_py_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_core = _import_core_schemas()

# Re-export all core schemas
ItemCreate = _core.ItemCreate
ItemUpdate = _core.ItemUpdate
ItemResponse = _core.ItemResponse
BillItemCreate = _core.BillItemCreate
BillItemResponse = _core.BillItemResponse
BillCreate = _core.BillCreate
BillResponse = _core.BillResponse
AgentMessageRequest = _core.AgentMessageRequest
ToolCall = _core.ToolCall
AgentMessageResponse = _core.AgentMessageResponse
ChatKitMessage = _core.ChatKitMessage
ChatKitResponse = _core.ChatKitResponse
ChatKitSession = _core.ChatKitSession
ChatKitSessionResponse = _core.ChatKitSessionResponse
AuthType = _core.AuthType
SystemToolResponse = _core.SystemToolResponse
ToolConnectRequest = _core.ToolConnectRequest
SystemToolsListResponse = _core.SystemToolsListResponse
DiscoveredTool = _core.DiscoveredTool
ConnectorCreateRequest = _core.ConnectorCreateRequest
ConnectorUpdateRequest = _core.ConnectorUpdateRequest
ConnectorTestRequest = _core.ConnectorTestRequest
ConnectorTestResponse = _core.ConnectorTestResponse
ConnectorToggleRequest = _core.ConnectorToggleRequest
ConnectorResponse = _core.ConnectorResponse
ConnectorListResponse = _core.ConnectorListResponse
DeleteResponse = _core.DeleteResponse
AppsTool = _core.AppsTool
AppsMenuResponse = _core.AppsMenuResponse

__all__ = [
    # Core schemas - Items
    "ItemCreate",
    "ItemUpdate",
    "ItemResponse",
    # Core schemas - Bills
    "BillItemCreate",
    "BillItemResponse",
    "BillCreate",
    "BillResponse",
    # Core schemas - Agent
    "AgentMessageRequest",
    "ToolCall",
    "AgentMessageResponse",
    # Core schemas - ChatKit
    "ChatKitMessage",
    "ChatKitResponse",
    "ChatKitSession",
    "ChatKitSessionResponse",
    # Core schemas - Connectors
    "AuthType",
    "SystemToolResponse",
    "ToolConnectRequest",
    "SystemToolsListResponse",
    "DiscoveredTool",
    "ConnectorCreateRequest",
    "ConnectorUpdateRequest",
    "ConnectorTestRequest",
    "ConnectorTestResponse",
    "ConnectorToggleRequest",
    "ConnectorResponse",
    "ConnectorListResponse",
    "DeleteResponse",
    "AppsTool",
    "AppsMenuResponse",
    # Developer portal schemas
    "CreateAgentRequest",
    "UpdateAgentRequest",
    "PublicChatRequest",
    "AgentResponse",
    "AgentCreatedResponse",
    "AgentListResponse",
    "PublicChatResponse",
    "UsageStatsResponse",
    "EmbedCodeResponse",
    "RegenerateKeyResponse",
    "RateLimitErrorResponse",
    "TableSummary",
]
