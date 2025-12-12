# Tasks: ChatKit UI Integration (Phase 6)

**Input**: Design documents from `/specs/006-chatkit-ui/`
**Prerequisites**: plan.md ✅, spec.md ✅
**Branch**: `006-chatkit-ui`

**Tests**: Conversation tests validating end-to-end flows (ChatKit UI → Agent → MCP tools → PostgreSQL)

**Organization**: Tasks grouped by user story (P1, P2) to enable independent implementation and testing. Frontend and backend tasks can run in parallel per Constitution Principle I.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- **File paths**: Frontend (`app/`, `lib/`, `components/`) and Backend (`backend/app/`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, environment configuration, and ChatKit dependencies

- [x] T001 Install `@openai/chatkit-react` and `@openai/chatkit` packages in `package.json`
- [x] T002 [P] Add ChatKit environment variables to `.env.local.example` (AGENT_API_URL, CHATKIT_DOMAIN_KEY, CHATKIT_THEME)
- [x] T003 [P] Add backend ChatKit integration dependencies (already have FastAPI, OpenAI Agents SDK, LiteLLM)
- [x] T004 [P] Configure TypeScript types for ChatKit in frontend tsconfig
- [x] T005 Create `.env.local` from `.env.local.example` with correct AGENT_API_URL pointing to `http://localhost:8000/agent/chat`

**Checkpoint**: Environment ready for ChatKit integration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infrastructure that MUST complete before user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Backend Foundation

- [x] T006 [P] Create Pydantic schema for `/agent/chat` request contract in `backend/app/schemas.py`: `ChatMessage(session_id, message_text, user_id)` ✅ DONE
- [x] T007 [P] Create Pydantic schema for `/agent/chat` response contract in `backend/app/schemas.py`: `ChatResponse(response_text, type, structured_data, session_id, timestamp)` ✅ DONE
- [x] T008 [P] Create session management utility in `backend/app/services/session_service.py` for tab-lifetime session tracking (generate session_id, track active sessions, cleanup on logout) ✅ DONE
- [x] T009 [P] Create conversation history model in `backend/app/models/conversation.py` for storing messages in PostgreSQL (id, session_id, user_id, message_text, response_text, created_at) ✅ DONE (Added to models.py)
- [x] T010 Extend existing `/agent/chat` router in `backend/app/routers/agent.py` with session management decorator (FR-004, FR-017) ✅ DONE (Created chatkit.py with /agent/session and /agent/chat endpoints, registered in main.py)

### Frontend Foundation

- [x] T011 [P] Create `components/ChatKitWidget.tsx` wrapper component with: ✅ DONE
  - ChatKit component initialization
  - Session ID management (generate/retrieve from sessionStorage)
  - Error boundary for graceful failure handling
  - Initial state management for tab-lifetime persistence (FR-002, FR-004, FR-012, FR-017)
  - **Implementation**: Pure vanilla ChatKit in `frontend/public/chatkit-embed.html` + integrated in `layout.tsx` via ChatKitWidgetContainer

- [x] T012 [P] Create API client function `lib/api.ts::chatWithAgent(message, sessionId)` that: ✅ DONE
  - Sends POST to `/agent/chat` endpoint
  - Handles request/response contract
  - Returns structured response for ChatKit rendering (FR-003, FR-006)
  - **Implementation**: Created `frontend/lib/chatkit-api.ts` with typed API calls

- [x] T013 [P] Create hook `lib/hooks/useChatSession.ts` to manage chat session state: ✅ DONE
  - Initialize session ID from sessionStorage
  - Restore message history from sessionStorage (backup for SC-005)
  - Persist session state across route navigation (FR-004, FR-007, FR-017)
  - **Implementation**: Created `frontend/lib/hooks/useChatKitSession.ts`

- [x] T014 Integrate `<ChatKitWidget>` into `app/layout.tsx` root layout to persist across all routes (`/admin`, `/pos`, `/agent`) (FR-002) ✅ DONE

**Checkpoint**: Foundation ready - user story implementation can begin in parallel

---

## Phase 3: User Story 1 - Store Admin Adds Inventory via ChatKit (Priority: P1) 🎯 MVP

**Goal**: Enable store admin to add inventory items through natural language ChatKit interface, demonstrating full pipeline (ChatKit → Agent → MCP tools → Database)

**Independent Test**:
1. Open ChatKit on `/admin` page
2. Type: "Add 10kg sugar at 160 per kg under grocery category"
3. Verify: Message appears in chat history with agent confirmation
4. Verify: Item appears in PostgreSQL (query `SELECT * FROM items WHERE name='Sugar'`)
5. Verify: Item visible in admin dashboard items list without page refresh

### Implementation for User Story 1

**Backend**:

- [ ] T015 [P] [US1] Implement agent prompt in `backend/app/agents/agent.py` to interpret inventory commands (extract: item name, quantity, unit price, category)
- [ ] T016 [P] [US1] Create inventory request handler in `backend/app/services/agent.py::handle_inventory_request()` that:
  - Parses agent response to extract inventory details
  - Calls MCP `inventory_add_item` tool
  - Returns JSON response: `{message, type: "item_created", item_data: {id, name, price, stock}}`
  - (Re-use Phase 5 MCP tools; no new tools needed)

- [ ] T017 [US1] Extend POST `/agent/chat` in `backend/app/routers/agent.py` to:
  - Call OpenAI Agent with user message + session context
  - Route response through appropriate handler (inventory, billing, query, etc.)
  - Include loading state callback for "Agent is thinking..." (FR-014)
  - Return JSON response with structured data (FR-016)
  - Add error handling with auto-retry (FR-015)
  - Log interaction to conversation_history table (FR-007, VIII. Observability)

- [ ] T018 [US1] Add conversation history logging in `backend/app/services/agent.py` to PostgreSQL (insert user message, agent response, session_id, timestamp)

**Frontend**:

- [ ] T019 [P] [US1] Implement ChatKit event handler in `components/ChatKitWidget.tsx` for message send:
  - Capture user message
  - Show loading state: "Agent is thinking... X seconds elapsed" (FR-014)
  - Call `lib/api.ts::chatWithAgent(message, sessionId)`
  - Render response in ChatKit (FR-005, FR-009)
  - Handle errors with auto-retry + "Retry" button (FR-015)

- [ ] T020 [P] [US1] Implement ChatKit JSON response renderer in `components/ChatKitWidget.tsx`:
  - If response.type == "item_created": Display item summary card (name, price, stock, category)
  - Preserve in message history (FR-007, FR-009, FR-016)

- [ ] T021 [US1] Add test: Conversation test in `backend/tests/agent/test_inventory_conversation.py`:
  - Mock MCP tools
  - Send: "Add 10kg sugar at 160 per kg under grocery"
  - Verify: Agent parses correctly
  - Verify: JSON response returned with type="item_created"
  - Verify: Item metadata in structured_data

- [ ] T022 [US1] Add test: Integration test in `backend/tests/integration/test_chatkit_inventory.py`:
  - Start FastAPI server + MCP tools
  - Send message through `/agent/chat`
  - Verify: Item created in PostgreSQL
  - Verify: Message stored in conversation_history

**Checkpoint**: User Story 1 fully functional. Admin can add items via natural language ChatKit. MVP ready to validate with stakeholders.

---

## Phase 4: User Story 2 - Salesperson Creates Bills via ChatKit (Priority: P1)

**Goal**: Enable salesperson to create bills through natural language ChatKit interface with structured JSON response showing bill summary.

**Independent Test**:
1. Open ChatKit on `/pos` page
2. Type: "Create a bill for Ali: 2kg sugar and 1 shampoo bottle"
3. Verify: ChatKit displays bill summary card (customer name, items, quantities, unit prices, line totals, grand total)
4. Verify: Bill created in PostgreSQL with correct totals
5. Verify: Bill items linked to correct inventory items

### Implementation for User Story 2

**Backend**:

- [ ] T023 [P] [US2] Implement billing request handler in `backend/app/services/agent.py::handle_billing_request()` that:
  - Parses agent response to extract: customer name, item descriptions, quantities
  - Calls MCP `inventory_list_items` to find matching items
  - Calls MCP `billing_create_bill` to create bill record
  - Calculates totals: line_totals = quantity × unit_price; grand_total = sum(line_totals)
  - Returns JSON response: `{message, type: "bill_created", bill_data: {bill_id, customer_name, items, grand_total}}`

- [ ] T024 [P] [US2] Enhance POST `/agent/chat` in `backend/app/routers/agent.py` to route billing requests to handler (reuse existing logic from T017)

- [ ] T025 [US2] Add test: Conversation test in `backend/tests/agent/test_billing_conversation.py`:
  - Mock MCP tools with sample inventory (sugar, shampoo)
  - Send: "Create a bill for Ali: 2kg sugar and 1 shampoo bottle"
  - Verify: Agent extracts customer name, items, quantities
  - Verify: JSON response type="bill_created"
  - Verify: Bill totals calculated correctly in structured_data

- [ ] T026 [US2] Add test: Integration test in `backend/tests/integration/test_chatkit_billing.py`:
  - Start FastAPI server + MCP tools + sample inventory
  - Send message through `/agent/chat`
  - Verify: Bill created in PostgreSQL
  - Verify: Bill totals match calculation
  - Verify: Bill items linked to inventory items

**Frontend**:

- [ ] T027 [P] [US2] Implement ChatKit JSON response renderer in `components/ChatKitWidget.tsx`:
  - If response.type == "bill_created": Display bill card with:
    - Customer name (header)
    - Item rows: item_name | quantity | unit_price | line_total
    - Grand total highlighted
  - Example: "Bill for Ali: Sugar 2kg × 160 = 320 | Shampoo 1 × 200 = 200 | **Total: 520**"
  - Preserve in message history

- [ ] T028 [P] [US2] Add edge case handler for insufficient stock:
  - If agent returns error: "Insufficient stock for [item]"
  - Display error message in ChatKit
  - Show "Retry" button if needed

**Checkpoint**: User Story 2 fully functional. Salesperson can create bills via ChatKit with formatted summary. Both P1 stories (US1 + US2) now complete.

---

## Phase 5: User Story 3 - Store Admin Queries Inventory via ChatKit (Priority: P2)

**Goal**: Enable store admin to query inventory using natural language (e.g., "show low stock items") with readable table response.

**Independent Test**:
1. Open ChatKit on `/admin` page
2. Type: "Show me all beauty items with stock less than 5 units"
3. Verify: ChatKit displays results as table: name | price | stock | low-stock warning
4. Verify: Only matching items displayed
5. If no matches: Display helpful message

### Implementation for User Story 3

**Backend**:

- [ ] T029 [P] [US3] Implement query request handler in `backend/app/services/agent.py::handle_query_request()` that:
  - Parses agent response to extract: category filter, stock threshold
  - Calls MCP `inventory_list_items` with filters
  - Returns JSON response: `{message, type: "item_list", items: [{name, price, stock, category}, ...], count: N}`

- [ ] T030 [P] [US3] Enhance POST `/agent/chat` in `backend/app/routers/agent.py` to route query requests to handler

- [ ] T031 [US3] Add test: Conversation test in `backend/tests/agent/test_query_conversation.py`:
  - Mock MCP tools with sample inventory
  - Send: "Show me all beauty items with low stock"
  - Verify: Agent extracts filters (category=beauty, stock<5)
  - Verify: JSON response type="item_list"
  - Verify: Only matching items in structured_data

**Frontend**:

- [ ] T032 [P] [US3] Implement ChatKit JSON response renderer in `components/ChatKitWidget.tsx`:
  - If response.type == "item_list": Display as table:
    ```
    | Item Name | Category | Unit Price | Stock | Status |
    |-----------|----------|------------|-------|--------|
    | Lipstick  | beauty   | 250        | 2     | ⚠️ LOW |
    | Shampoo   | beauty   | 200        | 0     | ⚠️ OUT |
    ```
  - Highlight low stock (<5) items with warning
  - Show count of results: "Found 5 items"

- [ ] T033 [P] [US3] Add empty result handler:
  - If response.items.length == 0: Display "No beauty items found with stock less than 5 units"

**Checkpoint**: User Story 3 complete. Query functionality working independently.

---

## Phase 6: User Story 4 - ChatKit Persists During Navigation (Priority: P2)

**Goal**: ChatKit widget remains visible and maintains state when user navigates between `/admin`, `/pos`, `/agent` routes.

**Independent Test**:
1. Open ChatKit on `/admin` page, send a message
2. Verify: Message appears in chat history
3. Navigate to `/pos` page
4. Verify: ChatKit still visible in bottom-right
5. Verify: Previous message history intact
6. Send another message on `/pos`
7. Verify: Both messages visible
8. Navigate back to `/admin`
9. Verify: All messages still visible (session preserved)

### Implementation for User Story 4

**Backend**:

- [ ] T034 [US4] Ensure session persistence across requests (already implemented in T008, T010)
  - Session ID maintained in HTTP header: `X-Session-ID`
  - Backend retrieves conversation history from PostgreSQL per session_id

**Frontend**:

- [ ] T035 [US4] Implement sessionStorage persistence in `lib/hooks/useChatSession.ts`:
  - Store session_id in sessionStorage (survives route navigation within tab)
  - Store message history in sessionStorage as backup
  - Restore on component mount (page refresh)

- [ ] T036 [US4] Verify ChatKit state persistence in `components/ChatKitWidget.tsx`:
  - Use `useChatSession` hook to maintain state across routes
  - Pass session_id to every `/agent/chat` call
  - Verify: Message history rendered from hook state (FR-007)

- [ ] T037 [US4] Add test: Navigation test in `backend/tests/integration/test_session_persistence.py`:
  - Create session on `/admin`
  - Send message (verify stored in conversation_history)
  - Simulate navigation (no API call needed, verify session_id preserved)
  - Send another message on "new route"
  - Verify: Both messages in conversation_history

**Checkpoint**: All 4 user stories complete. ChatKit fully integrated across all pages with persistent state.

---

## Phase 7: Error Handling & Edge Cases

**Purpose**: Implement error recovery and edge case handling per specification

### API Error Handling

- [ ] T038 [P] Implement error responses in `backend/app/routers/agent.py`:
  - Network error: Return 503 with message "Agent service temporarily unavailable"
  - Timeout (>5s): Return 504 with message "Agent did not respond in time"
  - Validation error: Return 400 with field-specific error messages
  - Session expired: Return 401 with message "Session expired. Please refresh the page."

- [ ] T039 [P] Implement auto-retry logic in `lib/api.ts::chatWithAgent()`:
  - First failure: Wait 1s, retry silently (exponential backoff per FR-015)
  - Second failure: Return error to ChatKit with "Retry" button
  - Do not retry more than once automatically (prevent infinite loops)

### Frontend Edge Cases

- [ ] T040 [P] Implement long message handling in `components/ChatKitWidget.tsx`:
  - Wrap responses >500 chars with line breaks
  - Allow scrolling within chat bubble (FR-009)

- [ ] T041 [P] Implement rapid send prevention:
  - Disable send button while awaiting response
  - Re-enable when response arrives
  - Prevent message queue buildup (per edge case spec)

- [ ] T042 [P] Implement special character sanitization:
  - Safely render `&`, `<`, `>`, quotes as-is (not as HTML entities)
  - Use React's built-in XSS protection (textContent, not dangerouslySetInnerHTML)

- [ ] T043 [P] Implement JSON rendering error handling:
  - If agent returns malformed JSON: Display "Unable to format response. Raw: [message text]"
  - Fall back to plain text display (FR-010)

**Checkpoint**: All error cases handled gracefully per specification.

---

## Phase 8: Performance Optimization & Observability

**Purpose**: Meet performance goals and enable debugging

### Performance

- [ ] T044 [P] Optimize ChatKit component load time (target SC-010: <2 seconds):
  - Lazy load ChatKit component on route mount
  - Measure load time with performance.mark()
  - Verify: <2 second initialization

- [ ] T045 [P] Optimize agent response time (target SC-004: <5 seconds):
  - Measure from request send to response display
  - Log timing in `backend/app/services/agent.py`

### Observability

- [ ] T046 [P] Add structured logging to `/agent/chat` endpoint in `backend/app/routers/agent.py`:
  - Log format: `[timestamp] POST /agent/chat - Session: {session_id} - Message: {truncated_message} - Response time: {ms} - Status: {success|error}`
  - Example: `[2025-12-09 10:30:45] POST /agent/chat - Session: abc123 - Message: "Add 10kg sugar..." - Response time: 2341ms - Status: success`

- [ ] T047 [P] Add frontend logging to `lib/api.ts`:
  - Log message send/receive events
  - Log error recovery attempts
  - Send to backend if debug mode enabled

- [ ] T048 Add monitoring test in `backend/tests/integration/test_observability.py`:
  - Send message through `/agent/chat`
  - Verify: Log entry created with correct format and timing
  - Verify: Response time <= 5 seconds (SC-004)

**Checkpoint**: Performance meets targets; debugging information available.

---

## Phase 9: Cross-Browser & Responsive Testing

**Purpose**: Verify SC-008 (responsive across 320px-2560px)

- [ ] T049 [P] Test responsive behavior in `components/ChatKitWidget.tsx`:
  - Mobile (320px): ChatKit widget fits without overflow
  - Tablet (768px): ChatKit accessible below content
  - Desktop (1920px): ChatKit in bottom-right corner
  - Ultra-wide (2560px): ChatKit positioned correctly

- [ ] T050 [P] Test browser compatibility:
  - Chrome/Chromium (ES2020+)
  - Firefox (ES2020+)
  - Safari 14+ (ES2020+)
  - Verify: No console errors

**Checkpoint**: Responsive design validated.

---

## Phase 10: Polish & Documentation

**Purpose**: Final quality improvements and documentation

- [ ] T051 [P] Add README for ChatKit integration in `docs/chatkit-setup.md`:
  - Environment variables required
  - Session management explanation
  - Supported commands (inventory add, bill create, inventory query)
  - Troubleshooting section

- [ ] T052 [P] Add inline code comments in:
  - `components/ChatKitWidget.tsx` (session management logic)
  - `lib/api.ts` (error retry logic)
  - `backend/app/services/agent.py` (response routing)

- [ ] T053 Update `docs/API.md` with `/agent/chat` endpoint contract:
  - Request schema: `{session_id, message_text, user_id}`
  - Response schema: `{response_text, type, structured_data, session_id, timestamp}`
  - Example responses for inventory, billing, query

- [ ] T054 [P] Validate quickstart.md test scenarios (SC-001 through SC-010):
  - Users can add items via ChatKit (SC-001)
  - ChatKit visible across routes (SC-002)
  - Messages reach endpoint (SC-003)
  - Responses display <5s (SC-004)
  - History preserved on refresh (SC-005)
  - Error handling works (SC-006)
  - Bills created with 95% accuracy (SC-007)
  - Responsive on all screen sizes (SC-008)
  - 90% NLP interpretation accuracy (SC-009)
  - ChatKit loads <2s (SC-010)

- [ ] T055 Code review checklist:
  - [ ] Tests written first and passing
  - [ ] No hardcoded secrets in frontend/backend
  - [ ] Structured logging present
  - [ ] API contracts documented
  - [ ] Error handling comprehensive
  - [ ] Conversation history stored in PostgreSQL
  - [ ] Session management works across routes
  - [ ] JSON responses render correctly

**Checkpoint**: Phase 6 complete and production-ready.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - CRITICAL, blocks all user stories
- **User Stories (Phase 3-6)**: Can start after Foundational completion
  - US1 (P1, T015-T022): Inventory add - no dependencies on other stories
  - US2 (P1, T023-T028): Bill creation - can run parallel with US1 after Foundational
  - US3 (P2, T029-T033): Inventory query - can run parallel with US1/US2 after Foundational
  - US4 (P2, T034-T037): Navigation persistence - can run parallel after Foundational
- **Error Handling (Phase 7)**: After all stories complete or during story implementation
- **Performance (Phase 8)**: After stories complete
- **Testing (Phase 9)**: After stories complete
- **Polish (Phase 10)**: Final phase before deployment

### Critical Path

```
Phase 1 Setup (T001-T005)
         ↓
Phase 2 Foundational (T006-T014) [BLOCKS ALL USER STORIES]
         ↓
Phase 3+6: User Stories in parallel or sequence
         ↓
Phase 7-10: Polish & Validation
```

### Parallel Opportunities

**During Foundational Phase**: All [P] tasks (T006-T013) can run in parallel

**During User Story 1**:
- Backend tasks T015-T018 can run in parallel (different files)
- Frontend tasks T019-T020 can run in parallel (different features)
- Tests T021-T022 can run in parallel

**During User Story 2-3**: Similar parallel opportunities within each story

**Across Stories**: After Foundational, all 4 user stories can run in parallel with different team members

### Minimal MVP Path

To deliver MVP (User Story 1 only):

1. ✅ Phase 1: Setup (T001-T005)
2. ✅ Phase 2: Foundational (T006-T014)
3. ✅ Phase 3: User Story 1 (T015-T022)
4. **STOP AND VALIDATE** - Verify admin can add items via ChatKit
5. Deploy if satisfied

## Implementation Strategy

### MVP First Approach

Focus on P1 stories (US1 + US2) to validate core value proposition:
- Natural language inventory add (US1)
- Natural language bill creation (US2)

Both stories demonstrate full pipeline: ChatKit → Agent → MCP tools → Database

### Incremental Delivery

1. **Sprint 1**: Phase 1 + Phase 2 (Foundational) → Foundation ready
2. **Sprint 2**: Phase 3 (US1) → Inventory add working, deployable
3. **Sprint 3**: Phase 4 (US2) → Bill creation working, deployable
4. **Sprint 4**: Phase 5-6 (US3, US4) → Query + persistence complete
5. **Sprint 5**: Phase 7-10 (Error handling, Polish) → Production ready

Each sprint delivers independently testable value without breaking prior work.

---

## Notes

- **[P] tasks** = different files, no dependencies within phase
- **[Story]** label enables traceability of which user story each task serves
- Each user story is independently completable and testable (per spec requirements)
- Tests follow TDD: write failing test first (RED), implement code (GREEN), refactor
- Constitution Principle VII (Simplicity): Use ChatKit as-is; direct HTTP calls; no custom UI wrapping
- Constitution Principle I (Separation): Frontend/backend completely separate, API contract only
- Commit after each logical group of tasks
- Stop at any checkpoint to validate story independently before proceeding
- All tasks follow strict checklist format: `- [ ] [ID] [P?] [Story] Description with file path`
