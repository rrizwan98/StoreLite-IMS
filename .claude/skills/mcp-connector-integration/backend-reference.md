# Backend Reference for MCP Connector Integration

This document provides detailed backend implementation patterns for MCP connector integrations.

## Directory Structure

```
backend/
  app/
    connector_agents/
      __init__.py                 # Exports all agents
      base.py                     # BaseConnectorAgent abstract class
      registry.py                 # ConnectorAgentRegistry + get_connector_agent_tools
      notion_agent.py             # Example: Notion implementation
      [new]_agent.py              # Your new connector agent
    connectors/
      __init__.py
      encryption.py               # encrypt_credentials / decrypt_credentials
      mcp_client.py               # UserMCPClient for MCP communication
      validator.py                # validate_mcp_connection
      agent_tools.py              # Helper functions
    routers/
      connectors.py               # CRUD endpoints for connectors
      schema_agent.py             # Main agent with ChatKit integration
    models.py                     # UserMCPConnection model
    schemas.py                    # Pydantic models
```

## Base Connector Agent

The `BaseConnectorAgent` class provides the foundation for all connector sub-agents:

```python
# backend/app/connector_agents/base.py

class BaseConnectorAgent(ABC):
    """Abstract base class for connector sub-agents."""

    CONNECTOR_TYPE: str = "base"      # Override: e.g., "Slack"
    TOOL_NAME: str = "connector"       # Override: e.g., "slack_connector"
    TOOL_DESCRIPTION: str = "..."      # Override with capabilities

    def __init__(
        self,
        connector_id: int,
        connector_name: str,
        server_url: str,
        auth_config: Dict[str, Any],
        user_id: int,
    ):
        self.connector_id = connector_id
        self.connector_name = connector_name
        self.server_url = server_url
        self.auth_config = auth_config
        self.user_id = user_id
        self._agent: Optional[Agent] = None
        self._tools: List[FunctionTool] = []
        self._is_initialized = False

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this connector agent."""
        pass

    @abstractmethod
    async def load_tools(self) -> List[FunctionTool]:
        """Load MCP tools from the connector's MCP server."""
        pass

    async def initialize(self) -> bool:
        """Initialize the agent with tools and instructions."""
        # Loads tools, creates Agent instance
        pass

    def as_tool(self, is_enabled: bool = True) -> Optional[Any]:
        """Convert this agent to a tool for the main schema_agent."""
        return self._agent.as_tool(
            tool_name=self.TOOL_NAME,
            tool_description=self.TOOL_DESCRIPTION,
            is_enabled=is_enabled,
        )
```

## Registry Pattern

The registry maps connector types to agent classes:

```python
# backend/app/connector_agents/registry.py

class ConnectorAgentRegistry:
    # Add new connectors here
    AGENT_CLASSES: Dict[str, Type[BaseConnectorAgent]] = {
        "notion": NotionConnectorAgent,
        "slack": SlackConnectorAgent,        # Example
        "airtable": AirtableConnectorAgent,  # Example
    }

    # URL patterns for auto-detection
    URL_PATTERNS: Dict[str, str] = {
        "notion": "notion",
        "slack": "slack",
        "airtable": "airtable",
    }

    def detect_connector_type(self, connector: UserMCPConnection) -> Optional[str]:
        """Detect connector type from URL or name."""
        url_lower = connector.server_url.lower()
        for pattern, conn_type in self.URL_PATTERNS.items():
            if pattern in url_lower:
                return conn_type
        return None

    async def create_agent(
        self,
        connector: UserMCPConnection,
        connector_type: str,
        decrypted_config: Dict[str, Any],
    ) -> Optional[BaseConnectorAgent]:
        """Create and initialize a connector agent."""
        agent_class = self.AGENT_CLASSES.get(connector_type)
        if not agent_class:
            return None

        agent = agent_class(
            connector_id=connector.id,
            connector_name=connector.name,
            server_url=connector.server_url,
            auth_config=decrypted_config,
            user_id=connector.user_id,
        )

        success = await agent.initialize()
        return agent if success else None
```

## MCP Client

The `UserMCPClient` handles communication with MCP servers:

