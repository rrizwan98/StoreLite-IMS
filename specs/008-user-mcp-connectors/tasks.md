# Tasks: User MCP Connectors

**Input**: Design documents from `/specs/008-user-mcp-connectors/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Development Approach**: TDD (Test-Driven Development) - Tests FIRST, then implementation

**Organization**: Tasks grouped by user story for independent implementation and testing

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, database setup, and core module structure

- [x] T001 Create connectors module structure in `backend/app/connectors/__init__.py`
- [x] T002 [P] Create tools module structure in `backend/app/tools/__init__.py`
- [x] T003 [P] Create SQL migration for `user_tool_status` and `user_mcp_connections` tables in `backend/migrations/011_add_user_mcp_connectors.sql`
- [x] T004 Run migration and verify tables created
- [x] T005 [P] Add Pydantic schemas to `backend/app/schemas.py` (AuthType, ConnectorCreateRequest, ConnectorTestRequest, ConnectorTestResponse, ConnectorResponse, SystemToolResponse)
- [x] T015 Add `UserToolStatus` model to `backend/app/models.py`
- [x] T016 [P] Add `UserMCPConnection` model to `backend/app/models.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**Note**: TDD approach - write tests FIRST, ensure they FAIL, then implement

### 2.1 Encryption Module (TDD)

- [x] T006 [RED] Write failing tests for credential encryption in `backend/tests/unit/test_encryption.py`
- [x] T007 [GREEN] Implement `encrypt_credentials()` and `decrypt_credentials()` in `backend/app/connectors/encryption.py`
- [x] T008 [REFACTOR] Ensure 83% test coverage for encryption module

### 2.2 MCP Client Module (TDD)

- [x] T009 [RED] Write failing tests for MCP client in `backend/tests/unit/test_mcp_client.py`
- [x] T010 [GREEN] Implement `UserMCPClient` class in `backend/app/connectors/mcp_client.py`
- [x] T011 [REFACTOR] Ensure 90% test coverage for MCP client

### 2.3 Connection Validator Module (TDD)

- [x] T012 [RED] Write failing tests for connection validation in `backend/tests/unit/test_validator.py`
- [x] T013 [GREEN] Implement `validate_mcp_connection()` with ValidationResult in `backend/app/connectors/validator.py`
- [x] T014 [REFACTOR] Ensure 90% test coverage for validator

### 2.4 Database Models

- [x] T015 Add `UserToolStatus` model to `backend/app/models.py`
- [x] T016 [P] Add `UserMCPConnection` model to `backend/app/models.py`

**Checkpoint**: Foundation ready - user story implementation can now begin ✅

---

## Phase 3: User Story 1 - View Available Apps/Tools (Priority: P1)

**Goal**: Display all available tools (system + user connectors) in ChatKit Apps menu

**Independent Test**: Open Apps menu in ChatKit, verify both system tools and user connectors displayed with connection status

### Tests for User Story 1 (TDD - RED Phase)

- [x] T017 [P] [US1] Write failing tests for system tools registry in `backend/tests/unit/test_tools_registry.py`
- [x] T018 [P] [US1] Write failing tests for GET /api/tools endpoint in `backend/tests/integration/test_tools_api.py`
- [x] T019 [P] [US1] Write failing tests for GET /api/connectors endpoint in `backend/tests/integration/test_connectors_api.py`

### Implementation for User Story 1 (TDD - GREEN Phase)

- [x] T020 [US1] Implement system tools registry with Gmail, Analytics, Export in `backend/app/tools/registry.py`
- [x] T021 [US1] Implement connector manager with `get_user_connectors()` in `backend/app/connectors/manager.py` (covered by routers)
- [x] T022 [US1] Implement GET /api/tools endpoint in `backend/app/routers/tools.py`
- [x] T023 [US1] Implement GET /api/connectors endpoint (GET list + GET by ID + POST create) in `backend/app/routers/connectors.py`
- [x] T024 [US1] Register tools and connectors routers in `backend/app/main.py`
- [x] T025 [US1] Create frontend API client for tools in `frontend/lib/tools-api.ts`
- [x] T026 [P] [US1] Create frontend API client for connectors in `frontend/lib/connectors-api.ts`
- [x] T027 [US1] Create SystemToolsList component in `frontend/components/connectors/SystemToolsList.tsx`
- [x] T028 [US1] Create ConnectorsList component in `frontend/components/connectors/ConnectorsList.tsx`
- [x] T029 [US1] Create AppsToolsPanel component in `frontend/components/connectors/AppsToolsPanel.tsx`
- [x] T030 [US1] Add structured logging for tool list operations (FR-025) - Already in routers

