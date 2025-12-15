"""
Authentication Router

Handles user signup, login, logout, and token refresh.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models import User, UserConnection
from app.services.auth_service import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    create_user,
    authenticate_user,
    create_tokens,
    decode_token,
    get_user_by_id,
    create_refresh_token,
    create_access_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme
security = HTTPBearer(auto_error=False)


# ============================================================================
# Request/Response Models
# ============================================================================

class SignupRequest(BaseModel):
    """Signup request body"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request body"""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class ConnectionChoiceRequest(BaseModel):
    """User's service choice"""
    connection_type: str  # 'own_database', 'our_database', or 'schema_query_only'
    database_uri: Optional[str] = None  # Required if connection_type is 'own_database' or 'schema_query_only'


class UserWithConnectionResponse(BaseModel):
    """User response with connection info"""
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    has_connection: bool
    connection_type: Optional[str]
    mcp_status: Optional[str]
    database_connected: bool

    model_config = {"from_attributes": True}


# ============================================================================
# Dependency: Get Current User
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    token_data = decode_token(token)

    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await get_user_by_id(db, token_data.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is disabled")

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Optional user dependency - returns None if not authenticated.
    Useful for routes that work differently for logged-in users.
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        token_data = decode_token(token)
        if not token_data:
            return None
        user = await get_user_by_id(db, token_data.user_id)
        return user if user and user.is_active else None
    except Exception:
        return None


# ============================================================================
# Auth Endpoints
# ============================================================================

@router.post("/signup", response_model=Token)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new user account.

    Returns JWT tokens on success.
    """
    try:
        user_data = UserCreate(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        user = await create_user(db, user_data)

        # Generate tokens
        tokens = create_tokens(user.id, user.email)

        logger.info(f"[Auth] New user registered: {user.email}")
        return tokens

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Auth] Signup error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=Token)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return JWT tokens.
    """
    user = await authenticate_user(db, request.email, request.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Generate tokens
    tokens = create_tokens(user.id, user.email)

    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Refresh access token using refresh token.
    """
    token_data = decode_token(request.refresh_token)

    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = await get_user_by_id(db, token_data.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Generate new tokens
    tokens = create_tokens(user.id, user.email)

    return tokens


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    """
    Logout user (client should discard tokens).

    Note: JWT tokens are stateless, so this just confirms the logout.
    For true token invalidation, implement a token blacklist.
    """
    logger.info(f"[Auth] User logged out: {user.email}")
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserWithConnectionResponse)
async def get_me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user info including connection status.
    """
    # Get user's connection info
    result = await db.execute(
        select(UserConnection).where(UserConnection.user_id == user.id)
    )
    connection = result.scalar_one_or_none()

    return UserWithConnectionResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
        has_connection=connection is not None,
        connection_type=connection.connection_type if connection else None,
        mcp_status=connection.mcp_server_status if connection else None,
        database_connected=connection.mcp_server_status == "connected" if connection else False
    )


# ============================================================================
# User Connection Management
# ============================================================================

@router.post("/connection/choose")
async def choose_connection_type(
    request: ConnectionChoiceRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Set user's database connection preference (first-time setup).

    - 'own_database': User connects their own PostgreSQL (Full IMS with Admin/POS)
    - 'our_database': User uses the shared IMS database
    - 'schema_query_only': User connects for AI Agent + Analytics only (read-only)
    """
    from app.services.schema_discovery import test_connection, discover_schema, TooManyTablesError, SchemaDiscoveryError

    # Validate connection type
    valid_types = ['own_database', 'our_database', 'schema_query_only']
    if request.connection_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid connection type. Must be one of: {valid_types}")

    # Require database_uri for own_database and schema_query_only
    if request.connection_type in ['own_database', 'schema_query_only'] and not request.database_uri:
        raise HTTPException(status_code=400, detail="database_uri required for this connection type")

    # Determine connection_mode based on connection_type
    connection_mode = 'schema_query' if request.connection_type == 'schema_query_only' else 'full_ims'

    # For schema_query_only, test the PostgreSQL connection first
    schema_metadata = None
    if request.connection_type == 'schema_query_only':
        logger.info(f"[Auth] Testing PostgreSQL connection for user {user.email}")

        # Test connection
        test_result = await test_connection(request.database_uri)
        if test_result["status"] != "success":
            raise HTTPException(
                status_code=400,
                detail=f"Database connection failed: {test_result.get('message', 'Unknown error')}"
            )

        logger.info(f"[Auth] Connection successful, discovering schema...")

        # Discover schema
        try:
            schema_metadata = await discover_schema(
                request.database_uri,
                allowed_schemas=["public"]
            )
            logger.info(f"[Auth] Schema discovered: {schema_metadata.get('total_tables', 0)} tables found")
        except TooManyTablesError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except SchemaDiscoveryError as e:
            logger.warning(f"[Auth] Schema discovery failed: {e}, continuing without schema")
            # Continue without schema - can be discovered later

    # Check if user already has a connection
    result = await db.execute(
        select(UserConnection).where(UserConnection.user_id == user.id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Clear cached agent when connection changes (important for reconnection)
        # Lazy import to avoid circular dependency
        from app.routers.schema_agent import clear_agent_cache
        clear_agent_cache(user.id)

        # Update existing
        existing.connection_type = request.connection_type
        existing.database_uri = request.database_uri if request.connection_type in ['own_database', 'schema_query_only'] else None
        existing.connection_mode = connection_mode
        existing.mcp_server_status = 'connected' if request.connection_type == 'schema_query_only' else 'disconnected'
        existing.updated_at = datetime.utcnow()
        existing.allowed_schemas = ["public"]
        # Set schema metadata for schema_query_only
        if request.connection_type == 'schema_query_only':
            existing.schema_metadata = schema_metadata
            existing.schema_last_updated = datetime.utcnow() if schema_metadata else None
            existing.last_connected_at = datetime.utcnow()
    else:
        # Create new
        connection = UserConnection(
            user_id=user.id,
            connection_type=request.connection_type,
            database_uri=request.database_uri if request.connection_type in ['own_database', 'schema_query_only'] else None,
            connection_mode=connection_mode,
            mcp_server_status='connected' if request.connection_type == 'schema_query_only' else 'disconnected',
            allowed_schemas=["public"],
            schema_metadata=schema_metadata if request.connection_type == 'schema_query_only' else None,
            schema_last_updated=datetime.utcnow() if schema_metadata else None,
            last_connected_at=datetime.utcnow() if request.connection_type == 'schema_query_only' else None
        )
        db.add(connection)

    await db.commit()

    logger.info(f"[Auth] User {user.email} chose connection type: {request.connection_type} (mode: {connection_mode})")

    return {
        "success": True,
        "message": f"Connection type set to {request.connection_type}",
        "connection_type": request.connection_type,
        "connection_mode": connection_mode,
        "needs_mcp_connect": request.connection_type == 'own_database',
        "needs_schema_discovery": False,  # Schema already discovered
        "tables_found": schema_metadata.get("total_tables", 0) if schema_metadata else 0,
        "connected": request.connection_type == 'schema_query_only'
    }


@router.get("/connection")
async def get_connection_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's current connection status.
    """
    result = await db.execute(
        select(UserConnection).where(UserConnection.user_id == user.id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        return {
            "has_connection": False,
            "needs_setup": True,
            "connection_type": None,
            "mcp_status": None,
            "schema_status": None
        }

    # Determine schema status for schema_query_only connections
    schema_status = None
    if connection.connection_type == 'schema_query_only':
        if connection.schema_metadata:
            schema_status = 'ready'
        elif connection.mcp_server_status == 'connected':
            schema_status = 'pending'  # Connected but schema not discovered
        else:
            schema_status = 'not_connected'

    return {
        "has_connection": True,
        "needs_setup": False,
        "connection_type": connection.connection_type,
        "connection_mode": connection.connection_mode,
        "mcp_status": connection.mcp_server_status,
        "mcp_session_id": connection.mcp_session_id,
        "last_connected_at": connection.last_connected_at,
        "database_uri_set": connection.database_uri is not None,
        "schema_status": schema_status,
        "tables_count": connection.schema_metadata.get("total_tables", 0) if connection.schema_metadata else 0
    }


@router.post("/connection/update-mcp-status")
async def update_mcp_status(
    mcp_status: str,
    mcp_session_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user's MCP connection status (called after MCP connect/disconnect).
    """
    result = await db.execute(
        select(UserConnection).where(UserConnection.user_id == user.id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="No connection setup found")

    connection.mcp_server_status = mcp_status
    connection.mcp_session_id = mcp_session_id
    if mcp_status == 'connected':
        connection.last_connected_at = datetime.utcnow()
    connection.updated_at = datetime.utcnow()

    await db.commit()

    return {
        "success": True,
        "mcp_status": mcp_status,
        "mcp_session_id": mcp_session_id
    }


@router.delete("/connection/disconnect")
async def disconnect_database(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Disconnect user's database and reset to service selection.
    """
    result = await db.execute(
        select(UserConnection).where(UserConnection.user_id == user.id)
    )
    connection = result.scalar_one_or_none()

    if connection:
        await db.delete(connection)
        await db.commit()

    # Clear cached schema agent for this user (important for reconnection)
    # Lazy import to avoid circular dependency
    from app.routers.schema_agent import clear_agent_cache
    clear_agent_cache(user.id)

    logger.info(f"[Auth] User {user.email} disconnected their database")

    return {
        "success": True,
        "message": "Database disconnected. Please choose a new service."
    }
