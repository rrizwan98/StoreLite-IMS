"""
Direct Analytics API Endpoints

Provides REST endpoints that return structured chart-ready data
for the AI-powered analytics dashboard.

These endpoints bypass the AI agent and directly fetch analytics data,
returning it in a format optimized for frontend visualization.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models import User
from app.routers.auth import get_current_user
from app.mcp_server.tools_analytics import (
    get_sales_by_month,
    compare_sales,
    get_sales_trends,
    get_inventory_analytics,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================================================
# Response Models
# ============================================================================

class ChartDataPoint(BaseModel):
    label: str
    value: float


class MetricData(BaseModel):
    title: str
    value: str
    icon: Optional[str] = None
    change: Optional[float] = None
    changeType: Optional[str] = None  # "increase", "decrease", "unchanged"


class VisualizationResponse(BaseModel):
    """Response with text and optional visualization data."""
    text: str
    visualizations: List[Dict[str, Any]] = []
    metrics: List[MetricData] = []


# ============================================================================
# Direct Analytics Endpoints (No AI, just data)
# ============================================================================

@router.get("/inventory-health")
async def get_inventory_health_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get inventory health data with chart-ready structure (user-scoped).
    Returns metrics, alerts, and category breakdown for visualization.
    """
    try:
        data = await get_inventory_analytics(session=db, user_id=current_user.id)

        summary = data.get("summary", {})
        category_breakdown = data.get("category_breakdown", [])
        alerts = data.get("alerts", {})

        # Prepare metrics for MetricCard display
        metrics = [
            {
                "title": "Total Items",
                "value": str(summary.get("total_items", 0)),
                "icon": "package"
            },
            {
                "title": "Inventory Value",
                "value": f"${summary.get('total_inventory_value', 0):,.2f}",
                "icon": "dollar"
            },
            {
                "title": "Out of Stock",
                "value": str(summary.get("out_of_stock_count", 0)),
                "icon": "alert",
                "status": "danger" if summary.get("out_of_stock_count", 0) > 0 else "success"
            },
            {
                "title": "Low Stock",
                "value": str(summary.get("low_stock_count", 0)),
                "icon": "warning",
                "status": "warning" if summary.get("low_stock_count", 0) > 0 else "success"
            },
        ]

        # Prepare bar chart data for category breakdown
        category_chart = [
            {"label": cat.get("category", "Unknown"), "value": cat.get("total_value", 0)}
            for cat in category_breakdown[:8]
        ]

        # Prepare stock status pie chart data
        stock_status_chart = [
            {"label": "Healthy", "value": summary.get("healthy_stock_count", 0)},
            {"label": "Low Stock", "value": summary.get("low_stock_count", 0)},
            {"label": "Out of Stock", "value": summary.get("out_of_stock_count", 0)},
        ]

        return {
            "success": True,
            "metrics": metrics,
            "visualizations": [
                {
                    "type": "bar-chart",
                    "title": "Inventory Value by Category",
                    "data": category_chart,
                    "formatValue": "currency"
                },
                {
                    "type": "metrics",
                    "title": "Stock Status",
                    "data": stock_status_chart
                }
            ],
            "alerts": {
                "out_of_stock": alerts.get("out_of_stock", [])[:5],
                "low_stock": alerts.get("low_stock", [])[:5]
            },
            "recommendations": data.get("recommendations", []),
            "raw_data": data
        }

    except Exception as e:
        logger.error(f"Error fetching inventory health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales-month")
