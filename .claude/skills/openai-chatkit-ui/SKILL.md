---
name: openai-chatkit-ui
description: >
  Connect AI agents to frontend UI using OpenAI ChatKit SDK with CUSTOM BACKEND (FastAPI).
  This skill is for Custom ChatKit (your own backend), NOT Managed ChatKit (OpenAI Agent ID).
  Use when: integrating ChatKit with FastAPI, adding chat UI to existing apps, connecting
  ChatKit to custom AI agents. CRITICAL: Use pure official ChatKit web component from CDN.
  Backend uses chatkit.server.ChatKitServer Python SDK. NO custom UI code.
  Triggers: ChatKit, chat UI, agent UI, embed chat, FastAPI chat, custom backend chat.
---

# OpenAI ChatKit UI Integration (Custom Backend)

Connect your **FastAPI backend** to ChatKit frontend using **Custom ChatKit** approach.

> ⚠️ **This skill is for Custom ChatKit with your own backend (FastAPI).**
> For Managed ChatKit with OpenAI Agent ID, see: https://platform.openai.com/docs/guides/chatkit

## Two ChatKit Approaches - Know the Difference!

| Approach | When to Use | Backend | Docs |
|----------|-------------|---------|------|
| **Managed ChatKit** | Using OpenAI Agent Builder | OpenAI hosted (needs Agent ID) | [Managed Guide](https://platform.openai.com/docs/guides/chatkit) |
| **Custom ChatKit** | Using your own backend (FastAPI, etc.) | Your server + ChatKitServer SDK | [Custom Guide](https://platform.openai.com/docs/guides/custom-chatkit) |

### ⚠️ This Skill is for CUSTOM ChatKit (FastAPI Backend)

If you need **Managed ChatKit** with OpenAI Agent ID, use the starter template:
```bash
git clone https://github.com/openai/openai-chatkit-starter-app
cd openai-chatkit-starter-app/managed-chatkit
```

**For Custom ChatKit (this skill):**
- DO NOT clone the starter template
- Follow the patterns in this skill
- Use `chatkit.server.ChatKitServer` Python SDK
- Connect to your FastAPI backend

**Template Structure:**
```
openai-chatkit-starter-app/
├── chatkit/                    # Self-hosted ChatKit (use this)
│   ├── frontend/               # Next.js frontend with ChatKit
│   └── backend/                # Python FastAPI backend
└── managed-chatkit/            # Managed (OpenAI hosted) version
```

## Critical Rules (MUST FOLLOW)

1. **🚨 CUSTOM BACKEND** - This skill is for Custom ChatKit with FastAPI backend (NOT OpenAI Agent ID)
2. **CDN ONLY** - Load ChatKit from CDN, never `npm install @openai/chatkit` (it's only types!)
3. **PURE CHATKIT** - Use only official `<openai-chatkit>` web component
4. **NO CUSTOM UI** - Never write custom chat UI code
5. **CORRECT CDN URL** - Use exactly: `https://cdn.platform.openai.com/deployments/chatkit/chatkit.js`
6. **CHATKIT SERVER SDK** - Backend must use `chatkit.server.ChatKitServer` and `Store` classes

## Official Documentation & Resources

| Resource | URL | Notes |
|----------|-----|-------|
| **Custom ChatKit Guide** | https://platform.openai.com/docs/guides/custom-chatkit | **USE THIS** (our approach) |
| Managed ChatKit Docs | https://platform.openai.com/docs/guides/chatkit | For OpenAI Agent ID (NOT us) |
| Starter Template | https://github.com/openai/openai-chatkit-starter-app | For Managed only, NOT Custom |
| ChatKit Python SDK | `pip install chatkit` | For backend ChatKitServer |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js/React)                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │    <openai-chatkit> Web Component (from CDN)          │  │
│  │    Loaded via: cdn.platform.openai.com/...            │  │
│  │    Configured via: element.setOptions({...})          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST (SSE Streaming)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND (Python FastAPI)                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  ChatKitServer (from chatkit.server)                    ││
│  │  ├── Store: Thread/Item persistence                     ││
│  │  ├── respond(): Process messages, yield events         ││
│  │  └── process(): Handle ChatKit protocol                ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                               │
│                              ▼                               │
│                    ┌─────────────────┐                       │
│                    │  Your AI Agent  │                       │
│                    │  (OpenAI, etc)  │                       │
│                    └─────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚨 COMMON ERRORS AND FIXES

### Error 1: `@openai/chatkit` npm package doesn't work

**Problem:** Installing `@openai/chatkit` via npm and trying to import it fails.

**Cause:** The npm package ONLY contains TypeScript type definitions, NOT the actual web component code.

**Fix:** Load ChatKit from CDN only:
```html
<script src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"></script>
```

---

### Error 2: `window.openai.ChatKit` is undefined

**Problem:** After loading CDN script, `window.openai` or `window.openai.ChatKit` is undefined.

**Cause:** The CDN script does NOT expose a global `window.openai` object. It registers a custom element instead.

**Fix:** Check for custom element registration, not global object:
```javascript
// WRONG - window.openai.ChatKit doesn't exist
if (window.openai?.ChatKit) { ... }

// CORRECT - Check custom element registration
await customElements.whenDefined('openai-chatkit');
// OR
if (customElements.get('openai-chatkit')) { ... }
```

---

### Error 3: Next.js "Event handlers cannot be passed to Client Component props"

**Problem:** Using `onLoad`/`onError` on `<Script>` in a Server Component throws this error.

**Cause:** In Next.js App Router, `layout.tsx` is a Server Component. Event handlers require Client Components.

**Fix:** Create a Client Component wrapper:
```tsx
// components/ChatKitWidget.tsx
'use client';  // <-- REQUIRED

import Script from 'next/script';

export default function ChatKitWidget() {
  return (
    <Script
      src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
      strategy="afterInteractive"
      onLoad={() => console.log('ChatKit loaded')}
      onError={(e) => console.error('ChatKit failed:', e)}
    />
  );
}
```

---

### Error 4: ChatKit shows but doesn't respond / UI resets

**Problem:** Messages sent but no response, or UI resets after sending.

**Cause:** Backend SSE streaming format is incorrect. ChatKit expects specific event format.

**Fix:** Backend must NOT double-wrap SSE events. The `chatkit.server` SDK already formats events as `data: {...}\n\n`:
```python
# WRONG - Double wrapping
async for event in result:
    yield f"data: {event}\n\n".encode()  # Creates: data: b'data: {...}\n\n'

# CORRECT - Events are already formatted
async for event in result:
    if isinstance(event, bytes):
        yield event  # Already: data: {...}\n\n
    elif isinstance(event, str):
        yield event.encode('utf-8')
```

---

### Error 5: Backend `Store` methods missing `context` parameter

**Problem:** `TypeError: method() got unexpected argument 'context'`

**Cause:** All `Store` abstract methods require a `context` parameter.

**Fix:** Add `context: Any` to ALL Store methods:
```python
# WRONG
async def save_thread(self, thread: ThreadMetadata) -> None:

# CORRECT
async def save_thread(self, thread: ThreadMetadata, context: Any) -> None:
```

---

### Error 6: `AssistantMessageItem` validation error

**Problem:** `status` field causes validation error.

**Cause:** `AssistantMessageItem` schema does NOT have a `status` field.

**Fix:** Remove `status` from AssistantMessageItem:
```python
# WRONG
AssistantMessageItem(
    id=msg_id,
    type="assistant_message",
    status="completed",  # <-- NOT VALID
    content=[...]
)

# CORRECT
AssistantMessageItem(
    id=msg_id,
    thread_id=thread.id,
    created_at=datetime.now().isoformat(),
    type="assistant_message",
    content=[AssistantMessageContent(
        type="output_text",
        text=response_text,
        annotations=[]
    )]
)
```

---

### Error 7: `setOptions` invalid format

**Problem:** `FatalAppError: ChatKit.create(): ✖ Invalid input`

**Cause:** Incorrect structure for `setOptions` configuration.

**Fix:** Use correct format per ChatKit type definitions:
```javascript
element.setOptions({
  // API config (required for custom backend)
  api: {
    url: 'http://localhost:8000/agent/chatkit',
    domainKey: '',  // Empty string for localhost development
    fetch: async (url, options) => { ... }  // Optional custom fetch
  },
  
  // Theme: string literal, NOT object
  theme: 'light',  // 'light' | 'dark' | 'auto'
  
  // Header config
  header: {
    enabled: true,
    title: {
      enabled: true,
      text: 'AI Assistant',  // <-- Use 'text', not 'content'
    },
  },
  
  // Start screen prompts: use 'label' and 'prompt'
  startScreen: {
    greeting: 'Hello! How can I help?',
    prompts: [
      { label: 'Help', prompt: 'Help me get started' },  // <-- 'label' not 'text'
    ],
  },
  
  // Composer
  composer: {
    placeholder: 'Type your message...',
  },
  
  // Disclaimer
  disclaimer: {
    text: 'AI may make mistakes.',
  },
});
```

---

## Installation

### Backend (Python)

```bash
pip install chatkit fastapi uvicorn
```

### Frontend

**NO npm install needed for ChatKit itself!** Only load from CDN.

If using Next.js:
```bash
npm install next react react-dom
```

---

## Complete Working Frontend (Next.js)

```tsx
// components/ChatKitWidget.tsx
'use client';

import { useEffect, useState, useRef } from 'react';
import Script from 'next/script';

// Session ID generator
const generateSessionId = (): string => {
  return `session-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
};

export default function ChatKitWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const chatkitRef = useRef<HTMLElement | null>(null);
  const configuredRef = useRef(false);
  
  // Persist session ID
  const [sessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      let id = sessionStorage.getItem('chatkit-session-id');
      if (!id) {
        id = generateSessionId();
        sessionStorage.setItem('chatkit-session-id', id);
      }
      return id;
    }
    return generateSessionId();
  });

  // Configure ChatKit when ready
  useEffect(() => {
    if (!isOpen || !isLoaded || configuredRef.current) return;

    const initChatKit = () => {
      const chatkit = chatkitRef.current as any;
      if (!chatkit || typeof chatkit.setOptions !== 'function') {
        setTimeout(initChatKit, 100);
        return;
      }

      configuredRef.current = true;

      chatkit.setOptions({
        api: {
          url: 'http://localhost:8000/agent/chatkit',  // Your backend URL
          domainKey: '',
          fetch: async (url: string, options: RequestInit) => {
            const body = options.body ? JSON.parse(options.body as string) : {};
            body.session_id = sessionId;
            return fetch(url, {
              ...options,
              body: JSON.stringify(body),
              headers: { ...options.headers, 'Content-Type': 'application/json' },
            });
          },
        },
        theme: 'light',
        header: {
          enabled: true,
          title: { enabled: true, text: 'AI Assistant' },
        },
        startScreen: {
          greeting: 'Hello! How can I help you?',
          prompts: [
            { label: 'Get Started', prompt: 'Help me get started' },
          ],
        },
        composer: { placeholder: 'Type your message...' },
        disclaimer: { text: 'AI may make mistakes.' },
      });

      // Event listeners
      chatkit.addEventListener('chatkit.message', (e: CustomEvent) => {
        console.log('Message:', e.detail);
      });
      chatkit.addEventListener('chatkit.error', (e: CustomEvent) => {
        console.error('Error:', e.detail);
      });
    };

    setTimeout(initChatKit, 300);
  }, [isOpen, isLoaded, sessionId]);

  // Reset config when closed
  useEffect(() => {
    if (!isOpen) configuredRef.current = false;
  }, [isOpen]);

  const handleScriptLoad = () => {
    const checkElement = () => {
      if (customElements.get('openai-chatkit')) {
        setIsLoaded(true);
      } else {
        setTimeout(checkElement, 100);
      }
    };
    checkElement();
  };

  return (
    <>
      {/* CDN Script - CORRECT URL */}
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        strategy="afterInteractive"
        onLoad={handleScriptLoad}
        onError={(e) => console.error('ChatKit load failed:', e)}
      />

      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-lg 
                   bg-blue-600 hover:bg-blue-700 text-white"
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
      >
        {isOpen ? '✕' : '💬'}
      </button>

      {/* ChatKit Container */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-96 h-[500px] rounded-xl 
                        shadow-2xl border overflow-hidden bg-white">
          {isLoaded ? (
            <openai-chatkit
              ref={chatkitRef as any}
              id="my-chatkit"
              style={{ width: '100%', height: '100%', display: 'block' }}
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          )}
        </div>
      )}
    </>
  );
}

