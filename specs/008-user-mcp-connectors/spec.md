# Feature Specification: User MCP Connectors

**Feature Branch**: `008-user-mcp-connectors`
**Created**: 2025-12-21
**Status**: Draft
**Input**: User-configurable MCP server connections with dynamic tool registration in ChatKit UI. Users can connect custom MCP servers, manage both system-provided tools and user-added connectors, with connection validation before saving.

---

## Overview

This feature enables users to connect their own MCP (Model Context Protocol) servers to the AI Agent, expanding the agent's capabilities with custom tools. The system provides two distinct types of tools:

1. **System Tools**: Pre-defined integrations managed by developers (Gmail, Analytics, Export, etc.)
2. **User Connectors**: Custom MCP server connections added by users

Both tool types appear in ChatKit's Apps/Tools menu, allowing users to select tools that the agent MUST use when processing their request.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Available Apps/Tools (Priority: P1)

As a user, I want to see all available tools (both system-provided and my custom connectors) in the ChatKit Apps menu so that I can select which tools the AI agent should use for my request.

**Why this priority**: This is the foundational feature that displays all tools to users. Without this, users cannot discover or use any tools.

**Independent Test**: Can be tested by opening the Apps menu in ChatKit and verifying both system tools and user connectors are displayed with their connection status.

**Acceptance Scenarios**:

1. **Given** I am logged in and on the Schema Agent page, **When** I click the Apps/Tools button (+) in ChatKit composer, **Then** I see a categorized list of all available tools
2. **Given** the Apps menu is open, **When** I view system tools, **Then** I see each tool with its name, icon, and connection status (Connected/Available/Disconnected)
3. **Given** I have added custom connectors, **When** I view the Apps menu, **Then** I see my custom connectors listed separately from system tools with a visual divider
4. **Given** I select a tool from the menu, **When** I send a message, **Then** the agent MUST use that selected tool to process my request

---

### User Story 2 - Add New MCP Connector (Priority: P1)

As a user, I want to add my own MCP server as a connector so that the AI agent can use tools from my custom MCP server.

**Why this priority**: This is a core feature that enables user customization. Users need to be able to add their own integrations.

**Independent Test**: Can be tested by opening the Connectors management UI, filling the form with valid MCP server details, testing the connection, and saving the connector.

**Acceptance Scenarios**:

1. **Given** I am in the Apps menu, **When** I click "Manage Connectors", **Then** I see the Connectors management modal/panel
2. **Given** I am in the Connectors panel, **When** I click "Add New Connection", **Then** I see a form with fields: Name (required), Description (optional), MCP Server URL (required), Authentication Type (dropdown: No Auth, OAuth)
3. **Given** I have filled the connector form, **When** I click "Test Connection", **Then** the system validates the URL format, attempts to connect to the MCP server, verifies authentication, and discovers available tools
4. **Given** the connection test succeeds, **When** I view the results, **Then** I see a success message with the list of discovered tools (name and description for each)
5. **Given** the connection test fails, **When** I view the results, **Then** I see a clear error message explaining what went wrong and suggestions to fix it
6. **Given** the connection test has NOT been run or has failed, **When** I look at the Save button, **Then** the Save button is DISABLED
7. **Given** the connection test succeeded, **When** I click Save, **Then** the connector is saved and immediately appears in my Apps menu

---

### User Story 3 - Connection Validation Before Save (Priority: P1)

As a user, I want the system to validate my MCP server connection before allowing me to save it so that I only save working connections.

**Why this priority**: Critical for user experience - prevents frustration from broken connectors and ensures data quality.

**Independent Test**: Can be tested by entering invalid/valid URLs and credentials and verifying appropriate success/error messages appear.

**Acceptance Scenarios**:

1. **Given** I enter an invalid URL format, **When** I attempt to test, **Then** I see an inline error "Invalid URL format. Must be a valid HTTP/HTTPS URL."
2. **Given** I enter a valid URL that is unreachable, **When** I click "Test Connection", **Then** I see an error "Cannot connect to server. Please check the URL." after a timeout
3. **Given** I enter a valid URL but wrong authentication, **When** I click "Test Connection", **Then** I see an error "Authentication failed. Please check your credentials."
4. **Given** I connect to a server that is not an MCP server, **When** I click "Test Connection", **Then** I see an error "This doesn't appear to be a valid MCP server."
5. **Given** I connect successfully but no tools are found, **When** I see the result, **Then** I see a warning "Connected but no tools found on this MCP server."
6. **Given** a connection test is in progress, **When** I view the UI, **Then** I see a loading state with progress indicators for each validation step

---

### User Story 4 - Manage Existing Connectors (Priority: P2)

As a user, I want to view, enable/disable, and delete my existing connectors so that I can manage which custom tools are available.

**Why this priority**: Secondary to adding connectors but essential for ongoing management.

**Independent Test**: Can be tested by viewing the connectors list, toggling a connector's status, and deleting a connector.

**Acceptance Scenarios**:

1. **Given** I have added connectors, **When** I open Manage Connectors, **Then** I see a list of all my connectors with their name, status, and tool count
2. **Given** I view a connector, **When** I click the enable/disable toggle, **Then** the connector's status changes and it shows/hides in the Apps menu accordingly
3. **Given** I want to remove a connector, **When** I click Delete and confirm, **Then** the connector is removed from my list and no longer appears in Apps menu
4. **Given** I want to update a connector, **When** I click Edit on a connector, **Then** I can modify its name, description, or re-test the connection

---

### User Story 5 - System Tools Integration (Priority: P2)

As a user, I want to connect and disconnect from system-provided tools (like Gmail) so that I can control which built-in integrations are available.

**Why this priority**: System tools need their own management flow separate from user connectors.

**Independent Test**: Can be tested by viewing system tools, connecting to Gmail via OAuth, and verifying the tool becomes usable.

**Acceptance Scenarios**:

1. **Given** I view the Apps menu, **When** I look at system tools, **Then** I see their current connection status (Connected, Available, or Coming Soon)
2. **Given** a system tool requires OAuth (e.g., Gmail), **When** I click Connect, **Then** I am guided through the OAuth authorization flow
3. **Given** I have connected a system tool, **When** I click Disconnect, **Then** my authorization is revoked and the tool shows as Available
4. **Given** a system tool is marked as "Coming Soon", **When** I view it, **Then** the Connect button is disabled with appropriate messaging

---

### User Story 6 - Tool Selection Enforces Agent Usage (Priority: P1)

As a user, when I select a tool from the Apps menu, I want the AI agent to MUST use that tool for my request so that I have control over which integrations are used.

**Why this priority**: Core functionality - the selected tool must be used by the agent.

**Independent Test**: Can be tested by selecting a tool, sending a message, and verifying in the response that the tool was invoked.

**Acceptance Scenarios**:

1. **Given** I select "Gmail" from the Apps menu, **When** I type "Send this to john@example.com", **Then** the agent uses the Gmail tool to send the email
2. **Given** I select a custom connector tool, **When** I send a relevant request, **Then** the agent uses that specific connector's tools
3. **Given** I have selected a tool, **When** I view the composer, **Then** the selected tool is visually indicated
4. **Given** I have selected a tool, **When** the message is sent, **Then** the tool selection is cleared for the next message (non-persistent by default)

---

### Edge Cases

- What happens when a user's MCP server goes offline after being saved?
  - System should gracefully handle connection failures and show error in chat response
- How does the system handle duplicate tool names across different connectors?
  - Tools should be namespaced by connector (e.g., "MySlack: send_message")
- What happens when OAuth tokens expire for system tools?
  - System should attempt token refresh; if failed, prompt user to re-authorize
- What if a user tries to add the same MCP server URL twice?
  - System should warn about duplicate but allow if user confirms
- What happens during connection test if server responds very slowly?
  - Timeout after 10 seconds with appropriate message
