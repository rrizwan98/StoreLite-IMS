# Gmail Tool Integration - Implementation Plan

**Version**: 1.0.0
**Date**: December 16, 2025
**Spec Reference**: `specs/010-gmail-tool-integration/spec.md`

---

## 1. Implementation Phases

### Phase 1: Database & Configuration Setup
**Goal**: Extend database schema and configure Google OAuth2 credentials

#### 1.1 Database Migration
- Extend `UserConnection` model with Gmail OAuth2 fields
- Add encrypted token storage columns
- Add recipient email field
- Create Alembic migration

#### 1.2 Environment Configuration
- Add Google OAuth2 credentials to `.env`
- Add token encryption key
- Configure redirect URIs

#### 1.3 Dependencies Installation
- Install Google API client libraries
- Install cryptography for token encryption

---

### Phase 2: OAuth2 Backend Implementation
**Goal**: Complete OAuth2 authorization flow with secure token storage

#### 2.1 Token Encryption Service
```
backend/app/services/encryption_service.py
├── encrypt_token(token: str) -> str
├── decrypt_token(encrypted: str) -> str
└── generate_encryption_key() -> str  # Utility
```

#### 2.2 Gmail OAuth2 Service
```
backend/app/services/gmail_oauth_service.py
├── get_authorization_url(user_id, state) -> str
├── exchange_code_for_tokens(code) -> TokenData
├── refresh_access_token(refresh_token) -> TokenData
├── revoke_tokens(access_token) -> bool
├── get_user_email(access_token) -> str
└── save_tokens_to_db(user_id, tokens) -> None
```

#### 2.3 Gmail Router
```
backend/app/routers/gmail.py
├── GET  /gmail/authorize     → Initiate OAuth2
├── GET  /gmail/callback      → Handle callback
├── GET  /gmail/status        → Get status
├── DELETE /gmail/disconnect  → Disconnect
├── GET  /gmail/recipient     → Get recipient
└── PUT  /gmail/recipient     → Update recipient
```

---

### Phase 3: Gmail Send Service & Tool
**Goal**: Create Gmail API service and agent tool

#### 3.1 Gmail Service
```
backend/app/services/gmail_service.py
├── async send_email(
│       user_id: int,
│       to: str,
│       subject: str,
│       body: str,
│       content_type: str = "text/plain"
│   ) -> SendResult
├── async _build_message(to, subject, body, from_email) -> dict
├── async _ensure_valid_token(user_id) -> str
└── async _get_gmail_service(access_token) -> Resource
```

#### 3.2 Agent Tool Definition
```
backend/app/mcp_server/tools_gmail.py
├── @function_tool
│   async def send_email_tool(
│       context: RunContextWrapper,
│       subject: str,
│       body: str,
│       to_email: Optional[str] = None
│   ) -> str
└── Tool schema with proper descriptions
```

---

### Phase 4: Schema Agent Integration
**Goal**: Connect Gmail tool to Schema Agent

#### 4.1 Agent Tool Registration
- Modify `SchemaQueryAgent` to include Gmail tool
- Add Gmail tool to available tools list
- Update agent system prompt to mention email capability

#### 4.2 Context Handling
- Pass user context to tool for token retrieval
- Handle "not connected" scenarios gracefully
- Return helpful error messages

---

### Phase 5: Frontend Dashboard UI
**Goal**: Build Connect Tools section in Dashboard

#### 5.1 API Client Functions
```
frontend/lib/gmail-api.ts
├── getGmailAuthUrl() -> Promise<{url: string}>
├── getGmailStatus() -> Promise<GmailStatus>
├── disconnectGmail() -> Promise<void>
├── getRecipientEmail() -> Promise<{email: string}>
└── updateRecipientEmail(email: string) -> Promise<void>
```

