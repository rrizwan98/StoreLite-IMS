# Gmail Tool Integration Specification

**Version**: 1.0.0
**Date**: December 16, 2025
**Status**: Draft
**Branch**: `010-gmail-tool-integration`

---

## 1. Overview

### 1.1 Goal
Integrate Gmail Send Message tool with the Schema Agent, enabling users to send any agent response via email. The integration includes OAuth2 authentication flow for seamless Gmail account connection from the dashboard.

### 1.2 Problem Statement
Users currently interact with the Schema Agent to query their databases and receive analytical responses. However, they have no way to share these responses via email directly from the application. This feature bridges that gap by:
1. Allowing users to connect their Gmail account via OAuth2
2. Storing recipient email preferences for convenience
3. Enabling the agent to send responses to the user's specified email recipient

### 1.3 Success Criteria
- [ ] User can connect Gmail account via OAuth2 from dashboard
- [ ] OAuth2 tokens persist across sessions (no re-auth needed)
- [ ] User can specify default recipient email address
- [ ] Schema Agent can send any response via Gmail tool
- [ ] Seamless UX with "Sign with Google" button
- [ ] Secure token storage in database

---

## 2. Requirements

### 2.1 Functional Requirements

#### FR-1: Gmail OAuth2 Connection
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | User can initiate Gmail OAuth2 flow from Dashboard "Connect Tools" section | Must Have |
| FR-1.2 | System redirects to Google consent screen with required scopes | Must Have |
| FR-1.3 | System handles OAuth2 callback and stores tokens securely | Must Have |
| FR-1.4 | System refreshes expired access tokens automatically | Must Have |
| FR-1.5 | User can disconnect Gmail account at any time | Must Have |
| FR-1.6 | System displays connection status (connected/disconnected) | Must Have |

#### FR-2: Recipient Email Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | User can input and save default recipient email address | Must Have |
| FR-2.2 | Recipient email is validated before saving | Must Have |
| FR-2.3 | Recipient email persists in database per user | Must Have |
| FR-2.4 | User can update recipient email at any time | Should Have |
| FR-2.5 | Agent can override recipient at send time (optional) | Nice to Have |

#### FR-3: Gmail Send Tool for Agent
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Schema Agent can invoke Gmail send tool when user requests | Must Have |
| FR-3.2 | Tool sends the specified content/response to recipient | Must Have |
| FR-3.3 | Tool uses connected user's Gmail account | Must Have |
| FR-3.4 | Tool returns confirmation message after successful send | Must Have |
| FR-3.5 | Tool handles errors gracefully (auth issues, API limits) | Must Have |
| FR-3.6 | Email includes proper subject and formatted body | Should Have |

#### FR-4: Dashboard UI
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | "Connect Tools" section visible on Dashboard | Must Have |
| FR-4.2 | "Connect Gmail" button/toggle for initiating OAuth2 | Must Have |
| FR-4.3 | Display connected Gmail account email when connected | Must Have |
| FR-4.4 | Recipient email input field with validation | Must Have |
| FR-4.5 | Save button for recipient email | Must Have |
| FR-4.6 | Visual indication of connection status (connected/not connected) | Must Have |

### 2.2 Non-Functional Requirements

| ID | Requirement | Category |
|----|-------------|----------|
| NFR-1 | OAuth2 tokens must be stored encrypted in database | Security |
| NFR-2 | Token refresh must be transparent to user | UX |
| NFR-3 | Gmail API calls must complete within 10 seconds | Performance |
| NFR-4 | System must handle Gmail API rate limits gracefully | Reliability |
| NFR-5 | OAuth2 flow must complete in under 30 seconds | Performance |
| NFR-6 | All sensitive data must use HTTPS | Security |

---

## 3. Technical Design

