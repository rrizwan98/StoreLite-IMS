"""
SQLAlchemy ORM models for IMS FastAPI backend
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Text, CheckConstraint, JSON, Enum, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
import enum
from app.database import Base, PortableJSON


# ============================================================================
# Enums
# ============================================================================

class ConnectionType(enum.Enum):
    """User's database connection type choice"""
    OWN_DATABASE = "own_database"           # Full IMS with table creation
    OUR_DATABASE = "our_database"           # Platform database
    SCHEMA_QUERY_ONLY = "schema_query_only" # Agent + Analytics only (no table creation)


class ConnectionMode(enum.Enum):
    """Connection mode for own_database users"""
    FULL_IMS = "full_ims"                   # Creates IMS tables (inventory_items, bills, etc.)
    SCHEMA_QUERY = "schema_query"           # Read-only access to existing schema


class MCPStatus(enum.Enum):
    """MCP server connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


# ============================================================================
# User Authentication Models
# ============================================================================

class User(Base):
    """User account for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    __table_args__ = ({"extend_existing": True},)

    # Relationships
    connection = relationship("UserConnection", back_populates="user", uselist=False, cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class UserConnection(Base):
    """User's database connection preferences and MCP state"""
    __tablename__ = "user_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    connection_type = Column(String(50), nullable=False)  # 'own_database', 'our_database', 'schema_query_only'
    database_uri = Column(Text, nullable=True)  # User's DATABASE_URI (encrypted at rest ideally)
    mcp_server_status = Column(String(50), default="disconnected")  # 'connected', 'disconnected', 'connecting', 'error'
    mcp_session_id = Column(String(255), nullable=True)  # MCP session reference
    last_connected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Schema Query Mode fields (Phase 9)
    connection_mode = Column(String(50), default="full_ims")  # 'full_ims' or 'schema_query'
    schema_metadata = Column(PortableJSON, nullable=True)  # Cached schema: tables, columns, relationships
    schema_last_updated = Column(DateTime, nullable=True)  # When schema was last discovered
    allowed_schemas = Column(PortableJSON, default=["public"])  # PostgreSQL schemas to query (JSONB array)

    # Gmail OAuth2 Integration fields (Phase 10)
    gmail_access_token = Column(Text, nullable=True)  # Encrypted OAuth2 access token
    gmail_refresh_token = Column(Text, nullable=True)  # Encrypted OAuth2 refresh token
    gmail_token_expiry = Column(DateTime, nullable=True)  # When access token expires
    gmail_email = Column(String(255), nullable=True)  # Connected Gmail account email
    gmail_connected_at = Column(DateTime, nullable=True)  # When Gmail was connected
    gmail_recipient_email = Column(String(255), nullable=True)  # Default recipient for sending emails
    gmail_scopes = Column(PortableJSON, nullable=True)  # Granted OAuth2 scopes

    __table_args__ = ({"extend_existing": True},)

    # Relationships
    user = relationship("User", back_populates="connection")

    def __repr__(self):
        return f"<UserConnection(user_id={self.user_id}, type={self.connection_type}, mode={self.connection_mode}, status={self.mcp_server_status})>"


class UserSettings(Base):
    """
    User preferences/settings.

    NOTE: Created as a separate table (instead of altering users/user_connections)
    so existing deployments can pick it up via Base.metadata.create_all without
    requiring a manual ALTER TABLE migration.
    """

    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # File retention policy for ChatKit attachments / local uploads
    # Modes:
    # - keep_24h: keep for 24 hours (default)
    # - keep_48h: keep for 48 hours
    # - delete_immediately: delete right after agent response completes
    file_retention_mode = Column(String(32), nullable=False, default="keep_24h")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "file_retention_mode IN ('keep_24h', 'keep_48h', 'delete_immediately')",
            name="user_settings_file_retention_mode_check",
        ),
        {"extend_existing": True},
    )

    user = relationship("User", back_populates="settings")

    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id}, file_retention_mode={self.file_retention_mode})>"


