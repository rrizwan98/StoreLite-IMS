#!/usr/bin/env python3
"""
Agent Boilerplate Generator

This script creates a complete agent project structure with all necessary files.
Run: python scripts/create_agent_project.py <project_name> [--output-dir <dir>]
"""

import argparse
import os
from pathlib import Path

# Templates
MAIN_PY = '''"""
{project_name} Agent - Entry Point
"""
import asyncio
import os
from dotenv import load_dotenv

from agents.main_agent import create_agent
from agents import Runner

load_dotenv()


async def main():
    agent = create_agent()
    
    print(f"{{agent.name}} is ready!")
    print("Type 'quit' to exit.")
    
    while True:
        user_input = input("\\nYou: ").strip()
        if user_input.lower() == "quit":
            break
        
        result = await Runner.run(agent, user_input)
        print(f"\\nAgent: {{result.final_output}}")


if __name__ == "__main__":
    asyncio.run(main())
'''

MAIN_AGENT_PY = '''"""
Main Agent Definition
"""
import os
from agents import Agent
from tools.custom_tools import example_tool

# For LiteLLM/Gemini support, uncomment:
# from agents.extensions.models.litellm_model import LitellmModel


def create_agent() -> Agent:
    """Create and configure the main agent."""
    
    # Default to OpenAI model
    model = os.environ.get("MODEL_NAME", "gpt-4o")
    
    # For Gemini via LiteLLM:
    # model = LitellmModel(
    #     model="gemini/gemini-2.0-flash-lite",
    #     api_key=os.environ["GEMINI_API_KEY"],
    # )
    
    return Agent(
        name="{project_name}Agent",
        instructions="""You are a helpful assistant.
        
Use available tools to help users with their requests.
Be concise and clear in your responses.""",
        model=model,
        tools=[example_tool],
    )
'''

CUSTOM_TOOLS_PY = '''"""
Custom Tool Definitions
"""
from agents import function_tool
from pydantic import BaseModel


class CalculationResult(BaseModel):
    """Structured calculation result."""
    expression: str
    result: float
    
    
@function_tool
def example_tool(query: str) -> str:
    """
    An example tool that echoes the query.
    
    Replace this with your actual tool implementation.
    
    Args:
        query: The user's query
        
    Returns:
        A response string
    """
    return f"You asked: {{query}}"


@function_tool
def calculate(expression: str) -> CalculationResult:
    """
    Evaluate a mathematical expression.
    
    Args:
        expression: A mathematical expression like "2 + 2"
        
    Returns:
        The calculation result
    """
    try:
        result = eval(expression)
        return CalculationResult(expression=expression, result=float(result))
    except Exception as e:
        return CalculationResult(expression=expression, result=0.0)
'''

MCP_SERVER_PY = '''"""
FastMCP Server for Local Development

Run: fastmcp run mcp_servers/server.py --transport streamable-http --port 8000
"""
from fastmcp import FastMCP

mcp = FastMCP("{project_name}Tools")


@mcp.tool
def search(query: str, limit: int = 10) -> list[dict]:
    """
    Search for items matching the query.
    
    Args:
        query: Search query string
        limit: Maximum results to return
        
    Returns:
        List of matching items
    """
    # Replace with actual implementation
    return [{{"id": 1, "title": f"Result for {{query}}"}}]


@mcp.tool
async def fetch_data(url: str) -> dict:
    """
    Fetch JSON data from a URL.
    
    Args:
        url: The URL to fetch
        
    Returns:
        JSON response data
    """
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()


@mcp.resource("config://{{key}}")
def get_config(key: str) -> str:
    """Get configuration value by key."""
    config = {{
        "version": "1.0.0",
        "environment": "development",
    }}
    return config.get(key, "")


if __name__ == "__main__":
    mcp.run()
'''

REQUIREMENTS_TXT = '''openai-agents>=0.6.0
fastmcp>=2.13.0
litellm>=1.50.0
pydantic>=2.0.0
asyncpg>=0.29.0
python-dotenv>=1.0.0
httpx>=0.27.0
'''

ENV_EXAMPLE = '''# OpenAI
OPENAI_API_KEY=sk-...

# LiteLLM / Gemini (optional)
GEMINI_API_KEY=

# Model Configuration
MODEL_NAME=gpt-4o
# MODEL_TYPE=gemini  # Uncomment to use Gemini

# PostgreSQL (for session management)
DATABASE_URL=postgresql://user:password@localhost:5432/agent_db

# MCP Server (Production)
MCP_SERVER_URL=http://localhost:8000/mcp
MCP_SERVER_TOKEN=
'''

CONFIG_PY = '''"""
Application Configuration
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Application configuration."""
    
    # OpenAI
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    
    # Gemini
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
    
    # Model
    model_name: str = os.environ.get("MODEL_NAME", "gpt-4o")
    model_type: str = os.environ.get("MODEL_TYPE", "openai")
    
    # Database
    database_url: str = os.environ.get("DATABASE_URL", "")
    
    # MCP
    mcp_server_url: str = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")
    mcp_server_token: str = os.environ.get("MCP_SERVER_TOKEN", "")
    
    @property
    def is_production(self) -> bool:
        return os.environ.get("ENVIRONMENT") == "production"


config = Config()
'''

INIT_PY = '''"""
{module_name} module
"""
'''


def create_project(project_name: str, output_dir: str = "."):
    """Create a complete agent project structure."""
    
    base_path = Path(output_dir) / project_name
    
    # Create directories
    directories = [
        "agents/sub_agents",
        "tools",
        "mcp_servers",
        "models",
        "sessions",
    ]
    
    for dir_path in directories:
        (base_path / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create files
    files = {
        "main.py": MAIN_PY.format(project_name=project_name),
        "config.py": CONFIG_PY,
        "requirements.txt": REQUIREMENTS_TXT,
        ".env.example": ENV_EXAMPLE,
        "agents/__init__.py": INIT_PY.format(module_name="agents"),
        "agents/main_agent.py": MAIN_AGENT_PY.format(project_name=project_name),
        "agents/sub_agents/__init__.py": INIT_PY.format(module_name="sub_agents"),
        "tools/__init__.py": INIT_PY.format(module_name="tools"),
        "tools/custom_tools.py": CUSTOM_TOOLS_PY,
        "mcp_servers/__init__.py": INIT_PY.format(module_name="mcp_servers"),
        "mcp_servers/server.py": MCP_SERVER_PY.format(project_name=project_name),
        "models/__init__.py": INIT_PY.format(module_name="models"),
        "sessions/__init__.py": INIT_PY.format(module_name="sessions"),
    }
    
    for file_path, content in files.items():
        full_path = base_path / file_path
        full_path.write_text(content)
        print(f"  Created: {file_path}")
    
    print(f"\n✅ Project '{project_name}' created at {base_path}")
    print("\nNext steps:")
    print(f"  1. cd {base_path}")
    print("  2. cp .env.example .env")
    print("  3. Edit .env with your API keys")
    print("  4. pip install -r requirements.txt")
    print("  5. python main.py")


def main():
    parser = argparse.ArgumentParser(description="Create agent project boilerplate")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    
    args = parser.parse_args()
    create_project(args.project_name, args.output_dir)


if __name__ == "__main__":
    main()
