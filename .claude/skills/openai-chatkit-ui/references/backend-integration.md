# Backend Integration (ChatKit Server Protocol)

Connect ChatKit frontend to your Python backend using the official `chatkit.server` SDK.

## ⚠️ CRITICAL: Use Official ChatKit Server Protocol

The ChatKit SDK provides `ChatKitServer` and `Store` classes. You MUST use these - no custom implementations!

## Installation

```bash
pip install chatkit fastapi uvicorn
```

## Architecture

```
ChatKit Frontend (CDN) ←→ FastAPI Backend ←→ ChatKitServer + Store ←→ Your AI Agent
```

## Project Structure

```
backend/
├── main.py                    # FastAPI app entry
├── routers/
│   └── chatkit_server.py      # ChatKit protocol endpoint
├── agents/
│   └── your_agent.py          # Your AI agent
└── requirements.txt
```

## Requirements

```txt
fastapi>=0.109.0
uvicorn>=0.27.0
chatkit>=0.1.0
python-dotenv>=1.0.0
```

---

## Complete Working Backend Implementation

### Step 1: Store Implementation

**CRITICAL:** All Store methods MUST have `context: Any` parameter!

```python
# routers/chatkit_server.py
from typing import Any
from chatkit.server import Store, ThreadMetadata, ThreadItem
from chatkit.types import Page

class SimpleStore(Store):
    """In-memory store for ChatKit threads and messages.
    
    CRITICAL: All methods MUST include 'context: Any' parameter!
    """
    
    def __init__(self):
        self._threads: dict[str, ThreadMetadata] = {}
        self._items: dict[str, list[ThreadItem]] = {}
        self._attachments: dict[str, Any] = {}
    
    # ✅ CORRECT: Has context parameter
    def generate_thread_id(self, context: Any) -> str:
        import uuid
        return f"thread-{uuid.uuid4().hex[:12]}"
    
    # ✅ CORRECT: Has context parameter
    def generate_item_id(self, item_type: str, thread: ThreadMetadata, context: Any) -> str:
        import uuid
        return f"{item_type}-{uuid.uuid4().hex[:12]}"
    
    # ✅ CORRECT: Has context parameter
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
```

### Step 2: ChatKitServer Implementation

**CRITICAL:**
- `respond()` method signature: `input_user_message` can be `None`
- `AssistantMessageItem` has NO `status` field
- Must yield correct event sequence

```python
from datetime import datetime
from typing import AsyncIterator
from chatkit.server import ChatKitServer, Store, ThreadMetadata, UserMessageItem, ThreadStreamEvent
from chatkit.types import (
    AssistantMessageContentPartTextDelta,
    AssistantMessageContentPartDone,
    ThreadItemDoneEvent,
    ThreadItemAddedEvent,
    AssistantMessageItem,
    AssistantMessageContent,
)

class MyChatKitServer(ChatKitServer):
    """ChatKit server that connects to your AI agent."""
    
    def __init__(self, store: Store):
        super().__init__(store)
        self._agent = None  # Initialize your agent here
    
    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,  # ⚠️ Can be None!
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Process user message and yield streaming response events.
        
        CRITICAL Event Sequence (in order):
        1. AssistantMessageContentPartTextDelta - Stream text content
        2. AssistantMessageContentPartDone - Signal content complete
        3. ThreadItemAddedEvent - Announce new message item
        4. ThreadItemDoneEvent - Signal message complete
        """
        import uuid
        
        # Handle None input
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
        
        # 3. Create message item (⚠️ NO status field!)
        assistant_msg = AssistantMessageItem(
            id=msg_id,
            thread_id=thread.id,
            created_at=datetime.now().isoformat(),
            type="assistant_message",
            content=[content]
            # ❌ NO status field here!
        )
        yield ThreadItemAddedEvent(type="thread.item.added", item=assistant_msg)
        
        # 4. Message done
        yield ThreadItemDoneEvent(type="thread.item.done", item=assistant_msg)
```

### Step 3: FastAPI Endpoint

**CRITICAL:** Do NOT double-wrap SSE events! ChatKit SDK already formats them.

```python
import json
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.responses import Response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["chatkit"])

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
                    # ⚠️ CRITICAL: Events are already SSE formatted!
                    # Do NOT wrap with another 'data:' prefix!
                    if isinstance(event, bytes):
                        yield event  # Already formatted as: data: {...}\n\n
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
                    "X-Accel-Buffering": "no",  # Disable nginx buffering
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

### Step 4: Main FastAPI App

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chatkit_server

app = FastAPI(title="ChatKit Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chatkit_server.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Common Errors and Fixes

### Error: `got unexpected argument 'context'`

**Cause:** Store methods missing `context` parameter.

**Fix:** Add `context: Any` to ALL Store methods.

### Error: AssistantMessageItem validation error

**Cause:** Adding `status` field to AssistantMessageItem.

**Fix:** Remove `status` field - it doesn't exist in the schema.

### Error: UI resets after sending message

**Cause:** SSE events are double-wrapped with `data:` prefix.

**Fix:** Don't wrap events that are already bytes - yield them directly.

### Error: No response received

**Cause:** Wrong event sequence or missing events.

**Fix:** Yield all 4 events in order:
1. `AssistantMessageContentPartTextDelta`
2. `AssistantMessageContentPartDone`
3. `ThreadItemAddedEvent`
4. `ThreadItemDoneEvent`

---

## Frontend Connection

```javascript
// In your frontend ChatKit setup
chatkit.setOptions({
  api: {
    url: 'http://localhost:8000/agent/chatkit',
    domainKey: '',  // Empty for localhost
    fetch: async (url, options) => {
      const body = options.body ? JSON.parse(options.body) : {};
      body.session_id = sessionId;  // Add session if needed
      return fetch(url, {
        ...options,
        body: JSON.stringify(body),
        headers: { ...options.headers, 'Content-Type': 'application/json' },
      });
    },
  },
});
```
