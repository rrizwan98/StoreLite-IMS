# Feature Specification: ChatKit UI Integration

**Feature Branch**: `006-chatkit-ui`
**Created**: 2025-12-09
**Status**: Draft
**Input**: User description: "Phase 6: ChatKit UI Integration - Build ChatKit chat interface and connect to agent/chat API endpoint. Place ChatKit widget on right side corner of web page, integrate with existing Next.js frontend."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Store Admin Uses ChatKit to Add Inventory via Natural Language (Priority: P1)

A store administrator opens the StoreLite application and uses the ChatKit chat widget to add new inventory items using natural language, rather than filling out forms. They type "Add 10kg sugar at 160 per kg under grocery category" and the system understands the request, calls the backend agent, which in turn uses MCP tools to add the item to PostgreSQL.

**Why this priority**: This is the core value proposition of Phase 6 - enabling natural language inventory management instead of manual form entry. It demonstrates that the full pipeline (ChatKit UI → Agent API → MCP tools → Database) works end-to-end.

**Independent Test**: Can be fully tested by opening the ChatKit UI, typing a natural language inventory request, and verifying the item appears in the PostgreSQL database without using any form interface.

**Acceptance Scenarios**:

1. **Given** the ChatKit UI is visible on the right side of the page, **When** an admin types "Add 10kg sugar at 160 per kg under grocery", **Then** ChatKit sends the message to `/agent/chat`, the agent processes it, MCP tools create the item, and ChatKit displays confirmation.
2. **Given** the ChatKit is active, **When** the admin sends an inventory command, **Then** the message appears in chat history with a response from the agent.
3. **Given** an inventory item is successfully added via ChatKit, **When** the admin navigates to the admin panel (`/admin`), **Then** the newly added item appears in the items list.

---

### User Story 2 - Salesperson Creates Bills via ChatKit Natural Language (Priority: P1)

A salesperson uses ChatKit to create bills for customers by describing items and quantities in natural language. They type "Create a bill for Ali: 2kg sugar and 1 shampoo bottle" and ChatKit displays the bill summary with total amount.

**Why this priority**: Second core use case - enabling natural language billing without navigating to a separate POS form. Critical for fast checkout experience.

**Independent Test**: Can be fully tested by typing a natural language bill request in ChatKit, verifying the agent calls `billing_create_bill` MCP tool, and confirming the bill is created in the database with correct totals.

**Acceptance Scenarios**:

1. **Given** ChatKit is displayed, **When** a salesperson types "Create a bill for customer Ali: 2kg sugar and 1 shampoo bottle", **Then** the agent finds matching items and creates a bill in the database.
2. **Given** a bill is successfully created, **When** ChatKit displays the response, **Then** it shows bill summary including customer name, items, quantities, unit prices, line totals, and grand total.
3. **Given** insufficient stock exists, **When** the salesperson requests a quantity exceeding available stock, **Then** the agent responds with an error message and suggests available quantity.

---

### User Story 3 - Store Admin Queries Inventory via ChatKit Natural Language (Priority: P2)

An administrator uses ChatKit to ask questions about inventory without navigating between pages. They type "Show me all beauty items with stock less than 5 units" and ChatKit displays the results formatted clearly in the chat.

**Why this priority**: Enhances analytics and monitoring capabilities. Less critical than add/bill operations but valuable for inventory management.

**Independent Test**: Can be fully tested by sending a natural language query through ChatKit and verifying the agent calls `inventory_list_items` with correct filters and displays results in the chat.

**Acceptance Scenarios**:

1. **Given** ChatKit is active, **When** an admin queries "Show me all beauty items with low stock", **Then** the agent calls the appropriate MCP tool and returns matching items.
2. **Given** multiple items match the query, **When** the agent responds, **Then** ChatKit displays them in a readable format (list or table summary).
3. **Given** no items match the query, **When** the agent processes the request, **Then** ChatKit displays a helpful message like "No beauty items found with stock less than 5 units".

---

### User Story 4 - ChatKit UI Persists in Corner During Navigation (Priority: P2)

Users navigate between different pages of the application (`/admin`, `/pos`, `/agent`) and the ChatKit widget remains visible and accessible in the bottom-right corner of the page, maintaining conversation history during navigation.

**Why this priority**: Ensures a seamless experience where users can reference or continue conversations while working in different parts of the application.

**Independent Test**: Can be tested by opening ChatKit, sending a message, navigating to another page, and verifying the widget is still visible with the previous message history intact.