// Type declaration for custom element
declare global {
  namespace JSX {
    interface IntrinsicElements {
      'openai-chatkit': React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement> & { id?: string },
        HTMLElement
      >;
    }
  }
}
```

---

## Complete Working Backend (FastAPI + Python)

```python
# backend/routers/chatkit_server.py
"""
ChatKit Server Integration using official chatkit.server SDK
"""

import logging
import os
import json
from datetime import datetime
from typing import Any, AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.responses import Response
from chatkit.server import (
    ChatKitServer,
    Store,
    Thread,
    ThreadMetadata,
    ThreadItem,
    UserMessageItem,
    ThreadStreamEvent,
)
from chatkit.types import (
    AssistantMessageContentPartTextDelta,
    AssistantMessageContentPartDone,
    ThreadItemDoneEvent,
    ThreadItemAddedEvent,
    AssistantMessageItem,
    AssistantMessageContent,
    Page,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["chatkit"])


class SimpleStore(Store):
    """In-memory store for ChatKit threads and messages.
    
    CRITICAL: All methods MUST have 'context: Any' parameter!
    """
    
    def __init__(self):
        self._threads: dict[str, ThreadMetadata] = {}
        self._items: dict[str, list[ThreadItem]] = {}
        self._attachments: dict[str, Any] = {}
    
    def generate_thread_id(self, context: Any) -> str:
        import uuid
        return f"thread-{uuid.uuid4().hex[:12]}"
    
    def generate_item_id(self, item_type: str, thread: ThreadMetadata, context: Any) -> str:
        import uuid
        return f"{item_type}-{uuid.uuid4().hex[:12]}"
    
    async def save_thread(self, thread: ThreadMetadata, context: Any) -> None:
        self._threads[thread.id] = thread
        if thread.id not in self._items:
            self._items[thread.id] = []
    
    async def load_thread(self, thread_id: str, context: Any) -> ThreadMetadata | None:
        return self._threads.get(thread_id)
    
    async def delete_thread(self, thread_id: str, context: Any) -> None:
        self._threads.pop(thread_id, None)
        self._items.pop(thread_id, None)
    
    async def load_threads(self, limit: int, after: str | None, order: str, context: Any) -> Any:
        threads = list(self._threads.values())
        return Page(data=threads[:limit], has_more=len(threads) > limit)
    
    async def add_thread_item(self, thread_id: str, item: ThreadItem, context: Any) -> None:
        if thread_id not in self._items:
            self._items[thread_id] = []
        self._items[thread_id].append(item)
    
    async def load_thread_items(self, thread_id: str, after: str | None, limit: int, order: str, context: Any) -> Any:
        items = self._items.get(thread_id, [])
        return Page(data=items[:limit], has_more=len(items) > limit)
    
    async def load_item(self, thread_id: str, item_id: str, context: Any) -> ThreadItem | None:
        for item in self._items.get(thread_id, []):
            if hasattr(item, 'id') and item.id == item_id:
                return item
        return None
    
    async def save_item(self, thread_id: str, item: ThreadItem, context: Any) -> None:
        if thread_id not in self._items:
            self._items[thread_id] = []
        items = self._items[thread_id]
        for i, existing in enumerate(items):
            if hasattr(existing, 'id') and hasattr(item, 'id') and existing.id == item.id:
                items[i] = item
                return
        items.append(item)
    
    async def delete_thread_item(self, thread_id: str, item_id: str, context: Any) -> None:
        if thread_id in self._items:
            self._items[thread_id] = [
                item for item in self._items[thread_id]
                if not (hasattr(item, 'id') and item.id == item_id)
            ]
    
    async def save_attachment(self, attachment: Any, context: Any) -> None:
        if hasattr(attachment, 'id'):
            self._attachments[attachment.id] = attachment
    
    async def load_attachment(self, attachment_id: str, context: Any) -> Any:
        return self._attachments.get(attachment_id)
    
    async def delete_attachment(self, attachment_id: str, context: Any) -> None:
        self._attachments.pop(attachment_id, None)


