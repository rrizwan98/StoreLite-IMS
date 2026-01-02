# OpenAI ChatKit UI Skill

> **Purpose**: Integrate official OpenAI ChatKit web component into any project with pure vanilla JS, persistent PostgreSQL-backed history, and streaming WorkflowItem progress display.

---

## Overview

This skill provides a complete, reusable pattern for implementing OpenAI ChatKit in any project. It covers:

1. **Frontend**: Pure `<openai-chatkit>` web component (NO React wrapper, NO custom UI)
2. **Backend**: FastAPI + ChatKit Python SDK with streaming responses
3. **Database**: PostgreSQL-backed persistent thread/message storage
4. **Streaming**: WorkflowItem-based progress display with collapsible dropdowns
5. **History**: Auto-generated titles, thread management, user-scoped data

---

## Critical Rules

### Frontend Rules (MUST FOLLOW)

| Rule | Description |
|------|-------------|
| Use ONLY `<openai-chatkit>` | Pure vanilla JS web component from OpenAI CDN |
| Load from CDN | `https://cdn.platform.openai.com/deployments/chatkit/chatkit.js` |
| Configure via `setOptions()` | All configuration through official API only |
| Theme via CSS variables | Official ChatKit CSS variables only |
| NO `@openai/chatkit-react` | Never use React wrapper |
| NO custom chat UI | Never write custom message bubbles, inputs, etc. |
| NO style overrides | Never override internal ChatKit styles |

### Backend Rules (MUST FOLLOW)

| Rule | Description |
|------|-------------|
| Use `chatkit.server.ChatKitServer` | Extend this class for custom agent integration |
| Use `chatkit.server.Store` | Implement this interface for persistence |
| Use SSE streaming | Return `StreamingResponse` with `text/event-stream` |
| User-scoped data | Always filter threads/messages by `user_id` |
| Auto-generate titles | Create thread title from first message |

---

## Tech Stack

| Component | Technology | Package/Source |
|-----------|------------|----------------|
| Frontend | Pure `<openai-chatkit>` | CDN script |
| Backend | FastAPI + ChatKit Python SDK | `chatkit` |
| Database | PostgreSQL | `asyncpg`, `sqlalchemy` |
| Streaming | Server-Sent Events (SSE) | FastAPI `StreamingResponse` |
| Agent | OpenAI Agents SDK | `openai-agents` |

---

## Reference Files

When implementing ChatKit, read the relevant reference files:

| If the task involves... | Read this file |
|------------------------|----------------|
| Backend server setup, FastAPI, ChatKitServer | `references/backend-integration.md` |
| Frontend widget, setOptions, events | `references/frontend-widget.md` |
| Streaming responses, WorkflowItem, progress | `references/streaming-workflow.md` |
| Thread/message persistence, PostgreSQL | `references/history-persistence.md` |
| CSS theming, colors, styles | `references/theming.md` |
| Event listeners, API methods | `references/events-api.md` |

---

## Quick Start Implementation

### 1. Frontend Widget

```tsx
// Pure OpenAI ChatKit SDK Integration
// NO React wrapper - vanilla JS web component only

import Script from 'next/script';

export default function ChatKitWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const chatkitRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isOpen || !isLoaded) return;

    const chatkit = chatkitRef.current as any;
    if (!chatkit?.setOptions) return;

    chatkit.setOptions({
      api: {
        url: `${API_BASE_URL}/agent/chatkit`,
        domainKey: '',
        fetch: async (url, options) => {
          const body = JSON.parse(options.body as string);
          body.session_id = sessionId;
          return fetch(url, { ...options, body: JSON.stringify(body) });
        },
      },
      theme: 'light',
      header: { enabled: true, title: { text: 'AI Assistant' } },
      startScreen: {
        greeting: 'Hello! How can I help?',
        prompts: [{ label: 'Help', prompt: 'Help me get started' }],
      },
      composer: { placeholder: 'Type your message...' },
      disclaimer: { text: 'AI may make mistakes.' },
    });
  }, [isOpen, isLoaded]);

  return (
    <>
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        onLoad={() => setIsLoaded(true)}
      />
      {isOpen && (
        <openai-chatkit ref={chatkitRef} style={{ width: '100%', height: '100%' }} />
      )}
    </>
  );
}
```

### 2. Backend ChatKit Server

