# Streaming Workflow Reference

> Complete guide for implementing WorkflowItem-based streaming progress display in ChatKit.

---

## Overview

WorkflowItem provides a collapsible progress display that shows:
- Real-time task progress with loading indicators
- Tool calls with icons and status
- Web search results with source URLs
- Thinking/reasoning steps
- Completion summary with duration

```
┌─────────────────────────────────────────────────────┐
│ ▼ Workflow                                    3s    │
├─────────────────────────────────────────────────────┤
│ ✓ Analyzing Request                                 │
│ ✓ Executing SQL Query                               │
│ ✓ Done - Completed 1 operation                      │
└─────────────────────────────────────────────────────┘
```

---

## WorkflowItem Types

### Import Statements

```python
from chatkit.types import (
    # Main workflow types
    WorkflowItem,
    Workflow,

    # Task types
    CustomTask,      # Generic task with icon
    SearchTask,      # Web search with URLs
    ThoughtTask,     # Reasoning/thinking

    # Source types
    URLSource,       # URL with title

    # Summary types
    DurationSummary, # Shows elapsed time
    CustomSummary,   # Custom text summary

    # Update events
    WorkflowTaskAdded,
    WorkflowTaskUpdated,
)
```

---

## Task Types

### CustomTask

Generic task with icon, title, content, and status.

```python
CustomTask(
    type="custom",
    title="Executing SQL Query",
    content="SELECT * FROM products WHERE stock < 10",
    status_indicator="loading",  # "loading" or "complete"
    icon="analytics"             # ChatKit icon name
)
```

### SearchTask

Web search task with query and source URLs.

```python
SearchTask(
    type="web_search",
    title="Searching the Web",
    title_query="best python frameworks 2024",  # Displayed in UI
    queries=["best python frameworks 2024"],
    sources=[
        URLSource(url="https://example.com", title="Example Site"),
        URLSource(url="https://docs.python.org", title="Python Docs"),
    ],
    status_indicator="loading"
)
```

### ThoughtTask

Reasoning/thinking display.

```python
ThoughtTask(
    type="thought",
    title="Reasoning",
    content="Let me analyze the user's request..."
)
```

---

## Valid Icon Names

```python
# Database/Analytics
"analytics"      # SQL queries, data operations
"chart"          # Data visualization

# Search
"search"         # Web search, file search

# Communication
"mail"           # Email operations

# Documents
"document"       # File operations
"notebook"       # Notion, notes

# Status
"check"          # Completion
"info"           # Information, errors

# AI/General
"sparkle"        # AI operations
"sparkle-double" # Enhanced AI
"lightbulb"      # Ideas, suggestions

# Other useful icons
"globe"          # Web/internet
"wreath"         # Special/important
"settings-slider"# Configuration
"cube"           # Objects/items
```

---