**Acceptance Scenarios**:

1. **Given** ChatKit is open with message history, **When** the user navigates from `/admin` to `/pos`, **Then** ChatKit remains visible with all previous messages intact.
2. **Given** ChatKit is minimized on one page, **When** the user navigates to another page, **Then** ChatKit maintains its state (minimized or expanded).
3. **Given** a user has a session ID established, **When** they navigate between pages, **Then** the same session context is preserved for the agent to recall previous conversation context.

### Edge Cases

- **Unreachable API Endpoint**: ChatKit automatically retries once; if still fails, displays "Unable to reach agent service. Retry?" button. User can manually retry the message.
- **Long Messages/Responses**: ChatKit displays text in scrollable chat bubbles; very long responses (>500 chars) are wrapped with line breaks and can be scrolled within the bubble.
- **Rapid Message Sending**: ChatKit disables the send button while awaiting a response, preventing multiple messages from queuing. Once response arrives, the button re-enables.
- **Network Timeouts**: If response exceeds 5 seconds (SC-004 timeout), ChatKit displays "Agent did not respond in time. Retry?" button; user can manually retry.
- **Special Characters in Response**: Agent responses (JSON or text) are safely sanitized; special characters are preserved in display (e.g., `&`, `<`, `>` rendered as-is, not as HTML entities).
- **Session Expiry**: Sessions persist while tab is open (FR-017). If backend session is lost (user manually clears cookies or extremely long idle), ChatKit detects the error on next message and prompts "Session expired. Please refresh the page."
- **JSON Rendering Errors**: If agent returns malformed JSON for structured data, ChatKit falls back to displaying the raw message with error indicator: "Unable to format response. Raw: [message text]"

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: ChatKit UI MUST be integrated as a React component using `@openai/chatkit-react` package in the Next.js frontend
- **FR-002**: ChatKit widget MUST be positioned in the bottom-right corner of the page and remain visible across all application routes (`/admin`, `/pos`, `/agent`)
- **FR-003**: ChatKit MUST connect to the backend `/agent/chat` API endpoint to send and receive messages
- **FR-004**: ChatKit MUST maintain a session ID per user to preserve conversation context and history across multiple turns
- **FR-005**: ChatKit MUST display the agent's response in real-time, either as streamed chunks or complete message when received from the backend
- **FR-006**: ChatKit MUST accept user messages in natural language and forward them to the agent without modification
- **FR-007**: ChatKit MUST display conversation history (all previous user messages and agent responses) within the chat interface
- **FR-008**: ChatKit MUST support message input through a text field with a send button or keyboard shortcut (Enter key)
- **FR-009**: ChatKit MUST handle agent responses that include structured data (e.g., bill summaries, item lists) and display them in a readable format
- **FR-010**: ChatKit MUST handle error responses from the agent (e.g., validation errors, database errors) and display user-friendly error messages
- **FR-011**: ChatKit configuration MUST be stored in environment variables (API endpoint URL, domain key, theming options)
- **FR-012**: ChatKit MUST have a minimize/expand toggle to allow users to collapse the widget when not in use
- **FR-013**: ChatKit MUST support self-hosted backend mode where all API calls are routed to the local FastAPI `/agent/chat` endpoint, not OpenAI's servers
- **FR-014**: ChatKit MUST display loading state with "Agent is thinking..." message and an elapsed time counter (e.g., "2 seconds...") while awaiting agent response
- **FR-015**: ChatKit MUST automatically retry failed messages once with exponential backoff (1s delay); if retry fails, display a "Retry" button for manual user retry
- **FR-016**: ChatKit MUST accept JSON-formatted structured responses from the agent and auto-render them as formatted cards for bills (showing items, line totals, grand total) and tables for item lists (showing name, price, stock with low-stock warnings)
- **FR-017**: ChatKit sessions MUST persist while the browser tab is open; sessions expire only when the page is closed or user logs out of the application

### Key Entities *(include if feature involves data)*

