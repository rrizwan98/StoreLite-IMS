# Gmail Tool Integration - Tasks

**Version**: 1.0.0
**Date**: December 16, 2025
**Status**: Ready for Implementation

---

## Phase 1: Database & Configuration Setup

### Task 1.1: Install Backend Dependencies
- [ ] Add google-auth>=2.25.0 to requirements.txt
- [ ] Add google-auth-oauthlib>=1.2.0 to requirements.txt
- [ ] Add google-api-python-client>=2.111.0 to requirements.txt
- [ ] Add cryptography>=41.0.0 to requirements.txt
- [ ] Run pip install -r requirements.txt

### Task 1.2: Configure Environment Variables
- [ ] Add GOOGLE_CLIENT_ID to .env.example
- [ ] Add GOOGLE_CLIENT_SECRET to .env.example
- [ ] Add GOOGLE_REDIRECT_URI to .env.example
- [ ] Add TOKEN_ENCRYPTION_KEY to .env.example
- [ ] Update backend/.env with actual values

### Task 1.3: Update Database Models
- [ ] Add gmail_access_token (Text, encrypted) to UserConnection
- [ ] Add gmail_refresh_token (Text, encrypted) to UserConnection
- [ ] Add gmail_token_expiry (DateTime) to UserConnection
- [ ] Add gmail_email (String 255) to UserConnection
- [ ] Add gmail_connected_at (DateTime) to UserConnection
- [ ] Add gmail_recipient_email (String 255) to UserConnection

### Task 1.4: Create Database Migration
- [ ] Generate Alembic migration for Gmail fields
- [ ] Test migration upgrade
- [ ] Test migration downgrade
- [ ] Apply migration to database

---

## Phase 2: OAuth2 Backend Implementation

### Task 2.1: Create Encryption Service
- [ ] Create backend/app/services/encryption_service.py
- [ ] Implement encrypt_token(token: str) -> str
- [ ] Implement decrypt_token(encrypted: str) -> str
- [ ] Add error handling for invalid encryption
- [ ] Write unit tests for encryption service

### Task 2.2: Create Gmail OAuth2 Service
- [ ] Create backend/app/services/gmail_oauth_service.py
- [ ] Implement get_authorization_url(user_id, redirect_uri) -> str
- [ ] Implement exchange_code_for_tokens(code) -> TokenData
- [ ] Implement refresh_access_token(refresh_token) -> TokenData
- [ ] Implement revoke_tokens(access_token) -> bool
- [ ] Implement get_user_email(access_token) -> str
- [ ] Implement save_tokens_to_db(user_id, tokens)
- [ ] Add proper error handling and logging
- [ ] Write unit tests for OAuth2 service

### Task 2.3: Create Gmail Router
- [ ] Create backend/app/routers/gmail.py
- [ ] Define Pydantic request/response models
- [ ] Implement GET /gmail/authorize endpoint
- [ ] Implement GET /gmail/callback endpoint
- [ ] Implement GET /gmail/status endpoint
- [ ] Implement DELETE /gmail/disconnect endpoint
- [ ] Implement GET /gmail/recipient endpoint
- [ ] Implement PUT /gmail/recipient endpoint
- [ ] Add authentication middleware to all endpoints
- [ ] Register router in main.py
- [ ] Write integration tests for endpoints

---

## Phase 3: Gmail Send Service & Tool

### Task 3.1: Create Gmail Service
- [ ] Create backend/app/services/gmail_service.py
- [ ] Implement async send_email(user_id, to, subject, body)
- [ ] Implement _build_message(to, subject, body, from_email)
- [ ] Implement _ensure_valid_token(user_id) with refresh logic
- [ ] Implement _get_gmail_service(access_token)
- [ ] Add proper error handling (rate limits, auth errors)
- [ ] Write unit tests for Gmail service

### Task 3.2: Create Gmail Agent Tool
- [ ] Create backend/app/mcp_server/tools_gmail.py
- [ ] Define send_email_tool with @function_tool decorator
- [ ] Add proper docstring for agent understanding
- [ ] Handle context to get user_id
- [ ] Handle "not connected" scenario gracefully
- [ ] Handle send errors with helpful messages
- [ ] Write unit tests for tool

---

## Phase 4: Schema Agent Integration

### Task 4.1: Integrate Gmail Tool with Agent
- [ ] Import Gmail tool in schema_query_agent.py
- [ ] Add Gmail tool to agent's available tools
- [ ] Update system prompt to mention email capability
- [ ] Add conditional tool inclusion (only if Gmail connected)
- [ ] Test agent with Gmail tool

### Task 4.2: Update Agent Context Handling
- [ ] Pass user_id in agent context
- [ ] Ensure tool can access user context
- [ ] Handle missing context gracefully
- [ ] Test context flow end-to-end

