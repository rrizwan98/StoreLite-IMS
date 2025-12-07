"""
Item ORM model for inventory management
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime
from sqlalchemy.orm import validates

from .base import Base


class Item(Base):
    """
    Item model representing products in inventory
    """

    __tablename__ = "items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    unit = Column(String(50), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    stock_qty = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates("category")
    def validate_category(self, key, value):
        """Validate category is in allowed list"""
        valid_categories = ["Grocery", "Garments", "Beauty", "Utilities", "Other"]
        if value not in valid_categories:
            raise ValueError(f"Invalid category: {value}. Must be one of {valid_categories}")
        return value

    @validates("unit")
    def validate_unit(self, key, value):
        """Validate unit is in allowed list"""
        valid_units = ["kg", "g", "liter", "ml", "piece", "box", "pack", "other"]
        if value not in valid_units:
            raise ValueError(f"Invalid unit: {value}. Must be one of {valid_units}")
        return value

    @validates("unit_price")
    def validate_unit_price(self, key, value):
        """Validate unit_price is non-negative"""
        if isinstance(value, str):
            value = Decimal(value)
        if value < 0:
            raise ValueError("unit_price must be non-negative")
        return value

    @validates("stock_qty")
    def validate_stock_qty(self, key, value):
        """Validate stock_qty is non-negative"""
        if isinstance(value, str):
            value = Decimal(value)
        if value < 0:
            raise ValueError("stock_qty must be non-negative")
        return value

    def __repr__(self):
        return (
            f"<Item(id={self.id}, name={self.name}, category={self.category}, "
            f"unit={self.unit}, price={self.unit_price}, stock={self.stock_qty})>"
        )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "unit": self.unit,
            "unit_price": float(self.unit_price),
            "stock_qty": float(self.stock_qty),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