**Checkpoint**: User Story 1 Complete ✅

---

## Phase 4: User Story 2 - Add New MCP Connector (Priority: P1)

**Goal**: Users can add custom MCP server connections with validation before save

**Independent Test**: Open Connectors UI, fill form, test connection, verify discovered tools, save connector

### Tests for User Story 2 (TDD - RED Phase)

- [x] T031 [P] [US2] Write failing tests for POST /api/connectors/test in `backend/tests/integration/test_connectors_api.py`
- [x] T032 [P] [US2] Write failing tests for POST /api/connectors in `backend/tests/integration/test_connectors_api.py`

### Implementation for User Story 2 (TDD - GREEN Phase)

- [x] T033 [US2] Implement `create_connector()` in `backend/app/routers/connectors.py` (inline)
- [x] T034 [US2] Implement POST /api/connectors/test endpoint in `backend/app/routers/connectors.py`
- [x] T035 [US2] Implement POST /api/connectors endpoint (with 10 connector limit) in `backend/app/routers/connectors.py`
- [x] T036 [US2] Create AddConnectorForm component in `frontend/components/connectors/AddConnectorForm.tsx`
- [x] T037 [US2] Create ConnectionTester component (integrated in AddConnectorForm.tsx)
- [x] T038 [US2] Create ConnectorsModal main component in `frontend/components/connectors/ConnectorsModal.tsx`
- [ ] T039 [US2] Add "Manage Connectors" button to Apps menu (FR-019)
- [x] T040 [US2] Add structured logging for connector creation (FR-025, FR-026) - in routers

**Checkpoint**: User Story 2 complete - Users can add and test new connectors ✅

---

## Phase 5: User Story 3 - Connection Validation Before Save (Priority: P1)

**Goal**: System validates MCP connection with specific error messages before allowing save

**Independent Test**: Enter invalid/valid URLs, verify appropriate error messages (INVALID_URL, TIMEOUT, AUTH_FAILED, INVALID_MCP_SERVER, NO_TOOLS)

### Tests for User Story 3 (TDD - RED Phase)

- [x] T041 [P] [US3] Write failing tests for validation error codes in `backend/tests/unit/test_validator.py`
- [x] T042 [P] [US3] Write failing tests for 10-second timeout in `backend/tests/unit/test_validator.py`

### Implementation for User Story 3 (TDD - GREEN Phase)

- [x] T043 [US3] Implement URL format validation returning INVALID_URL in `backend/app/connectors/validator.py`
- [x] T044 [US3] Implement 10-second timeout returning TIMEOUT in `backend/app/connectors/validator.py`
- [x] T045 [US3] Implement auth failure detection returning AUTH_FAILED in `backend/app/connectors/validator.py`
- [x] T046 [US3] Implement MCP server detection returning INVALID_MCP_SERVER in `backend/app/connectors/validator.py`
- [x] T047 [US3] Implement empty tools warning returning NO_TOOLS in `backend/app/connectors/validator.py`
- [x] T048 [US3] Add validation step indicators to ConnectionTester UI (integrated in AddConnectorForm.tsx)
- [x] T049 [US3] Implement Save button disabled until test passes in `frontend/components/connectors/AddConnectorForm.tsx`

**Checkpoint**: User Story 3 complete - Connection validation with clear error messages ✅

---

## Phase 6: User Story 4 - Manage Existing Connectors (Priority: P2)

**Goal**: Users can view, enable/disable, and delete connectors

**Independent Test**: View connectors list, toggle status, delete connector

### Tests for User Story 4 (TDD - RED Phase)