---

## Phase 5: Frontend Dashboard UI

### Task 5.1: Create Gmail API Client
- [ ] Create frontend/lib/gmail-api.ts
- [ ] Implement getGmailAuthUrl() function
- [ ] Implement getGmailStatus() function
- [ ] Implement disconnectGmail() function
- [ ] Implement getRecipientEmail() function
- [ ] Implement updateRecipientEmail(email) function
- [ ] Add proper error handling and types

### Task 5.2: Create Connect Tools Section Component
- [ ] Create frontend/app/dashboard/components/ConnectToolsSection.tsx
- [ ] Design Gmail connection card UI
- [ ] Implement "Connect Gmail" button with popup flow
- [ ] Implement connection status display
- [ ] Implement "Disconnect" button
- [ ] Implement recipient email input form
- [ ] Add validation for email input
- [ ] Add loading states
- [ ] Add success/error toast notifications

### Task 5.3: Create OAuth Callback Page
- [ ] Create frontend/app/auth/gmail/callback/page.tsx
- [ ] Handle OAuth redirect parameters
- [ ] Show loading state during processing
- [ ] Post message to parent window on success
- [ ] Handle and display errors
- [ ] Auto-close or redirect on completion

### Task 5.4: Update Dashboard Page
- [ ] Import ConnectToolsSection component
- [ ] Add "Connect Tools" section to dashboard layout
- [ ] Position appropriately in dashboard flow
- [ ] Ensure responsive design
- [ ] Test on mobile viewport

---

## Phase 6: Testing & Quality Assurance

### Task 6.1: Backend Testing
- [ ] Run all unit tests
- [ ] Run all integration tests
- [ ] Test OAuth flow with mocked Google
- [ ] Test token refresh logic
- [ ] Test Gmail send with mocked API
- [ ] Test error scenarios

### Task 6.2: Frontend Testing
- [ ] Test OAuth popup flow
- [ ] Test callback handling
- [ ] Test status display updates
- [ ] Test recipient email saving
- [ ] Test disconnect flow
- [ ] Test on Chrome, Firefox, Safari

### Task 6.3: End-to-End Testing
- [ ] Test complete OAuth flow with real Google account
- [ ] Test sending email via agent
- [ ] Test token expiry and refresh
- [ ] Test disconnect and reconnect
- [ ] Test with expired/revoked tokens

### Task 6.4: Security Review
- [ ] Verify tokens are encrypted in database
- [ ] Verify state parameter prevents CSRF
- [ ] Verify no tokens exposed in API responses
- [ ] Verify HTTPS used for all OAuth calls
- [ ] Review error messages for information leakage

---

## Phase 7: Documentation & Deployment

### Task 7.1: Update Documentation
- [ ] Update README with Gmail integration info
- [ ] Document environment variables needed
- [ ] Document Google Cloud Console setup steps
- [ ] Add troubleshooting section
- [ ] Update CLAUDE.md if needed

### Task 7.2: Create Google Cloud Setup Guide
- [ ] Document creating Google Cloud project
- [ ] Document enabling Gmail API
- [ ] Document creating OAuth2 credentials
- [ ] Document configuring consent screen
- [ ] Document setting redirect URIs

### Task 7.3: Deployment Preparation
- [ ] Update deployment environment variables
- [ ] Update production redirect URIs
- [ ] Test in staging environment
- [ ] Create rollback plan
- [ ] Deploy to production

---

## Task Dependencies

```
Phase 1 (Config) ──┬──> Phase 2 (OAuth) ──> Phase 3 (Service) ──> Phase 4 (Agent)
                   │
                   └──> Phase 5 (Frontend) ──────────────────────────────────────┐
                                                                                  │
                                                      Phase 6 (Testing) <─────────┘
                                                             │
                                                             v
                                                      Phase 7 (Docs)
```

---

## Estimated Effort

| Phase | Tasks | Estimated Hours |
|-------|-------|-----------------|
| Phase 1 | 4 | 2-3 hours |
| Phase 2 | 3 | 4-6 hours |
| Phase 3 | 2 | 3-4 hours |
| Phase 4 | 2 | 2-3 hours |
| Phase 5 | 4 | 4-6 hours |
| Phase 6 | 4 | 3-4 hours |
| Phase 7 | 3 | 2-3 hours |
| **Total** | **22** | **20-29 hours** |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Google OAuth approval delays | Use test users during development |
| Token refresh failures | Implement robust retry with exponential backoff |
| Gmail API rate limits | Add rate limiting on our side |
| Frontend popup blocked | Fall back to redirect flow |
| Database migration issues | Test migration on copy of prod data |
