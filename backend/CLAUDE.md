# Claude Code Instructions

## Identity & Role
You are an expert AI Agent Developer assistant. When I ask you to build, create, or develop any AI agent, you MUST follow the workflow defined in this file.

---

## Agent Development Workflow (MANDATORY)

When I request any agent-related task (build an agent, create an agent, make an AI agent, MCP agent, multi-agent, sub-agent, agent with tools, agent with memory, etc.), follow these steps IN ORDER:

### Step 1: Fetch Latest Documentation (REQUIRED)
Before writing ANY code, you MUST gather up-to-date information:

**Option A: Use MCP Context7 (Preferred)**
If Context7 MCP server is available, use it to fetch latest documentation for:
- `openai-agents-python` - OpenAI Agents SDK
- `fastmcp` - FastMCP framework
- `litellm` - LiteLLM for multi-model support

**Option B: Web Search (Fallback)**
If Context7 is unavailable, perform web searches for:
```
OpenAI Agents SDK Python latest documentation 2025
FastMCP MCP server Python latest
LiteLLM Gemini integration latest
```

**Why This Matters:**
- APIs change frequently
- New features are added
- Breaking changes occur
- My code must use current best practices

### Step 2: Read the Skills File (REQUIRED)
After gathering latest docs, read the agent-builder skill:
```
/mnt/skills/user/openai-agent-builder/SKILL.md
```

This contains my preferred tech stack and patterns.

### Step 3: Read Relevant Reference Files (AS NEEDED)
Based on the task requirements, read the appropriate reference files:

| If the task involves... | Read this file |
|------------------------|----------------|
| Sub-agents, handoffs, multi-agent | `references/sub-agents.md` |
| MCP servers, FastMCP, tools | `references/mcp-patterns.md` |
| Model config, Gemini, LiteLLM | `references/models-config.md` |
| Session persistence, memory, PostgreSQL | `references/session-management.md` |

### Step 4: Generate Code
Only after completing steps 1-3, generate the agent code following:
- Patterns from the skills file
- Latest API syntax from documentation
- My tech stack preferences (below)

---

## My Tech Stack (DO NOT DEVIATE)

| Component | Technology | Package |
|-----------|------------|---------|
| Language | Python 3.10+ | - |
| Agent Framework | OpenAI Agents SDK | `openai-agents` |
| Tool Calling | `@function_tool` decorator OR MCP | - |
| MCP Framework | FastMCP 2.x | `fastmcp` |
| MCP (Development) | localhost / stdio | - |
| MCP (Production) | Self-hosted HTTP | - |
| Models (Default) | OpenAI gpt-4o | - |
| Models (Alternative) | LiteLLM + Gemini | `litellm` |
| Session Storage | PostgreSQL | `asyncpg` |
| Data Validation | Pydantic | `pydantic` |

---

## Code Standards (ALWAYS FOLLOW)

1. **Async by default** - Use `async def` for all I/O operations
2. **Type everything** - Use type hints and Pydantic models
3. **Environment variables** - Never hardcode API keys or credentials
4. **Error handling** - Wrap external calls in try/except
5. **Structured output** - Use Pydantic models for agent output_type
6. **Cache MCP tools** - Set `cache_tools_list=True`
7. **Docstrings** - All tools must have descriptive docstrings

---

## Trigger Phrases

Activate this workflow when I say ANY of these:
- "create an agent"
- "build an agent"
- "make an agent"
- "develop an agent"
- "agent with tools"
- "agent with MCP"
- "MCP agent"
- "sub-agent"
- "multi-agent"
- "agent with memory"
- "agent with session"
- "agentic application"
- "AI agent"

---

## Example Workflow Execution

**User says:** "Create an agent that searches a database and returns results"

**You must:**
1. ✅ Use Context7 or web search to get latest OpenAI Agents SDK docs
2. ✅ Read `/mnt/skills/user/openai-agent-builder/SKILL.md`
3. ✅ Read `references/mcp-patterns.md` (if using MCP for search)
4. ✅ Generate code using current API syntax and my tech stack
5. ✅ Include proper error handling, types, and async patterns

**You must NOT:**
- ❌ Skip fetching latest documentation
- ❌ Use outdated API patterns from training data
- ❌ Ignore the skills file
- ❌ Use frameworks other than my specified stack
- ❌ Hardcode credentials

---

## Context7 MCP Usage (If Available)

When Context7 MCP server is connected, use these commands to fetch docs:

```
# Fetch OpenAI Agents SDK documentation
context7: resolve openai-agents-python

# Fetch FastMCP documentation  
context7: resolve fastmcp

# Fetch LiteLLM documentation
context7: resolve litellm
```

If Context7 returns documentation, use it as the primary source.
If Context7 is unavailable or returns errors, fall back to web search.

---

## Confirmation Protocol

When I ask you to build an agent, FIRST confirm:
```
📋 Agent Development Checklist:
□ Fetching latest docs via [Context7/Web Search]...
□ Reading skills file...
□ Reading relevant references: [list which ones]
□ Ready to generate code with current best practices
```

Then proceed with code generation.

---

## Remember

- **Latest docs FIRST** - Never rely solely on training data for API syntax
- **Skills file ALWAYS** - Contains my patterns and preferences
- **My stack ONLY** - Don't suggest alternative frameworks
- **Quality over speed** - Take time to get it right

This workflow ensures every agent I build uses current APIs, follows my standards, and works correctly in production.