# Implementation Plan: User MCP Connectors

**Branch**: `008-user-mcp-connectors` | **Date**: 2025-12-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-user-mcp-connectors/spec.md`

## Summary

This feature enables users to connect their own MCP (Model Context Protocol) servers to the AI Agent, with two distinct tool types: System Tools (developer-managed) and User Connectors (user-managed). The implementation uses the MCP Python SDK for dynamic connections, AES-256 encryption for credential security, and integrates with the existing ChatKit UI through the `composer.tools[]` configuration.

## Technical Context

**Language/Version**: Python 3.12+ (Backend), TypeScript/Next.js 14+ (Frontend)
**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy 2.x (async), MCP Python SDK, cryptography (Fernet/AES-256)
- Frontend: Next.js, OpenAI ChatKit SDK
**Storage**: PostgreSQL (Neon) - new tables: `user_tool_status`, `user_mcp_connections`
**Testing**: pytest with pytest-asyncio (Backend), Jest (Frontend - optional)
**Target Platform**: Web application (Linux server backend, browser frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**:
- Connection test < 10 seconds
- Apps menu load < 2 seconds
- Connector save < 30 seconds
**Constraints**:
- 10 connectors per user maximum
- 10-second connection timeout
- Retry once with 3-second delay on failure
**Scale/Scope**: Multi-user, 10 connectors per user, ~50 tools per connector max

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Separation of Concerns | ✅ PASS | Backend: `app/tools/`, `app/connectors/`. Frontend: `components/connectors/`. API contracts only. |
| II. Test-Driven Development | ✅ PASS | Tests required for all connector operations, MCP client, encryption |
| III. Phased Implementation | ✅ PASS | Builds on Phase 5 (Agents) - extends existing agent with dynamic tools |
| IV. Database-First Design | ✅ PASS | New tables for UserToolStatus, UserMCPConnection with proper relationships |
| V. Contract-First APIs | ✅ PASS | OpenAPI contracts defined for all connector endpoints |
| VI. Local-First Development | ✅ PASS | MCP connections work locally, encryption keys via .env |
| VII. Simplicity Over Abstraction | ✅ PASS | Direct MCP client usage, no complex patterns |
| VIII. Observability by Default | ✅ PASS | Structured logging for all connector operations (FR-025, FR-026, FR-027) |

**Gate Status**: ✅ ALL GATES PASSED

## Project Structure

### Documentation (this feature)

```text
specs/008-user-mcp-connectors/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── tools-api.yaml   # System tools endpoints
│   └── connectors-api.yaml  # User connectors endpoints
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── tools/                    # NEW: System Tools Module
│   │   ├── __init__.py
│   │   ├── registry.py           # System tools registry
│   │   ├── base.py               # Base tool class
│   │   └── gmail/                # Gmail integration (existing, refactored)
│   │       ├── __init__.py
│   │       └── tool.py
│   │
│   ├── connectors/               # NEW: User Connectors Module
│   │   ├── __init__.py
│   │   ├── manager.py            # Connector CRUD operations
│   │   ├── validator.py          # Connection testing/validation
│   │   ├── mcp_client.py         # Dynamic MCP client
│   │   ├── encryption.py         # AES-256 credential encryption
│   │   └── auth/
│   │       ├── __init__.py
│   │       ├── oauth.py          # OAuth flow handler
│   │       └── none.py           # No auth handler
│   │
│   ├── routers/
│   │   ├── tools.py              # NEW: System tools endpoints
│   │   └── connectors.py         # NEW: User connectors endpoints
│   │
│   ├── models.py                 # Add UserToolStatus, UserMCPConnection
│   └── agents/
│       └── schema_query_agent.py # Extend to load dynamic tools
│
└── tests/
    ├── unit/
    │   ├── test_tools_registry.py
    │   ├── test_connector_manager.py
    │   ├── test_mcp_client.py
    │   └── test_encryption.py
    ├── integration/
    │   ├── test_tools_api.py
    │   └── test_connectors_api.py
    └── contract/
        └── test_connector_contracts.py

frontend/
├── app/
│   └── dashboard/
│       └── schema-agent/
│           └── page.tsx          # Update ChatKit tools[] config
│
├── components/
│   └── connectors/               # NEW: Connectors UI
│       ├── ConnectorsModal.tsx   # Main modal
│       ├── ConnectorsList.tsx    # List user's connectors
│       ├── AddConnectorForm.tsx  # Add new connector form
│       ├── ConnectionTester.tsx  # Test connection UI
│       └── SystemToolsList.tsx   # Display system tools
│
└── lib/
    ├── tools-api.ts              # NEW: System tools API calls
    └── connectors-api.ts         # NEW: Connectors API calls