async def get_sales_month_data(
    year: int = Query(default=None, description="Year (defaults to current)"),
    month: int = Query(default=None, description="Month 1-12 (defaults to current)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get monthly sales data with chart-ready structure (user-scoped).
    Returns metrics, top products, and daily trends for visualization.
    """
    try:
        now = datetime.utcnow()
        year = year or now.year
        month = month or now.month

        data = await get_sales_by_month(year=year, month=month, session=db, user_id=current_user.id)

        summary = data.get("summary", {})
        top_products = data.get("top_products", [])
        daily_trends = data.get("daily_trends", [])
        period = data.get("period", {})

        # Prepare metrics
        metrics = [
            {
                "title": "Total Sales",
                "value": f"${summary.get('total_sales', 0):,.2f}",
                "icon": "dollar"
            },
            {
                "title": "Transactions",
                "value": str(summary.get("total_transactions", 0)),
                "icon": "cart"
            },
            {
                "title": "Avg Transaction",
                "value": f"${summary.get('average_transaction_value', 0):,.2f}",
                "icon": "average"
            },
            {
                "title": "Products Sold",
                "value": str(summary.get("unique_products_sold", 0)),
                "icon": "package"
            },
        ]

        # Prepare top products bar chart
        products_chart = [
            {"label": p.get("name", "Unknown")[:20], "value": p.get("revenue", 0)}
            for p in top_products[:5]
        ]

        # Prepare daily trends line chart
        trends_chart = [
            {"label": t.get("date", "")[-5:], "value": t.get("sales", 0)}  # Show MM-DD
            for t in daily_trends[-30:]  # Last 30 days
        ]

        return {
            "success": True,
            "period": period,
            "metrics": metrics,
            "visualizations": [
                {
                    "type": "bar-chart",
                    "title": "Top 5 Products by Revenue",
                    "data": products_chart,
                    "formatValue": "currency"
                },
                {
                    "type": "line-chart",
                    "title": f"Daily Sales - {period.get('month_name', '')} {year}",
                    "data": trends_chart,
                    "formatValue": "currency"
                }
            ],
            "raw_data": data
        }

    except Exception as e:
        logger.error(f"Error fetching sales month data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales-trends")
async def get_sales_trends_data(
    days: int = Query(default=30, ge=1, le=365, description="Number of days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get sales trends data with chart-ready structure (user-scoped).
    Returns daily trends, moving averages, and insights.
    """
    try:
        data = await get_sales_trends(days=days, session=db, user_id=current_user.id)

        summary = data.get("summary", {})
        daily_trends = data.get("daily_trends", [])
        moving_averages = data.get("moving_averages", [])
        category_breakdown = data.get("category_breakdown", [])
        best_days = data.get("best_days", [])
        worst_days = data.get("worst_days", [])

        # Prepare metrics
        growth_rate = summary.get("growth_rate", 0)
        growth_direction = summary.get("growth_direction", "flat")

        metrics = [
            {
                "title": f"Sales ({days}d)",
                "value": f"${summary.get('total_sales', 0):,.2f}",
                "icon": "dollar"
            },
            {
                "title": "Avg Daily",
                "value": f"${summary.get('average_daily_sales', 0):,.2f}",
                "icon": "calendar"
            },
            {
                "title": "Growth",
                "value": f"{'+' if growth_rate > 0 else ''}{growth_rate:.1f}%",
                "icon": "trending-up" if growth_direction == "up" else ("trending-down" if growth_direction == "down" else "minus"),
                "status": "success" if growth_direction == "up" else ("danger" if growth_direction == "down" else "neutral")
            },
            {
                "title": "Transactions",
                "value": str(summary.get("total_transactions", 0)),
                "icon": "cart"
            },
        ]

        # Prepare trends line chart with moving average
        trends_chart = [
            {"label": t.get("date", "")[-5:], "value": t.get("sales", 0)}
            for t in daily_trends[-30:]
        ]

        # Category breakdown for bar chart
        category_chart = [
            {"label": c.get("category", "Unknown")[:15], "value": c.get("revenue", 0)}
            for c in category_breakdown[:6]
        ]

        return {
            "success": True,
            "period": data.get("period", {}),
            "metrics": metrics,
            "visualizations": [
                {
                    "type": "line-chart",
                    "title": f"Sales Trend - Last {days} Days",
                    "data": trends_chart,
                    "formatValue": "currency"
                },
                {
                    "type": "bar-chart",
                    "title": "Sales by Category",
                    "data": category_chart,
                    "formatValue": "currency"
                }
            ],
            "insights": {
                "best_days": [
                    {"date": d.get("date"), "sales": d.get("sales", 0)}
                    for d in best_days[:3]
                ],
                "worst_days": [
                    {"date": d.get("date"), "sales": d.get("sales", 0)}
                    for d in worst_days[:3]
                ]
            },
            "raw_data": data
        }

    except Exception as e:
        logger.error(f"Error fetching sales trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare")
async def get_sales_comparison_data(
    period1: str = Query(..., description="First period YYYY-MM"),
    period2: str = Query(..., description="Second period YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Compare sales between two periods with chart-ready structure (user-scoped).
    """
    try:
        data = await compare_sales(period1=period1, period2=period2, session=db, user_id=current_user.id)

        comparison = data.get("comparison", {})
        changes = data.get("changes", {})
        product_changes = data.get("product_changes", [])

        p1 = comparison.get("period1", {})
        p2 = comparison.get("period2", {})
        sales_change = changes.get("sales", {})

        # Prepare metrics
        metrics = [
            {
                "title": p1.get("label", "Period 1"),
                "value": f"${p1.get('total_sales', 0):,.2f}",
                "icon": "calendar"
            },
            {
                "title": p2.get("label", "Period 2"),
                "value": f"${p2.get('total_sales', 0):,.2f}",
                "icon": "calendar"
            },
            {
                "title": "Change",
                "value": f"{'+' if sales_change.get('percentage', 0) > 0 else ''}{sales_change.get('percentage', 0):.1f}%",
                "icon": "trending-up" if sales_change.get("direction") == "increase" else "trending-down",
                "status": "success" if sales_change.get("direction") == "increase" else "danger"
            },
        ]

        # Comparison bar chart
        comparison_chart = [
            {"label": p1.get("label", "Period 1"), "value": p1.get("total_sales", 0)},
            {"label": p2.get("label", "Period 2"), "value": p2.get("total_sales", 0)},
        ]

        # Product changes chart (top movers)
        product_chart = [
            {
                "label": p.get("name", "Unknown")[:15],
                "value": p.get("change", {}).get("percentage", 0)
            }
            for p in product_changes[:5]
        ]

        return {
            "success": True,
            "metrics": metrics,
            "visualizations": [
                {
                    "type": "bar-chart",
                    "title": "Period Comparison",
                    "data": comparison_chart,
                    "formatValue": "currency"
                },
                {
                    "type": "bar-chart",
                    "title": "Top Product Changes (%)",
                    "data": product_chart,
                    "formatValue": "percentage"
                }
            ],
            "changes": changes,
            "raw_data": data
        }

    except Exception as e:
        logger.error(f"Error comparing sales: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-products")
async def get_top_products_data(
    limit: int = Query(default=5, ge=1, le=20, description="Number of products"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get top selling products with chart-ready structure (user-scoped).
    """
    try:
        now = datetime.utcnow()
        data = await get_sales_by_month(year=now.year, month=now.month, session=db, user_id=current_user.id)

        top_products = data.get("top_products", [])[:limit]

        # Prepare bar chart data
        products_chart = [
            {"label": p.get("name", "Unknown")[:20], "value": p.get("revenue", 0)}
            for p in top_products
        ]

        # Quantity chart
        quantity_chart = [
            {"label": p.get("name", "Unknown")[:20], "value": p.get("quantity", 0)}
            for p in top_products
        ]

        return {
            "success": True,
            "visualizations": [
                {
                    "type": "bar-chart",
                    "title": f"Top {limit} Products by Revenue",
                    "data": products_chart,
                    "formatValue": "currency"
                },
                {
                    "type": "bar-chart",
                    "title": f"Top {limit} Products by Quantity Sold",
                    "data": quantity_chart,
                    "formatValue": "number"
                }
            ],
            "products": top_products,
            "raw_data": data
        }

    except Exception as e:
        logger.error(f"Error fetching top products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AI-POWERED VISUALIZATION ENDPOINT
# Expert-level analytics that ONLY shows real data from AI responses
# ============================================================================

class VisualizeRequest(BaseModel):
    """Request model for visualization endpoint."""
    query: str
    response_text: Optional[str] = None
    user_id: Optional[int] = None
    use_mcp: bool = False  # True if user has own_database with MCP connection


@router.post("/visualize")
async def get_visualization_for_query(
    request: VisualizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    AI-POWERED VISUALIZATION ENDPOINT

    This endpoint creates intelligent visualizations by:
    1. Parsing the AI agent's actual response text
    2. Extracting REAL data mentioned in the response
    3. Creating appropriate chart types based on data structure
    4. NEVER showing fake/default data - only what's in the response

    For own_database users (use_mcp=True):
    - Only uses data extracted from AI response
    - Never queries our platform database
    - Creates visualizations from the agent's answer

    For our_database users (use_mcp=False):
    - Can use our platform database for additional context
    - Still prioritizes data from AI response
    """
    try:
        query = request.query
        response_text = request.response_text or ""
        use_mcp = request.use_mcp

        logger.info(f"[Visualize] Query: {query[:50]}... | use_mcp={use_mcp}")
        logger.info(f"[Visualize] Response text length: {len(response_text)}")

        # EXPERT MODE: Only extract data from AI response
        # Never generate fake data
        viz_data = _extract_visualization_from_response(query, response_text)

        # If no data found in response, return empty (no fake fallbacks)
        if not viz_data.get("metrics") and not viz_data.get("charts"):
            logger.info("[Visualize] No visualizable data found in response")
            return {
                "success": True,
                "query": request.query,
                "metrics": [],
                "charts": [],
                "message": "No numerical data to visualize for this response"
            }

        return {
            "success": True,
            "query": request.query,
            **viz_data
        }

    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "metrics": [],
            "charts": []
        }


def _extract_visualization_from_response(query: str, response_text: str) -> Dict[str, Any]:
    """
    EXPERT AI VISUALIZATION EXTRACTOR

    This function intelligently parses the AI agent's response text
    to extract REAL data for visualization.

    Strategy:
    1. Parse response for numerical data patterns
    2. Identify data type (counts, prices, quantities, percentages)
    3. Create appropriate visualization type
    4. Return ONLY data that exists in the response
    5. NEVER generate fake/placeholder data

    Returns empty if no visualizable data found.
    """
    import re

    metrics = []
    chart_data = []

    if not response_text or len(response_text) < 10:
        logger.info("[Visualize] Response too short for visualization")
        return {"metrics": [], "charts": []}

    logger.info(f"[Visualize] Parsing response: {response_text[:200]}...")

    # =========================================================================
    # PATTERN 1: Total/Summary Numbers
    # Examples: "there is a total of **1 item**", "total: 5 items", "count: 10"
    # =========================================================================
    total_patterns = [
        r'total\s+of\s+\*?\*?(\d+)\s*\*?\*?\s*(item|product|record|row|entr)',
        r'(?:there\s+(?:is|are)|have)\s+\*?\*?(\d+)\s*\*?\*?\s*(item|product|record|row|entr)',
        r'(?:count|total)[:\s]+\*?\*?(\d+)\*?\*?',
        r'\*?\*?(\d+)\*?\*?\s+(?:item|product|record)s?\s+(?:in|found|total)',
    ]

    total_found = None
    for pattern in total_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            total_found = int(match.group(1))
            logger.info(f"[Visualize] Found total count: {total_found}")
            metrics.append({
                "title": "Total Items",
                "value": str(total_found),
                "status": "success" if total_found > 0 else "warning"
            })
            break

    # =========================================================================
    # PATTERN 2: Named Items with Quantities
    # Examples: '"Rice" has stock quantity of **50**', 'Rice: 50 units'
    # =========================================================================
    item_patterns = [
        # "ProductName" has (stock) quantity of X (units)
        r'["\']([^"\']+)["\']\s+has\s+(?:a\s+)?(?:stock\s+)?(?:quantity\s+of\s+)?\*?\*?(\d+)\s*\*?\*?\s*(?:unit)?',
        # **ProductName**: X units
        r'\*\*([^*]+)\*\*[:\s]+\*?\*?(\d+)\s*\*?\*?\s*(?:unit|stock|quantit)?',
        # ProductName: X units/items
        r'^[•\-\*]?\s*([A-Za-z][A-Za-z\s]{2,30})[:\s]+(\d+)\s*(?:unit|item|stock|pcs?)?',
        # name: "X", quantity: Y
        r'name[:\s]+["\']?([^"\',:]+)["\']?[,\s]+(?:quantity|stock|count)[:\s]+(\d+)',
        # Row format: ProductName | X | ...
        r'\|\s*([A-Za-z][A-Za-z\s]{2,25})\s*\|\s*(\d+)\s*\|',
    ]

    found_items = {}
    for pattern in item_patterns:
        for match in re.finditer(pattern, response_text, re.IGNORECASE | re.MULTILINE):
            name = match.group(1).strip()
            quantity = int(match.group(2))

            # Clean up name
            name = name.strip('*').strip()

            # Skip if name is too short, too long, or is a generic word
            skip_words = {'the', 'item', 'product', 'total', 'count', 'stock', 'quantity',
                         'database', 'table', 'result', 'row', 'record', 'value'}
            if len(name) < 2 or len(name) > 50 or name.lower() in skip_words:
                continue

            # Avoid duplicates (case-insensitive)
            name_key = name.lower()
            if name_key not in found_items:
                found_items[name_key] = {"name": name, "value": quantity}
                logger.info(f"[Visualize] Found item: {name} = {quantity}")

    # Convert to chart data
    for item_data in list(found_items.values())[:10]:  # Max 10 items
        chart_data.append(item_data)
        metrics.append({
            "title": item_data["name"],
            "value": f"{item_data['value']} units"
        })

    # =========================================================================
    # PATTERN 3: Price/Currency Data
    # Examples: "$25.99", "price: $100", "total value: $500"
    # =========================================================================
    price_patterns = [
        r'(?:price|cost|value)[:\s]+\$?\s?(\d+(?:\.\d{2})?)',
        r'\$(\d+(?:\.\d{2})?)',
    ]

    prices_found = []
    for pattern in price_patterns:
        for match in re.finditer(pattern, response_text, re.IGNORECASE):
            try:
                price = float(match.group(1))
                if price > 0 and price not in prices_found:
                    prices_found.append(price)
            except:
                continue

    # Add price metrics if found
    if prices_found and len(prices_found) <= 5:
        for i, price in enumerate(prices_found[:3]):
            metrics.append({
                "title": f"Price {i+1}" if len(prices_found) > 1 else "Price",
                "value": f"${price:,.2f}"
            })

    # =========================================================================
    # PATTERN 4: Percentage Data
    # Examples: "50%", "growth: 25%"
    # =========================================================================
    percentage_pattern = r'(\d+(?:\.\d+)?)\s*%'
    percentages = []
    for match in re.finditer(percentage_pattern, response_text):
        try:
            pct = float(match.group(1))
            if 0 <= pct <= 100 and pct not in percentages:
                percentages.append(pct)
        except:
            continue

    if percentages and len(percentages) <= 3:
        for pct in percentages[:2]:
            metrics.append({
                "title": "Percentage",
                "value": f"{pct:.1f}%"
            })

    # =========================================================================
    # BUILD CHART ONLY IF WE HAVE REAL DATA
    # =========================================================================
    charts = []

    if chart_data and len(chart_data) >= 1:
        # Determine best chart type
        if len(chart_data) == 1:
            # Single item - show as metric only, no chart needed
            pass
        elif len(chart_data) <= 5:
            # Few items - bar chart is best
            charts.append({
                "type": "bar",
                "title": "Data Overview",
                "data": chart_data,
                "dataKey": "value",
                "xAxisKey": "name"
            })
        else:
            # Many items - horizontal bar chart
            charts.append({
                "type": "bar",
                "title": "Data Overview",
                "data": chart_data,
                "dataKey": "value",
                "xAxisKey": "name"
            })

    return {
        "metrics": metrics,
        "charts": charts,
        "data_extracted": len(found_items) > 0 or total_found is not None
    }


# ============================================================================
# NOTE: Old helper functions removed. Now using _extract_visualization_from_response
# which only extracts data from the AI response text - never from database.
# This prevents fake/incorrect visualizations for own_database users.
# ============================================================================
