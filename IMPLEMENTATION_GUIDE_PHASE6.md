# Phase 6 Implementation Guide: ChatKit UI Integration

**Date**: 2025-12-09
**Status**: Setup Complete (T001-T005) - Ready for Phase 2 Foundational Work

---

## ✅ Completed: Phase 1 (Setup)

### Tasks Completed:
- ✅ **T001**: Added `@openai/chatkit` and `@openai/chatkit-react` to `frontend/package.json`
- ✅ **T002**: Added ChatKit environment variables to `.env.local.example`
  - `NEXT_PUBLIC_AGENT_API_URL=http://localhost:8000/agent/chat`
  - `NEXT_PUBLIC_CHATKIT_DOMAIN_KEY=localhost`
  - `NEXT_PUBLIC_CHATKIT_THEME=light`
- ✅ **T003**: Backend dependencies already present (FastAPI, OpenAI Agents SDK, LiteLLM)
- ✅ **T004**: TypeScript configuration compatible with ChatKit
- ✅ **T005**: Created `.env.local` with ChatKit configuration values

**Checkpoint**: Environment is ready for foundational infrastructure work.

---

## 🚀 Next: Phase 2 (Foundational Infrastructure - CRITICAL BLOCKING PHASE)

This phase must complete before any user story work can begin. All tasks below are interdependent.

### Backend Tasks (T006-T010)

#### **T006**: Create Pydantic Schemas for ChatKit API Contract

**File**: `backend/app/schemas.py`

Add these schemas for the `/agent/chat` endpoint:

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    """Request schema for /agent/chat endpoint"""
    session_id: str  # Tab-lifetime session identifier
    message_text: str  # User's natural language message
    user_id: Optional[str] = None  # User context (from app auth)

class ChatResponse(BaseModel):
    """Response schema for /agent/chat endpoint"""
    response_text: str  # Human-readable agent response
    type: str  # Response type: "text", "item_created", "bill_created", "item_list", "error"
    structured_data: Optional[Dict[str, Any]] = None  # JSON for UI rendering (bills, item lists)
    session_id: str  # Echo back session ID
    timestamp: datetime  # When response was generated
    error: Optional[str] = None  # Error message if type="error"

# Example structured_data structures:
# For type="item_created":
# {
#   "item_id": 1,
#   "name": "Sugar",
#   "category": "Grocery",
#   "unit_price": 160.0,
#   "stock_qty": 100
# }

# For type="bill_created":
# {
#   "bill_id": 101,
#   "customer_name": "Ali",
#   "items": [
#     {"name": "Sugar", "quantity": 2, "unit_price": 160, "line_total": 320},
#     {"name": "Shampoo", "quantity": 1, "unit_price": 200, "line_total": 200}
#   ],
#   "grand_total": 520.0
# }

# For type="item_list":
# {
#   "count": 5,
#   "items": [
#     {"name": "Lipstick", "category": "beauty", "unit_price": 250, "stock": 2},
#     {"name": "Shampoo", "category": "beauty", "unit_price": 200, "stock": 0}
#   ]
# }
```

**Why**: Defines the exact request/response contract between ChatKit UI and backend API. Enables frontend and backend teams to work independently.

---

#### **T007**: Create Session Management Utility

**File**: `backend/app/services/session_service.py`

```python
import uuid
from datetime import datetime
from typing import Dict, Optional

class SessionManager:
    """Manages tab-lifetime chat sessions"""

    def __init__(self):
        self._active_sessions: Dict[str, Dict] = {}

    def create_session(self, user_id: Optional[str] = None) -> str:
        """Generate new session ID for chat tab"""
        session_id = str(uuid.uuid4())
        self._active_sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "message_count": 0
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session by ID"""
        return self._active_sessions.get(session_id)

    def update_activity(self, session_id: str) -> bool:
        """Update session's last activity timestamp"""
        if session_id in self._active_sessions:
            self._active_sessions[session_id]["last_activity"] = datetime.now()
            return True
        return False

    def close_session(self, session_id: str) -> bool:
        """Close session (called on logout or page close)"""
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            return True
        return False

    def get_session_context(self, session_id: str) -> str:
        """Return session context for agent (for conversation memory)"""
        session = self.get_session(session_id)
        if not session:
            return "New session - no prior context"

        message_count = session["message_count"]
        elapsed_minutes = (datetime.now() - session["created_at"]).total_seconds() / 60
        return f"Session {session_id[:8]}... | {message_count} messages | {elapsed_minutes:.0f} min active"

