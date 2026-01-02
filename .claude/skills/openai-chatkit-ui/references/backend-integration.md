# Backend Integration Reference

> Complete guide for integrating ChatKit with FastAPI backend using ChatKit Python SDK.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                          │
├─────────────────────────────────────────────────────────────────┤
│  POST /chatkit                                                   │
│  ├── Parse request body                                          │
│  ├── Create PostgreSQLChatKitStore(db, user_id)                 │
│  ├── Create MyChatKitServer(store)                              │
│  ├── Build context {user_id, headers, db_session, ...}          │
│  ├── result = await server.process(body, context)               │
│  └── Return StreamingResponse or JSON Response                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Required Imports

```python
# ChatKit SDK imports
from chatkit.server import (
    ChatKitServer,
    Store,
    ThreadMetadata,
    ThreadItem,
    UserMessageItem,
    ThreadStreamEvent,
)
from chatkit.store import AttachmentStore
from chatkit.types import (
    # Thread events
    ThreadItemDoneEvent,
    ThreadItemAddedEvent,
    ThreadItemUpdatedEvent,
    # Message types
    AssistantMessageItem,
    AssistantMessageContent,
    UserMessageTextContent,
    # Progress events
    ProgressUpdateEvent,
    ErrorEvent,
    ErrorCode,
    # Pagination
    Page,
    # Attachments
    ImageAttachment,
    FileAttachment,
    # WorkflowItem types (for streaming progress)
    WorkflowItem,
    Workflow,
    CustomTask,
    SearchTask,
    ThoughtTask,
    URLSource,
    DurationSummary,
    # Workflow update events
    WorkflowTaskAdded,
    WorkflowTaskUpdated,
)

# FastAPI imports
from fastapi import APIRouter, Request, Depends, Response
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
```

---

## ChatKitServer Implementation

### Basic Structure

```python
class MyChatKitServer(ChatKitServer):
    """
    Custom ChatKit Server for your agent integration.

    Extends ChatKitServer to:
    - Process user messages with your agent
    - Stream progress updates (WorkflowItem)
    - Return formatted responses
    """

    def __init__(self, store: Store, attachment_store: AttachmentStore | None = None):
        super().__init__(store, attachment_store=attachment_store)

    async def delete_thread(self, thread_id: str, context: Any) -> None:
        """Ensure thread deletion works properly."""
        await self.store.delete_thread(thread_id, context)

    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Process user message and yield streaming response events.

        Args:
            thread: Thread metadata (id, title, created_at)
            input_user_message: User's message with content and attachments
            context: Custom context (user_id, db_session, etc.)

        Yields:
            ThreadStreamEvent: Streaming events for ChatKit UI
        """
        # Implementation here...
```

### Complete respond() Method

