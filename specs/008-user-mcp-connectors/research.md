# Research: User MCP Connectors

**Feature**: 008-user-mcp-connectors | **Date**: 2025-12-21

## Executive Summary

This research validates the technical approach for User MCP Connectors feature. The codebase already uses **FastMCP** for MCP server implementation and has established patterns for encryption, HTTP client communication, and SQLAlchemy models that we will extend.

---

## 1. Existing Codebase Patterns

### 1.1 FastMCP Server (Already Implemented)

**Location**: `backend/app/mcp_server/server.py`

```python
from fastmcp import FastMCP

def create_server() -> FastMCP:
    server = FastMCP("ims-mcp-server")
    return server

# Tool registration pattern
@server.tool()
async def add_inventory_item(name: str, category: str, ...) -> dict:
    """Tool description for LLM"""
    async with async_session() as session:
        return await inventory_add_item(...)
```

**Key Findings**:
- Uses `fastmcp` package (already in dependencies)
- SSE transport on port 8001: `server.run_async(transport="sse", host="127.0.0.1", port=8001)`
- Tools registered via `@server.tool()` decorator
- Async session management for database operations

### 1.2 MCP HTTP Client (Already Implemented)

**Location**: `backend/app/agents/tools_client.py`

```python
class MCPClient:
    def __init__(self, base_url: str = "http://localhost:8001", timeout: int = 10):
        self.client = httpx.Client(timeout=timeout)
        self._tools_cache: Optional[List[Dict]] = None

    def discover_tools(self) -> List[Dict]:
        response = self.client.get(f"{self.base_url}/mcp/tools")
        return response.json().get("tools", [])

    def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        response = self.client.post(
            f"{self.base_url}/mcp/call",
            json={"tool": tool_name, "arguments": arguments}
        )
        return response.json().get("result", {})
```

**Key Findings**:
- HTTP-based client using `httpx`
- 10-second default timeout (matches FR-012)
- Tool caching with TTL (300 seconds)
- Endpoints: `/mcp/tools` (discovery), `/mcp/call` (execution)

### 1.3 Encryption Service (Already Implemented)

**Location**: `backend/app/services/encryption_service.py`

```python
from cryptography.fernet import Fernet

class EncryptionService:
    def encrypt(self, plaintext: str) -> str:
        encrypted = self._fernet.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> str:
        decrypted = self._fernet.decrypt(ciphertext.encode())
        return decrypted.decode()

# Convenience functions
def encrypt_token(token: str) -> str: ...
def decrypt_token(encrypted_token: str) -> str: ...
```

**Key Findings**:
- Fernet encryption (AES-128-CBC with HMAC) - secure for credential storage
- Key from `TOKEN_ENCRYPTION_KEY` environment variable
- Singleton pattern with `get_encryption_service()`
- Ready to use for MCP connector credentials

### 1.4 SQLAlchemy Models Pattern

**Location**: `backend/app/models.py`

**Existing Patterns**:
- `User` - User account with relationships
- `UserConnection` - Database connection preferences (has Gmail OAuth fields)
- JSONB columns for flexible data (e.g., `schema_metadata`, `gmail_scopes`)
- Encrypted token storage pattern (e.g., `gmail_access_token`, `gmail_refresh_token`)

---

## 2. FastMCP Client for User Connectors

### 2.1 Connecting to External MCP Servers

For user-added MCP connectors, we need to connect to **external** MCP servers (not our own). FastMCP supports both server and client modes.

**Client Connection Pattern**:
```python
from fastmcp import Client

async def connect_to_user_mcp(server_url: str) -> list:
    """Connect to user's MCP server and discover tools"""
    async with Client(server_url) as client:
        tools = await client.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            for tool in tools
        ]
```

**HTTP Client Pattern** (for SSE/HTTP MCP servers):
```python
import httpx

async def discover_tools_http(server_url: str, timeout: float = 10.0) -> list:
    """Discover tools from HTTP-based MCP server"""
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(f"{server_url}/mcp/tools")
        response.raise_for_status()
        return response.json().get("tools", [])
```

### 2.2 Transport Detection

MCP servers can use different transports. For user connectors:

| Transport | URL Pattern | Use Case |
|-----------|-------------|----------|
| HTTP/SSE | `http://`, `https://` | Remote servers (primary) |
| stdio | `command://` | Local CLI tools (future) |