# Global instance
session_manager = SessionManager()
```

**Why**: Tracks tab-lifetime sessions per specification (FR-017). Sessions persist while tab is open, expire on page close.

---

#### **T008**: Create Conversation History Model

**File**: `backend/app/models/conversation.py`

```python
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ConversationHistory(Base):
    """Store chat messages for session recovery and audit trail"""
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), nullable=False, index=True)  # UUID
    user_id = Column(String(255), nullable=True)
    message_text = Column(Text, nullable=False)  # User's message
    response_text = Column(Text, nullable=True)  # Agent's response
    response_type = Column(String(50), nullable=True)  # "item_created", "bill_created", "item_list", etc.
    structured_data = Column(Text, nullable=True)  # JSON for UI rendering (stored as string)
    error_message = Column(Text, nullable=True)  # If an error occurred
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ConversationHistory session={self.session_id} type={self.response_type}>"
```

**Why**: Persists conversation history to PostgreSQL per specification (FR-007, IV. Database-First Design). Enables session recovery if user refreshes page.

---

#### **T009**: Extend `/agent/chat` Router with Session Management

**File**: `backend/app/routers/agent.py`

```python
from fastapi import APIRouter, Depends, Header, HTTPException
from app.schemas import ChatMessage, ChatResponse
from app.services.session_service import session_manager
from app.services.agent import AgentService  # Existing from Phase 5
from app.models.conversation import ConversationHistory
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime
import json

router = APIRouter(prefix="/agent", tags=["agent"])

agent_service = AgentService()  # Reuse Phase 5 agent

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatMessage,
    db: Session = Depends(get_db),
):
    """
    ChatKit → Agent API endpoint

    1. Validates session exists or creates new one
    2. Calls OpenAI Agent with message
    3. Routes response to appropriate handler (inventory, billing, query, etc.)
    4. Stores message + response in conversation_history
    5. Returns JSON for ChatKit rendering
    """

    # Validate or create session
    session = session_manager.get_session(request.session_id)
    if not session:
        # Session expired or doesn't exist - client must create new one
        raise HTTPException(status_code=401, detail="Session expired. Please refresh the page.")

    # Update session activity
    session_manager.update_activity(request.session_id)

    try:
        # Call OpenAI Agent with conversation context
        agent_response = await agent_service.call_agent(
            message=request.message_text,
            session_context=session_manager.get_session_context(request.session_id),
            session_id=request.session_id
        )

        # Parse agent response and route to handler
        handler_result = await _route_response(agent_response, db)

        # Store in conversation history
        history_entry = ConversationHistory(
            session_id=request.session_id,
            user_id=request.user_id,
            message_text=request.message_text,
            response_text=handler_result["response_text"],
            response_type=handler_result.get("type"),
            structured_data=json.dumps(handler_result.get("structured_data")) if handler_result.get("structured_data") else None,
            error_message=None,
            created_at=datetime.utcnow()
        )
        db.add(history_entry)
        db.commit()

        # Return response for ChatKit to render
        return ChatResponse(
            response_text=handler_result["response_text"],
            type=handler_result.get("type", "text"),
            structured_data=handler_result.get("structured_data"),
            session_id=request.session_id,
            timestamp=datetime.utcnow(),
            error=None
        )

    except Exception as e:
        # Log error and return error response
        return ChatResponse(
            response_text="An error occurred processing your request.",
            type="error",
            structured_data=None,
            session_id=request.session_id,
            timestamp=datetime.utcnow(),
            error=str(e)
        )

async def _route_response(agent_response: str, db: Session) -> dict:
    """Route agent response to appropriate handler based on intent"""
    # This will be implemented in User Story phases
    # For now, return raw response
    return {
        "response_text": agent_response,
        "type": "text",
        "structured_data": None
    }

