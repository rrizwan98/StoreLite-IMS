# Backend Integration

Connect ChatKit frontend to OpenAI Agents SDK backend.

## Architecture

```
ChatKit Frontend  ←→  FastAPI Backend  ←→  OpenAI Agents SDK  ←→  MCP Servers
```

## FastAPI Backend Setup

### Project Structure

```
backend/
├── main.py              # FastAPI app entry
├── routers/
│   └── chatkit.py       # ChatKit endpoints
├── agents/
│   └── main_agent.py    # OpenAI Agents SDK
├── config.py            # Configuration
└── requirements.txt
```

### Requirements

```txt
fastapi>=0.109.0
uvicorn>=0.27.0
chatkit>=0.1.0
openai>=1.0.0
openai-agents>=0.6.0
python-dotenv>=1.0.0
```

## Session Endpoint (Hosted Backend)

For OpenAI-hosted workflows (Agent Builder):

```python
# routers/chatkit.py
from fastapi import APIRouter, HTTPException
from openai import OpenAI
import os

router = APIRouter(prefix="/api/chatkit")
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

@router.post("/session")
async def create_session():
    """Create ChatKit session for hosted backend."""
    try:
        session = client.beta.chatkit.sessions.create(
            user="user_id",  # Your user identification
            workflow={
                "id": os.environ["CHATKIT_WORKFLOW_ID"],
            },
            expires_after=1800,  # 30 minutes
            max_requests_per_1_minute=60,
        )
        return {"client_secret": session.client_secret}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Self-Hosted Backend (Recommended for Agents SDK)

For custom backend with OpenAI Agents SDK:

### Main FastAPI App

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chatkit

app = FastAPI(title="Agent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chatkit.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### ChatKit Python SDK Integration

```python
# routers/chatkit.py
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from chatkit import ChatKit
from agents.main_agent import agent
from agents import Runner
import json

router = APIRouter(prefix="/api")

# Initialize ChatKit with custom handler
chatkit = ChatKit()

@chatkit.on_message
async def handle_message(message: str, context: dict):
    """Handle incoming chat messages with OpenAI Agents SDK."""
    
    # Run your agent
    result = await Runner.run(
        agent,
        message,
        context=context,
    )
    
    return result.final_output

@router.post("/chat")
async def chat_endpoint(request: Request):
    """Main chat endpoint for ChatKit."""
    body = await request.json()
    
    # Process with ChatKit
    response = await chatkit.process(body)
    
    return response

@router.post("/chat/stream")
async def chat_stream_endpoint(request: Request):
    """Streaming chat endpoint for ChatKit."""
    body = await request.json()
    
    async def generate():
        async for chunk in chatkit.stream(body):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )
```

### Agent Definition

```python
# agents/main_agent.py
from agents import Agent, function_tool
from agents.mcp import MCPServerStreamableHttp
import os

@function_tool
def search_knowledge(query: str) -> str:
    """Search the knowledge base."""
    # Your implementation
    return f"Results for: {query}"

# Create agent
agent = Agent(
    name="ChatAgent",
    instructions="""You are a helpful assistant.
    Use available tools to help users with their requests.
    Be concise and friendly.""",
    tools=[search_knowledge],
)

# With MCP Server
async def create_agent_with_mcp():
    async with MCPServerStreamableHttp(
        name="Tools",
        params={"url": os.environ["MCP_SERVER_URL"]},
        cache_tools_list=True,
    ) as mcp_server:
        return Agent(
            name="MCPAgent",
            instructions="Help users with available tools.",
            mcp_servers=[mcp_server],
        )
```

## Streaming Responses

For real-time streaming with ChatKit:

```python
# routers/chatkit.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from agents import Runner

@router.post("/chat/stream")
async def stream_chat(request: Request):
    body = await request.json()
    message = body.get("message", "")
    
    async def generate():
        result = Runner.run_streamed(agent, message)
        
        async for event in result.stream_events():
            if event.type == "text_delta":
                yield f"data: {json.dumps({'delta': event.text})}\n\n"
        
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )
```

## Widgets Integration

Return ChatKit widgets from your agent:

```python
from chatkit.widgets import Card, Button, Row

@function_tool
def show_options(options: list[str]) -> dict:
    """Display options to user as widget."""
    return Card(
        children=[
            Row(
                children=[
                    Button(text=opt, action={"type": "select", "value": opt})
                    for opt in options
                ]
            )
        ]
    ).to_dict()
```

## Session Management

For persistent conversations:

```python
# routers/chatkit.py
from uuid import uuid4

# In-memory sessions (use Redis/DB in production)
sessions = {}

@router.post("/session/create")
async def create_session(user_id: str):
    session_id = str(uuid4())
    sessions[session_id] = {
        "user_id": user_id,
        "messages": [],
        "created_at": datetime.utcnow(),
    }
    return {"session_id": session_id}

@router.post("/chat")
async def chat(request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    message = body.get("message")
    
    # Get session history
    session = sessions.get(session_id, {"messages": []})
    history = session["messages"]
    
    # Run agent with history
    result = await Runner.run(
        agent,
        message,
        context={"history": history},
    )
    
    # Save to session
    session["messages"].append({"role": "user", "content": message})
    session["messages"].append({"role": "assistant", "content": result.final_output})
    
    return {"response": result.final_output}
```

## Error Handling

```python
from fastapi import HTTPException
from chatkit.errors import ChatKitError

@router.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        result = await process_message(body)
        return result
    except ChatKitError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal error")
```

## Frontend Connection

Connect your vanilla JS ChatKit to this backend:

```javascript
const chatkit = document.getElementById('chat');

chatkit.setOptions({
  api: {
    url: 'http://localhost:8000/api/chat',
    
    // Custom auth
    fetch: async (url, options) => {
      const token = localStorage.getItem('auth_token');
      return fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${token}`,
        },
      });
    },
  },
});
```

## MCP Server Compatibility

Ensure your MCP servers work with both:
1. OpenAI Agents SDK (backend)
2. ChatKit widgets (frontend display)

```python
# MCP server tool that returns ChatKit-compatible widget
@mcp.tool
def get_user_profile(user_id: str) -> dict:
    """Get user profile as ChatKit widget."""
    user = fetch_user(user_id)
    
    return {
        "widget": {
            "type": "card",
            "title": user.name,
            "description": user.email,
            "actions": [
                {"type": "button", "text": "Edit", "action": "edit_profile"}
            ]
        }
    }
```