#### 5.2 Dashboard Components
```
frontend/app/dashboard/
├── page.tsx (update with Connect Tools section)
└── components/
    └── ConnectToolsSection.tsx
        ├── GmailConnectionCard
        │   ├── ConnectButton
        │   ├── StatusBadge
        │   └── DisconnectButton
        └── RecipientEmailForm
            ├── EmailInput
            └── SaveButton
```

#### 5.3 OAuth Callback Page
```
frontend/app/auth/gmail/callback/page.tsx
├── Handle OAuth redirect
├── Show loading state
├── Redirect to dashboard on success
└── Show error on failure
```

---

## 2. File Structure

```
backend/
├── app/
│   ├── services/
│   │   ├── encryption_service.py     # NEW: Token encryption
│   │   ├── gmail_oauth_service.py    # NEW: OAuth2 handling
│   │   └── gmail_service.py          # NEW: Gmail API operations
│   ├── routers/
│   │   └── gmail.py                  # NEW: Gmail endpoints
│   ├── mcp_server/
│   │   └── tools_gmail.py            # NEW: Agent Gmail tool
│   ├── agents/
│   │   └── schema_query_agent.py     # UPDATE: Add Gmail tool
│   ├── models.py                     # UPDATE: Add Gmail fields
│   └── main.py                       # UPDATE: Register router
├── alembic/
│   └── versions/
│       └── xxx_add_gmail_oauth.py    # NEW: Migration
└── requirements.txt                  # UPDATE: Add dependencies

frontend/
├── app/
│   ├── dashboard/
│   │   ├── page.tsx                  # UPDATE: Add Connect Tools
│   │   └── components/
│   │       └── ConnectToolsSection.tsx  # NEW: UI component
│   └── auth/
│       └── gmail/
│           └── callback/
│               └── page.tsx          # NEW: OAuth callback
└── lib/
    └── gmail-api.ts                  # NEW: API client
```

---

## 3. Implementation Order

```
Week 1: Foundation
├── Day 1-2: Phase 1 (Database & Config)
│   ├── Install dependencies
│   ├── Create migration
│   ├── Update models
│   └── Configure environment
│
├── Day 3-4: Phase 2 (OAuth2 Backend)
│   ├── Encryption service
│   ├── OAuth2 service
│   └── Gmail router
│
└── Day 5: Phase 3 (Gmail Service)
    ├── Gmail send service
    └── Basic testing

Week 2: Integration & UI
├── Day 1-2: Phase 3-4 (Tool & Agent)
│   ├── Agent tool definition
│   ├── Agent integration
│   └── Tool testing
│
├── Day 3-4: Phase 5 (Frontend)
│   ├── API client
│   ├── UI components
│   └── OAuth callback page
│
└── Day 5: Testing & Polish
    ├── E2E testing
    ├── Error handling
    └── Documentation
```

---

## 4. Key Design Decisions

### 4.1 Token Storage Strategy
**Decision**: Store encrypted tokens in `UserConnection` table
**Rationale**:
- Single source of truth for user connections
- Already has user relationship
- Easy to extend for other tools later

### 4.2 OAuth2 Flow Type
**Decision**: Authorization Code Flow (server-side)
**Rationale**:
- More secure than implicit flow
- Refresh tokens available
- Standard for web applications

### 4.3 Tool Context Passing
**Decision**: Use `RunContextWrapper` to pass user context
**Rationale**:
- OpenAI Agents SDK pattern
- Access to user_id for token retrieval
- Clean separation of concerns

### 4.4 Frontend OAuth Handling
**Decision**: Popup window for OAuth (not redirect)
**Rationale**:
- Better UX - user stays on dashboard
- No loss of application state
- Standard pattern for OAuth

---

## 5. Critical Implementation Details

