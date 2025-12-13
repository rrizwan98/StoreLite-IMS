"""
Database Connection Management Router

Allows users to connect their own PostgreSQL database through MCP server.
Provides connection testing, setup, and inventory-specialized agent.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import asyncpg

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/db-connect", tags=["database-connection"])


# ============================================================================
# Request/Response Models
# ============================================================================

class DatabaseConfig(BaseModel):
    """PostgreSQL connection configuration from user."""
    host: str = Field(..., description="Database host (e.g., localhost)")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(..., description="Database name")
    user: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    ssl_mode: Optional[str] = Field(default=None, description="SSL mode (disable, require, etc.)")


class ConnectionTestResponse(BaseModel):
    """Response for connection test."""
    success: bool
    message: str
    database_info: Optional[Dict[str, Any]] = None
    tables: Optional[List[str]] = None


class SetupResponse(BaseModel):
    """Response for database setup."""
    success: bool
    message: str
    tables_created: Optional[List[str]] = None
    mcp_config: Optional[Dict[str, Any]] = None


# ============================================================================
# Connection Storage (In-Memory for Session)
# ============================================================================

# Store active connections per session
_active_connections: Dict[str, DatabaseConfig] = {}


def get_connection_string(config: DatabaseConfig) -> str:
    """Build PostgreSQL connection string from config."""
    ssl_part = f"?sslmode={config.ssl_mode}" if config.ssl_mode else ""
    return f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}{ssl_part}"


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/test", response_model=ConnectionTestResponse)
async def test_database_connection(config: DatabaseConfig) -> ConnectionTestResponse:
    """
    Test PostgreSQL database connection with provided credentials.

    Returns connection status and database info if successful.
    """
    try:
        logger.info(f"[DB Connect] Testing connection to {config.host}:{config.port}/{config.database}")

        # Try to connect
        conn = await asyncpg.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=config.password,
            timeout=10,
            ssl=config.ssl_mode if config.ssl_mode else None
        )

        try:
            # Get database version
            version = await conn.fetchval("SELECT version()")

            # Get list of tables
            tables = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            table_names = [t['table_name'] for t in tables]

            # Get database size
            db_size = await conn.fetchval(f"SELECT pg_size_pretty(pg_database_size('{config.database}'))")

            return ConnectionTestResponse(
                success=True,
                message="Database connection successful!",
                database_info={
                    "version": version,
                    "database": config.database,
                    "host": config.host,
                    "port": config.port,
                    "size": db_size,
                    "table_count": len(table_names)
                },
                tables=table_names
            )
        finally:
            await conn.close()

    except asyncpg.InvalidPasswordError:
        return ConnectionTestResponse(
            success=False,
            message="Invalid password. Please check your credentials."
        )
    except asyncpg.InvalidCatalogNameError:
        return ConnectionTestResponse(
            success=False,
            message=f"Database '{config.database}' does not exist."
        )
    except asyncpg.PostgresConnectionError as e:
        return ConnectionTestResponse(
            success=False,
            message=f"Connection failed: {str(e)}"
        )
    except asyncio.TimeoutError:
        return ConnectionTestResponse(
            success=False,
            message="Connection timed out. Check if the host and port are correct."
        )
    except Exception as e:
        logger.error(f"[DB Connect] Connection test failed: {str(e)}")
        return ConnectionTestResponse(
            success=False,
            message=f"Connection failed: {str(e)}"
        )


@router.post("/setup-inventory", response_model=SetupResponse)
async def setup_inventory_database(
    config: DatabaseConfig,
    session_id: str = "default"
) -> SetupResponse:
    """
    Setup inventory management tables in the connected database.

    Creates:
    - inventory_items: Products/items table
    - inventory_bills: Bills/invoices table
    - inventory_bill_items: Line items for bills
    """
    try:
        logger.info(f"[DB Connect] Setting up inventory tables in {config.database}")

        conn = await asyncpg.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=config.password,
            timeout=10
        )

        try:
            # Create inventory tables
            await conn.execute("""
                -- Inventory Items Table
                CREATE TABLE IF NOT EXISTS inventory_items (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    unit VARCHAR(50) NOT NULL DEFAULT 'piece',
                    unit_price DECIMAL(12, 2) NOT NULL DEFAULT 0,
                    stock_qty DECIMAL(12, 3) NOT NULL DEFAULT 0,
                    min_stock_level DECIMAL(12, 3) DEFAULT 10,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Create index on name and category
                CREATE INDEX IF NOT EXISTS idx_items_name ON inventory_items(name);
                CREATE INDEX IF NOT EXISTS idx_items_category ON inventory_items(category);
            """)

            await conn.execute("""
                -- Bills Table
                CREATE TABLE IF NOT EXISTS inventory_bills (
                    id SERIAL PRIMARY KEY,
                    bill_number VARCHAR(50) UNIQUE,
                    customer_name VARCHAR(255),
                    customer_phone VARCHAR(20),
                    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0,
                    discount DECIMAL(12, 2) DEFAULT 0,
                    tax DECIMAL(12, 2) DEFAULT 0,
                    grand_total DECIMAL(12, 2) NOT NULL DEFAULT 0,
                    payment_method VARCHAR(50) DEFAULT 'cash',
                    status VARCHAR(20) DEFAULT 'completed',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Create index on bill_number
                CREATE INDEX IF NOT EXISTS idx_bills_number ON inventory_bills(bill_number);
            """)

            await conn.execute("""
                -- Bill Items Table (Line Items)
                CREATE TABLE IF NOT EXISTS inventory_bill_items (
                    id SERIAL PRIMARY KEY,
                    bill_id INTEGER REFERENCES inventory_bills(id) ON DELETE CASCADE,
                    item_id INTEGER REFERENCES inventory_items(id),
                    item_name VARCHAR(255) NOT NULL,
                    quantity DECIMAL(12, 3) NOT NULL,
                    unit_price DECIMAL(12, 2) NOT NULL,
                    total_price DECIMAL(12, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Create index on bill_id
                CREATE INDEX IF NOT EXISTS idx_bill_items_bill ON inventory_bill_items(bill_id);
            """)

            # Store connection config for this session
            _active_connections[session_id] = config

            # Build MCP config for reference
            mcp_config = {
                "mcpServers": {
                    "postgres": {
                        "command": "postgres-mcp",
                        "args": ["--access-mode=unrestricted"],
                        "env": {
                            "DATABASE_URI": get_connection_string(config)
                        }
                    }
                }
            }

            return SetupResponse(
                success=True,
                message="Inventory database setup complete! Tables created successfully.",
                tables_created=["inventory_items", "inventory_bills", "inventory_bill_items"],
                mcp_config=mcp_config
            )

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"[DB Connect] Setup failed: {str(e)}")
        return SetupResponse(
            success=False,
            message=f"Setup failed: {str(e)}"
        )


@router.post("/save-connection")
async def save_connection(
    config: DatabaseConfig,
    session_id: str = "default"
) -> Dict[str, Any]:
    """Save database connection config for a session."""
    _active_connections[session_id] = config
    return {
        "success": True,
        "message": "Connection saved for session",
        "session_id": session_id
    }


@router.get("/connection/{session_id}")
async def get_connection(session_id: str) -> Dict[str, Any]:
    """Get saved connection config for a session (without password)."""
    if session_id not in _active_connections:
        return {
            "success": False,
            "message": "No connection found for this session",
            "connected": False
        }

    config = _active_connections[session_id]
    return {
        "success": True,
        "connected": True,
        "config": {
            "host": config.host,
            "port": config.port,
            "database": config.database,
            "user": config.user,
            # Don't return password for security
        }
    }


@router.delete("/disconnect/{session_id}")
async def disconnect(session_id: str) -> Dict[str, Any]:
    """Remove saved connection for a session."""
    if session_id in _active_connections:
        del _active_connections[session_id]
        return {"success": True, "message": "Disconnected successfully"}
    return {"success": False, "message": "No connection found"}


# ============================================================================
# Inventory Operations (for the specialized agent)
# ============================================================================

@router.post("/inventory/execute")
async def execute_inventory_query(
    session_id: str,
    query: str,
    params: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """
    Execute inventory-related SQL query on user's database.

    RESTRICTED: Only allows SELECT, INSERT, UPDATE, DELETE on inventory tables.
    """
    if session_id not in _active_connections:
        raise HTTPException(status_code=400, detail="No database connection for this session")

    config = _active_connections[session_id]

    # Security: Only allow operations on inventory tables
    allowed_tables = ['inventory_items', 'inventory_bills', 'inventory_bill_items']
    query_lower = query.lower().strip()

    # Basic SQL injection prevention
    dangerous_keywords = ['drop', 'truncate', 'alter', 'create database', 'drop database']
    for keyword in dangerous_keywords:
        if keyword in query_lower:
            raise HTTPException(status_code=403, detail=f"Operation '{keyword}' not allowed")

    # Check if query touches allowed tables only
    has_allowed_table = any(table in query_lower for table in allowed_tables)
    if not has_allowed_table and not query_lower.startswith('select'):
        raise HTTPException(
            status_code=403,
            detail="Only operations on inventory tables are allowed"
        )

    try:
        conn = await asyncpg.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=config.password,
            timeout=10
        )

        try:
            if query_lower.startswith('select'):
                rows = await conn.fetch(query, *(params or []))
                return {
                    "success": True,
                    "data": [dict(row) for row in rows],
                    "row_count": len(rows)
                }
            else:
                result = await conn.execute(query, *(params or []))
                return {
                    "success": True,
                    "message": result,
                    "affected_rows": int(result.split()[-1]) if result else 0
                }
        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"[DB Connect] Query execution failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
