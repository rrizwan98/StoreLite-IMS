"""
MCP tool implementations for sales analytics and dashboard operations.

Task T025: Analytics tools for AI-powered dashboard feature (007-ai-dashboard)
"""
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from sqlalchemy.orm import selectinload
from collections import defaultdict

from app.models import Bill, BillItem, Item
from app.mcp_server.exceptions import (
    MCPValidationError,
    MCPNotFoundError,
    MCPDatabaseError,
)
from app.mcp_server.utils import mcp_error_handler

logger = logging.getLogger(__name__)


# ============================================================================
# Task T025: get_sales_by_month - Sales summary for AI dashboard
# ============================================================================

@mcp_error_handler("get_sales_by_month")
async def get_sales_by_month(
    year: int,
    month: int,
    session: AsyncSession = None,
    user_id: Optional[int] = None
) -> dict:
    """
    Get sales summary for a specific month with top products (user-scoped).

    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
        session: AsyncSession for database operations
        user_id: Optional user ID to filter bills by user

    Returns:
        Sales summary with total, top products, daily trends, and statistics
    """
    # Validate inputs
    if not 1 <= month <= 12:
        raise MCPValidationError("MONTH_INVALID", "Month must be between 1 and 12")
    if year < 2000 or year > 2100:
        raise MCPValidationError("YEAR_INVALID", "Year must be between 2000 and 2100")

    try:
        # Define date range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        # Build query conditions - filter by date range and optionally by user
        conditions = [
            Bill.created_at >= start_date,
            Bill.created_at < end_date
        ]
        if user_id is not None:
            conditions.append(Bill.user_id == user_id)

        # Query bills within the date range (user-scoped if user_id provided)
        stmt = (
            select(Bill)
            .options(selectinload(Bill.bill_items))
            .where(and_(*conditions))
            .order_by(Bill.created_at)
        )

        result = await session.execute(stmt)
        bills = result.scalars().all()

        # Calculate statistics
        total_sales = Decimal("0.00")
        total_transactions = len(bills)
        product_sales = defaultdict(lambda: {"quantity": Decimal("0"), "revenue": Decimal("0.00"), "name": ""})
        daily_sales = defaultdict(lambda: Decimal("0.00"))

        for bill in bills:
            total_sales += bill.total_amount
            day_key = bill.created_at.strftime("%Y-%m-%d")
            daily_sales[day_key] += bill.total_amount

            for item in bill.bill_items:
                product_sales[item.item_id]["quantity"] += item.quantity
                product_sales[item.item_id]["revenue"] += item.line_total
                product_sales[item.item_id]["name"] = item.item_name

        # Top 5 products by revenue
        top_products = sorted(
            [
                {
                    "item_id": item_id,
                    "name": data["name"],
                    "quantity": float(data["quantity"]),
                    "revenue": float(data["revenue"])
                }
                for item_id, data in product_sales.items()
            ],
            key=lambda x: x["revenue"],
            reverse=True
        )[:5]

        # Daily trends (sorted by date)
        daily_trends = [
            {"date": date, "sales": float(amount)}
            for date, amount in sorted(daily_sales.items())
        ]

        # Calculate average transaction value
        avg_transaction = float(total_sales / total_transactions) if total_transactions > 0 else 0.0

        return {
            "period": {
                "year": year,
                "month": month,
                "month_name": start_date.strftime("%B"),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_sales": float(total_sales),
                "total_transactions": total_transactions,
                "average_transaction_value": round(avg_transaction, 2),
                "unique_products_sold": len(product_sales)
            },
            "top_products": top_products,
            "daily_trends": daily_trends,
            "generated_at": datetime.utcnow().isoformat()
        }

    except MCPValidationError:
        raise
    except Exception as e:
        logger.error(f"Error getting sales by month: {str(e)}")
        raise MCPDatabaseError("DATABASE_ERROR", str(e))


# ============================================================================
# Task T025: compare_sales - Period comparison for AI dashboard
# ============================================================================