class Item(Base):
    """Inventory item model"""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # Owner of this item
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    unit = Column(String(50), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    stock_qty = Column(Numeric(12, 3), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Check constraint: category must be one of the allowed values
    __table_args__ = (
        CheckConstraint(
            "category IN ('Grocery', 'Beauty', 'Garments', 'Utilities', 'Other')",
            name="items_category_check"
        ),
        {"extend_existing": True},
    )

    # Relationships
    user = relationship("User", backref="items")
    bill_items = relationship("BillItem", back_populates="item", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Item(id={self.id}, name={self.name}, category={self.category})>"


class Bill(Base):
    """Bill/Invoice model"""
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # Owner of this bill
    customer_name = Column(String(255), nullable=True)
    store_name = Column(String(255), nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = ({"extend_existing": True},)

    # Relationships
    user = relationship("User", backref="bills")
    bill_items = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Bill(id={self.id}, total_amount={self.total_amount})>"


class BillItem(Base):
    """Line item in a bill (many-to-many between Bill and Item)"""
    __tablename__ = "bill_items"

    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    item_name = Column(String(255), nullable=False)  # Snapshot of item name at time of sale
    unit_price = Column(Numeric(12, 2), nullable=False)  # Snapshot of unit price at time of sale
    quantity = Column(Numeric(12, 3), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    __table_args__ = ({"extend_existing": True},)

    # Relationships
    bill = relationship("Bill", back_populates="bill_items")
    item = relationship("Item", back_populates="bill_items")

    def __repr__(self):
        return f"<BillItem(id={self.id}, bill_id={self.bill_id}, item_name={self.item_name})>"


class AgentSession(Base):
    """Agent conversation session for Phase 5 OpenAI Agents SDK integration"""
    __tablename__ = "agent_sessions"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    conversation_history = Column(JSON, nullable=False, default=[])  # Array of message dicts
    session_metadata = Column(JSON, nullable=False, default={})  # User context, store info, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = ({"extend_existing": True},)

    def __repr__(self):
        return f"<AgentSession(session_id={self.session_id}, messages={len(self.conversation_history)})>"


class ConversationHistory(Base):
    """
    Persistent storage for ChatKit conversations.
    Enables conversation recovery if user refreshes page (SC-005).
    """
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)

    # Message content
    user_message = Column(Text, nullable=False)  # What user typed
    agent_response = Column(Text, nullable=False)  # What agent said

    # Response metadata
    response_type = Column(
        String(50),
        nullable=True,
        default="text"  # "text", "item_created", "bill_created", "item_list"
    )
    structured_data = Column(Text, nullable=True)  # JSON for UI rendering

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = ({"extend_existing": True},)

    def __repr__(self):
        return f"<ConversationHistory(session={self.session_id}, type={self.response_type})>"


# ============================================================================
# ChatKit Thread & Item Models (Phase 11 - Persistent Chat History)
# ============================================================================

class ChatKitThread(Base):
    """
    ChatKit thread for persistent conversation sessions.
    Each thread represents a chat conversation for a user.
    """
    __tablename__ = "chatkit_threads"

    id = Column(String(100), primary_key=True, index=True)  # Thread ID from ChatKit
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)  # Optional conversation title
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    thread_metadata = Column(PortableJSON, nullable=True, default={})  # Additional thread metadata (renamed to avoid reserved word)

    __table_args__ = ({"extend_existing": True},)

    # Relationships
    user = relationship("User", backref="chatkit_threads")
    items = relationship("ChatKitThreadItem", back_populates="thread", cascade="all, delete-orphan", order_by="ChatKitThreadItem.created_at")

    def __repr__(self):
        return f"<ChatKitThread(id={self.id}, user_id={self.user_id})>"


class ChatKitThreadItem(Base):
    """
    ChatKit thread item (message) for persistent conversation history.
    Stores both user messages and assistant responses.
    """
    __tablename__ = "chatkit_thread_items"

    id = Column(String(100), primary_key=True, index=True)  # Item ID from ChatKit
    thread_id = Column(String(100), ForeignKey("chatkit_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(50), nullable=False, index=True)  # "user_message", "assistant_message", etc.
    content = Column(Text, nullable=False)  # JSON serialized content
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = ({"extend_existing": True},)

    # Relationships
    thread = relationship("ChatKitThread", back_populates="items")

    def __repr__(self):
        return f"<ChatKitThreadItem(id={self.id}, thread_id={self.thread_id}, type={self.item_type})>"


# ============================================================================
# User MCP Connectors Models (Feature 008)
# ============================================================================

class UserToolStatus(Base):
    """
    Track user's connection status for SYSTEM tools (Gmail, Analytics, etc.).
    Each user can have one entry per system tool.
    """
    __tablename__ = "user_tool_status"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tool_id = Column(String(50), nullable=False, index=True)  # 'gmail', 'analytics', 'export'
    is_connected = Column(Boolean, default=False, nullable=False)
    config = Column(PortableJSON, nullable=True)  # Tool-specific settings
    connected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        # One entry per user per tool
        {"extend_existing": True},
    )

    # Relationships
    user = relationship("User", backref="tool_statuses")

    def __repr__(self):
        return f"<UserToolStatus(user_id={self.user_id}, tool={self.tool_id}, connected={self.is_connected})>"


class UserMCPConnection(Base):
    """
    User's custom MCP server connection.
    Stores connection details with encrypted credentials.
    Max 10 connectors per user (enforced at application level).
    """
    __tablename__ = "user_mcp_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(String(255), nullable=False)  # Clean tool name (e.g., "Gmail", "Google Drive")
    email = Column(String(255), nullable=True)  # Connected account email (e.g., "user@gmail.com")
    description = Column(Text, nullable=True)
    server_url = Column(String(500), nullable=False)
    auth_type = Column(String(50), default="none", nullable=False)  # 'none', 'oauth', 'api_key'
    auth_config = Column(Text, nullable=True)  # Encrypted JSON with credentials
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    discovered_tools = Column(PortableJSON, nullable=True)  # Cached list of tools from server
    last_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "auth_type IN ('none', 'oauth', 'api_key')",
            name="auth_type_check"
        ),
        {"extend_existing": True},
    )

    # Relationships
    user = relationship("User", backref="mcp_connections")

    @property
    def tool_count(self) -> int:
        """Return number of discovered tools"""
        if self.discovered_tools:
            return len(self.discovered_tools)
        return 0

    def __repr__(self):
        return f"<UserMCPConnection(id={self.id}, name={self.name}, active={self.is_active})>"


# ============================================================================
# Uploaded Files Models (Feature 012 - File Upload Processing)
# ============================================================================

class UploadedFile(Base):
    """
    Uploaded file for Schema Agent analysis.
    Stores file metadata and processed content.
    Files auto-expire after 24 hours.
    """
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # csv, excel, pdf, image
    file_size = Column(Integer, nullable=False)  # bytes
    mime_type = Column(String(100), nullable=False)
    status = Column(String(20), default='processing', nullable=False, index=True)  # processing, ready, error
    storage_path = Column(String(500), nullable=True)  # Path to stored file
    processed_data = Column(PortableJSON, nullable=True)  # Parsed content
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)  # Auto-delete time
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('processing', 'ready', 'error', 'deleted')",
            name="uploaded_file_status_check"
        ),
        CheckConstraint(
            "file_type IN ('csv', 'excel', 'pdf', 'image')",
            name="uploaded_file_type_check"
        ),
        {"extend_existing": True},
    )

    # Relationships
    user = relationship("User", backref="uploaded_files")

    @property
    def is_expired(self) -> bool:
        """Check if file has expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    @property
    def is_ready(self) -> bool:
        """Check if file is ready for use."""
        return self.status == 'ready' and not self.is_expired

    def __repr__(self):
        return f"<UploadedFile(id={self.file_id}, name={self.file_name}, status={self.status})>"