```python
# backend/app/connectors/mcp_client.py

class UserMCPClient:
    """Client for connecting to user's MCP servers."""

    def __init__(
        self,
        server_url: str,
        timeout: float = 30.0,
        auth_type: str = "none",
        auth_config: Optional[Dict[str, Any]] = None,
    ):
        self.server_url = server_url
        self.timeout = timeout
        self.auth_type = auth_type
        self.auth_config = auth_config or {}

    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover available tools from the MCP server."""
        # Returns list of tool definitions with name, description, inputSchema
        pass

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a specific tool on the MCP server."""
        pass
```

## Credential Encryption

Always encrypt OAuth tokens before storing:

```python
# backend/app/connectors/encryption.py

def encrypt_credentials(credentials: Dict[str, Any]) -> str:
    """Encrypt credentials dict to encrypted string."""
    pass

def decrypt_credentials(encrypted: str) -> Dict[str, Any]:
    """Decrypt encrypted string back to credentials dict."""
    pass
```

## Database Model

```python
# backend/app/models.py

class UserMCPConnection(Base):
    __tablename__ = "user_mcp_connections"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    server_url = Column(String(1024), nullable=False)
    auth_type = Column(String(50), default="none")  # none, api_key, oauth
    auth_config = Column(Text, nullable=True)  # Encrypted JSON
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    discovered_tools = Column(JSON, nullable=True)
    last_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    @property
    def tool_count(self) -> int:
        return len(self.discovered_tools) if self.discovered_tools else 0
```

## Integration with Schema Agent

The schema_agent loads connector tools via the registry:

```python
# In schema_agent.py router

# Load connector sub-agents as tools
connector_tools = await get_connector_agent_tools(db_session, user_id)

# Create agent with connector tools
agent = await create_schema_query_agent(
    database_uri=database_uri,
    schema_metadata=schema_metadata,
    user_id=user_id,
    connector_tools=connector_tools,  # Sub-agents as tools
)
```

## API Endpoints

Key endpoints in `backend/app/routers/connectors.py`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/connectors` | List user's connectors |
| POST | `/api/connectors` | Create new connector |
| GET | `/api/connectors/{id}` | Get specific connector |
| PUT | `/api/connectors/{id}` | Update connector |
| DELETE | `/api/connectors/{id}` | Delete connector |
| POST | `/api/connectors/{id}/verify` | Verify connection |
| GET | `/api/connectors/{id}/health` | Health check |
| POST | `/api/connectors/{id}/toggle` | Toggle active status |
| POST | `/api/connectors/{id}/refresh` | Refresh tools |

## Environment Variables

```bash
# backend/.env

# Encryption key for storing OAuth tokens
TOKEN_ENCRYPTION_KEY=your_32_byte_key_here

# Per-connector OAuth credentials (if backend handles token exchange)
NOTION_CLIENT_ID=...
NOTION_CLIENT_SECRET=...

SLACK_CLIENT_ID=...
SLACK_CLIENT_SECRET=...
```

## Testing Connector Agent

```python
# Test script
import asyncio
from app.connector_agents.new_connector_agent import NewConnectorAgent

async def test():
    agent = NewConnectorAgent(
        connector_id=1,
        connector_name="Test",
        server_url="https://mcp.service.com/mcp",
        auth_config={"access_token": "test_token"},
        user_id=1,
    )

    success = await agent.initialize()
    print(f"Initialized: {success}")
    print(f"Tools: {agent.tool_count}")

    # Test as tool
    tool = agent.as_tool()
    print(f"Tool name: {tool.name}")

asyncio.run(test())
```

## Error Handling Patterns

```python
async def load_tools(self) -> List[FunctionTool]:
    try:
        client = UserMCPClient(...)
        mcp_tools = await client.discover_tools()
        return [self._create_function_tool(t) for t in mcp_tools]
    except ConnectionError as e:
        logger.error(f"MCP connection failed: {e}")
        return []
    except AuthenticationError as e:
        logger.error(f"OAuth token invalid: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []
```

## Streaming Progress Messages

Tool outputs should include connector context for UI streaming:

```python
# In tool caller function
return f"[{connector_name}:{tool_name}] {result_text}"
```

This format is parsed by the streaming handler to show messages like:
- "Slack: message-send completed"
- "Airtable: create-record completed"
