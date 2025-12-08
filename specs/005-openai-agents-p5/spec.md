# Feature Specification: OpenAI Agents SDK Integration with MCP Server

**Feature Branch**: `005-openai-agents-p5`
**Created**: 2025-12-09
**Status**: Draft
**Input**: User description: "Build Phase 5 using OpenAI Agent SDK to orchestrate agents that connect to the existing MCP server. Create a FastAPI endpoint that allows users to have natural language conversations with an agent that calls MCP tools to solve inventory and billing problems. Use TDD approach with clear, sample code."

---

## Clarifications

### Session 2025-12-09

- Q: How much conversation history should agent retain per session? → A: Recent N messages (last 5 exchanges) to balance context availability with API cost
- Q: Should agent discover MCP tools dynamically or use hardcoded list? What transport protocol? → A: Dynamic discovery at startup via HTTP to localhost:8001
- Q: Should `/agent/chat` require authentication and role-based permissions? → A: No authentication required for Phase 5 (can be added in later phases)
- Q: How should user confirm destructive actions (bill creation, item deletion)? → A: Inline yes/no question in conversation flow
- Q: What streaming format for agent responses (SSE, WebSocket, chunked HTTP)? → A: Server-Sent Events (SSE) for real-time chunked output

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Store Admin Adds Inventory via Natural Language (Priority: P1)

A store admin interacts with a chat-like interface powered by the OpenAI Agents SDK. The admin speaks naturally (e.g., "Add 20kg sugar at 160 per kg to the grocery category") and the agent interprets the request, calls the appropriate MCP tool, and confirms the action was completed.

**Why this priority**: This is the primary entry point for users to interact with the system via natural language instead of forms. It demonstrates the core value of using an AI agent with MCP tool integration.

**Independent Test**: Can be fully tested by sending a natural language message to the `/agent/chat` endpoint with a request to add inventory, verifying the agent calls the `inventory_add_item` MCP tool with correct parameters, and confirming the item is persisted in PostgreSQL.

**Acceptance Scenarios**:

1. **Given** a user sends message "Add 10kg flour at 50 per kg under grocery" to `/agent/chat`, **When** the agent processes the request, **Then** the agent calls `inventory_add_item(name="flour", category="grocery", unit="kg", unit_price=50, stock_qty=10)` and responds with confirmation: "I've added 10kg Flour at 50 per kg to Grocery category."
2. **Given** a user sends an ambiguous request (e.g., "Add something"), **When** the agent cannot determine required fields, **Then** the agent asks clarifying questions: "What item would you like to add? What's the name, unit, price, and quantity?"
3. **Given** a user tries to add an item with invalid data (negative price), **When** the agent processes the request, **Then** the MCP tool rejects it and the agent responds with the error: "I couldn't add that item—the price must be positive."

---

### User Story 2 - Salesperson Creates a Bill via Natural Language (Priority: P1)

A salesperson says something like "Create a bill for Ali: 2kg sugar and 1 shampoo bottle" and the agent interprets it, searches the inventory via MCP, verifies stock availability, creates the bill, updates inventory, and returns the bill details with a total.

**Why this priority**: Creating bills is the core revenue-generating workflow. Natural language bill creation removes friction from the sales process and reduces data entry errors.

**Independent Test**: Can be fully tested by sending a natural language bill request to `/agent/chat`, verifying the agent calls `inventory_list_items` to find matching items, calls `billing_create_bill` with correct line items, and returns a bill summary with bill ID and total amount.

**Acceptance Scenarios**:

1. **Given** inventory has "Sugar" (10kg at 160 per kg) and "Shampoo" (5 bottles at 200 each), **When** user sends "Create bill for customer Ali: 2kg sugar and 1 shampoo", **Then** agent calls `billing_create_bill` with items=[{item_id: sugar_id, quantity: 2}, {item_id: shampoo_id, quantity: 1}] and responds with: "Bill created! Total: 820 (Sugar: 320 + Shampoo: 500). Bill ID: [ID]"
2. **Given** user requests more quantity than available (e.g., "5kg sugar" but only 3kg in stock), **When** agent processes the request, **Then** agent warns: "Only 3kg of sugar in stock. Would you like to add 3kg instead?" and waits for confirmation.
3. **Given** user references an item that doesn't exist, **When** agent searches for the item, **Then** agent responds: "I couldn't find [item_name]. Available items in [category] are: [list]."

---

### User Story 3 - Admin Queries Inventory via Natural Language (Priority: P2)

An admin asks questions like "Show me all items with stock less than 5 units" or "Which items are in the beauty category?" and the agent calls `inventory_list_items` with appropriate filters to retrieve and summarize the results.

**Why this priority**: Query capability enhances the system's analytics and decision-support value, but is secondary to core add/bill operations. It can be built after primary workflows are solid.

**Independent Test**: Can be fully tested by sending query requests to `/agent/chat`, verifying the agent calls `inventory_list_items` with correct filter parameters, and confirming the response summarizes the results in a readable format.

**Acceptance Scenarios**:

1. **Given** inventory has items with varying stock levels, **When** user asks "Show items with low stock (under 5)", **Then** agent calls `inventory_list_items` and responds with a formatted list: "Low stock items: [item1: 2 units], [item2: 4 units]"
2. **Given** multiple items in a category, **When** user asks "What's in beauty category?", **Then** agent returns filtered list with names, prices, and stock quantities.

---

### User Story 4 - Update Inventory Stock via Natural Language (Priority: P2)

An admin says "Increase flour stock by 25kg" and the agent updates the inventory via the `inventory_update_item` MCP tool.

**Why this priority**: Stock updates are important but less frequent than initial adds and bills. Secondary priority allows focus on core workflows first.