- How does the system handle MCP servers that require client certificates?
  - Initial version will not support client certificates; document as limitation

---

## Requirements *(mandatory)*

### Functional Requirements

#### System Tools Management

- **FR-001**: System MUST provide a registry of pre-defined system tools (Gmail, Analytics, Export, etc.) that developers can extend
- **FR-002**: System MUST track each user's connection status for system tools independently
- **FR-003**: System MUST support OAuth-based authentication for system tools that require it
- **FR-004**: System MUST allow developers to add new system tools without database migrations

#### User Connectors Management

- **FR-005**: System MUST allow users to create custom MCP server connections with Name, Description (optional), URL, and Authentication Type
- **FR-006**: System MUST validate MCP server connections BEFORE allowing save
- **FR-007**: System MUST support authentication types: No Auth, OAuth
- **FR-008**: System MUST discover and cache the list of tools available on each connected MCP server
- **FR-009**: System MUST allow users to enable, disable, and delete their custom connectors
- **FR-010**: System MUST store user connector credentials securely using application-level AES-256 encryption with separate key management

#### Connection Validation

- **FR-011**: System MUST validate URL format before attempting connection
- **FR-012**: System MUST timeout connection attempts after 10 seconds
- **FR-013**: System MUST provide specific error messages for different failure types (URL invalid, unreachable, auth failed, not MCP, no tools)
- **FR-014**: System MUST display discovered tools on successful connection test
- **FR-015**: System MUST disable the Save button until connection test passes

#### ChatKit Integration

- **FR-016**: System MUST display both system tools and user connectors in ChatKit's Apps/Tools menu
- **FR-017**: System MUST visually separate system tools from user connectors in the menu
- **FR-018**: System MUST show connection status (Connected/Available/Disconnected) for each tool
- **FR-019**: System MUST provide a "Manage Connectors" option in the Apps menu that opens the connector management UI
- **FR-020**: ChatKit UI MUST remain pure OpenAI ChatKit SDK (connector management UI is separate from ChatKit)

#### Agent Integration

- **FR-021**: When a user selects a tool, the agent MUST use that tool for processing the request
- **FR-022**: System MUST dynamically load tools from user's connected MCP servers at agent initialization
- **FR-023**: System MUST handle tool namespacing to prevent conflicts between connectors
- **FR-024**: System MUST gracefully handle failures when a user's MCP server becomes unavailable (retry once with 3-second delay, then fail with user notification)

#### Observability

- **FR-025**: System MUST implement structured logging for all connector operations (connection tests, tool invocations, enable/disable, deletions)
- **FR-026**: System MUST log failures with sufficient context for debugging (connector ID, error type, timestamp, user ID)
- **FR-027**: System MUST provide error alerting for repeated connector failures

### Key Entities

- **SystemTool**: Represents a developer-defined tool integration (id, name, description, icon, category, auth_type, is_enabled, is_beta)
- **UserToolStatus**: Tracks a user's connection status for system tools (user_id, tool_id, is_connected, config)
- **UserMCPConnection**: User's custom MCP server connection (user_id, name, description, server_url, auth_type, auth_config, is_active, is_verified, discovered_tools)
- **DiscoveredTool**: A tool discovered from an MCP server (name, description, input_schema, parent_connector)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can add a new MCP connector and have it available in the Apps menu within 30 seconds of successful connection test
- **SC-002**: Connection validation provides clear feedback (success or specific error) within 10 seconds
- **SC-003**: 95% of users can successfully add a working MCP connector on their first attempt (given a valid MCP server)
- **SC-004**: The Apps menu loads all tools (system + user connectors) within 2 seconds of opening
- **SC-005**: When a tool is selected, 100% of agent responses utilize that tool as instructed
- **SC-006**: System supports at least 10 custom connectors per user without performance degradation
- **SC-007**: Users can manage (view, enable/disable, delete) their connectors without leaving the agent interface

---

## Assumptions

