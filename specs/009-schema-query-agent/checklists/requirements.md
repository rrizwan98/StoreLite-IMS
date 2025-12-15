# Requirements Checklist: Schema Query Agent

**Version:** 1.0
**Date:** December 15, 2025

---

## Functional Requirements

### FR-1: Connection Flow
- [ ] FR-1.1: User can select "Agent + Analytics Only" option
- [ ] FR-1.2: User can input PostgreSQL connection URI
- [ ] FR-1.3: System tests connection before saving
- [ ] FR-1.4: System discovers database schema automatically
- [ ] FR-1.5: User can view discovered schema
- [ ] FR-1.6: Connection persists across sessions

### FR-2: Schema Discovery
- [ ] FR-2.1: Discover all tables in allowed schemas
- [ ] FR-2.2: Discover columns with data types
- [ ] FR-2.3: Discover foreign key relationships
- [ ] FR-2.4: Cache schema in database
- [ ] FR-2.5: Allow manual schema refresh

### FR-3: Natural Language Queries
- [ ] FR-3.1: Accept natural language input
- [ ] FR-3.2: Generate appropriate SQL
- [ ] FR-3.3: Display generated SQL to user
- [ ] FR-3.4: Execute query and return results
- [ ] FR-3.5: Format results readably

### FR-4: Visualizations
- [ ] FR-4.1: Suggest chart types based on data
- [ ] FR-4.2: Display bar charts
- [ ] FR-4.3: Display line charts
- [ ] FR-4.4: Display data tables with pagination

### FR-5: UI/UX
- [ ] FR-5.1: Three-option service selection
- [ ] FR-5.2: Schema browser sidebar
- [ ] FR-5.3: Chat interface for queries
- [ ] FR-5.4: Hide Admin/POS for schema-only users
- [ ] FR-5.5: Connection status indicator

---

## Non-Functional Requirements

### NFR-1: Security
- [ ] NFR-1.1: Only SELECT queries executed
- [ ] NFR-1.2: No INSERT/UPDATE/DELETE allowed
- [ ] NFR-1.3: No DROP/CREATE/ALTER allowed
- [ ] NFR-1.4: SQL injection prevention
- [ ] NFR-1.5: SSL connection required
- [ ] NFR-1.6: Database URI encrypted at rest

### NFR-2: Performance
- [ ] NFR-2.1: Query timeout: 30 seconds max
- [ ] NFR-2.2: Result limit: 10,000 rows max
- [ ] NFR-2.3: Schema discovery: < 10 seconds
- [ ] NFR-2.4: Connection test: < 5 seconds

### NFR-3: Reliability
- [ ] NFR-3.1: Rate limiting: 60 queries/min/user
- [ ] NFR-3.2: Connection pooling (5 per user)
- [ ] NFR-3.3: Graceful error handling
- [ ] NFR-3.4: Reconnection on failure

### NFR-4: Compatibility
- [ ] NFR-4.1: PostgreSQL 12+ support
- [ ] NFR-4.2: Works with any schema structure
- [ ] NFR-4.3: Handles NULL values
- [ ] NFR-4.4: Handles special characters

---

## Acceptance Criteria

### AC-1: Happy Path
- [ ] User connects database successfully
- [ ] Schema displayed correctly
- [ ] Natural language query works
- [ ] Visualization renders
- [ ] No tables created in user's DB

### AC-2: Error Handling
- [ ] Invalid URI shows clear error
- [ ] Connection failure handled gracefully
- [ ] Query timeout shows message
- [ ] Rate limit shows retry time

### AC-3: Security Verification
- [ ] Attempted INSERT rejected
- [ ] Attempted DELETE rejected
- [ ] Attempted DROP rejected
- [ ] SQL injection blocked

---

## Sign-Off

| Reviewer | Date | Status |
|----------|------|--------|
| Developer | - | Pending |
| QA | - | Pending |
| Product | - | Pending |