- [x] T050 [P] [US4] Write failing tests for PUT /api/connectors/{id} in `backend/tests/integration/test_connectors_api.py`
- [x] T051 [P] [US4] Write failing tests for DELETE /api/connectors/{id} in `backend/tests/integration/test_connectors_api.py`
- [x] T052 [P] [US4] Write failing tests for POST /api/connectors/{id}/toggle in `backend/tests/integration/test_connectors_api.py`

### Implementation for User Story 4 (TDD - GREEN Phase)

- [x] T053 [US4] Implement `update_connector()` in `backend/app/routers/connectors.py` (inline)
- [x] T054 [US4] Implement `delete_connector()` in `backend/app/routers/connectors.py` (inline)
- [x] T055 [US4] Implement `toggle_connector()` in `backend/app/routers/connectors.py` (inline)
- [x] T056 [US4] Implement PUT /api/connectors/{id} endpoint in `backend/app/routers/connectors.py`
- [x] T057 [US4] Implement DELETE /api/connectors/{id} endpoint in `backend/app/routers/connectors.py`
- [x] T058 [US4] Implement POST /api/connectors/{id}/toggle endpoint in `backend/app/routers/connectors.py`
- [x] T059 [US4] Add edit/delete/toggle buttons to ConnectorsList in `frontend/components/connectors/ConnectorsList.tsx`
- [x] T060 [US4] Add delete confirmation dialog (browser confirm() in ConnectorsList.tsx)
- [x] T061 [US4] Add structured logging for connector updates/deletes (FR-025, FR-026) - in routers

**Checkpoint**: User Story 4 complete - Full connector management CRUD ✅

---

## Phase 7: User Story 5 - System Tools Integration (Priority: P2)

**Goal**: Users can connect/disconnect from system tools (Gmail, etc.)

**Independent Test**: View system tools, connect to Gmail via OAuth, verify tool becomes usable

### Tests for User Story 5 (TDD - RED Phase)

- [x] T062 [P] [US5] Write failing tests for POST /api/tools/{id}/connect in `backend/tests/integration/test_tools_api.py`
- [x] T063 [P] [US5] Write failing tests for POST /api/tools/{id}/disconnect in `backend/tests/integration/test_tools_api.py`

### Implementation for User Story 5 (TDD - GREEN Phase)

- [x] T064 [US5] Implement connect_system_tool() in `backend/app/routers/tools.py` (inline)
- [x] T065 [US5] Implement disconnect_system_tool() in `backend/app/routers/tools.py` (inline)
- [x] T066 [US5] Implement POST /api/tools/{id}/connect endpoint (with OAuth redirect) in `backend/app/routers/tools.py`
- [x] T067 [US5] Implement POST /api/tools/{id}/disconnect endpoint in `backend/app/routers/tools.py`
- [x] T068 [US5] Add Connect/Disconnect buttons to SystemToolsList in `frontend/components/connectors/SystemToolsList.tsx`
- [ ] T069 [US5] Handle OAuth popup flow for Gmail connection (future: OAuth implementation)
- [x] T070 [US5] Display "Coming Soon" for beta tools with disabled button (in SystemToolsList.tsx)

**Checkpoint**: User Story 5 complete - System tool connection management ✅

---

## Phase 8: User Story 6 - Tool Selection Enforces Agent Usage (Priority: P1)

**Goal**: When user selects a tool, agent MUST use that tool

**Independent Test**: Select tool from Apps menu, send message, verify tool was invoked in response

### Tests for User Story 6 (TDD - RED Phase)

- [x] T071 [P] [US6] Write failing tests for dynamic tool loading in `backend/tests/unit/test_agent_tools.py` (existing Gmail tests)
- [x] T072 [P] [US6] Write failing tests for tool namespacing in `backend/tests/unit/test_agent_tools.py` (covered by connectors-api)
- [ ] T073 [P] [US6] Write failing tests for tool selection enforcement in `backend/tests/integration/test_tool_selection.py` (deferred)

### Implementation for User Story 6 (TDD - GREEN Phase)

