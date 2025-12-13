# MCP Server Patterns

Patterns for building and connecting MCP servers with FastMCP (local) and self-hosted (production).

## FastMCP Server (Development)

### Basic FastMCP Server

```python
# mcp_servers/server.py
from fastmcp import FastMCP

mcp = FastMCP("MyTools")

@mcp.tool
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    return eval(expression)

@mcp.tool
async def fetch_data(url: str) -> dict:
    """Fetch JSON data from a URL."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

@mcp.resource("config://{key}")
def get_config(key: str) -> str:
    """Get configuration value."""
    config = {"api_version": "v1", "max_retries": "3"}
    return config.get(key, "")

if __name__ == "__main__":
    mcp.run()  # Default: stdio transport
```

### Run FastMCP Server Locally

```bash
# Development (stdio - for local testing)
python mcp_servers/server.py

# Development (HTTP - for agent connection)
fastmcp run mcp_servers/server.py --transport streamable-http --port 8000

# Or programmatically:
if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8000)
```

## Connecting Agent to MCP Server

### Local Development (Stdio)

```python
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from agents.model_settings import ModelSettings

async def main():
    async with MCPServerStdio(
        name="LocalTools",
        params={
            "command": "python",
            "args": ["mcp_servers/server.py"],
        },
        cache_tools_list=True,  # Cache for performance
    ) as server:
        agent = Agent(
            name="MCPAgent",
            instructions="Use available tools to help the user.",
            mcp_servers=[server],
            model_settings=ModelSettings(tool_choice="auto"),
        )
        
        result = await Runner.run(agent, "Calculate 15 * 7")
        print(result.final_output)

asyncio.run(main())
```

### Local Development (HTTP)

```python
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

async def main():
    async with MCPServerStreamableHttp(
        name="LocalHTTPTools",
        params={
            "url": "http://localhost:8000/mcp",
            "timeout": 10,
        },
        cache_tools_list=True,
        max_retry_attempts=3,
    ) as server:
        agent = Agent(
            name="MCPAgent",
            instructions="Use available tools to help the user.",
            mcp_servers=[server],
        )
        
        result = await Runner.run(agent, "Fetch data from an API")
        print(result.final_output)

asyncio.run(main())
```

### Production (Self-Hosted MCP Server)

```python
import os
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

async def main():
    token = os.environ["MCP_SERVER_TOKEN"]
    server_url = os.environ["MCP_SERVER_URL"]
    
    async with MCPServerStreamableHttp(
        name="ProductionTools",
        params={
            "url": server_url,
            "headers": {"Authorization": f"Bearer {token}"},
            "timeout": 30,
        },
        cache_tools_list=True,
        max_retry_attempts=3,
    ) as server:
        agent = Agent(
            name="ProductionAgent",
            instructions="Use available tools to help the user.",
            mcp_servers=[server],
        )
        
        result = await Runner.run(agent, "Process this request")
        print(result.final_output)

asyncio.run(main())
```

## Production FastMCP Server Setup

### Server with Authentication

```python
# mcp_servers/production_server.py
from fastmcp import FastMCP
from fastmcp.auth import BearerAuth
import os

mcp = FastMCP(
    "ProductionTools",
    auth=BearerAuth(token=os.environ["MCP_AUTH_TOKEN"]),
)

@mcp.tool
async def process_order(order_id: str) -> dict:
    """Process an order by ID."""
    # Implementation
    return {"status": "processed", "order_id": order_id}

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
    )
```

### Dockerfile for MCP Server

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_servers/ ./mcp_servers/

EXPOSE 8000

CMD ["python", "-m", "fastmcp", "run", "mcp_servers/production_server.py", \
     "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
```

## Combining Function Tools and MCP

```python
from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerStreamableHttp

@function_tool
def local_calculation(x: int, y: int) -> int:
    """Perform local calculation."""
    return x + y

async def main():
    async with MCPServerStreamableHttp(
        name="RemoteTools",
        params={"url": "http://localhost:8000/mcp"},
        cache_tools_list=True,
    ) as mcp_server:
        agent = Agent(
            name="HybridAgent",
            instructions="Use both local and remote tools.",
            tools=[local_calculation],  # Function tools
            mcp_servers=[mcp_server],   # MCP tools
        )
        
        result = await Runner.run(agent, "Add 5 and 3, then fetch some data")
        print(result.final_output)

asyncio.run(main())
```

## Multiple MCP Servers

```python
async def main():
    async with MCPServerStreamableHttp(
        name="DatabaseTools",
        params={"url": "http://localhost:8001/mcp"},
    ) as db_server, MCPServerStreamableHttp(
        name="APITools", 
        params={"url": "http://localhost:8002/mcp"},
    ) as api_server:
        agent = Agent(
            name="MultiServerAgent",
            instructions="Use database and API tools as needed.",
            mcp_servers=[db_server, api_server],
        )
        
        result = await Runner.run(agent, "Query the database and call the API")
        print(result.final_output)
```

## Environment-Based Configuration

```python
import os

def get_mcp_config():
    """Get MCP configuration based on environment."""
    env = os.environ.get("ENVIRONMENT", "development")
    
    if env == "production":
        return {
            "url": os.environ["MCP_SERVER_URL"],
            "headers": {"Authorization": f"Bearer {os.environ['MCP_SERVER_TOKEN']}"},
            "timeout": 30,
        }
    else:
        return {
            "url": "http://localhost:8000/mcp",
            "timeout": 10,
        }
```

## Best Practices

1. **Always cache tools** - Set `cache_tools_list=True` for performance
2. **Use retry logic** - Set `max_retry_attempts=3` for reliability
3. **Environment variables** - Never hardcode URLs or tokens
4. **Timeouts** - Set appropriate timeouts for your use case
5. **Health checks** - Implement `/health` endpoint in production servers
6. **Logging** - Add structured logging for debugging