### 3.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
├─────────────────────────────────────────────────────────────────┤
│  Dashboard                                                       │
│  ├── Connect Tools Section                                       │
│  │   ├── Gmail Connection Card                                   │
│  │   │   ├── "Sign with Google" Button                          │
│  │   │   ├── Connected Status Display                           │
│  │   │   └── Disconnect Button                                   │
│  │   └── Recipient Email Input                                   │
│  └── Schema Agent (existing)                                     │
│       └── Uses Gmail tool when requested                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                         │
├─────────────────────────────────────────────────────────────────┤
│  Routers                                                         │
│  ├── /gmail/authorize      → Initiate OAuth2 flow               │
│  ├── /gmail/callback       → Handle OAuth2 callback             │
│  ├── /gmail/status         → Get connection status              │
│  ├── /gmail/disconnect     → Revoke and remove tokens           │
│  ├── /gmail/recipient      → Get/Set recipient email            │
│  └── /gmail/send           → Direct send (optional)             │
│                                                                  │
│  Services                                                        │
│  ├── GmailOAuth2Service    → Handle OAuth2 flow                 │
│  └── GmailService          → Send emails via API                │
│                                                                  │
│  Tools                                                           │
│  └── send_email_tool       → OpenAI Agent SDK tool              │
│                                                                  │
│  Agent Integration                                               │
│  └── SchemaQueryAgent      → Uses send_email_tool               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATABASE (PostgreSQL)                     │
├─────────────────────────────────────────────────────────────────┤
│  UserConnection (extended)                                       │
│  ├── gmail_access_token     (encrypted)                         │
│  ├── gmail_refresh_token    (encrypted)                         │
│  ├── gmail_token_expiry     (datetime)                          │
│  ├── gmail_email            (connected account email)           │
│  ├── gmail_connected_at     (datetime)                          │
│  └── gmail_recipient_email  (default recipient)                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL (Google APIs)                      │
├─────────────────────────────────────────────────────────────────┤
│  OAuth2 Authorization Server                                     │
│  └── https://accounts.google.com/o/oauth2/v2/auth               │
│                                                                  │
│  Token Endpoint                                                  │
│  └── https://oauth2.googleapis.com/token                        │
│                                                                  │
│  Gmail API v1                                                    │
│  └── https://gmail.googleapis.com/gmail/v1/users/me/messages    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Database Schema Changes

```sql
-- Extend UserConnection table with Gmail OAuth2 fields
ALTER TABLE user_connection ADD COLUMN gmail_access_token TEXT;
ALTER TABLE user_connection ADD COLUMN gmail_refresh_token TEXT;
ALTER TABLE user_connection ADD COLUMN gmail_token_expiry TIMESTAMP;
ALTER TABLE user_connection ADD COLUMN gmail_email VARCHAR(255);
ALTER TABLE user_connection ADD COLUMN gmail_connected_at TIMESTAMP;
ALTER TABLE user_connection ADD COLUMN gmail_recipient_email VARCHAR(255);
ALTER TABLE user_connection ADD COLUMN gmail_scopes TEXT[];  -- Array of granted scopes
```

### 3.3 OAuth2 Flow

```
┌──────────┐     ┌──────────┐     ┌────────────┐     ┌─────────┐
│  User    │     │ Frontend │     │  Backend   │     │ Google  │
└────┬─────┘     └────┬─────┘     └─────┬──────┘     └────┬────┘
     │                │                  │                 │
     │ Click "Connect │                  │                 │
     │ Gmail"         │                  │                 │
     │───────────────>│                  │                 │
     │                │                  │                 │
     │                │ GET /gmail/      │                 │
     │                │ authorize        │                 │
     │                │─────────────────>│                 │
     │                │                  │                 │
     │                │ Redirect URL     │                 │
     │                │<─────────────────│                 │
     │                │                  │                 │
     │ Redirect to Google consent screen │                 │
     │<───────────────────────────────────────────────────>│
     │                │                  │                 │
     │ Grant permissions                 │                 │
     │───────────────────────────────────────────────────>│
     │                │                  │                 │
     │                │ Redirect with    │                 │
     │                │ auth code        │                 │
     │<───────────────────────────────────────────────────│
     │                │                  │                 │
     │ Callback to    │                  │                 │
     │ /gmail/callback│                  │                 │
     │───────────────────────────────────>│                │
     │                │                  │                 │
     │                │                  │ Exchange code   │
     │                │                  │ for tokens      │
     │                │                  │────────────────>│
     │                │                  │                 │
     │                │                  │ Access + Refresh│
     │                │                  │ tokens          │
     │                │                  │<────────────────│
     │                │                  │                 │
     │                │                  │ Store tokens    │
     │                │                  │ in DB           │
     │                │                  │                 │
     │ Redirect to dashboard with success│                 │
     │<───────────────────────────────────│                │
     │                │                  │                 │
```

### 3.4 Gmail Scopes Required

```python
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",           # Send emails
    "https://www.googleapis.com/auth/userinfo.email",       # Get user email
    "openid"                                                 # OpenID Connect
]
```

### 3.5 API Endpoints

#### 3.5.1 Gmail Router Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/gmail/authorize` | Initiate OAuth2, return redirect URL | Yes |
| GET | `/gmail/callback` | Handle OAuth2 callback | No (state token) |
| GET | `/gmail/status` | Get Gmail connection status | Yes |
| DELETE | `/gmail/disconnect` | Disconnect Gmail account | Yes |
| GET | `/gmail/recipient` | Get saved recipient email | Yes |
| PUT | `/gmail/recipient` | Update recipient email | Yes |
| POST | `/gmail/send` | Direct send email (optional) | Yes |

#### 3.5.2 Request/Response Models