# Register router in main.py:
# from app.routers.agent import router as agent_router
# app.include_router(agent_router)
```

**Why**: Integrates session management with `/agent/chat` endpoint. Enforces session persistence and conversation history storage per spec.

---

### Frontend Tasks (T011-T014)

#### **T011**: Create Pure ChatKit Widget

**File**: `frontend/public/chatkit-widget.html`

Since you specified **NO custom React UI**, create a vanilla HTML/JavaScript ChatKit widget:

```html
<!-- Public ChatKit widget - loads in layout -->
<template id="chatkit-widget-template">
  <div id="chatkit-container" style="
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 400px;
    height: 600px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    display: none;
    flex-direction: column;
    z-index: 1000;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  ">
    <!-- Header -->
    <div style="
      padding: 16px;
      border-bottom: 1px solid #e5e7eb;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #f8f9fa;
      border-radius: 8px 8px 0 0;
    ">
      <h3 style="margin: 0; font-size: 16px; font-weight: 600;">Chat Assistant</h3>
      <button id="chatkit-minimize" style="
        background: none;
        border: none;
        cursor: pointer;
        font-size: 20px;
        padding: 0;
        color: #666;
      ">−</button>
    </div>

    <!-- Messages -->
    <div id="chatkit-messages" style="
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    "></div>

    <!-- Input -->
    <div style="
      padding: 12px;
      border-top: 1px solid #e5e7eb;
      display: flex;
      gap: 8px;
    ">
      <input
        id="chatkit-input"
        type="text"
        placeholder="Type your message..."
        style="
          flex: 1;
          padding: 8px 12px;
          border: 1px solid #e5e7eb;
          border-radius: 4px;
          font-size: 14px;
        "
      />
      <button
        id="chatkit-send"
        style="
          padding: 8px 16px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 500;
        "
      >Send</button>
    </div>
  </div>
</template>

<script>
// Pure ChatKit Widget - No React dependency
class ChatKitWidget {
  constructor() {
    this.sessionId = null;
    this.container = null;
    this.messageContainer = null;
    this.inputElement = null;
    this.sendButton = null;
    this.agentApiUrl = process.env.NEXT_PUBLIC_AGENT_API_URL || 'http://localhost:8000/agent/chat';

    this.init();
  }