@mcp_error_handler("compare_sales")
async def compare_sales(
    period1: str,
    period2: str,
    session: AsyncSession = None,
    user_id: Optional[int] = None
) -> dict:
    """
    Compare sales between two periods with percentage changes (user-scoped).

    Args:
        period1: First period in format "YYYY-MM" (e.g., "2025-11")
        period2: Second period in format "YYYY-MM" (e.g., "2025-12")
        session: AsyncSession for database operations
        user_id: Optional user ID to filter bills by user

    Returns:
        Comparative analysis with percentage changes, product differences
    """
    def parse_period(period_str: str) -> tuple:
        """Parse YYYY-MM format into year and month."""
        try:
            parts = period_str.split("-")
            return int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            raise MCPValidationError(
                "PERIOD_INVALID",
                f"Period '{period_str}' must be in YYYY-MM format"
            )

    try:
        year1, month1 = parse_period(period1)
        year2, month2 = parse_period(period2)

        # Get sales data for both periods (user-scoped if user_id provided)
        async def get_period_data(year: int, month: int) -> dict:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            # Build conditions with optional user filter
            conditions = [
                Bill.created_at >= start_date,
                Bill.created_at < end_date
            ]
            if user_id is not None:
                conditions.append(Bill.user_id == user_id)

            stmt = (
                select(Bill)
                .options(selectinload(Bill.bill_items))
                .where(and_(*conditions))
            )

            result = await session.execute(stmt)
            bills = result.scalars().all()

            total_sales = Decimal("0.00")
            total_transactions = len(bills)
            product_sales = defaultdict(lambda: {"quantity": Decimal("0"), "revenue": Decimal("0.00"), "name": ""})

            for bill in bills:
                total_sales += bill.total_amount
                for item in bill.bill_items:
                    product_sales[item.item_id]["quantity"] += item.quantity
                    product_sales[item.item_id]["revenue"] += item.line_total
                    product_sales[item.item_id]["name"] = item.item_name

            return {
                "total_sales": float(total_sales),
                "total_transactions": total_transactions,
                "products": {
                    item_id: {
                        "name": data["name"],
                        "quantity": float(data["quantity"]),
                        "revenue": float(data["revenue"])
                    }
                    for item_id, data in product_sales.items()
                }
            }

        data1 = await get_period_data(year1, month1)
        data2 = await get_period_data(year2, month2)

        # Calculate percentage changes
        def calc_change(old_val: float, new_val: float) -> dict:
            if old_val == 0:
                if new_val == 0:
                    return {"value": 0.0, "percentage": 0.0, "direction": "unchanged"}
                return {"value": new_val, "percentage": 100.0, "direction": "increase"}

            diff = new_val - old_val
            pct = (diff / old_val) * 100
            direction = "increase" if diff > 0 else ("decrease" if diff < 0 else "unchanged")
            return {"value": round(diff, 2), "percentage": round(pct, 2), "direction": direction}

        sales_change = calc_change(data1["total_sales"], data2["total_sales"])
        transactions_change = calc_change(data1["total_transactions"], data2["total_transactions"])

        # Find new products (in period2 but not in period1)
        new_products = [
            {"item_id": item_id, **data}
            for item_id, data in data2["products"].items()
            if item_id not in data1["products"]
        ]

        # Find discontinued products (in period1 but not in period2)
        discontinued_products = [
            {"item_id": item_id, **data}
            for item_id, data in data1["products"].items()
            if item_id not in data2["products"]
        ]

        # Top changes by revenue
        product_changes = []
        for item_id, data2_prod in data2["products"].items():
            if item_id in data1["products"]:
                data1_prod = data1["products"][item_id]
                change = calc_change(data1_prod["revenue"], data2_prod["revenue"])
                product_changes.append({
                    "item_id": item_id,
                    "name": data2_prod["name"],
                    "period1_revenue": data1_prod["revenue"],
                    "period2_revenue": data2_prod["revenue"],
                    "change": change
                })

        # Sort by absolute change percentage
        product_changes.sort(key=lambda x: abs(x["change"]["percentage"]), reverse=True)

        return {
            "comparison": {
                "period1": {
                    "label": period1,
                    "year": year1,
                    "month": month1,
                    "total_sales": data1["total_sales"],
                    "total_transactions": data1["total_transactions"]
                },
                "period2": {
                    "label": period2,
                    "year": year2,
                    "month": month2,
                    "total_sales": data2["total_sales"],
                    "total_transactions": data2["total_transactions"]
                }
            },
            "changes": {
                "sales": sales_change,
                "transactions": transactions_change
            },
            "product_changes": product_changes[:10],  # Top 10 changes
            "new_products": new_products[:5],
            "discontinued_products": discontinued_products[:5],
            "generated_at": datetime.utcnow().isoformat()
        }

    except MCPValidationError:
        raise
    except Exception as e:
        logger.error(f"Error comparing sales: {str(e)}")
        raise MCPDatabaseError("DATABASE_ERROR", str(e))