```python
# GET /gmail/authorize response
class GmailAuthorizeResponse(BaseModel):
    authorization_url: str
    state: str  # CSRF token stored in session

# GET /gmail/status response
class GmailStatusResponse(BaseModel):
    connected: bool
    email: Optional[str] = None
    connected_at: Optional[datetime] = None
    recipient_email: Optional[str] = None

# PUT /gmail/recipient request
class UpdateRecipientRequest(BaseModel):
    email: EmailStr

# POST /gmail/send request
class SendEmailRequest(BaseModel):
    to: Optional[EmailStr] = None  # Override default recipient
    subject: str
    body: str
    content_type: str = "text/plain"  # or "text/html"

# POST /gmail/send response
class SendEmailResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
```

### 3.6 Gmail Tool for Agent

```python
from agents import function_tool

@function_tool
async def send_email(
    subject: str,
    body: str,
    to_email: Optional[str] = None
) -> str:
    """
    Send an email via the user's connected Gmail account.

    Args:
        subject: Email subject line
        body: Email body content (plain text or markdown)
        to_email: Optional override recipient (uses default if not provided)

    Returns:
        Confirmation message with message ID or error details
    """
    # Implementation uses GmailService
    ...
```

### 3.7 Environment Variables

```bash
# Google OAuth2 Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/gmail/callback

# Token Encryption (for storing tokens in DB)
TOKEN_ENCRYPTION_KEY=your-32-byte-encryption-key

# Frontend URL (for OAuth callback redirect)
FRONTEND_URL=http://localhost:3000
```

---

## 4. User Experience Flow

### 4.1 Connect Gmail Flow

1. **User navigates to Dashboard**
   - Dashboard displays "Connect Tools" section
   - Gmail card shows "Not Connected" status

2. **User clicks "Connect Gmail"**
   - Button triggers OAuth2 flow
   - User is redirected to Google consent screen

3. **User authorizes on Google**
   - User sees requested permissions (send emails)
   - User clicks "Allow"

4. **Redirect back to application**
   - Backend exchanges code for tokens
   - Stores tokens in database
   - Redirects to dashboard with success message

5. **Dashboard shows connected status**
   - Gmail card shows connected email
   - Recipient email input becomes available

### 4.2 Set Recipient Email Flow

1. **User enters recipient email**
   - Input field with email validation
   - Shows validation errors inline

2. **User clicks "Save"**
   - API call to save recipient
   - Success toast notification

### 4.3 Send Email via Agent Flow

1. **User chats with Schema Agent**
   - "Show me sales by month and email this to my manager"

2. **Agent processes request**
   - Runs SQL query for sales data
   - Formats response
   - Invokes `send_email` tool

3. **Email sent confirmation**
   - Agent responds: "I've sent the sales report to [recipient]"

---

## 5. Security Considerations

### 5.1 Token Storage
- Access and refresh tokens encrypted using Fernet (AES-128)
- Encryption key stored in environment variable
- Tokens never exposed in API responses

### 5.2 OAuth2 State Parameter
- Random state token generated per auth request
- Stored in user session
- Verified on callback to prevent CSRF

### 5.3 Scope Limitations
- Only request `gmail.send` scope (minimal permissions)
- Do not request read access to emails
- Display clear permission explanation to users

### 5.4 Token Refresh
- Check token expiry before each API call
- Refresh automatically if expired
- If refresh fails, prompt user to reconnect

---

## 6. Error Handling

| Error Scenario | Handling |
|----------------|----------|
| OAuth2 cancelled by user | Show friendly message, allow retry |
| Token refresh fails | Mark as disconnected, prompt reconnect |
| Gmail API rate limit | Retry with exponential backoff |
| Invalid recipient email | Show validation error |
| Gmail send fails | Return error to agent, inform user |
| Network timeout | Retry once, then show error |

---

## 7. Testing Strategy

### 7.1 Unit Tests
- OAuth2 URL generation
- Token encryption/decryption
- Email message construction
- Recipient validation

### 7.2 Integration Tests
- Full OAuth2 flow (mocked Google)
- Token refresh flow
- Gmail send API call (mocked)
- Database CRUD for tokens

### 7.3 End-to-End Tests
- Connect Gmail flow in browser
- Send email via agent
- Disconnect and reconnect

---

## 8. Dependencies

### 8.1 Backend Dependencies
```txt
google-auth>=2.25.0
google-auth-oauthlib>=1.2.0
google-api-python-client>=2.111.0
cryptography>=41.0.0  # For token encryption
aiohttp>=3.9.0  # Async HTTP client
```

### 8.2 Frontend Dependencies
```txt
# No new dependencies - using existing auth patterns
```

---

## 9. Future Enhancements (Out of Scope)

- [ ] Support for multiple recipients (CC, BCC)
- [ ] Email attachments
- [ ] Email templates
- [ ] Schedule email sending
- [ ] Integration with other email providers (Outlook)
- [ ] Email tracking/read receipts

---

## 10. References

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Google OAuth2 for Web Apps](https://developers.google.com/identity/protocols/oauth2/web-server)
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [FastAPI OAuth2](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