class MyChatKitServer(ChatKitServer):
    """ChatKit server that connects to your AI agent."""
    
    def __init__(self, store: Store):
        super().__init__(store)
        # Initialize your agent here
        self._agent = None  # Replace with your agent
    
    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,  # Can be None!
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Process user message and yield streaming response events.
        
        CRITICAL Event Sequence:
        1. AssistantMessageContentPartTextDelta - Stream text content
        2. AssistantMessageContentPartDone - Signal content complete
        3. ThreadItemAddedEvent - Announce new message item
        4. ThreadItemDoneEvent - Signal message complete
        """
        import uuid
        
        if input_user_message is None:
            return
        
        # Extract user message text
        user_message = ""
        if hasattr(input_user_message, 'content'):
            for content in input_user_message.content:
                if hasattr(content, 'text'):
                    user_message += content.text
        
        # Process with your agent
        # response_text = await self._agent.process(user_message)
        response_text = f"You said: {user_message}"  # Replace with real agent
        
        msg_id = f"msg-{uuid.uuid4().hex[:12]}"
        
        # 1. Stream text delta
        yield AssistantMessageContentPartTextDelta(
            type="assistant_message.content_part.text_delta",
            content_index=0,
            delta=response_text
        )
        
        # 2. Content part done
        content = AssistantMessageContent(
            type="output_text",
            text=response_text,
            annotations=[]
        )
        yield AssistantMessageContentPartDone(
            type="assistant_message.content_part.done",
            content_index=0,
            content=content
        )
        
        # 3. Create message item (NO status field!)
        assistant_msg = AssistantMessageItem(
            id=msg_id,
            thread_id=thread.id,
            created_at=datetime.now().isoformat(),
            type="assistant_message",
            content=[content]
        )
        yield ThreadItemAddedEvent(type="thread.item.added", item=assistant_msg)
        
        # 4. Message done
        yield ThreadItemDoneEvent(type="thread.item.done", item=assistant_msg)


# Global instances
_store = SimpleStore()
_server = MyChatKitServer(_store)


@router.post("/chatkit")
async def chatkit_endpoint(request: Request):
    """Main ChatKit endpoint - handles all ChatKit protocol requests."""
    try:
        body = await request.body()
        context = {"headers": dict(request.headers)}
        
        result = await _server.process(body, context)
        
        # Handle streaming result
        if hasattr(result, '__aiter__'):
            async def generate():
                async for event in result:
                    # CRITICAL: Events are already SSE formatted!
                    # Do NOT double-wrap with another 'data:' prefix
                    if isinstance(event, bytes):
                        yield event
                    elif isinstance(event, str):
                        yield event.encode('utf-8')
                    elif hasattr(event, 'model_dump_json'):
                        yield f"data: {event.model_dump_json()}\n\n".encode('utf-8')
                    else:
                        yield f"data: {json.dumps(event)}\n\n".encode('utf-8')
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )
        
        # Handle non-streaming result
        if hasattr(result, 'model_dump_json'):
            return Response(content=result.model_dump_json(), media_type="application/json")
        return Response(content=json.dumps(result), media_type="application/json")
        
    except Exception as e:
        logger.error(f"ChatKit error: {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/chatkit/health")
async def chatkit_health():
    """Health check endpoint."""
    return {"status": "ok", "service": "ChatKit Server"}
```

**Add to main.py:**
```python
from app.routers import chatkit_server
app.include_router(chatkit_server.router)
```

---

## Environment Variables

```bash
# Backend
OPENAI_API_KEY=sk-...           # If using OpenAI models
GEMINI_API_KEY=...              # If using Gemini models

# Optional
CHATKIT_WORKFLOW_ID=wf_...      # Only for managed ChatKit
```

---

## Quick Setup Checklist (Custom ChatKit with FastAPI)

- [ ] 🚨 **This is Custom ChatKit** - Do NOT clone starter template (that's for Managed/Agent ID)
- [ ] Backend: `pip install chatkit fastapi uvicorn`
- [ ] Frontend: Load CDN script (no npm install for ChatKit itself)
- [ ] CDN URL: `https://cdn.platform.openai.com/deployments/chatkit/chatkit.js`
- [ ] Wait for custom element: `customElements.whenDefined('openai-chatkit')`
- [ ] Configure with `setOptions()` using correct format
- [ ] Backend `Store` methods all have `context: Any` parameter
- [ ] Backend `respond()` yields correct event sequence
- [ ] Backend SSE does NOT double-wrap events
- [ ] `AssistantMessageItem` has NO `status` field

---

## What NOT To Do

❌ **Never clone starter template for Custom ChatKit** - Template is for Managed (OpenAI Agent ID) only
❌ **Never `npm install @openai/chatkit`** - It's only types, not the component
❌ **Never check `window.openai.ChatKit`** - It doesn't exist
❌ **Never use event handlers in Next.js Server Components**
❌ **Never add `status` field to AssistantMessageItem**
❌ **Never double-wrap SSE events with `data:` prefix**
❌ **Never forget `context: Any` in Store methods**

## What TO Do

✅ **Use Custom ChatKit approach with FastAPI backend (this skill)**
✅ **Follow the patterns in this skill for frontend + backend setup**
✅ **Always load from CDN: `cdn.platform.openai.com/deployments/chatkit/chatkit.js`**
✅ **Always use `customElements.whenDefined('openai-chatkit')`**
✅ **Always use 'use client' for components with event handlers**
✅ **Always include `context: Any` in ALL Store methods**
✅ **Always follow the correct event sequence in respond()**