```python
from chatkit.server import ChatKitServer, Store, ThreadMetadata, ThreadItem
from chatkit.types import (
    ThreadItemDoneEvent, ThreadItemAddedEvent, ThreadItemUpdatedEvent,
    AssistantMessageItem, AssistantMessageContent,
    WorkflowItem, Workflow, CustomTask, SearchTask,
    WorkflowTaskAdded, WorkflowTaskUpdated, DurationSummary,
)

class MyChatKitServer(ChatKitServer):
    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        # Extract user message
        user_message = ""
        if input_user_message and input_user_message.content:
            for content_item in input_user_message.content:
                if hasattr(content_item, 'text'):
                    user_message += content_item.text

        # Auto-generate thread title
        if not thread.title and user_message:
            thread.title = user_message[:47] + "..." if len(user_message) > 50 else user_message
            await self.store.save_thread(thread, context)

        # Create WorkflowItem for progress display
        workflow_id = f"workflow-{uuid.uuid4().hex[:12]}"
        initial_task = CustomTask(
            type="custom",
            title="Analyzing Request",
            content="Processing your question...",
            status_indicator="loading",
            icon="search"
        )

        workflow_item = WorkflowItem(
            id=workflow_id,
            thread_id=thread.id,
            created_at=datetime.now(),
            type="workflow",
            workflow=Workflow(
                type="custom",
                tasks=[initial_task],
                expanded=True,
                summary=None
            )
        )

        yield ThreadItemAddedEvent(type="thread.item.added", item=workflow_item)

        # Process with your agent (streaming)
        async for event in agent.query_streamed(user_message):
            if event["type"] == "tool_call":
                # Add new task
                new_task = CustomTask(
                    type="custom",
                    title=f"Using {event['tool_name']}",
                    content="Processing...",
                    status_indicator="loading",
                    icon="sparkle"
                )
                yield ThreadItemUpdatedEvent(
                    type="thread.item.updated",
                    item_id=workflow_id,
                    update=WorkflowTaskAdded(
                        type="workflow.task.added",
                        task_index=len(workflow_tasks),
                        task=new_task
                    )
                )

            elif event["type"] == "complete":
                response_text = event["response"]

                # Mark workflow complete
                workflow_item.workflow.expanded = False
                workflow_item.workflow.summary = DurationSummary(duration=elapsed_seconds)
                yield ThreadItemDoneEvent(type="thread.item.done", item=workflow_item)

                # Emit final response
                assistant_msg = AssistantMessageItem(
                    id=f"msg-{uuid.uuid4().hex[:12]}",
                    thread_id=thread.id,
                    created_at=datetime.now(),
                    type="assistant_message",
                    content=[AssistantMessageContent(text=response_text)]
                )
                yield ThreadItemAddedEvent(type="thread.item.added", item=assistant_msg)
                yield ThreadItemDoneEvent(type="thread.item.done", item=assistant_msg)
```

### 3. PostgreSQL Store

```python
from chatkit.server import Store, ThreadMetadata, ThreadItem
from chatkit.types import Page, UserMessageItem, AssistantMessageItem

class PostgreSQLChatKitStore(Store):
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id

    async def save_thread(self, thread: ThreadMetadata, context: Any) -> None:
        # Insert or update thread in database
        ...

    async def load_thread(self, thread_id: str, context: Any) -> ThreadMetadata | None:
        # Load thread with user_id filter
        result = await self.db.execute(
            select(ChatKitThread).where(
                ChatKitThread.id == thread_id,
                ChatKitThread.user_id == self.user_id
            )
        )
        ...

    async def load_threads(self, limit: int, after: str | None, order: str, context: Any) -> Page:
        # Paginated list of threads for history panel
        ...

    async def add_thread_item(self, thread_id: str, item: ThreadItem, context: Any) -> None:
        # Serialize and store message
        ...

    async def load_thread_items(self, thread_id: str, after: str | None, limit: int, order: str, context: Any) -> Page:
        # Load messages for thread
        ...
```

### 4. Database Models

```python
class ChatKitThread(Base):
    __tablename__ = "chatkit_threads"

    id = Column(String(100), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    thread_metadata = Column(JSON, default={})

    items = relationship("ChatKitThreadItem", cascade="all, delete-orphan")


class ChatKitThreadItem(Base):
    __tablename__ = "chatkit_thread_items"

    id = Column(String(100), primary_key=True)
    thread_id = Column(String(100), ForeignKey("chatkit_threads.id", ondelete="CASCADE"))
    item_type = Column(String(50), nullable=False)  # "user_message", "assistant_message"
    content = Column(Text, nullable=False)  # JSON serialized
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## Key Patterns

### 1. Session Management

```typescript
// Generate session ID (tab-lifetime persistence)
const generateSessionId = (): string => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 15);
  return `session-${timestamp}-${random}`;
};

