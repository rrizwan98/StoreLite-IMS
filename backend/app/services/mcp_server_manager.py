"""
MCP Server Manager - HTTP/SSE Transport for Fast Response Times

This service manages postgres-mcp servers running in HTTP/SSE mode instead of
stdio mode. This dramatically reduces response times from ~60 seconds to ~2-3 seconds.

Why HTTP/SSE is faster:
- Stdio: Each query spawns a new subprocess (~30-60s startup)
- HTTP/SSE: Server runs persistently, instant connections (~1-2s)

Architecture:
- Each user gets their own postgres-mcp server (data isolation)
- Servers are started on database connect
- Servers are stopped on database disconnect
- Automatic port assignment and cleanup

Version: 1.0.0
"""

import asyncio
import logging
import os
import subprocess
import time
import socket
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

# Base port for MCP servers (each user gets base_port + user_id % 1000)
MCP_BASE_PORT = int(os.getenv("MCP_BASE_PORT", "9000"))
MCP_PORT_RANGE = int(os.getenv("MCP_PORT_RANGE", "1000"))

# Server startup timeout
MCP_STARTUP_TIMEOUT = float(os.getenv("MCP_STARTUP_TIMEOUT", "30.0"))

# Health check interval
MCP_HEALTH_CHECK_INTERVAL = int(os.getenv("MCP_HEALTH_CHECK_INTERVAL", "60"))


# ============================================================================
# MCP Server Entry
# ============================================================================

@dataclass
class MCPServerEntry:
    """Represents a running postgres-mcp HTTP server."""
    user_id: int
    database_uri: str
    access_mode: str
    port: int
    process: Optional[subprocess.Popen] = None
    started_at: float = field(default_factory=time.time)
    last_health_check: float = field(default_factory=time.time)
    is_healthy: bool = True
    url: str = ""

    def __post_init__(self):
        self.url = f"http://localhost:{self.port}/sse"

    @property
    def age_seconds(self) -> float:
        return time.time() - self.started_at

    def is_running(self) -> bool:
        """Check if the process is still running."""
        if self.process is None:
            return False
        return self.process.poll() is None


# ============================================================================
# Port Manager
# ============================================================================