```python
async def respond(
    self,
    thread: ThreadMetadata,
    input_user_message: UserMessageItem | None,
    context: Any,
) -> AsyncIterator[ThreadStreamEvent]:
    import time
    import uuid
    from datetime import datetime

    try:
        if input_user_message is None:
            return

        # ============================================
        # Step 1: Extract user message text
        # ============================================
        user_message = ""
        attachments_list = []

        if hasattr(input_user_message, 'content') and input_user_message.content:
            for content_item in input_user_message.content:
                if hasattr(content_item, 'text'):
                    user_message += content_item.text

        if hasattr(input_user_message, 'attachments') and input_user_message.attachments:
            for att in input_user_message.attachments:
                if getattr(att, 'id', None):
                    attachments_list.append(att)

        # ============================================
        # Step 2: Auto-generate thread title
        # ============================================
        if not thread.title and user_message:
            title_text = user_message.strip()
            # Remove any tool prefixes
            title_text = re.sub(r'\[TOOL:\w+\]\s*', '', title_text)
            if len(title_text) > 50:
                thread.title = title_text[:47] + "..."
            else:
                thread.title = title_text if title_text else "New Conversation"
            await self.store.save_thread(thread, context)

        # ============================================
        # Step 3: Get context data
        # ============================================
        user_id = context.get("user_id")
        db_session = context.get("db_session")

        if not user_id:
            yield ErrorEvent(
                type="error",
                code=ErrorCode.INVALID_REQUEST,
                message="User not authenticated",
                allow_retry=False
            )
            return

        # ============================================
        # Step 4: Initialize WorkflowItem for progress
        # ============================================
        start_time = time.time()
        workflow_id = f"workflow-{uuid.uuid4().hex[:12]}"
        workflow_tasks = []
        tools_used = []

        initial_task = CustomTask(
            type="custom",
            title="Analyzing Request",
            content="Understanding your question...",
            status_indicator="loading",
            icon="search"
        )
        workflow_tasks.append(initial_task)

        workflow_item = WorkflowItem(
            id=workflow_id,
            thread_id=thread.id,
            created_at=datetime.now(),
            type="workflow",
            workflow=Workflow(
                type="custom",
                tasks=workflow_tasks.copy(),
                expanded=True,
                summary=None
            )
        )

        yield ThreadItemAddedEvent(type="thread.item.added", item=workflow_item)

        # ============================================
        # Step 5: Process with your agent (streaming)
        # ============================================
        response_text = ""

        async for event in your_agent.query_streamed(user_message):
            event_type = event.get("type")

            if event_type == "progress":
                # Update current task content
                if workflow_tasks and workflow_tasks[0].status_indicator == "loading":
                    workflow_tasks[0].content = event.get("text", "Processing...")
                    yield ThreadItemUpdatedEvent(
                        type="thread.item.updated",
                        item_id=workflow_id,
                        update=WorkflowTaskUpdated(
                            type="workflow.task.updated",
                            task_index=0,
                            task=workflow_tasks[0]
                        )
                    )

            elif event_type == "tool_call":
                tool_name = event.get("tool_name", "tool")
                tools_used.append(tool_name)

                # Mark previous tasks as complete
                for t in workflow_tasks:
                    if t.status_indicator == "loading":
                        t.status_indicator = "complete"

                # Add new task
                new_task = CustomTask(
                    type="custom",
                    title=f"Using {tool_name}",
                    content="Processing...",
                    status_indicator="loading",
                    icon=get_tool_icon(tool_name)
                )
                workflow_tasks.append(new_task)

                yield ThreadItemUpdatedEvent(
                    type="thread.item.updated",
                    item_id=workflow_id,
                    update=WorkflowTaskAdded(
                        type="workflow.task.added",
                        task_index=len(workflow_tasks) - 1,
                        task=new_task
                    )
                )

            elif event_type == "tool_output":
                # Mark current task as complete
                for i, t in enumerate(workflow_tasks):
                    if t.status_indicator == "loading":
                        t.status_indicator = "complete"
                        t.content = event.get("output_preview", "")[:200]
                        yield ThreadItemUpdatedEvent(
                            type="thread.item.updated",
                            item_id=workflow_id,
                            update=WorkflowTaskUpdated(
                                type="workflow.task.updated",
                                task_index=i,
                                task=t
                            )
                        )
                        break

            elif event_type == "complete":
                response_text = event.get("response", "")

                # Mark all tasks complete
                for t in workflow_tasks:
                    if hasattr(t, 'status_indicator'):
                        t.status_indicator = "complete"

                # Add "Done" task
                done_task = CustomTask(
                    type="custom",
                    title="Done",
                    content=f"Completed {len(tools_used)} operation(s)",
                    status_indicator="complete",
                    icon="check"
                )
                workflow_tasks.append(done_task)

                yield ThreadItemUpdatedEvent(
                    type="thread.item.updated",
                    item_id=workflow_id,
                    update=WorkflowTaskAdded(
                        type="workflow.task.added",
                        task_index=len(workflow_tasks) - 1,
                        task=done_task
                    )
                )

                # Collapse workflow with summary
                duration_seconds = int(time.time() - start_time)
                workflow_item.workflow.tasks = workflow_tasks.copy()
                workflow_item.workflow.summary = DurationSummary(duration=duration_seconds)
                workflow_item.workflow.expanded = False

                yield ThreadItemDoneEvent(type="thread.item.done", item=workflow_item)

            elif event_type == "error":
                error_text = event.get("text", "An error occurred")
                response_text = error_text

                error_task = CustomTask(
                    type="custom",
                    title="Error",
                    content=error_text[:200],
                    status_indicator="complete",
                    icon="info"
                )
                workflow_tasks.append(error_task)

                workflow_item.workflow.tasks = workflow_tasks.copy()
                workflow_item.workflow.expanded = False
                yield ThreadItemDoneEvent(type="thread.item.done", item=workflow_item)

        # ============================================
        # Step 6: Emit final assistant message
        # ============================================
        if not response_text:
            response_text = "I processed your request but couldn't generate a response."

        msg_id = f"msg-{uuid.uuid4().hex[:12]}"
        assistant_msg = AssistantMessageItem(
            id=msg_id,
            thread_id=thread.id,
            created_at=datetime.now(),
            type="assistant_message",
            content=[AssistantMessageContent(text=response_text)]
        )

        yield ThreadItemAddedEvent(type="thread.item.added", item=assistant_msg)
        yield ThreadItemDoneEvent(type="thread.item.done", item=assistant_msg)

    except Exception as e:
        yield ErrorEvent(
            type="error",
            code=ErrorCode.STREAM_ERROR,
            message=f"Error: {str(e)}",
            allow_retry=True
        )
```

---

## FastAPI Endpoint

