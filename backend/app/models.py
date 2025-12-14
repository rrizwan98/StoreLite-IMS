"""
SQLAlchemy ORM models for IMS FastAPI backend
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Text, CheckConstraint, JSON, Enum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


# ============================================================================
# Enums
# ============================================================================

class ConnectionType(enum.Enum):
    """User's database connection type choice"""
    OWN_DATABASE = "own_database"
    OUR_DATABASE = "our_database"


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

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class UserConnection(Base):
    """User's database connection preferences and MCP state"""
    __tablename__ = "user_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    connection_type = Column(String(50), nullable=False)  # 'own_database' or 'our_database'
    database_uri = Column(Text, nullable=True)  # User's DATABASE_URI (encrypted at rest ideally)
    mcp_server_status = Column(String(50), default="disconnected")  # 'connected', 'disconnected', 'connecting', 'error'
    mcp_session_id = Column(String(255), nullable=True)  # MCP session reference
    last_connected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = ({"extend_existing": True},)

    # Relationships
    user = relationship("User", back_populates="connection")

    def __repr__(self):
        return f"<UserConnection(user_id={self.user_id}, type={self.connection_type}, status={self.mcp_server_status})>"


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