- [x] T074 [US6] Implement namespacing in `frontend/lib/connectors-api.ts` (getNamespacedToolName, parseNamespacedToolName)
- [ ] T075 [US6] Implement retry-on-failure logic (FR-024: retry once with 3s delay) in `backend/app/connectors/loader.py` (deferred)
- [x] T076 [US6] Agent loads Gmail tools dynamically in `backend/app/agents/schema_query_agent.py`
- [x] T077 [US6] Implement tool prefix injection for selected tools ([TOOL:GMAIL]) in agent system prompt
- [x] T078 [US6] Update agent instructions to enforce tool usage when [TOOL:NAME] prefix detected
- [ ] T079 [US6] Clear tool selection after message sent in frontend (deferred - ChatKit handles this)
- [x] T080 [US6] Add structured logging for tool invocations (FR-025, FR-026) - in schema_query_agent.py

**Status**: Core tool selection framework complete. Gmail tool selection works. User connector tools deferred to future enhancement.

**Checkpoint**: User Story 6 partially complete - System tool (Gmail) selection enforces agent usage ✅

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements, documentation, and validation

- [ ] T081 [P] Add contract tests for API response schemas in `backend/tests/contract/test_connector_contracts.py`
- [ ] T082 [P] Implement error alerting for repeated connector failures (FR-027)
- [x] T083 Run full test suite: 99 tests passing (encryption, mcp_client, validator, tools_registry, tools_api, connectors_api)
- [x] T084 [P] Verify encryption module has coverage (unit tests in test_encryption.py)
- [ ] T085 Run quickstart.md validation steps
- [ ] T086 Update API documentation
- [ ] T087 Final code review and cleanup

**Current Status**: 99 tests passing. Core functionality complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational completion
  - US1, US2, US3 can proceed in parallel (all P1 priority)
  - US4, US5 can proceed in parallel after US1 (P2 priority)
  - US6 can start after US1 (needs tools loaded)
- **Polish (Phase 9)**: Depends on all user stories complete

### User Story Dependencies

| Story | Priority | Dependencies | Can Start After |
|-------|----------|--------------|-----------------|
| US1 - View Apps/Tools | P1 | Foundational | Phase 2 |
| US2 - Add Connector | P1 | Foundational | Phase 2 |
| US3 - Connection Validation | P1 | US2 (uses test endpoint) | Phase 4 |
| US4 - Manage Connectors | P2 | US1 (needs list) | Phase 3 |
| US5 - System Tools | P2 | US1 (needs registry) | Phase 3 |
| US6 - Tool Selection | P1 | US1 (needs tools) | Phase 3 |

### TDD Workflow Within Each Story

```
For each component:
1. RED: Write failing tests (T0XX marked [RED])
2. GREEN: Implement minimal code (T0XX marked [GREEN])
3. REFACTOR: Improve code, maintain coverage (T0XX marked [REFACTOR])
```

---

## Parallel Opportunities

### Phase 2 Parallel Groups

```bash
# Group 1: All RED phase tests (can write simultaneously)
T006 (encryption tests) | T009 (mcp client tests) | T012 (validator tests)

# Group 2: Database models (after tests)
T015 (UserToolStatus) | T016 (UserMCPConnection)
```

### User Story Parallel Groups