```python
@router.post("/chatkit")
async def chatkit_endpoint(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Response:
    """
    ChatKit-compatible endpoint for agent integration.

    Handles:
    - threads.list: List all threads for history panel
    - threads.get: Get single thread
    - threads.delete: Delete thread
    - threads.create: Create new thread
    - respond: Process user message
    """
    try:
        body = await request.body()

        # Parse operation type
        operation = None
        try:
            body_json = json.loads(body.decode('utf-8'))
            operation = body_json.get('op')
        except:
            pass

        # Create PostgreSQL-backed store
        store = create_chatkit_store(db, user.id)
        server = MyChatKitServer(store, attachment_store=NoopAttachmentStore())

        # Build context
        context = {
            "headers": dict(request.headers),
            "user_id": user.id,
            "db_session": db,
            # Add your project-specific context...
        }

        # Process with ChatKit server
        result = await server.process(body, context)

        # Handle streaming vs non-streaming response
        if hasattr(result, '__aiter__'):
            async def generate():
                try:
                    async for event in result:
                        if isinstance(event, bytes):
                            yield event
                        elif isinstance(event, str):
                            yield event.encode('utf-8')
                        elif hasattr(event, 'model_dump_json'):
                            yield f"data: {event.model_dump_json()}\n\n".encode('utf-8')
                        else:
                            yield f"data: {json.dumps(event)}\n\n".encode('utf-8')
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n".encode('utf-8')

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )
        elif hasattr(result, 'json'):
            return Response(content=result.json, media_type="application/json")
        else:
            return Response(content=json.dumps(result), media_type="application/json")

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
```

---

## Noop Attachment Store

When using direct upload strategy (uploading files to your own endpoint first), use a no-op attachment store:

```python
class NoopAttachmentStore(AttachmentStore):
    """
    No-op attachment store for direct upload strategy.

    ChatKit may call attachments.delete during UI lifecycle.
    We handle uploads via separate /upload endpoint.
    """

    async def delete_attachment(self, attachment_id: str, context: Any) -> None:
        # Do nothing - files managed separately
        return
```

---

## Request/Response Flow

### 1. Thread List (History Panel)

**Request:**
```json
{"op": "threads.list", "limit": 20, "order": "desc"}
```

**Response (from store.load_threads):**
```json
{
  "data": [
    {"id": "thread-abc123", "title": "Help with inventory", "created_at": "2024-01-01T..."},
    {"id": "thread-def456", "title": "Create report", "created_at": "2024-01-02T..."}
  ],
  "has_more": false,
  "after": null
}
```

### 2. Thread Delete

**Request:**
```json
{"op": "threads.delete", "thread_id": "thread-abc123"}
```

**Response:**
```json
{"success": true}
```

### 3. Respond (Chat Message)

**Request:**
```json
{
  "op": "respond",
  "thread_id": "thread-abc123",
  "item": {
    "type": "user_message",
    "content": [{"type": "input_text", "text": "Hello, help me!"}],
    "attachments": []
  }
}
```

**Response (SSE Stream):**
```
data: {"type": "thread.item.added", "item": {...WorkflowItem...}}

data: {"type": "thread.item.updated", "item_id": "workflow-xxx", "update": {...}}

data: {"type": "thread.item.done", "item": {...WorkflowItem...}}

data: {"type": "thread.item.added", "item": {...AssistantMessageItem...}}

data: {"type": "thread.item.done", "item": {...AssistantMessageItem...}}
```

---

## Helper Functions

### Tool Icon Mapping

```python
def get_tool_icon(tool_name: str) -> str:
    """Get ChatKit icon for tool type."""
    if "sql" in tool_name.lower() or "query" in tool_name.lower():
        return "analytics"
    elif "search" in tool_name.lower():
        return "search"
    elif "mail" in tool_name.lower() or "email" in tool_name.lower():
        return "mail"
    elif "file" in tool_name.lower():
        return "document"
    elif "notion" in tool_name.lower():
        return "notebook"
    else:
        return "sparkle"
```

### Tool Title Mapping

```python
def get_tool_title(tool_name: str) -> str:
    """Get display title for tool."""
    mappings = {
        "execute_sql": "Executing SQL Query",
        "google_search": "Searching the Web",
        "gmail_connector": "Processing Email",
        "notion_connector": "Connecting to Notion",
        "file_search": "Searching Files",
    }
    return mappings.get(tool_name, f"Using {tool_name}")
```

---

## Error Handling

```python
# For validation errors
yield ErrorEvent(
    type="error",
    code=ErrorCode.INVALID_REQUEST,
    message="Missing required field",
    allow_retry=False
)

# For transient errors (can retry)
yield ErrorEvent(
    type="error",
    code=ErrorCode.STREAM_ERROR,
    message="Connection timeout",
    allow_retry=True
)

# For rate limiting
yield ErrorEvent(
    type="error",
    code=ErrorCode.RATE_LIMIT,
    message="Too many requests",
    allow_retry=True
)
```

---

## Dependencies

```
chatkit>=0.1.0
fastapi>=0.100.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.28.0
pydantic>=2.0.0
```
