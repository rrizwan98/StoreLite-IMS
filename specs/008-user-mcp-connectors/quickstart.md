# Quickstart Guide: User MCP Connectors

**Feature**: 008-user-mcp-connectors | **Date**: 2025-12-21

This guide helps developers get started with implementing the User MCP Connectors feature.

---

## Prerequisites

### 1. Environment Setup

Ensure you have the required environment variables:

```bash
# backend/.env

# Existing (required)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/ims
TOKEN_ENCRYPTION_KEY=<your-fernet-key>  # For credential encryption

# Generate a new Fernet key if needed:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Dependencies

All required dependencies are already in the project:

```toml
# backend/pyproject.toml (already present)
dependencies = [
    "fastapi",
    "sqlalchemy[asyncio]",
    "asyncpg",
    "httpx",
    "cryptography",  # For Fernet encryption
    "fastmcp",       # MCP framework
    # ...
]
```

---

## Database Setup

### 1. Create Migration

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "add user mcp connectors tables"

# Review the generated migration file, then apply:
alembic upgrade head
```

### 2. Verify Tables

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('user_tool_status', 'user_mcp_connections');

-- Expected output:
-- user_tool_status
-- user_mcp_connections
```

---

## TDD Development Workflow

### Phase 1: Write Failing Tests First (RED)

Start with encryption tests:

```bash
# Create test file
touch backend/tests/unit/test_encryption.py
```

```python
# backend/tests/unit/test_encryption.py
import pytest
from app.connectors.encryption import (
    encrypt_credentials,
    decrypt_credentials,
    CredentialEncryptionError
)

class TestCredentialEncryption:
    """RED phase - Write these tests BEFORE implementation"""

    def test_encrypt_returns_non_empty_string(self):
        result = encrypt_credentials({"token": "secret"})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_encrypted_data_not_readable(self):
        plain = {"oauth_token": "my-secret-token-123"}
        encrypted = encrypt_credentials(plain)
        assert "my-secret-token-123" not in encrypted
        assert "oauth_token" not in encrypted

    def test_decrypt_returns_original(self):
        original = {"oauth_token": "secret", "refresh_token": "refresh"}
        encrypted = encrypt_credentials(original)
        decrypted = decrypt_credentials(encrypted)
        assert decrypted == original

    def test_invalid_encrypted_data_raises_error(self):
        with pytest.raises(CredentialEncryptionError):
            decrypt_credentials("not-valid-encrypted-data")
```

Run tests (should fail):

```bash
cd backend
pytest tests/unit/test_encryption.py -v

# Expected: All tests FAIL (module doesn't exist yet)
```

### Phase 2: Implement to Pass Tests (GREEN)

```python
# backend/app/connectors/encryption.py
import json
from app.services.encryption_service import encrypt_token, decrypt_token, EncryptionError

class CredentialEncryptionError(Exception):
    """Raised when credential encryption/decryption fails"""
    pass

def encrypt_credentials(credentials: dict) -> str:
    """Encrypt credentials dict to string"""
    try:
        json_str = json.dumps(credentials)
        return encrypt_token(json_str)
    except Exception as e:
        raise CredentialEncryptionError(f"Encryption failed: {e}")

def decrypt_credentials(encrypted: str) -> dict:
    """Decrypt string to credentials dict"""
    try:
        json_str = decrypt_token(encrypted)
        return json.loads(json_str)
    except EncryptionError as e:
        raise CredentialEncryptionError(f"Decryption failed: {e}")
    except json.JSONDecodeError as e:
        raise CredentialEncryptionError(f"Invalid JSON: {e}")
```

Run tests again:

```bash
pytest tests/unit/test_encryption.py -v

# Expected: All tests PASS
```

### Phase 3: Continue with Next Component

Repeat RED-GREEN-REFACTOR for each component:

1. `test_mcp_client.py` → `mcp_client.py`
2. `test_validator.py` → `validator.py`
3. `test_connector_manager.py` → `manager.py`
4. `test_tools_api.py` → `routers/tools.py`
5. `test_connectors_api.py` → `routers/connectors.py`

---

## Implementation Order

### Backend (in order)

```
1. app/connectors/__init__.py
2. app/connectors/encryption.py      # Wrap existing service for dict
3. app/connectors/mcp_client.py      # Extend existing MCPClient
4. app/connectors/validator.py       # Connection validation
5. app/connectors/manager.py         # CRUD operations
6. app/connectors/auth/              # Auth handlers
7. app/tools/__init__.py
8. app/tools/registry.py             # System tools registry
9. app/routers/tools.py              # System tools API
10. app/routers/connectors.py        # User connectors API
11. app/agents/schema_query_agent.py # Extend for dynamic tools
```

### Frontend (in order)

```
1. lib/tools-api.ts                  # API client for tools
2. lib/connectors-api.ts             # API client for connectors
3. components/connectors/SystemToolsList.tsx
4. components/connectors/ConnectorsList.tsx
5. components/connectors/AddConnectorForm.tsx
6. components/connectors/ConnectionTester.tsx
7. components/connectors/ConnectorsModal.tsx
8. app/dashboard/schema-agent/page.tsx  # Update ChatKit config
```

---

## Quick Implementation Examples

### 1. MCP Client Extension

```python
# backend/app/connectors/mcp_client.py
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None