```

**Structure Decision**: Web application structure with clear backend/frontend separation. Backend adds two new modules (`tools/` and `connectors/`) following the spec's architecture notes. Frontend adds a `connectors/` component folder for the management UI.

## Complexity Tracking

> No violations detected. All implementations follow constitution principles.

| Area | Approach | Rationale |
|------|----------|-----------|
| MCP Client | Direct SDK usage | Simplicity - no wrapper patterns needed |
| Encryption | Fernet (AES-256) | Python cryptography library, battle-tested |
| Tool Registry | Simple dict-based | No need for complex plugin system initially |

---

## Test-Driven Development (TDD) Implementation Plan

**MANDATORY**: All code MUST be written following the Red-Green-Refactor cycle. NO feature code without a failing test first.

### TDD Execution Order

Implementation follows this strict order - tests FIRST, then code:

#### Phase 1: Core Infrastructure (Tests First)

| Order | Component | Test File | Key Tests |
|-------|-----------|-----------|-----------|
| 1.1 | Encryption | `test_encryption.py` | `test_encrypt_decrypt_roundtrip`, `test_encrypted_not_readable`, `test_invalid_key_fails` |
| 1.2 | MCP Client | `test_mcp_client.py` | `test_connect_valid_server`, `test_timeout_after_10s`, `test_discover_tools` |
| 1.3 | Connector Manager | `test_connector_manager.py` | `test_create_connector`, `test_list_user_connectors`, `test_delete_connector` |
| 1.4 | Validator | `test_validator.py` | `test_invalid_url_format`, `test_unreachable_server`, `test_auth_failure`, `test_not_mcp_server` |

#### Phase 2: API Layer (Tests First)

| Order | Component | Test File | Key Tests |
|-------|-----------|-----------|-----------|
| 2.1 | Tools Router | `test_tools_api.py` | `test_list_system_tools`, `test_connect_tool`, `test_disconnect_tool` |
| 2.2 | Connectors Router | `test_connectors_api.py` | `test_create_connector_endpoint`, `test_test_connection_endpoint`, `test_delete_requires_auth` |
| 2.3 | Contract Tests | `test_connector_contracts.py` | `test_response_schema_matches`, `test_error_format_consistent` |

#### Phase 3: Agent Integration (Tests First)

| Order | Component | Test File | Key Tests |
|-------|-----------|-----------|-----------|
| 3.1 | Dynamic Tool Loading | `test_agent_tools.py` | `test_load_user_tools`, `test_tool_namespacing`, `test_retry_on_failure` |
| 3.2 | Tool Selection | `test_tool_selection.py` | `test_selected_tool_must_be_used`, `test_tool_prefix_injection` |

### TDD Workflow for Each Component

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TDD CYCLE FOR EACH COMPONENT                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 1: RED - Write Failing Tests                                     │
│  ─────────────────────────────────                                     │
│  • Create test file: tests/unit/test_<component>.py                    │
│  • Write tests for ALL expected behaviors                              │
│  • Run tests: pytest tests/unit/test_<component>.py                    │
│  • Verify: ALL TESTS FAIL (no implementation yet)                      │
│                                                                         │
│  STEP 2: GREEN - Implement Minimal Code                                │
│  ───────────────────────────────────────                               │
│  • Create implementation file: app/<module>/<component>.py             │
│  • Write MINIMUM code to pass tests                                    │
│  • Run tests: pytest tests/unit/test_<component>.py                    │
│  • Verify: ALL TESTS PASS                                              │
│                                                                         │
│  STEP 3: REFACTOR - Clean Up                                           │
│  ───────────────────────────────                                       │
│  • Improve code quality (no new features!)                             │
│  • Remove duplication                                                   │
│  • Run tests: pytest tests/unit/test_<component>.py                    │
│  • Verify: ALL TESTS STILL PASS                                        │
│                                                                         │
│  STEP 4: COMMIT                                                         │
│  ─────────────                                                          │
│  • Commit with message: "feat(connectors): add <component> with tests" │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Test Coverage Requirements

| Component | Target | Minimum |
|-----------|--------|---------|
| `connectors/encryption.py` | 100% | 100% (security-critical) |
| `connectors/mcp_client.py` | 90% | 85% |
| `connectors/manager.py` | 90% | 85% |
| `connectors/validator.py` | 90% | 85% |
| `tools/registry.py` | 90% | 85% |
| `routers/connectors.py` | 80% | 75% |
| `routers/tools.py` | 80% | 75% |
| **Overall Feature** | ≥80% | 80% |

### Example Test Structure

```python
# tests/unit/test_encryption.py
# ═══════════════════════════════════════════════════════════════════════
# WRITE THESE TESTS FIRST - BEFORE ANY IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════

import pytest
from app.connectors.encryption import encrypt_credentials, decrypt_credentials