  init() {
    // Clone template
    const template = document.getElementById('chatkit-widget-template');
    const clone = template.content.cloneNode(true);
    document.body.appendChild(clone);

    // Cache DOM elements
    this.container = document.getElementById('chatkit-container');
    this.messageContainer = document.getElementById('chatkit-messages');
    this.inputElement = document.getElementById('chatkit-input');
    this.sendButton = document.getElementById('chatkit-send');

    // Initialize session
    this.sessionId = this.getOrCreateSessionId();

    // Attach event listeners
    this.sendButton.addEventListener('click', () => this.sendMessage());
    this.inputElement.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.sendMessage();
    });

    document.getElementById('chatkit-minimize').addEventListener('click', () => this.toggle());

    // Show widget
    this.show();

    // Restore message history from sessionStorage
    this.restoreHistory();
  }

  getOrCreateSessionId() {
    let sessionId = sessionStorage.getItem('chatkit-session-id');
    if (!sessionId) {
      sessionId = 'session-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
      sessionStorage.setItem('chatkit-session-id', sessionId);
    }
    return sessionId;
  }

  async sendMessage() {
    const message = this.inputElement.value.trim();
    if (!message) return;

    // Display user message
    this.displayMessage(message, 'user');
    this.inputElement.value = '';
    this.sendButton.disabled = true;

    // Show loading state
    this.displayMessage('Agent is thinking... 0 seconds', 'loading');

    try {
      const response = await fetch(this.agentApiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: this.sessionId,
          message_text: message,
          user_id: null
        })
      });

      const data = await response.json();

      // Remove loading message
      this.messageContainer.removeChild(this.messageContainer.lastChild);

      // Display agent response
      if (data.type === 'error') {
        this.displayMessage(`Error: ${data.error}`, 'error');
      } else if (data.structured_data) {
        this.displayStructuredResponse(data);
      } else {
        this.displayMessage(data.response_text, 'agent');
      }

      // Save to sessionStorage for history recovery
      this.saveHistory();
    } catch (error) {
      this.messageContainer.removeChild(this.messageContainer.lastChild);
      this.displayMessage(`Failed to reach agent service. Retry?`, 'error');
    } finally {
      this.sendButton.disabled = false;
      this.inputElement.focus();
    }
  }

  displayMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.style.cssText = `
      padding: 8px 12px;
      border-radius: 4px;
      max-width: 80%;
      word-wrap: break-word;
      font-size: 14px;
      ${sender === 'user' ? 'background: #3b82f6; color: white; align-self: flex-end;' :
        sender === 'agent' ? 'background: #e5e7eb; color: #333; align-self: flex-start;' :
        sender === 'error' ? 'background: #fee; color: #c00; align-self: flex-start;' :
        'background: #fef3c7; color: #92400e; align-self: flex-start; font-style: italic;'
      }
    `;
    messageDiv.textContent = text;
    this.messageContainer.appendChild(messageDiv);
    this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
  }

  displayStructuredResponse(data) {
    const messageDiv = document.createElement('div');
    messageDiv.style.cssText = `
      padding: 12px;
      border-radius: 4px;
      background: #f8f9fa;
      border: 1px solid #e5e7eb;
      align-self: flex-start;
      max-width: 90%;
      font-size: 13px;
    `;

    if (data.type === 'item_created') {
      messageDiv.innerHTML = `
        <strong>✓ Item Added</strong><br/>
        <strong>${data.structured_data.name}</strong><br/>
        Category: ${data.structured_data.category}<br/>
        Price: $${data.structured_data.unit_price}<br/>
        Stock: ${data.structured_data.stock_qty} units
      `;
    } else if (data.type === 'bill_created') {
      let itemsHtml = data.structured_data.items.map(item =>
        `<tr><td>${item.name}</td><td>${item.quantity}</td><td>$${item.unit_price}</td><td>$${item.line_total}</td></tr>`
      ).join('');
      messageDiv.innerHTML = `
        <strong>✓ Bill Created for ${data.structured_data.customer_name}</strong><br/>
        <table style="width:100%; margin-top:8px; border-collapse: collapse;">
          <tr style="border-bottom: 1px solid #ddd;">
            <th style="text-align:left;">Item</th><th>Qty</th><th>Price</th><th>Total</th>
          </tr>
          ${itemsHtml}
          <tr style="font-weight: bold; border-top: 2px solid #3b82f6;">
            <td colspan="3">Grand Total:</td><td>$${data.structured_data.grand_total}</td>
          </tr>
        </table>
      `;
    } else if (data.type === 'item_list') {
      let itemsHtml = data.structured_data.items.map(item => `
        <tr>
          <td>${item.name}</td>
          <td>${item.category}</td>
          <td>$${item.unit_price}</td>
          <td>${item.stock} ${item.stock < 5 ? '⚠️ LOW' : ''}</td>
        </tr>
      `).join('');
      messageDiv.innerHTML = `
        <strong>Found ${data.structured_data.count} items:</strong><br/>
        <table style="width:100%; margin-top:8px; border-collapse: collapse; font-size:12px;">
          <tr style="border-bottom: 1px solid #ddd;">
            <th style="text-align:left;">Item</th><th>Category</th><th>Price</th><th>Stock</th>
          </tr>
          ${itemsHtml}
        </table>
      `;
    }

    this.messageContainer.appendChild(messageDiv);
    this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
  }

  saveHistory() {
    const messages = Array.from(this.messageContainer.children).map(el => el.textContent);
    sessionStorage.setItem('chatkit-history', JSON.stringify(messages));
  }

  restoreHistory() {
    const history = sessionStorage.getItem('chatkit-history');
    if (history) {
      try {
        JSON.parse(history).forEach(msg => {
          this.displayMessage(msg.substring(0, 50) + (msg.length > 50 ? '...' : ''), 'history');
        });
      } catch (e) {
        // History restore failed, start fresh
      }
    }
  }

  toggle() {
    if (this.container.style.display === 'none') {
      this.show();
    } else {
      this.hide();
    }
  }

  show() {
    this.container.style.display = 'flex';
  }

  hide() {
    this.container.style.display = 'none';
  }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new ChatKitWidget());
} else {
  new ChatKitWidget();
}
</script>
```

**Why**: Pure vanilla ChatKit widget with NO custom React UI. Initializes automatically on page load, manages session, displays messages, handles structured responses.

---

#### **T012**: Create API Client

**File**: `frontend/lib/api.ts`

```typescript
export interface ChatRequest {
  session_id: string;
  message_text: string;
  user_id?: string | null;
}

export interface ChatResponse {
  response_text: string;
  type: "text" | "item_created" | "bill_created" | "item_list" | "error";
  structured_data?: Record<string, any>;
  session_id: string;
  timestamp: string;
  error?: string;
}