def find_available_port(start_port: int, end_port: int) -> Optional[int]:
    """Find an available port in the given range."""
    for port in range(start_port, end_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None


def is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return False
    except OSError:
        return True


# ============================================================================
# MCP Server Manager
# ============================================================================

class MCPServerManager:
    """
    Manages postgres-mcp HTTP/SSE servers for each user.

    Each user gets their own isolated server instance running on a unique port.
    Servers persist across queries, providing instant connection times.
    """

    def __init__(self):
        # Active servers: {user_id: MCPServerEntry}
        self._servers: Dict[int, MCPServerEntry] = {}
        self._locks: Dict[int, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

        # Background health check task
        self._health_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info("[MCPServerManager] Initialized")

    async def _get_user_lock(self, user_id: int) -> asyncio.Lock:
        """Get or create a lock for a specific user."""
        if user_id not in self._locks:
            async with self._global_lock:
                if user_id not in self._locks:
                    self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    def _get_port_for_user(self, user_id: int) -> int:
        """Get a deterministic port for a user, or find an available one."""
        # Try deterministic port first
        target_port = MCP_BASE_PORT + (user_id % MCP_PORT_RANGE)

        if not is_port_in_use(target_port):
            return target_port

        # If deterministic port is in use, find any available port
        available = find_available_port(MCP_BASE_PORT, MCP_BASE_PORT + MCP_PORT_RANGE)
        if available:
            return available

        raise RuntimeError(f"No available ports in range {MCP_BASE_PORT}-{MCP_BASE_PORT + MCP_PORT_RANGE}")

    async def start_server(
        self,
        user_id: int,
        database_uri: str,
        access_mode: str = "restricted"
    ) -> MCPServerEntry:
        """
        Start a postgres-mcp HTTP server for a user.

        If server is already running, returns existing entry.

        Args:
            user_id: User ID for server isolation
            database_uri: PostgreSQL connection string
            access_mode: "restricted" (read-only) or "unrestricted"

        Returns:
            MCPServerEntry with server details
        """
        lock = await self._get_user_lock(user_id)

        async with lock:
            # Check if server already exists and is healthy
            if user_id in self._servers:
                entry = self._servers[user_id]
                if entry.is_running() and entry.database_uri == database_uri:
                    logger.info(f"[MCPServerManager] Reusing existing server for user {user_id} on port {entry.port}")
                    return entry
                else:
                    # Server died or database changed, restart it
                    await self._stop_server_internal(entry)

            # Get port
            port = self._get_port_for_user(user_id)

            logger.info(f"[MCPServerManager] Starting postgres-mcp for user {user_id} on port {port}")

            # Start postgres-mcp with SSE transport
            try:
                # Command: postgres-mcp <database_uri> --access-mode=<mode> --transport=sse --sse-port=<port>
                cmd = [
                    "postgres-mcp",
                    database_uri,
                    f"--access-mode={access_mode}",
                    "--transport=sse",
                    f"--sse-port={port}",
                ]

                # Start process
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    # Don't use shell=True for security
                )

                # Wait for server to start
                start_time = time.time()
                while time.time() - start_time < MCP_STARTUP_TIMEOUT:
                    if is_port_in_use(port):
                        logger.info(f"[MCPServerManager] Server started on port {port}")
                        break
                    if process.poll() is not None:
                        # Process exited
                        stderr = process.stderr.read().decode() if process.stderr else ""
                        raise RuntimeError(f"postgres-mcp failed to start: {stderr}")
                    await asyncio.sleep(0.5)
                else:
                    # Timeout
                    process.kill()
                    raise RuntimeError(f"postgres-mcp startup timeout ({MCP_STARTUP_TIMEOUT}s)")

                # Create entry
                entry = MCPServerEntry(
                    user_id=user_id,
                    database_uri=database_uri,
                    access_mode=access_mode,
                    port=port,
                    process=process,
                )

                self._servers[user_id] = entry
                logger.info(f"[MCPServerManager] Server ready for user {user_id}: {entry.url}")

                return entry

            except Exception as e:
                logger.error(f"[MCPServerManager] Failed to start server for user {user_id}: {e}")
                raise

    async def _stop_server_internal(self, entry: MCPServerEntry):
        """Stop a server (internal, no lock)."""
        if entry.process and entry.is_running():
            try:
                entry.process.terminate()
                try:
                    entry.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    entry.process.kill()
                logger.info(f"[MCPServerManager] Stopped server for user {entry.user_id}")
            except Exception as e:
                logger.warning(f"[MCPServerManager] Error stopping server: {e}")

    async def stop_server(self, user_id: int):
        """Stop the MCP server for a user."""
        lock = await self._get_user_lock(user_id)

        async with lock:
            if user_id in self._servers:
                entry = self._servers[user_id]
                await self._stop_server_internal(entry)
                del self._servers[user_id]
                logger.info(f"[MCPServerManager] Server stopped and removed for user {user_id}")

    async def stop_all_servers(self):
        """Stop all running MCP servers."""
        async with self._global_lock:
            for user_id in list(self._servers.keys()):
                await self.stop_server(user_id)
            self._servers.clear()
            logger.info("[MCPServerManager] All servers stopped")

    def get_server(self, user_id: int) -> Optional[MCPServerEntry]:
        """Get the server entry for a user (if exists and running)."""
        entry = self._servers.get(user_id)
        if entry and entry.is_running():
            return entry
        return None

    def get_server_url(self, user_id: int) -> Optional[str]:
        """Get the SSE URL for a user's server."""
        entry = self.get_server(user_id)
        return entry.url if entry else None

    async def ensure_server(
        self,
        user_id: int,
        database_uri: str,
        access_mode: str = "restricted"
    ) -> str:
        """
        Ensure a server is running and return its URL.

        This is the main method to call from query handlers.

        Args:
            user_id: User ID
            database_uri: PostgreSQL connection string
            access_mode: "restricted" or "unrestricted"

        Returns:
            SSE URL for the server
        """
        entry = await self.start_server(user_id, database_uri, access_mode)
        return entry.url

    async def _health_check_loop(self):
        """Background health check for all servers."""
        while self._running:
            try:
                await asyncio.sleep(MCP_HEALTH_CHECK_INTERVAL)

                async with self._global_lock:
                    dead_servers = []
                    for user_id, entry in self._servers.items():
                        if not entry.is_running():
                            logger.warning(f"[MCPServerManager] Server for user {user_id} died")
                            dead_servers.append(user_id)
                        else:
                            entry.last_health_check = time.time()

                    # Clean up dead servers
                    for user_id in dead_servers:
                        del self._servers[user_id]

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[MCPServerManager] Health check error: {e}")

    def start_health_checks(self):
        """Start background health check task."""
        if not self._running:
            self._running = True
            self._health_task = asyncio.create_task(self._health_check_loop())
            logger.info("[MCPServerManager] Health check task started")

    async def stop_health_checks(self):
        """Stop background health check task."""
        self._running = False
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
            logger.info("[MCPServerManager] Health check task stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            "total_servers": len(self._servers),
            "servers": {
                user_id: {
                    "port": entry.port,
                    "url": entry.url,
                    "age_seconds": entry.age_seconds,
                    "is_running": entry.is_running(),
                    "access_mode": entry.access_mode,
                }
                for user_id, entry in self._servers.items()
            },
            "config": {
                "base_port": MCP_BASE_PORT,
                "port_range": MCP_PORT_RANGE,
                "startup_timeout": MCP_STARTUP_TIMEOUT,
            }
        }


# ============================================================================
# Global Manager Instance
# ============================================================================

_manager: Optional[MCPServerManager] = None


def get_mcp_server_manager() -> MCPServerManager:
    """Get the global MCP server manager instance."""
    global _manager
    if _manager is None:
        _manager = MCPServerManager()
    return _manager


async def shutdown_mcp_server_manager():
    """Shutdown the global MCP server manager."""
    global _manager
    if _manager:
        await _manager.stop_health_checks()
        await _manager.stop_all_servers()
        _manager = None
        logger.info("[MCPServerManager] Shutdown complete")


# ============================================================================
# Convenience Functions
# ============================================================================

async def ensure_mcp_server_for_user(
    user_id: int,
    database_uri: str,
    access_mode: str = "restricted"
) -> str:
    """
    Convenience function to ensure an MCP server is running for a user.

    Returns the SSE URL to connect to.
    """
    manager = get_mcp_server_manager()
    return await manager.ensure_server(user_id, database_uri, access_mode)


async def stop_mcp_server_for_user(user_id: int):
    """Stop the MCP server for a user."""
    manager = get_mcp_server_manager()
    await manager.stop_server(user_id)