### 5.1 Token Refresh Logic
```python
async def _ensure_valid_token(self, user_id: int) -> str:
    """Get valid access token, refreshing if needed."""
    connection = await self.get_user_connection(user_id)

    if not connection.gmail_access_token:
        raise GmailNotConnectedError("Gmail not connected")

    # Check if token expired (with 5 min buffer)
    if connection.gmail_token_expiry < datetime.utcnow() + timedelta(minutes=5):
        # Refresh token
        new_tokens = await self.refresh_access_token(
            decrypt_token(connection.gmail_refresh_token)
        )
        await self.save_tokens_to_db(user_id, new_tokens)
        return new_tokens.access_token

    return decrypt_token(connection.gmail_access_token)
```

### 5.2 Agent Tool Error Handling
```python
@function_tool
async def send_email_tool(
    context: RunContextWrapper,
    subject: str,
    body: str,
    to_email: Optional[str] = None
) -> str:
    try:
        user_id = context.context.get("user_id")
        result = await gmail_service.send_email(user_id, to_email, subject, body)
        return f"Email sent successfully! Message ID: {result.message_id}"
    except GmailNotConnectedError:
        return "Gmail is not connected. Please connect your Gmail account in the dashboard settings."
    except GmailSendError as e:
        return f"Failed to send email: {str(e)}"
```

### 5.3 Frontend Popup OAuth
```typescript
const handleConnectGmail = async () => {
  try {
    const { url } = await getGmailAuthUrl();

    // Open popup
    const popup = window.open(
      url,
      'gmail-oauth',
      'width=500,height=600,left=100,top=100'
    );

    // Listen for callback message
    window.addEventListener('message', (event) => {
      if (event.data.type === 'GMAIL_OAUTH_SUCCESS') {
        popup?.close();
        refreshStatus();
        toast.success('Gmail connected successfully!');
      }
    });
  } catch (error) {
    toast.error('Failed to start Gmail connection');
  }
};
```

---

## 6. Testing Strategy

### 6.1 Unit Tests
```
tests/
├── test_encryption_service.py
│   ├── test_encrypt_decrypt_roundtrip
│   └── test_invalid_key_error
├── test_gmail_oauth_service.py
│   ├── test_authorization_url_generation
│   ├── test_token_exchange
│   └── test_token_refresh
└── test_gmail_service.py
    ├── test_message_building
    └── test_send_email_success
```

### 6.2 Integration Tests
```
tests/integration/
├── test_oauth_flow.py
│   ├── test_full_oauth_flow_mocked
│   └── test_callback_with_invalid_state
├── test_gmail_endpoints.py
│   └── test_status_connected_user
└── test_agent_gmail_tool.py
    └── test_agent_sends_email
```

### 6.3 Mocking Strategy
- Mock Google OAuth2 endpoints for testing
- Mock Gmail API for send operations
- Use pytest-asyncio for async tests

---

## 7. Rollback Plan

If issues arise:

1. **Database**: Migration includes down migration
2. **Backend**: New files can be removed, router unregistered
3. **Frontend**: Component is isolated, can be hidden
4. **Agent**: Tool can be removed from agent config

---

## 8. Monitoring & Logging

### 8.1 Key Metrics
- OAuth2 success/failure rate
- Token refresh rate
- Email send success rate
- API response times

### 8.2 Logging
```python
logger.info(f"Gmail OAuth2 initiated for user {user_id}")
logger.info(f"Gmail tokens saved for user {user_id}")
logger.error(f"Gmail send failed for user {user_id}: {error}")
logger.warning(f"Gmail token refresh failed for user {user_id}")
```

---

## 9. Dependencies to Install

```bash
# Backend
pip install google-auth google-auth-oauthlib google-api-python-client cryptography

# Or add to requirements.txt
google-auth>=2.25.0
google-auth-oauthlib>=1.2.0
google-api-python-client>=2.111.0
cryptography>=41.0.0
```

---

## 10. Next Steps After Implementation

1. Create Google Cloud Project and OAuth2 credentials
2. Configure consent screen with proper scopes
3. Test with real Gmail account
4. Document user setup process
5. Consider additional email features (templates, attachments)