// Store in sessionStorage
let id = sessionStorage.getItem('chatkit-session-id');
if (!id) {
  id = generateSessionId();
  sessionStorage.setItem('chatkit-session-id', id);
}
```

### 2. Tool Prefix Injection

```typescript
// Inject tool prefix into message before sending
if (selectedToolPrefix && body.messages) {
  const lastMessage = body.messages[body.messages.length - 1];
  if (lastMessage.role === 'user' && !lastMessage.content.startsWith('[TOOL:')) {
    lastMessage.content = `${selectedToolPrefix} ${lastMessage.content}`;
  }
}
```

### 3. Streaming Response Flow

```
User sends message
    ↓
ThreadItemAddedEvent (WorkflowItem with initial task)
    ↓
For each tool call:
    → WorkflowTaskAdded (new task with loading state)
    → WorkflowTaskUpdated (mark complete when done)
    ↓
ThreadItemDoneEvent (collapse workflow with summary)
    ↓
ThreadItemAddedEvent (AssistantMessageItem)
    ↓
ThreadItemDoneEvent (mark response complete)
```

### 4. Source Formatting

```python
def format_response_with_sources(response_text: str, sources: List[dict]) -> str:
    """Format response with markdown sources section."""
    if sources:
        clean_text = response_text.strip()
        clean_text += "\n\n---\n\n**Sources:**\n"
        for i, source in enumerate(sources[:8], 1):
            clean_text += f"[{i}] {source['title']}\n{source['url']}\n\n"
    return clean_text.strip()
```

---

## Workflow Task Icons

Valid ChatKit icons for CustomTask:

| Icon | Use For |
|------|---------|
| `analytics` | SQL queries, database operations |
| `search` | Web search, file search |
| `mail` | Email operations |
| `notebook` | Notion, documentation |
| `document` | File operations |
| `check` | Completion status |
| `sparkle` | AI operations, general tools |
| `chart` | Data visualization |
| `info` | Information, errors |

---

## FastAPI Endpoint Template

```python
@router.post("/chatkit")
async def chatkit_endpoint(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Response:
    body = await request.body()

    # Create store with user context
    store = PostgreSQLChatKitStore(db, user.id)
    server = MyChatKitServer(store)

    # Build context
    context = {
        "headers": dict(request.headers),
        "user_id": user.id,
        "db_session": db,
        # Add project-specific context...
    }

    # Process request
    result = await server.process(body, context)

    # Handle streaming vs non-streaming
    if hasattr(result, '__aiter__'):
        async def generate():
            async for event in result:
                if hasattr(event, 'model_dump_json'):
                    yield f"data: {event.model_dump_json()}\n\n".encode()
                else:
                    yield f"data: {json.dumps(event)}\n\n".encode()

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    else:
        return Response(content=result.json, media_type="application/json")
```

---

## Dependencies

### Python (Backend)
```
chatkit>=0.1.0
fastapi
sqlalchemy[asyncio]
asyncpg
openai-agents
```

### JavaScript (Frontend)
```
# Loaded from CDN - no npm packages needed
https://cdn.platform.openai.com/deployments/chatkit/chatkit.js
```

---

## Checklist for Implementation

- [ ] Create database models (ChatKitThread, ChatKitThreadItem)
- [ ] Implement PostgreSQLChatKitStore
- [ ] Create ChatKitServer subclass with respond() method
- [ ] Add /chatkit FastAPI endpoint
- [ ] Create frontend widget with Script loader
- [ ] Configure setOptions() with API URL
- [ ] Implement session ID management
- [ ] Add WorkflowItem streaming for progress
- [ ] Test history panel (load_threads, delete_thread)
- [ ] Verify auto-generated thread titles

---

## Common Mistakes to Avoid

1. **Using React ChatKit wrapper** - Always use vanilla `<openai-chatkit>` web component
2. **Custom message UI** - ChatKit handles all UI, never create custom bubbles
3. **Missing user_id filter** - All queries MUST filter by user_id
4. **Forgetting thread title** - Auto-generate from first message for history panel
5. **Not collapsing workflow** - Set `expanded=False` after completion
6. **Missing SSE headers** - Include Cache-Control, Connection, X-Accel-Buffering
7. **Hardcoded session IDs** - Use sessionStorage for tab-lifetime persistence
