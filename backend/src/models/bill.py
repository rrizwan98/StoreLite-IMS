"""
Bill and BillItem ORM models for invoice management
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship, validates

from .base import Base


class Bill(Base):
    """
    Bill model representing invoices
    """

    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String(255), nullable=True)
    store_name = Column(String(255), nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    bill_items = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan")

    @validates("total_amount")
    def validate_total_amount(self, key, value):
        """Validate total_amount is non-negative"""
        if isinstance(value, str):
            value = Decimal(value)
        if value < 0:
            raise ValueError("total_amount must be non-negative")
        return value

    def __repr__(self):
        return (
            f"<Bill(id={self.id}, customer={self.customer_name}, "
            f"store={self.store_name}, total={self.total_amount})>"
        )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "store_name": self.store_name,
            "total_amount": float(self.total_amount),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "bill_items": [item.to_dict() for item in self.bill_items],
        }


class BillItem(Base):
    """
    BillItem model representing line items in an invoice
    Stores snapshots of item name and price at time of billing
    """

    __tablename__ = "bill_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(Integer, ForeignKey("bills.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    item_name = Column(String(255), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    bill = relationship("Bill", back_populates="bill_items")

    @validates("unit_price")
    def validate_unit_price(self, key, value):
        """Validate unit_price is non-negative"""
        if isinstance(value, str):
            value = Decimal(value)
        if value < 0:
            raise ValueError("unit_price must be non-negative")
        return value

    @validates("quantity")
    def validate_quantity(self, key, value):
        """Validate quantity is positive"""
        if isinstance(value, str):
            value = Decimal(value)
        if value <= 0:
            raise ValueError("quantity must be positive")
        return value

    @validates("line_total")
    def validate_line_total(self, key, value):
        """Validate line_total is non-negative"""
        if isinstance(value, str):
            value = Decimal(value)
        if value < 0:
            raise ValueError("line_total must be non-negative")
        return value

    def __repr__(self):
        return (
            f"<BillItem(id={self.id}, bill_id={self.bill_id}, "
            f"item_name={self.item_name}, qty={self.quantity}, total={self.line_total})>"
        )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "bill_id": self.bill_id,
            "item_id": self.item_id,
            "item_name": self.item_name,
            "unit_price": float(self.unit_price),
            "quantity": float(self.quantity),
            "line_total": float(self.line_total),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