class TestCredentialEncryption:
    """Test AES-256 credential encryption - RED phase tests"""

    def test_encrypt_returns_non_empty_string(self):
        """Encryption should return a non-empty encrypted string"""
        result = encrypt_credentials({"token": "secret"})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_encrypted_data_not_readable(self):
        """Encrypted data should not contain original values"""
        plain = {"oauth_token": "my-secret-token-123"}
        encrypted = encrypt_credentials(plain)
        assert "my-secret-token-123" not in encrypted
        assert "oauth_token" not in encrypted

    def test_decrypt_returns_original(self):
        """Decryption should return exact original data"""
        original = {"oauth_token": "secret", "refresh_token": "refresh"}
        encrypted = encrypt_credentials(original)
        decrypted = decrypt_credentials(encrypted)
        assert decrypted == original

    def test_different_inputs_produce_different_outputs(self):
        """Different inputs should produce different encrypted outputs"""
        enc1 = encrypt_credentials({"a": "1"})
        enc2 = encrypt_credentials({"b": "2"})
        assert enc1 != enc2

    def test_invalid_encrypted_data_raises_error(self):
        """Invalid encrypted data should raise DecryptionError"""
        with pytest.raises(DecryptionError):
            decrypt_credentials("not-valid-encrypted-data")


# tests/unit/test_validator.py
# ═══════════════════════════════════════════════════════════════════════
# WRITE THESE TESTS FIRST - BEFORE ANY IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════

import pytest
from app.connectors.validator import validate_mcp_connection, ValidationResult

class TestConnectionValidation:
    """Test MCP connection validation - RED phase tests"""

    def test_invalid_url_format_returns_error(self):
        """Invalid URL format should return INVALID_URL error"""
        result = validate_mcp_connection("not-a-url")
        assert result.success is False
        assert result.error_code == "INVALID_URL"
        assert "Invalid URL" in result.error_message

    def test_unreachable_server_returns_error(self):
        """Unreachable server should return CONNECTION_FAILED error"""
        result = validate_mcp_connection("http://192.0.2.1:9999")  # TEST-NET
        assert result.success is False
        assert result.error_code == "CONNECTION_FAILED"

    @pytest.mark.timeout(15)
    def test_timeout_after_10_seconds(self):
        """Connection should timeout after 10 seconds"""
        # Use a server that accepts but never responds
        result = validate_mcp_connection("http://httpstat.us/200?sleep=20000")
        assert result.success is False
        assert result.error_code == "TIMEOUT"

    def test_non_mcp_server_returns_error(self):
        """Non-MCP server should return INVALID_MCP_SERVER error"""
        result = validate_mcp_connection("https://example.com")
        assert result.success is False
        assert result.error_code == "INVALID_MCP_SERVER"

    def test_successful_connection_returns_tools(self):
        """Successful connection should return discovered tools"""
        # This test requires a mock MCP server
        result = validate_mcp_connection("http://localhost:8001/mcp")
        assert result.success is True
        assert isinstance(result.tools, list)


# tests/integration/test_connectors_api.py
# ═══════════════════════════════════════════════════════════════════════
# WRITE THESE TESTS FIRST - BEFORE ANY IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════

import pytest
from httpx import AsyncClient

class TestConnectorsAPI:
    """Integration tests for connectors API - RED phase tests"""

    @pytest.mark.asyncio
    async def test_create_connector_requires_auth(self, client: AsyncClient):
        """POST /connectors should require authentication"""
        response = await client.post("/api/connectors", json={
            "name": "Test",
            "server_url": "http://example.com"
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_connector_validates_url(self, auth_client: AsyncClient):
        """POST /connectors should validate URL format"""
        response = await auth_client.post("/api/connectors", json={
            "name": "Test",
            "server_url": "invalid-url"
        })
        assert response.status_code == 422
        assert "url" in response.json()["detail"][0]["loc"]

    @pytest.mark.asyncio
    async def test_test_connection_before_save(self, auth_client: AsyncClient):
        """Connector should be tested before saving"""
        response = await auth_client.post("/api/connectors/test", json={
            "name": "Test",
            "server_url": "http://invalid.example.com",
            "auth_type": "none"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error_code" in data
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml (excerpt)
jobs:
  test:
    steps:
      - name: Run tests with coverage
        run: |
          pytest tests/ \
            --cov=app/connectors \
            --cov=app/tools \
            --cov-report=xml \
            --cov-fail-under=80

      - name: Check coverage per module
        run: |
          # Encryption must be 100%
          pytest tests/unit/test_encryption.py \
            --cov=app/connectors/encryption \
            --cov-fail-under=100
```

### TDD Checklist (Per Task)

Before marking any implementation task as complete:

- [ ] Unit tests written FIRST (before implementation)
- [ ] All tests initially FAILED (RED phase verified)
- [ ] Implementation written to pass tests (GREEN phase)
- [ ] Code refactored without breaking tests (REFACTOR phase)
- [ ] Coverage meets component target
- [ ] Integration tests pass
- [ ] Contract tests pass (for API endpoints)