## Complete Streaming Implementation

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

    if input_user_message is None:
        return

    # Extract user message
    user_message = ""
    for content_item in (input_user_message.content or []):
        if hasattr(content_item, 'text'):
            user_message += content_item.text

    # Initialize tracking
    start_time = time.time()
    workflow_id = f"workflow-{uuid.uuid4().hex[:12]}"
    workflow_tasks = []
    tools_used = []
    search_sources = []

    # ========================================
    # Step 1: Create initial workflow
    # ========================================
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
            expanded=True,    # Expanded while processing
            summary=None
        )
    )

    # Emit workflow started
    yield ThreadItemAddedEvent(type="thread.item.added", item=workflow_item)

    # ========================================
    # Step 2: Stream agent events
    # ========================================
    response_text = ""

    async for event in agent.query_streamed(user_message):
        event_type = event.get("type")

        if event_type == "progress":
            # Update first task with progress text
            progress_text = event.get("text", "Processing...")
            if workflow_tasks[0].status_indicator == "loading":
                workflow_tasks[0].content = progress_text
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
            args = event.get("arguments", "")
            tools_used.append(tool_name)

            # Mark previous loading tasks as complete
            for t in workflow_tasks:
                if t.status_indicator == "loading":
                    t.status_indicator = "complete"

            # Create appropriate task type
            if "search" in tool_name.lower():
                # Extract search query
                search_query = "searching..."
                if args:
                    try:
                        args_dict = json.loads(args) if isinstance(args, str) else args
                        search_query = args_dict.get("query", str(args_dict)[:100])
                    except:
                        search_query = str(args)[:100]

                new_task = SearchTask(
                    type="web_search",
                    title="Searching the Web",
                    title_query=search_query,
                    queries=[search_query],
                    sources=[],
                    status_indicator="loading"
                )
            else:
                new_task = CustomTask(
                    type="custom",
                    title=get_tool_title(tool_name),
                    content="Processing...",
                    status_indicator="loading",
                    icon=get_tool_icon(tool_name)
                )

            workflow_tasks.append(new_task)
            task_index = len(workflow_tasks) - 1

            # Emit task added
            yield ThreadItemUpdatedEvent(
                type="thread.item.updated",
                item_id=workflow_id,
                update=WorkflowTaskAdded(
                    type="workflow.task.added",
                    task_index=task_index,
                    task=new_task
                )
            )

        elif event_type == "tool_output":
            tool_name = event.get("tool_name", "")
            output_preview = event.get("output_preview", "")

            # Find and update the loading task
            for i, t in enumerate(workflow_tasks):
                if t.status_indicator == "loading":
                    t.status_indicator = "complete"

                    # Extract URLs for SearchTask
                    if isinstance(t, SearchTask) and "search" in tool_name.lower():
                        urls = extract_urls_from_output(output_preview)
                        t.sources = [
                            URLSource(url=u["url"], title=u["title"])
                            for u in urls[:5]
                        ]
                        search_sources.extend(urls)
                    elif hasattr(t, 'content'):
                        t.content = output_preview[:200]

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

        elif event_type == "thinking":
            thinking_text = event.get("text", "")
            if thinking_text:
                # Add or update ThoughtTask
                thought_exists = False
                for i, t in enumerate(workflow_tasks):
                    if isinstance(t, ThoughtTask):
                        t.content = thinking_text[:500]
                        thought_exists = True
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

                if not thought_exists:
                    thought_task = ThoughtTask(
                        type="thought",
                        title="Reasoning",
                        content=thinking_text[:500]
                    )
                    workflow_tasks.append(thought_task)
                    yield ThreadItemUpdatedEvent(
                        type="thread.item.updated",
                        item_id=workflow_id,
                        update=WorkflowTaskAdded(
                            type="workflow.task.added",
                            task_index=len(workflow_tasks) - 1,
                            task=thought_task
                        )
                    )

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

            # ========================================
            # Step 3: Collapse workflow with summary
            # ========================================
            duration_seconds = int(time.time() - start_time)

            workflow_item.workflow.tasks = workflow_tasks.copy()
            workflow_item.workflow.summary = DurationSummary(duration=duration_seconds)
            workflow_item.workflow.expanded = False  # Collapse after completion

            yield ThreadItemDoneEvent(type="thread.item.done", item=workflow_item)

        elif event_type == "error":
            error_text = event.get("text", "An error occurred")
            response_text = error_text

            # Add error task
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

    # ========================================
    # Step 4: Emit final response
    # ========================================
    if not response_text:
        response_text = "I processed your request."

    # Format with sources if available
    final_text = format_response_with_sources(response_text, search_sources)

    msg_id = f"msg-{uuid.uuid4().hex[:12]}"
    assistant_msg = AssistantMessageItem(
        id=msg_id,
        thread_id=thread.id,
        created_at=datetime.now(),
        type="assistant_message",
        content=[AssistantMessageContent(text=final_text)]
    )

    yield ThreadItemAddedEvent(type="thread.item.added", item=assistant_msg)
    yield ThreadItemDoneEvent(type="thread.item.done", item=assistant_msg)
```

---

## Helper Functions

### Extract URLs from Output

```python
import re
from urllib.parse import urlparse

def extract_urls_from_output(output: str) -> list[dict]:
    """Extract URLs with titles from search output."""
    urls = []
    seen = set()

    # Try markdown links first: [Title](URL)
    markdown_links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', output)
    for title, url in markdown_links:
        if url.startswith('http') and url not in seen:
            seen.add(url)
            urls.append({'url': url, 'title': title})

    # Fallback to plain URLs
    if not urls:
        plain_urls = re.findall(r'https?://[^\s\)\]\"\'\<\>]+', output)
        for url in plain_urls:
            if url not in seen:
                seen.add(url)
                try:
                    domain = urlparse(url).netloc
                    urls.append({'url': url, 'title': domain})
                except:
                    urls.append({'url': url, 'title': 'Source'})

    return urls[:5]  # Limit to 5 sources
