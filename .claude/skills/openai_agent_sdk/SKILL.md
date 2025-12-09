---
name: openai-agent-builder
description: >
  Build AI agents using the OpenAI Agents SDK in Python. Use this skill when
  creating agentic AI applications with function tools, MCP servers (FastMCP
  for local development, self-hosted for production), multi-model support
  (OpenAI and LiteLLM with Gemini), sub-agents, handoffs, guardrails, and
  PostgreSQL session management. Triggers include requests to create an agent,
  build an agent, agent with tools, MCP agent, sub-agent, multi-agent system,
  agent with memory, or agent with session persistence.
---

# OpenAI Agent Builder

Build production-ready AI agents using the OpenAI Agents SDK with the developer's preferred tech stack.

## Tech Stack Overview

| Component | Technology | Notes |
|-----------|------------|-------|
| Language | Python 3.10+ | |
| Agent Framework | OpenAI Agents SDK | `pip install openai-agents` |
| Tool Calling | `function_tool` decorator OR MCP servers | |
| MCP Framework | FastMCP 2.x | `pip install fastmcp` |
| MCP Transport | localhost (dev) / self-hosted HTTP (prod) | |
| Models | OpenAI (gpt-4o, etc.) + LiteLLM (Gemini) | |
| Session Storage | PostgreSQL | Persistent conversation history |

## Critical: Fetch Latest Documentation

**Before generating any agent code, ALWAYS search the web for the latest documentation:**

1. OpenAI Agents SDK: `https://openai.github.io/openai-agents-python/`
2. FastMCP: `https://gofastmcp.com/` or `https://github.com/jlowin/fastmcp`
3. LiteLLM: `https://docs.litellm.ai/`

This ensures compatibility with the latest API changes, breaking changes, and new features.

## Quick Start Template

```python
import asyncio
from agents import Agent, Runner, function_tool
from pydantic import BaseModel

# Define tools using function_tool decorator
@function_tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: Sunny, 22°C"

# Create agent
agent = Agent(
    name="WeatherAgent",
    instructions="Help users with weather information.",
    tools=[get_weather],
)

# Run agent
async def main():
    result = await Runner.run(agent, "What's the weather in Tokyo?")
    print(result.final_output)

asyncio.run(main())
```

## Core Patterns

### 1. Function Tools (Simple Tool Calling)

Use `@function_tool` for Python functions with automatic schema generation:

```python
from agents import function_tool
from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

@function_tool
def search_database(query: str, limit: int = 10) -> list[SearchResult]:
    """Search the database for relevant items."""
    # Implementation
    return results
```

### 2. MCP Server Integration

For MCP tools, see `references/mcp-patterns.md` for:
- FastMCP server setup (development)
- Self-hosted MCP server (production)
- Connecting agents to MCP servers

### 3. Sub-Agents and Handoffs

For multi-agent patterns, see `references/sub-agents.md` for:
- Agents as tools
- Handoffs between agents
- Triage patterns

### 4. Model Configuration

For multi-model support, see `references/models-config.md` for:
- OpenAI models setup
- LiteLLM with Gemini
- Model switching strategies

### 5. Session Management

For persistent conversations, see `references/session-management.md` for:
- PostgreSQL session storage
- Conversation history management
- Cross-session context

## Agent Creation Workflow

1. **Define the agent's purpose** - What task should it accomplish?
2. **Identify required tools** - Function tools vs MCP tools
3. **Design sub-agent structure** - Single agent or multi-agent?
4. **Configure model** - OpenAI or LiteLLM/Gemini?
5. **Set up session management** - Stateless or persistent?
6. **Add guardrails** - Input/output validation
7. **Enable tracing** - For debugging and monitoring

## File Structure Convention

```
my_agent_project/
├── agents/
│   ├── __init__.py
│   ├── main_agent.py        # Primary agent
│   └── sub_agents/          # Sub-agents
│       ├── __init__.py
│       └── specialist.py
├── tools/
│   ├── __init__.py
│   └── custom_tools.py      # function_tool definitions
├── mcp_servers/
│   ├── __init__.py
│   └── server.py            # FastMCP server
├── models/
│   ├── __init__.py
│   └── config.py            # Model configuration
├── sessions/
│   ├── __init__.py
│   └── postgres_store.py    # PostgreSQL session
├── config.py                # Environment config
├── main.py                  # Entry point
└── requirements.txt
```

## Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# LiteLLM / Gemini
GEMINI_API_KEY=...

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/agent_sessions

# MCP Server (Production)
MCP_SERVER_URL=http://your-mcp-server:8000/mcp
MCP_SERVER_TOKEN=...
```

## Dependencies

```txt
openai-agents>=0.6.0
fastmcp>=2.13.0
litellm>=1.50.0
pydantic>=2.0.0
asyncpg>=0.29.0
python-dotenv>=1.0.0
```

## Best Practices

1. **Type everything** - Use Pydantic models for structured I/O
2. **Async by default** - Use `async def` for all tools with I/O
3. **Cache MCP tools** - Set `cache_tools_list=True` for performance
4. **Use guardrails** - Validate inputs/outputs for production
5. **Enable tracing** - For debugging and monitoring
6. **Handle errors gracefully** - Wrap external calls in try/except
7. **Use environment variables** - Never hardcode credentials