**Decision**: Start with HTTP/SSE only (matches existing `MCPClient` pattern).

---

## 3. Connection Validation Strategy

### 3.1 Validation Steps (FR-011 to FR-014)

```python
from dataclasses import dataclass
from enum import Enum

class ValidationErrorCode(Enum):
    INVALID_URL = "INVALID_URL"
    CONNECTION_FAILED = "CONNECTION_FAILED"
    TIMEOUT = "TIMEOUT"
    AUTH_FAILED = "AUTH_FAILED"
    INVALID_MCP_SERVER = "INVALID_MCP_SERVER"
    NO_TOOLS = "NO_TOOLS"

@dataclass
class ValidationResult:
    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    tools: Optional[list] = None

async def validate_mcp_connection(
    server_url: str,
    auth_type: str = "none",
    auth_config: dict = None
) -> ValidationResult:
    # Step 1: URL format validation
    if not is_valid_url(server_url):
        return ValidationResult(
            success=False,
            error_code="INVALID_URL",
            error_message="Invalid URL format. Must be HTTP/HTTPS."
        )

    # Step 2: Connection with 10-second timeout
    try:
        async with asyncio.timeout(10):
            tools = await discover_tools_http(server_url)
    except asyncio.TimeoutError:
        return ValidationResult(
            success=False,
            error_code="TIMEOUT",
            error_message="Connection timed out after 10 seconds."
        )
    except httpx.ConnectError:
        return ValidationResult(
            success=False,
            error_code="CONNECTION_FAILED",
            error_message="Cannot connect to server."
        )

    # Step 3: Verify it's an MCP server
    if tools is None:
        return ValidationResult(
            success=False,
            error_code="INVALID_MCP_SERVER",
            error_message="Not a valid MCP server."
        )

    # Step 4: Check for tools
    if len(tools) == 0:
        return ValidationResult(
            success=True,  # Connected but warning
            tools=[],
            error_message="Connected but no tools found."
        )

    return ValidationResult(success=True, tools=tools)
```

### 3.2 Retry Strategy (FR-024)

```python
async def call_tool_with_retry(
    client: MCPClient,
    tool_name: str,
    arguments: dict,
    max_retries: int = 1,
    retry_delay: float = 3.0
) -> dict:
    """Call tool with one retry on failure"""
    for attempt in range(max_retries + 1):
        try:
            return await client.call_tool(tool_name, arguments)
        except (ConnectionError, TimeoutError) as e:
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)
                continue
            raise
```

---

## 4. Tool Namespacing Strategy (FR-023)

### 4.1 Namespace Pattern

To prevent tool name conflicts between connectors:

```python
def namespace_tool(connector_name: str, tool_name: str) -> str:
    """Create namespaced tool name: 'ConnectorName: tool_name'"""
    return f"{connector_name}: {tool_name}"

# Example:
# Connector: "My Slack"
# Tool: "send_message"
# Result: "My Slack: send_message"
```

### 4.2 Tool Loading for Agent

```python
async def load_user_tools(user_id: int) -> list:
    """Load all tools from user's active connectors"""
    connectors = await get_active_connectors(user_id)
    all_tools = []

    for connector in connectors:
        try:
            client = MCPClient(connector.server_url)
            tools = client.discover_tools()

            for tool in tools:
                tool["name"] = namespace_tool(connector.name, tool["name"])
                tool["connector_id"] = connector.id
                all_tools.append(tool)
        except Exception as e:
            logger.warning(f"Failed to load tools from {connector.name}: {e}")
            # Continue with other connectors

    return all_tools
```

---

## 5. Database Schema Design

### 5.1 New Models Required

```python
class UserToolStatus(Base):
    """Track user's connection status for SYSTEM tools"""
    __tablename__ = "user_tool_status"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tool_id = Column(String(50), nullable=False)  # 'gmail', 'analytics', etc.
    is_connected = Column(Boolean, default=False)
    config = Column(JSONB, nullable=True)  # Tool-specific settings
    connected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'tool_id', name='uq_user_tool'),
    )


class UserMCPConnection(Base):
    """User's custom MCP server connection"""
    __tablename__ = "user_mcp_connections"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    server_url = Column(String(500), nullable=False)
    auth_type = Column(String(50), default="none")  # 'none', 'oauth', 'api_key'
    auth_config = Column(Text, nullable=True)  # Encrypted JSON
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    discovered_tools = Column(JSONB, nullable=True)  # Cached tools list
    last_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("auth_type IN ('none', 'oauth', 'api_key')", name="auth_type_check"),
    )
```