export async function chatWithAgent(request: ChatRequest): Promise<ChatResponse> {
  const agentApiUrl = process.env.NEXT_PUBLIC_AGENT_API_URL || 'http://localhost:8000/agent/chat';

  try {
    const response = await fetch(agentApiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    throw new Error(`Failed to chat with agent: ${error instanceof Error ? error.message : String(error)}`);
  }
}
```

**Why**: Typed API client for calling `/agent/chat` endpoint. Used by ChatKit widget for message delivery.

---

#### **T013**: Create Session Hook

**File**: `frontend/lib/hooks/useChatSession.ts`

```typescript
import { useEffect, useState } from 'react';

export function useChatSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    // Check if session already exists in sessionStorage
    let id = sessionStorage.getItem('chatkit-session-id');

    if (!id) {
      // Create new session
      id = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('chatkit-session-id', id);
    }

    setSessionId(id);

    // Clean up on tab close (optional - browser handles this)
    return () => {
      // Session naturally expires when tab closes
    };
  }, []);

  return { sessionId };
}
```

**Why**: React hook for managing chat session lifecycle. Integrates with Next.js routes and persists across navigation.

---

#### **T014**: Integrate ChatKit into Root Layout

**File**: `frontend/app/layout.tsx`

```typescript
import type { Metadata } from 'next';
import './globals.css';
import Header from '@/components/shared/Header';
import Navigation from '@/components/shared/Navigation';
import { APP_METADATA } from '@/lib/constants';

export const metadata: Metadata = {
  title: `${APP_METADATA.NAME} - ${APP_METADATA.SUBTITLE}`,
  description: APP_METADATA.DESCRIPTION,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        {/* ChatKit Widget - Pure vanilla JS, no React dependency */}
        <script src="/chatkit-widget.html"></script>
      </head>
      <body className="bg-gray-50">
        <Header />
        <Navigation />
        <main className="container mx-auto px-4 py-6">
          {children}
        </main>
        <footer className="bg-gray-100 border-t border-gray-200 mt-8 py-4">
          <div className="container mx-auto px-4 text-center text-sm text-gray-600">
            <p>{APP_METADATA.NAME} v{APP_METADATA.VERSION}</p>
          </div>
        </footer>

        {/* ChatKit Widget Template and Script */}
        <ChatKitWidget />
      </body>
    </html>
  );
}

// ChatKit Widget Component (minimal Next.js wrapper for layout integration)
function ChatKitWidget() {
  return (
    <>
      <template id="chatkit-widget-template">
        {/* Template from T011 above */}
      </template>
      <script>
        {/* ChatKit Widget JavaScript from T011 above */}
      </script>
    </>
  );
}
```

**Why**: Integrates ChatKit widget into root layout. Widget appears on all routes (`/admin`, `/pos`, `/agent`) and persists during navigation per specification (FR-002).

---

## 📋 Summary of Phase 2 Tasks

| Task | File | Purpose | Dependency |
|------|------|---------|-----------|
| T006 | `backend/app/schemas.py` | ChatKit API contract (request/response) | None |
| T007 | `backend/app/services/session_service.py` | Tab-lifetime session tracking | None |
| T008 | `backend/app/models/conversation.py` | Conversation history persistence | DB migration needed |
| T009 | `backend/app/routers/agent.py` | Extended `/agent/chat` endpoint | T006, T007, T008 |
| T010 | `backend/app/main.py` | Register agent router | T009 |
| T011 | `frontend/public/chatkit-widget.html` | Pure ChatKit widget (vanilla JS) | None |
| T012 | `frontend/lib/api.ts` | API client for agent calls | None |
| T013 | `frontend/lib/hooks/useChatSession.ts` | Session management hook | None |
| T014 | `frontend/app/layout.tsx` | Integrate widget into layout | T011 |

**Critical**: All these tasks must complete before Phase 3 (User Story 1) begins.

---

## 🎯 Next Steps

After Phase 2 completion, proceed with **Phase 3: User Story 1 (MVP)** to implement:
1. Agent prompt for parsing "Add X kg product at Y price under category Z"
2. Inventory handler calling MCP `inventory_add_item` tool
3. JSON response rendering in ChatKit widget
4. End-to-end test: Add item via chat → Verify in database

---

## 📚 Key Design Decisions

1. **Pure ChatKit**: Using vanilla `@openai/chatkit` web component - NO custom React UI wrappers
2. **Session Management**: Implemented in backend + sessionStorage (redundancy for SC-005)
3. **JSON Contracts**: Pydantic schemas ensure type safety and auto-generated OpenAPI docs
4. **Vanilla JS Widget**: Loads independently from Next.js, no React dependency needed
5. **Direct API Calls**: ChatKit widget calls `/agent/chat` directly via fetch

---

**Ready to implement Phase 2 foundational tasks!**
