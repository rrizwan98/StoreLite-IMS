"""
FastMCP server package for IMS backend

Provides MCP tool implementations for inventory and billing operations.
"""

__version__ = "0.1.0"

from .server import create_server

__all__ = [
    "create_server",
]