# ============================================================================
# Task T025: get_sales_trends - Trend analysis for AI dashboard
# ============================================================================

@mcp_error_handler("get_sales_trends")
async def get_sales_trends(
    days: int = 30,
    session: AsyncSession = None,
    user_id: Optional[int] = None
) -> dict:
    """
    Get sales trends for the specified number of days (user-scoped).

    Args:
        days: Number of days to analyze (default 30, max 365)
        session: AsyncSession for database operations
        user_id: Optional user ID to filter bills by user

    Returns:
        Trends analysis with daily data, moving averages, and insights
    """
    # Validate input
    if days < 1:
        days = 30
    if days > 365:
        days = 365

    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Build conditions with optional user filter
        conditions = [Bill.created_at >= start_date]
        if user_id is not None:
            conditions.append(Bill.user_id == user_id)

        # Query bills within the date range (user-scoped if user_id provided)
        stmt = (
            select(Bill)
            .options(selectinload(Bill.bill_items))
            .where(and_(*conditions))
            .order_by(Bill.created_at)
        )

        result = await session.execute(stmt)
        bills = result.scalars().all()

        # Aggregate by day
        daily_data = defaultdict(lambda: {
            "sales": Decimal("0.00"),
            "transactions": 0,
            "items_sold": Decimal("0")
        })

        category_sales = defaultdict(lambda: Decimal("0.00"))

        for bill in bills:
            day_key = bill.created_at.strftime("%Y-%m-%d")
            daily_data[day_key]["sales"] += bill.total_amount
            daily_data[day_key]["transactions"] += 1

            for item in bill.bill_items:
                daily_data[day_key]["items_sold"] += item.quantity

        # Get category breakdown from items
        item_ids = set()
        for bill in bills:
            for item in bill.bill_items:
                item_ids.add(item.item_id)

        if item_ids:
            items_stmt = select(Item).where(Item.id.in_(item_ids))
            items_result = await session.execute(items_stmt)
            items_by_id = {item.id: item for item in items_result.scalars().all()}

            for bill in bills:
                for bill_item in bill.bill_items:
                    item = items_by_id.get(bill_item.item_id)
                    if item:
                        category_sales[item.category] += bill_item.line_total

        # Fill in missing days with zeros
        all_days = []
        current = start_date
        while current <= end_date:
            day_key = current.strftime("%Y-%m-%d")
            data = daily_data.get(day_key, {"sales": Decimal("0.00"), "transactions": 0, "items_sold": Decimal("0")})
            all_days.append({
                "date": day_key,
                "sales": float(data["sales"]),
                "transactions": data["transactions"],
                "items_sold": float(data["items_sold"])
            })
            current += timedelta(days=1)

        # Calculate 7-day moving average
        moving_avg = []
        for i in range(len(all_days)):
            start_idx = max(0, i - 6)
            window = all_days[start_idx:i + 1]
            avg_sales = sum(d["sales"] for d in window) / len(window)
            moving_avg.append({
                "date": all_days[i]["date"],
                "moving_average": round(avg_sales, 2)
            })

        # Calculate summary statistics
        total_sales = sum(d["sales"] for d in all_days)
        total_transactions = sum(d["transactions"] for d in all_days)
        avg_daily_sales = total_sales / len(all_days) if all_days else 0

        # Best and worst days
        sorted_by_sales = sorted(all_days, key=lambda x: x["sales"], reverse=True)
        best_days = sorted_by_sales[:3]
        worst_days = sorted_by_sales[-3:]

        # Category breakdown
        category_breakdown = [
            {"category": cat, "revenue": float(rev)}
            for cat, rev in sorted(category_sales.items(), key=lambda x: x[1], reverse=True)
        ]

        # Growth analysis (compare first half to second half)
        midpoint = len(all_days) // 2
        first_half_sales = sum(d["sales"] for d in all_days[:midpoint])
        second_half_sales = sum(d["sales"] for d in all_days[midpoint:])

        if first_half_sales > 0:
            growth_rate = ((second_half_sales - first_half_sales) / first_half_sales) * 100
        else:
            growth_rate = 100.0 if second_half_sales > 0 else 0.0

        return {
            "period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_sales": round(total_sales, 2),
                "total_transactions": total_transactions,
                "average_daily_sales": round(avg_daily_sales, 2),
                "growth_rate": round(growth_rate, 2),
                "growth_direction": "up" if growth_rate > 0 else ("down" if growth_rate < 0 else "flat")
            },
            "daily_trends": all_days,
            "moving_averages": moving_avg,
            "best_days": best_days,
            "worst_days": worst_days,
            "category_breakdown": category_breakdown,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting sales trends: {str(e)}")
        raise MCPDatabaseError("DATABASE_ERROR", str(e))