### 5.2 Relationship to Existing Models

- `UserMCPConnection.user_id` → `User.id` (many-to-one)
- `UserToolStatus.user_id` → `User.id` (many-to-one)
- Max 10 `UserMCPConnection` per user (application-level constraint)

---

## 6. System Tools Registry

### 6.1 Code-Based Registry Pattern

```python
# backend/app/tools/registry.py

from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class SystemTool:
    id: str
    name: str
    description: str
    icon: str
    category: str
    auth_type: str  # 'none', 'oauth'
    is_enabled: bool = True
    is_beta: bool = False

# Registry of all system tools (developer-managed)
SYSTEM_TOOLS: Dict[str, SystemTool] = {
    "gmail": SystemTool(
        id="gmail",
        name="Gmail",
        description="Send emails via Gmail",
        icon="mail",
        category="communication",
        auth_type="oauth",
        is_enabled=True,
    ),
    "analytics": SystemTool(
        id="analytics",
        name="Analytics",
        description="View sales and inventory analytics",
        icon="chart",
        category="insights",
        auth_type="none",
        is_enabled=True,
    ),
    "export": SystemTool(
        id="export",
        name="Export",
        description="Export data to various formats",
        icon="download",
        category="utilities",
        auth_type="none",
        is_enabled=False,  # Coming soon
        is_beta=True,
    ),
}

def get_system_tools() -> List[SystemTool]:
    """Get all system tools"""
    return list(SYSTEM_TOOLS.values())

def get_system_tool(tool_id: str) -> Optional[SystemTool]:
    """Get a specific system tool"""
    return SYSTEM_TOOLS.get(tool_id)
```

---

## 7. API Endpoints Design

### 7.1 System Tools API (`/api/tools`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tools` | List all system tools with user's connection status |
| POST | `/api/tools/{tool_id}/connect` | Connect to system tool (trigger OAuth if needed) |
| POST | `/api/tools/{tool_id}/disconnect` | Disconnect from system tool |

### 7.2 User Connectors API (`/api/connectors`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/connectors` | List user's MCP connectors |
| POST | `/api/connectors` | Create new connector (must be verified first) |
| POST | `/api/connectors/test` | Test connection before saving |
| GET | `/api/connectors/{id}` | Get connector details |
| PUT | `/api/connectors/{id}` | Update connector |
| DELETE | `/api/connectors/{id}` | Delete connector |
| POST | `/api/connectors/{id}/toggle` | Enable/disable connector |

---

## 8. Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| MCP Framework | FastMCP | Already in use, proven patterns |
| Transport | HTTP/SSE only | Matches existing MCPClient, simpler |
| Encryption | Existing Fernet service | Reuse, already tested |
| Tool caching | JSONB in PostgreSQL | Persistent, queryable |
| Namespacing | "Connector: tool" format | Clear, prevents conflicts |
| Validation timeout | 10 seconds | Matches spec FR-012 |
| Retry strategy | 1 retry, 3s delay | Matches spec FR-024 |

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| External MCP server downtime | Retry with delay, graceful error messages |
| Credential exposure | Fernet encryption, never log credentials |
| Tool name conflicts | Namespace with connector name |
| Slow MCP servers | 10-second timeout, async operations |
| Too many connectors | 10 per user limit (application-level) |

---

## 10. Dependencies

### Existing (No Changes)
- `fastmcp` - MCP server/client
- `httpx` - HTTP client
- `cryptography` - Fernet encryption
- `sqlalchemy` - ORM

### New (To Add)
- None required - all dependencies already in place

---

## Conclusion

The codebase is well-prepared for User MCP Connectors:

1. **FastMCP** already implemented for server-side
2. **MCPClient** pattern ready to extend for user connectors
3. **EncryptionService** ready for credential storage
4. **SQLAlchemy patterns** established for new models

**Next Steps**:
1. Create data-model.md with detailed schema
2. Create API contracts (OpenAPI specs)
3. Create quickstart.md for development setup