class UserMCPClient:
    """Client for connecting to user's external MCP servers"""

    def __init__(self, server_url: str, timeout: float = 10.0):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout

    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover tools from MCP server"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.server_url}/mcp/tools")
            response.raise_for_status()
            return response.json().get("tools", [])

    async def validate_connection(self) -> ValidationResult:
        """Validate connection with 10-second timeout"""
        try:
            async with asyncio.timeout(10):
                tools = await self.discover_tools()

                if not tools:
                    return ValidationResult(
                        success=True,
                        error_message="Connected but no tools found.",
                        tools=[]
                    )

                return ValidationResult(success=True, tools=tools)

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
        except Exception as e:
            return ValidationResult(
                success=False,
                error_code="INVALID_MCP_SERVER",
                error_message=f"Not a valid MCP server: {e}"
            )
```

### 2. System Tools Registry

```python
# backend/app/tools/registry.py
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

@dataclass
class SystemTool:
    id: str
    name: str
    description: str
    icon: str
    category: str
    auth_type: str
    is_enabled: bool = True
    is_beta: bool = False

SYSTEM_TOOLS: Dict[str, SystemTool] = {
    "gmail": SystemTool(
        id="gmail",
        name="Gmail",
        description="Send emails via Gmail",
        icon="mail",
        category="communication",
        auth_type="oauth",
    ),
    "analytics": SystemTool(
        id="analytics",
        name="Analytics",
        description="View sales and inventory analytics",
        icon="chart",
        category="insights",
        auth_type="none",
    ),
}

def get_all_system_tools() -> List[Dict]:
    return [asdict(tool) for tool in SYSTEM_TOOLS.values()]

def get_system_tool(tool_id: str) -> Optional[SystemTool]:
    return SYSTEM_TOOLS.get(tool_id)
```

### 3. Connector Router

```python
# backend/app/routers/connectors.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.services.auth_service import get_current_user
from app.connectors.manager import ConnectorManager
from app.connectors.mcp_client import UserMCPClient
from app.schemas import (
    ConnectorCreateRequest,
    ConnectorTestRequest,
    ConnectorTestResponse,
    ConnectorResponse,
)

router = APIRouter(prefix="/connectors", tags=["Connectors"])

@router.post("/test", response_model=ConnectorTestResponse)
async def test_connection(
    request: ConnectorTestRequest,
    current_user = Depends(get_current_user),
):
    """Test an MCP server connection before saving"""
    client = UserMCPClient(str(request.server_url))
    result = await client.validate_connection()

    return ConnectorTestResponse(
        success=result.success,
        error_code=result.error_code,
        error_message=result.error_message,
        tools=result.tools,
    )

@router.post("", response_model=ConnectorResponse, status_code=201)
async def create_connector(
    request: ConnectorCreateRequest,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new connector (must be tested first)"""
    manager = ConnectorManager(session)

    # Check connector limit
    count = await manager.count_user_connectors(current_user.id)
    if count >= 10:
        raise HTTPException(
            status_code=400,
            detail={"error": "CONNECTOR_LIMIT_REACHED", "message": "Maximum 10 connectors allowed"}
        )

    # Connection must be tested first
    client = UserMCPClient(str(request.server_url))
    result = await client.validate_connection()

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={"error": "CONNECTION_NOT_VERIFIED", "message": result.error_message}
        )

    connector = await manager.create_connector(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        server_url=str(request.server_url),
        auth_type=request.auth_type,
        auth_config=request.auth_config,
        discovered_tools=result.tools,
    )

    return connector
```

---

## Testing

### Run All Tests

```bash
cd backend

# Unit tests
pytest tests/unit/ -v --cov=app/connectors --cov=app/tools

# Integration tests
pytest tests/integration/ -v

# Specific component
pytest tests/unit/test_encryption.py -v

# With coverage report
pytest tests/ --cov=app/connectors --cov=app/tools --cov-report=html
```

### Test Coverage Requirements

| Component | Target |
|-----------|--------|
| `connectors/encryption.py` | 100% |
| `connectors/mcp_client.py` | 90% |
| `connectors/manager.py` | 90% |
| `connectors/validator.py` | 90% |
| `tools/registry.py` | 90% |
| `routers/connectors.py` | 80% |
| `routers/tools.py` | 80% |

---

## API Testing with curl

### Test Connection

```bash
# Test a connection (replace token and URL)
curl -X POST http://localhost:8000/api/connectors/test \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "server_url": "https://my-mcp-server.example.com",
    "auth_type": "none"
  }'
```

### Create Connector

```bash
curl -X POST http://localhost:8000/api/connectors \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Slack Bot",
    "description": "Slack integration",
    "server_url": "https://my-slack-mcp.example.com",
    "auth_type": "oauth",
    "auth_config": {"access_token": "xoxb-xxx"}
  }'
```

### List Connectors

```bash
curl http://localhost:8000/api/connectors \
  -H "Authorization: Bearer <your-token>"
```

### List System Tools

```bash
curl http://localhost:8000/api/tools \
  -H "Authorization: Bearer <your-token>"
```

---

## Common Issues & Solutions

### 1. Encryption Key Missing

**Error**: `TOKEN_ENCRYPTION_KEY not set`

**Solution**:
```bash
# Generate and add to .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to backend/.env
TOKEN_ENCRYPTION_KEY=<generated-key>
```

### 2. Connection Timeout

**Error**: `Connection timed out after 10 seconds`

**Cause**: MCP server is slow or unreachable

**Solution**: Check server URL, ensure server is running, verify network connectivity

### 3. Invalid MCP Server

**Error**: `This doesn't appear to be a valid MCP server`

**Cause**: Server doesn't respond to `/mcp/tools` endpoint

**Solution**: Verify server is a FastMCP server with proper endpoints

---

## Next Steps

After completing the quickstart:

1. Run `/sp.tasks` to generate detailed implementation tasks
2. Follow TDD cycle for each task
3. Create PR when feature is complete