- **ChatKit Configuration**: Stores API endpoint URL, domain key, theme colors, and initial greeting message
- **User Session**: Maintains session_id to track conversation context across multiple messages and page navigations
- **Chat Message**: Individual user message or agent response, timestamped and stored in conversation history
- **Conversation History**: Complete record of all messages in a session, maintained both in client memory and backend PostgreSQL database

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Users can send natural language inventory commands through ChatKit and see items added to the database within 3 seconds of sending the message
- **SC-002**: ChatKit widget remains visible and functional when navigating between all application routes (`/admin`, `/pos`, `/agent`)
- **SC-003**: 100% of user messages sent through ChatKit reach the `/agent/chat` endpoint without loss
- **SC-004**: Agent responses are displayed in ChatKit within 5 seconds of the agent completing processing (latency measured from agent response to UI display)
- **SC-005**: Conversation history is fully preserved and displayed when the page is refreshed (either from browser memory or backend session storage)
- **SC-006**: ChatKit handles network errors gracefully, displaying an error message and allowing users to retry without losing conversation context
- **SC-007**: Users can create valid bills through ChatKit with 95% accuracy (bill totals calculated correctly, items properly linked)
- **SC-008**: ChatKit interface is responsive and maintains usability on screen sizes from 320px (mobile) to 2560px (large desktop)
- **SC-009**: At least 90% of natural language inventory queries are correctly interpreted by the agent and return expected results
- **SC-010**: ChatKit component loads and initializes in under 2 seconds after page load

---

## Clarifications

### Session 2025-12-09

- **Q1: Session Persistence & Expiry** → **A: Option C** - Sessions persist indefinitely while the browser tab is open; expire only when the page is closed or user logs out of the application. Backend naturally cleans up the session on application shutdown.

- **Q2: Loading & Typing State Indicators** → **A: Option B** - ChatKit displays "Agent is thinking..." with elapsed time counter (e.g., "2 seconds...") so users see real-time feedback on wait duration. This manages expectations against SC-004 5-second response time SLA.

- **Q3: Error Recovery & Retry Strategy** → **A: Option C** - System automatically retries failed messages once silently with exponential backoff. If the retry fails, a "Retry" button appears for user control. This balances resilience (transient failures recover) with transparency (persistent failures need user action).

- **Q4: Structured Data Rendering (Bills & Item Lists)** → **A: Option D** - Agent returns structured JSON responses (not markdown or HTML). ChatKit auto-formats JSON into bill cards (displaying items, line totals, grand total highlighted) and item list tables (displaying name, price, stock with visual warnings for low stock). Decouples agent output from UI rendering.

---

## Assumptions

- The `/agent/chat` API endpoint is already implemented in the FastAPI backend (Phase 5) and is ready to receive requests
- PostgreSQL database is running and accessible by the backend to store bills, inventory, and session data
- The OpenAI Agents SDK with Gemini-lite model is already configured in the backend
- The MCP tools (`inventory_add_item`, `inventory_list_items`, `billing_create_bill`, etc.) are registered and functional
- The Next.js frontend is running as a server-side rendered or static-export application where routing is handled by Next.js App Router
- Users have JavaScript enabled in their browsers (ChatKit is a JavaScript/React component)
- Network connectivity is available between the frontend and backend for API calls
- Session management is handled by the backend (session_id generation and PostgreSQL storage)
- Agent responses to ChatKit include a JSON structure with fields: `message` (text response), `type` (e.g., "text", "bill", "item_list"), and structured data (items array, totals, etc.) for complex responses

---

## Constraints & Non-Goals

**Constraints**:
- ChatKit must use self-hosted backend mode (not OpenAI's hosted ChatKit service) since the agent uses Gemini-lite model, not OpenAI models
- ChatKit positioning must not interfere with existing page content or layouts; it should float above the main content
- All communication between ChatKit and backend must use HTTP/REST (JSON payloads)

**Non-Goals**:
- Adding authentication/authorization to ChatKit (assume users are already authenticated at the application level)
- Building custom chat UI components (must use ChatKit's built-in components)
- Implementing voice input or speech-to-text (text-only for Phase 6)
- Adding file upload capabilities to ChatKit (text messages only)
- Custom styling beyond simple theme configuration (use ChatKit's default styling)
- Real-time collaboration or multi-user chat (single-user sessions)

---

## Dependencies & Integration Points

- **Frontend**: Next.js 14+, React 18+, TypeScript
- **ChatKit Libraries**: `@openai/chatkit`, `@openai/chatkit-react` (latest stable version)
- **Backend API**: FastAPI `/agent/chat` endpoint (must be implemented in Phase 5)
- **Database**: PostgreSQL (existing from Phase 1-5)
- **Agent Runtime**: OpenAI Agents SDK with Gemini 2.5 Flash Lite model (existing from Phase 5)
- **MCP Server**: Local FastMCP server exposing inventory and billing tools (existing from Phase 4)
- **Environment**: Node.js 18+ for frontend, Python 3.10+ for backend