# ============================================================================
# Task T025: get_inventory_analytics - Inventory analysis for AI dashboard
# ============================================================================

@mcp_error_handler("get_inventory_analytics")
async def get_inventory_analytics(
    session: AsyncSession = None,
    user_id: Optional[int] = None
) -> dict:
    """
    Get comprehensive inventory analytics including stock levels, alerts, and recommendations (user-scoped).

    Args:
        session: AsyncSession for database operations
        user_id: Optional user ID to filter items by user

    Returns:
        Inventory analysis with stock status, reorder alerts, and recommendations
    """
    try:
        # Build conditions with optional user filter
        conditions = [Item.is_active == True]
        if user_id is not None:
            conditions.append(Item.user_id == user_id)

        # Get all active items (user-scoped if user_id provided)
        stmt = select(Item).where(and_(*conditions))
        result = await session.execute(stmt)
        items = result.scalars().all()

        total_items = len(items)
        total_value = Decimal("0.00")
        low_stock_items = []
        out_of_stock_items = []
        overstocked_items = []
        category_stats = defaultdict(lambda: {
            "count": 0,
            "total_stock": Decimal("0"),
            "total_value": Decimal("0.00")
        })

        # Define thresholds
        LOW_STOCK_THRESHOLD = 10
        OVERSTOCK_THRESHOLD = 1000

        for item in items:
            item_value = item.unit_price * item.stock_qty
            total_value += item_value

            # Category aggregation
            category_stats[item.category]["count"] += 1
            category_stats[item.category]["total_stock"] += item.stock_qty
            category_stats[item.category]["total_value"] += item_value

            # Stock status classification
            if item.stock_qty == 0:
                out_of_stock_items.append({
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "unit_price": float(item.unit_price)
                })
            elif item.stock_qty < LOW_STOCK_THRESHOLD:
                low_stock_items.append({
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "stock_qty": float(item.stock_qty),
                    "unit_price": float(item.unit_price)
                })
            elif item.stock_qty > OVERSTOCK_THRESHOLD:
                overstocked_items.append({
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "stock_qty": float(item.stock_qty),
                    "unit_price": float(item.unit_price)
                })

        # Category breakdown
        category_breakdown = [
            {
                "category": cat,
                "item_count": stats["count"],
                "total_stock": float(stats["total_stock"]),
                "total_value": float(stats["total_value"])
            }
            for cat, stats in sorted(category_stats.items(), key=lambda x: x[1]["total_value"], reverse=True)
        ]

        # Generate recommendations
        recommendations = []

        if out_of_stock_items:
            recommendations.append({
                "type": "urgent",
                "action": "restock",
                "message": f"{len(out_of_stock_items)} items are out of stock and need immediate restocking",
                "items": [item["name"] for item in out_of_stock_items[:5]]
            })

        if low_stock_items:
            recommendations.append({
                "type": "warning",
                "action": "reorder",
                "message": f"{len(low_stock_items)} items are running low (below {LOW_STOCK_THRESHOLD} units)",
                "items": [item["name"] for item in low_stock_items[:5]]
            })

        if overstocked_items:
            recommendations.append({
                "type": "info",
                "action": "promote",
                "message": f"{len(overstocked_items)} items may be overstocked (above {OVERSTOCK_THRESHOLD} units)",
                "items": [item["name"] for item in overstocked_items[:5]]
            })

        return {
            "summary": {
                "total_items": total_items,
                "total_inventory_value": float(total_value),
                "out_of_stock_count": len(out_of_stock_items),
                "low_stock_count": len(low_stock_items),
                "overstocked_count": len(overstocked_items),
                "healthy_stock_count": total_items - len(out_of_stock_items) - len(low_stock_items) - len(overstocked_items)
            },
            "alerts": {
                "out_of_stock": out_of_stock_items[:10],
                "low_stock": low_stock_items[:10],
                "overstocked": overstocked_items[:10]
            },
            "category_breakdown": category_breakdown,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting inventory analytics: {str(e)}")
        raise MCPDatabaseError("DATABASE_ERROR", str(e))