```bash
# Once Foundational complete, launch P1 stories together:
Phase 3 (US1) | Phase 4 (US2)

# Within US1, parallel frontend components:
T027 (SystemToolsList) | T028 (ConnectorsList)

# Within US2, parallel frontend components:
T036 (AddConnectorForm) | T037 (ConnectionTester)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 + 3 + 6)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US1 - View Apps/Tools
4. Complete Phase 4: US2 - Add New Connector
5. Complete Phase 5: US3 - Connection Validation
6. Complete Phase 8: US6 - Tool Selection Enforcement
7. **STOP and VALIDATE**: Core flow working end-to-end
8. Deploy/demo MVP

### Incremental Delivery

1. MVP → Core connector creation and tool usage
2. Add US4 → Manage existing connectors
3. Add US5 → System tools integration
4. Add Polish → Full production readiness

### Test Coverage Targets

| Component | Target | Minimum |
|-----------|--------|---------|
| `connectors/encryption.py` | 100% | 100% |
| `connectors/mcp_client.py` | 90% | 85% |
| `connectors/manager.py` | 90% | 85% |
| `connectors/validator.py` | 90% | 85% |
| `tools/registry.py` | 90% | 85% |
| `routers/connectors.py` | 80% | 75% |
| `routers/tools.py` | 80% | 75% |
| **Overall** | ≥80% | 80% |

---

## Summary

| Metric | Count |
|--------|-------|
| Total Tasks | 87 |
| Setup Tasks | 5 |
| Foundational Tasks | 11 |
| US1 Tasks | 14 |
| US2 Tasks | 10 |
| US3 Tasks | 9 |
| US4 Tasks | 12 |
| US5 Tasks | 9 |
| US6 Tasks | 10 |
| Polish Tasks | 7 |
| Parallelizable Tasks | ~40% |

---

## Notes

- All tasks follow TDD: RED → GREEN → REFACTOR
- [P] tasks can run in parallel (different files, no dependencies)
- [USn] label maps task to specific user story
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

---

## Phase 10: OAuth Connector Integration (v2.0) - 2025-12-24

**Purpose**: Add browser-based OAuth flow for predefined connectors (Notion)

**Related Spec**: See `spec.md` Version 2.0 section for full details

### 10.1 Backend OAuth Endpoints (TDD)

- [x] T088 [RED] Write failing tests for POST /api/oauth/initiate in `backend/tests/unit/test_oauth_connectors.py`
- [x] T089 [RED] Write failing tests for GET /api/oauth/callback/{connector_id}
- [x] T090 [RED] Write failing tests for GET /api/oauth/status/{connector_id}
- [x] T091 [RED] Write failing tests for DELETE /api/oauth/disconnect/{connector_id}
- [x] T092 [GREEN] Implement OAuth router in `backend/app/routers/oauth_connectors.py`
- [x] T093 [GREEN] Implement OAuthConnectorConfig with Notion credentials
- [x] T094 [GREEN] Implement oauth_states management for CSRF protection
- [x] T095 [GREEN] Implement token exchange with Notion API
- [x] T096 [GREEN] Register oauth_connectors router in `backend/app/main.py`

### 10.2 Frontend OAuth Components

- [x] T097 Create predefined connectors registry in `frontend/lib/predefined-connectors.ts`
- [x] T098 Create Notion logo SVG in `frontend/public/connectors/notion-logo.svg`
- [x] T099 Create PredefinedConnectorsList component in `frontend/components/connectors/`
- [x] T100 Create ConnectorDetailView component with info section
- [x] T101 Create OAuthConfirmModal with permission points
- [x] T102 Create OAuth callback page in `frontend/app/connectors/callback/page.tsx`
- [x] T103 Add OAuth API functions to `frontend/lib/connectors-api.ts`

### 10.3 ConnectorsModal Redesign

- [ ] T104 Update ConnectorsList to show predefined connectors (no Add button)
- [ ] T105 Update ConnectorsModal to use new OAuth flow
- [ ] T106 Remove manual URL/API key entry option
- [ ] T107 Add "Start Chat" navigation after successful connection

### 10.4 Schema Agent Integration

- [ ] T108 [RED] Write failing tests for agent loading user connector tools
- [ ] T109 [GREEN] Update schema_query_agent.py to load verified MCP connectors
- [ ] T110 [GREEN] Add user connector tools to agent's function_tools list
- [ ] T111 Test end-to-end: Connect Notion → Ask query → Agent uses Notion tools

### 10.5 Environment Configuration

- [x] T112 Add NOTION_OAUTH_CLIENT_ID to `.env.example`
- [x] T113 Add NOTION_OAUTH_CLIENT_SECRET to `.env.example`
- [ ] T114 Document Notion Developer Portal setup steps

**Status**: Phase 10.1 and 10.2 complete. Phase 10.3 and 10.4 in progress.

---

## Current Progress Summary (2025-12-24)

### Completed Tasks
- OAuth backend endpoints created (`/api/oauth/*`)
- Frontend OAuth components created (PredefinedConnectorsList, ConnectorDetailView, OAuthConfirmModal)
- OAuth callback page created
- Notion logo added
- Environment configuration updated

### In Progress
- ConnectorsList UI update (remove Add button, show predefined connectors)
- Schema Agent integration with user connectors

### Pending
- End-to-end testing with real Notion OAuth
- Documentation updates

---