```

### Format Response with Sources

```python
def format_response_with_sources(response_text: str, sources: list[dict]) -> str:
    """Format response with sources section."""
    if not sources:
        return response_text.strip()

    # Clean up existing sources section
    clean_text = response_text.strip()

    # Add formatted sources
    clean_text += "\n\n---\n\n**Sources:**\n"
    seen = set()
    for i, source in enumerate(sources[:8], 1):
        if source['url'] not in seen:
            seen.add(source['url'])
            title = source['title'][:40]
            clean_text += f"[{i}] {title}\n{source['url']}\n\n"

    return clean_text.strip()
```

### Get Tool Icon

```python
def get_tool_icon(tool_name: str) -> str:
    """Get ChatKit icon for tool type."""
    tool_lower = tool_name.lower()

    if "sql" in tool_lower or "query" in tool_lower or "database" in tool_lower:
        return "analytics"
    elif "search" in tool_lower:
        return "search"
    elif "mail" in tool_lower or "email" in tool_lower or "gmail" in tool_lower:
        return "mail"
    elif "file" in tool_lower or "document" in tool_lower:
        return "document"
    elif "notion" in tool_lower or "note" in tool_lower:
        return "notebook"
    elif "chart" in tool_lower or "graph" in tool_lower:
        return "chart"
    else:
        return "sparkle"
```

### Get Tool Title

```python
def get_tool_title(tool_name: str) -> str:
    """Get display title for tool."""
    mappings = {
        "execute_sql": "Executing SQL Query",
        "google_search": "Searching the Web",
        "gmail_connector": "Processing Email",
        "notion_connector": "Connecting to Notion",
        "file_search": "Searching Files",
        "analyze_file": "Analyzing File",
        "list_tables": "Listing Tables",
    }

    if tool_name in mappings:
        return mappings[tool_name]

    # Generate from tool name
    return f"Using {tool_name.replace('_', ' ').title()}"
```

---

## Event Flow Diagram

```
User sends message
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ ThreadItemAddedEvent(WorkflowItem)                  │
│   - Initial task: "Analyzing Request" (loading)     │
│   - expanded: true                                  │
└─────────────────────────────────────────────────────┘
    │
    ▼ (for each tool call)
┌─────────────────────────────────────────────────────┐
│ ThreadItemUpdatedEvent(WorkflowTaskAdded)           │
│   - New task: "Using tool_name" (loading)           │
└─────────────────────────────────────────────────────┘
    │
    ▼ (when tool completes)
┌─────────────────────────────────────────────────────┐
│ ThreadItemUpdatedEvent(WorkflowTaskUpdated)         │
│   - Task status: "complete"                         │
│   - Content: tool output preview                    │
└─────────────────────────────────────────────────────┘
    │
    ▼ (when all done)
┌─────────────────────────────────────────────────────┐
│ ThreadItemUpdatedEvent(WorkflowTaskAdded)           │
│   - "Done" task (complete)                          │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ ThreadItemDoneEvent(WorkflowItem)                   │
│   - expanded: false (collapsed)                     │
│   - summary: DurationSummary(duration=seconds)      │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ ThreadItemAddedEvent(AssistantMessageItem)          │
│   - Final response text                             │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ ThreadItemDoneEvent(AssistantMessageItem)           │
│   - Mark message complete                           │
└─────────────────────────────────────────────────────┘
```

---

## Summary Types

### DurationSummary

Shows elapsed time in collapsed state.

```python
DurationSummary(
    duration=15  # Seconds
)
# Displays: "15s" or "1m 30s"
```

### CustomSummary

Custom text summary.

```python
CustomSummary(
    type="custom",
    text="Completed 3 operations"
)
```

---

## Best Practices

1. **Always emit ThreadItemAddedEvent first** - Before any updates
2. **Mark previous tasks complete** - Before adding new loading task
3. **Use appropriate icons** - Match icon to tool type
4. **Limit source URLs** - Cap at 5-8 for readability
5. **Collapse on completion** - Set `expanded=False` in final event
6. **Include duration summary** - Users expect timing feedback
7. **Handle errors gracefully** - Add error task, collapse workflow
8. **Format sources section** - Use consistent markdown format