**Independent Test**: Can be fully tested by sending an update request to `/agent/chat`, verifying the agent looks up the item, calls `inventory_update_item` with the new quantity, and confirms the update.

**Acceptance Scenarios**:

1. **Given** flour currently has 5kg in stock, **When** user says "Increase flour stock by 25kg", **Then** agent updates stock to 30kg and confirms: "Flour stock updated to 30kg."
2. **Given** multiple items with similar names, **When** user says "Update rice", **Then** agent asks: "Which rice did you mean? [Option1], [Option2]?"

---

### Edge Cases

- What happens when the agent receives a request outside its domain (e.g., "What's the weather?")? → Agent politely declines and refocuses on inventory/billing capabilities.
- How does the system handle concurrent requests from multiple users? → Each conversation session maintains independent state via `session_id`.
- What if an MCP tool call fails due to database connectivity? → Agent catches the error and responds: "I encountered a system error. Please try again."
- What happens when a user sends an empty message? → Agent prompts: "How can I help with inventory or billing today?"

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept natural language messages via HTTP POST to `/agent/chat` endpoint with parameters `session_id` (optional) and `message` (required).
- **FR-002**: System MUST use OpenAI Agents SDK to create an agent that can reason about user requests and discover available MCP tools dynamically from the FastMCP server (via HTTP to localhost:8001) at startup.
- **FR-003**: Agent MUST discover and be able to call MCP tools from the existing FastMCP server, including at minimum:
  - `inventory_add_item` – add a new item to inventory
  - `inventory_list_items` – retrieve items with optional filters (name, category, active_only)
  - `inventory_update_item` – modify price, stock, or other item attributes
  - `billing_create_bill` – create a new bill with line items
  - `billing_get_bill` – retrieve a bill by ID
- **FR-004**: Agent MUST validate user intent before calling destructive MCP tools by asking an inline yes/no confirmation question (e.g., "Are you sure you want to create this bill? Reply 'yes' to confirm.") and waiting for user confirmation before executing.
- **FR-005**: Agent MUST maintain conversation context across multiple messages using `session_id` to enable multi-turn conversations, retaining the most recent 5 message exchanges to balance context availability with API cost.
- **FR-006**: `/agent/chat` endpoint MUST support streaming responses via Server-Sent Events (SSE) to return the agent's response in real-time chunks, and MUST also support non-streaming mode returning complete response as JSON (with response, session_id, and optional metadata).
- **FR-007**: System MUST handle MCP tool errors gracefully and return user-friendly error messages (not raw exception traces).
- **FR-008**: System MUST support Server-Sent Events (SSE) streaming format where each chunk of the agent's response is sent as a separate SSE event for real-time display.

### Key Entities

- **Agent Session**: A conversation context identified by `session_id` that persists across multiple user messages. Stores the most recent 5 message exchanges (user message + agent response pairs) for context; older exchanges are discarded to control API cost.
- **MCP Tool**: A function dynamically discovered from the FastMCP server (inventory_add_item, billing_create_bill, etc.) that the agent can call. Tools are discovered at agent startup via HTTP request to localhost:8001.
- **Agent Response**: The text response from the agent to the user, streamed in real-time via Server-Sent Events (SSE) as separate chunks, optionally including structured data (e.g., bill ID, item details).
- **Confirmation Prompt**: An inline yes/no question posed by the agent before executing destructive actions (bill creation, item deletion), requiring explicit "yes" confirmation from the user before proceeding.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agent correctly interprets and executes at least 90% of well-formed natural language requests (measured by manual test cases covering 20+ scenarios).
- **SC-002**: `/agent/chat` endpoint responds to user messages within 3 seconds on average (measured across 100 representative requests).
- **SC-003**: When user requests an invalid action, agent provides a clarifying question or error message within 1 second.
- **SC-004**: All MCP tool calls from the agent correctly persist changes to PostgreSQL (verified by post-action database queries).
- **SC-005**: Multi-turn conversations (5+ back-and-forth exchanges) work correctly with session state maintained across messages.
- **SC-006**: Agent can handle at least 10 concurrent user sessions without degradation.

---

## Assumptions

- The FastMCP server (Phase 4) is fully implemented and running locally (via HTTP on localhost or stdio).
- OpenAI Agents SDK is installed and available in the Python environment.
- OpenAI API key is configured and available via environment variable.
- FastAPI application structure exists from Phase 2.
- PostgreSQL database and existing tables (items, bills, bill_items) are accessible.

---

## Dependencies & Constraints

### External Dependencies

- **OpenAI Agents SDK**: Required for agent orchestration and tool calling.
- **FastMCP Server**: Must be running and accessible (localhost:8001 or via stdio transport).
- **OpenAI API**: Agent reasoning requires API calls (cost implications for production use).

### Constraints

- Agent responses must complete within 3 seconds to keep user experience snappy.
- Session state is stored in-memory with a rolling window of 5 message exchanges per session (can be replaced with persistent storage later).
- MCP tool errors must be caught and translated to user-friendly messages.
- FastMCP server must be accessible via HTTP at localhost:8001 during agent startup for tool discovery.
- No authentication is required for `/agent/chat` endpoint in Phase 5; this can be added in later phases.
- SSE streaming requires client-side event listener support (standard in modern browsers; important for real-time agent response display).

---

## Out of Scope

- ChatKit UI integration (that's Phase 6).
- Advanced conversation features like file uploads or image recognition.
- Persistent session storage across server restarts (in-memory only for Phase 5).
- Rate limiting or usage tracking per user (can be added in future phases).
- Authentication and role-based access control (deferred to Phase 6+; no auth required in Phase 5).