1. Users have access to valid MCP servers that follow the Model Context Protocol specification
2. MCP servers expose a standard tools discovery endpoint
3. ChatKit SDK supports the `composer.tools[]` configuration for displaying selectable tools
4. OAuth flows for system tools will open in a popup/new tab and redirect back
5. The current agent architecture can be extended to dynamically load tools at runtime
6. Users understand what MCP servers are and have the technical ability to obtain server URLs and credentials

---

## Out of Scope

1. Creating or hosting MCP servers for users
2. MCP server marketplace or directory
3. Automatic discovery of MCP servers
4. Client certificate authentication for MCP servers
5. Tool usage analytics or billing
6. Sharing connectors between users
7. Team/organization-level connectors

---

## Clarifications

### Session 2025-12-21

- Q: Credential security level for storing OAuth tokens and API keys? → A: Application-level AES-256 encryption with separate key management
- Q: Connection retry strategy when MCP server temporarily unavailable? → A: Retry once with 3-second delay, then fail gracefully with user notification
- Q: Observability level for connector operations? → A: Structured logging for all connector operations with error alerting

---

## Development Approach: Test-Driven Development (TDD)

**MANDATORY**: All implementation MUST follow the Red-Green-Refactor TDD cycle.

### TDD Requirements

1. **RED Phase** - Write failing tests FIRST for each component:
   - Unit tests for encryption module (AES-256)
   - Unit tests for MCP client connection/validation
   - Unit tests for connector CRUD operations
   - Integration tests for API endpoints
   - Contract tests for API responses

2. **GREEN Phase** - Write minimal code to make tests pass:
   - No feature code without a failing test
   - Focus on making tests pass, not perfect code

3. **REFACTOR Phase** - Clean up while keeping tests green:
   - Improve code quality
   - Remove duplication
   - All tests must still pass

### Test Coverage Requirements

| Component | Test Type | Coverage Target |
|-----------|-----------|-----------------|
| `connectors/encryption.py` | Unit | 100% |
| `connectors/mcp_client.py` | Unit + Integration | 90% |
| `connectors/manager.py` | Unit | 90% |
| `connectors/validator.py` | Unit + Integration | 90% |
| `tools/registry.py` | Unit | 90% |
| `routers/connectors.py` | Contract + Integration | 80% |
| `routers/tools.py` | Contract + Integration | 80% |
| **Overall Backend** | All | ≥80% |

### Test Examples (Must Write Before Code)

```python
# Example: RED phase - Write this test BEFORE implementing encryption
def test_encrypt_credentials_returns_encrypted_string():
    """Credentials should be encrypted and not readable"""
    plain_text = {"oauth_token": "secret123"}
    encrypted = encrypt_credentials(plain_text)
    assert encrypted != str(plain_text)
    assert "secret123" not in encrypted

def test_decrypt_credentials_returns_original():
    """Decryption should return original credentials"""
    original = {"oauth_token": "secret123"}
    encrypted = encrypt_credentials(original)
    decrypted = decrypt_credentials(encrypted)
    assert decrypted == original

# Example: RED phase - Write this test BEFORE implementing connection validation
def test_validate_connection_timeout_after_10_seconds():
    """Connection test should timeout after 10 seconds"""
    with pytest.raises(ConnectionTimeoutError):
        validate_mcp_connection("http://slow-server.example.com")

def test_validate_connection_invalid_url_returns_error():
    """Invalid URL should return specific error"""
    result = validate_mcp_connection("not-a-valid-url")
    assert result.success is False
    assert result.error_code == "INVALID_URL"
```

---

## Architecture Notes (For Planning Phase)

The implementation should maintain clear separation between:

1. **System Tools Module** (`backend/app/tools/`) - Code-managed, developer-extensible
2. **User Connectors Module** (`backend/app/connectors/`) - Database-managed, user CRUD operations

This separation ensures:
- System tools can be updated via code deployment
- User connectors are fully dynamic and user-managed
- Both integrate seamlessly in the ChatKit UI
- Future tools can be added without database migrations
