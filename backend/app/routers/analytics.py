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
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get inventory health data with chart-ready structure.
    Returns metrics, alerts, and category breakdown for visualization.
    """
    try:
        data = await get_inventory_analytics(session=db)

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
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get monthly sales data with chart-ready structure.
    Returns metrics, top products, and daily trends for visualization.
    """
    try:
        now = datetime.utcnow()
        year = year or now.year
        month = month or now.month

        data = await get_sales_by_month(year=year, month=month, session=db)

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
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get sales trends data with chart-ready structure.
    Returns daily trends, moving averages, and insights.
    """
    try:
        data = await get_sales_trends(days=days, session=db)

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
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Compare sales between two periods with chart-ready structure.
    """
    try:
        data = await compare_sales(period1=period1, period2=period2, session=db)

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
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get top selling products with chart-ready structure.
    """
    try:
        now = datetime.utcnow()
        data = await get_sales_by_month(year=now.year, month=now.month, session=db)

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
# NEW: Dynamic Visualization Endpoint for ChatKit Integration
# ============================================================================

class VisualizeRequest(BaseModel):
    """Request model for visualization endpoint."""
    query: str
    response_text: Optional[str] = None


@router.post("/visualize")
async def get_visualization_for_query(
    request: VisualizeRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    NEW ENDPOINT: Generate chart-ready visualization data based on user query.

    This endpoint analyzes the query, fetches relevant data, and returns
    structured chart data that Recharts can render directly.

    Flow:
    1. Frontend sends user query after ChatKit response
    2. This endpoint detects intent and fetches appropriate data
    3. Returns structured visualization data
    4. Frontend renders charts with Recharts
    """
    try:
        query = request.query.lower()
        response_text = request.response_text or ""

        logger.info(f"[Visualize] Processing query: {query[:100]}")

        # Detect intent and generate appropriate visualization
        viz_data = await _generate_visualization_for_query(query, response_text, db)

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


async def _generate_visualization_for_query(
    query: str,
    response_text: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    UNIVERSAL visualization generator - works for ANY query.

    Strategy:
    1. First, search database for ANY matching products from the query
    2. If products found, show their data
    3. If sales-related query, show sales data
    4. ALWAYS return some visualization - fallback to overview
    """
    from sqlalchemy import text

    metrics = []
    charts = []
    detected_intent = "unknown"

    query_lower = query.lower()

    # Intent detection (flexible)
    sales_keywords = ['sale', 'sales', 'revenue', 'sold', 'income', 'transaction', 'bill', 'order']
    trend_keywords = ['trend', 'over time', 'history', 'monthly', 'daily', 'weekly', 'chart', 'graph']
    low_keywords = ['low', 'out of stock', 'restock', 'empty', 'minimum', 'running out', 'need to order']
    top_keywords = ['top', 'best', 'highest', 'most', 'popular', 'selling']
    category_keywords = ['category', 'categories', 'type', 'types', 'grocery', 'beauty', 'garments', 'utilities']

    is_sales = any(kw in query_lower for kw in sales_keywords)
    is_trend = any(kw in query_lower for kw in trend_keywords)
    is_low = any(kw in query_lower for kw in low_keywords)
    is_top = any(kw in query_lower for kw in top_keywords)
    is_category = any(kw in query_lower for kw in category_keywords)

    logger.info(f"[Visualize] Query: {query[:50]}... | sales={is_sales}, trend={is_trend}, low={is_low}, top={is_top}")

    # STEP 1: Try to find matching products from the query in database
    found_products = await _smart_product_search(query, db)

    if found_products:
        # Products found! Show their data
        detected_intent = "product_search"
        logger.info(f"[Visualize] Found {len(found_products)} products from query")

        for item in found_products[:10]:  # Limit to 10 products
            stock_qty = float(item['stock_qty']) if item['stock_qty'] else 0
            unit_price = float(item['unit_price']) if item['unit_price'] else 0
            metrics.append({
                "title": item['name'],
                "value": f"{stock_qty:.0f} units",
                "subtitle": f"${unit_price:.2f} each | {item['category']}"
            })

        chart_data = [
            {"name": item['name'][:20], "value": float(item['stock_qty']) if item['stock_qty'] else 0}
            for item in found_products[:10]
        ]

        if chart_data:
            charts.append({
                "type": "bar",
                "title": "Stock Levels",
                "data": chart_data,
                "dataKey": "value",
                "xAxisKey": "name"
            })

    # STEP 2: Sales-related queries
    elif is_sales:
        detected_intent = "sales"
        if is_trend:
            viz = await _get_sales_trend_visualization(db)
        elif is_top:
            viz = await _get_top_sales_visualization(db)
        else:
            viz = await _get_sales_overview_visualization(db)
        metrics.extend(viz.get("metrics", []))
        charts.extend(viz.get("charts", []))

    # STEP 3: Low stock queries
    elif is_low:
        detected_intent = "low_stock"
        viz = await _get_low_stock_visualization(db)
        metrics.extend(viz.get("metrics", []))
        charts.extend(viz.get("charts", []))

    # STEP 4: Top/best items queries
    elif is_top:
        detected_intent = "top_items"
        viz = await _get_top_stock_visualization(db)
        metrics.extend(viz.get("metrics", []))
        charts.extend(viz.get("charts", []))

    # STEP 5: Category-based queries
    elif is_category:
        detected_intent = "category"
        viz = await _get_inventory_overview_visualization(db)
        metrics.extend(viz.get("metrics", []))
        charts.extend(viz.get("charts", []))

    # STEP 6: FALLBACK - Always show something relevant
    if not charts:
        detected_intent = "fallback_overview"
        logger.info("[Visualize] No specific match, showing inventory overview as fallback")

        # Try to parse AI response for any data
        if response_text:
            viz = _parse_response_for_visualization(response_text)
            if viz.get("charts"):
                metrics.extend(viz.get("metrics", []))
                charts.extend(viz.get("charts", []))

        # Still nothing? Show inventory overview
        if not charts:
            viz = await _get_inventory_overview_visualization(db)
            metrics.extend(viz.get("metrics", []))
            charts.extend(viz.get("charts", []))

    return {
        "metrics": metrics,
        "charts": charts,
        "intent": detected_intent,
        "products_found": len(found_products) if found_products else 0
    }


async def _smart_product_search(query: str, db: AsyncSession) -> List[Dict]:
    """
    SMART product search - searches database for ANY words from the query.
    This makes visualization work for ANY product type (grocery, beauty, garments, etc.)
    """
    from sqlalchemy import text
    import re

    # Words to skip when searching (common English words)
    skip_words = {
        'show', 'me', 'the', 'a', 'an', 'is', 'are', 'what', 'how', 'many', 'much',
        'get', 'find', 'search', 'list', 'all', 'can', 'you', 'tell', 'about',
        'stock', 'inventory', 'item', 'items', 'product', 'products', 'level', 'levels',
        'quantity', 'check', 'please', 'give', 'want', 'need', 'have', 'do', 'does',
        'for', 'in', 'on', 'at', 'to', 'of', 'and', 'or', 'with', 'my', 'our', 'your',
        'i', 'we', 'they', 'it', 'this', 'that', 'these', 'those', 'there', 'here',
        'be', 'been', 'being', 'was', 'were', 'has', 'had', 'having', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall'
    }

    # Extract potential search words from query
    words = re.findall(r'\b[a-zA-Z]{2,}\b', query.lower())
    search_words = [w for w in words if w not in skip_words]

    if not search_words:
        return []

    logger.info(f"[SmartSearch] Searching for words: {search_words}")

    found_products = []
    seen_ids = set()

    # Search for each word in the database
    for word in search_words[:5]:  # Limit to first 5 search words
        try:
            search_query = text("""
                SELECT id, name, stock_qty, unit_price, category
                FROM items
                WHERE LOWER(name) LIKE :pattern
                   OR LOWER(category) LIKE :pattern
                ORDER BY stock_qty DESC
                LIMIT 10
            """)

            result = await db.execute(search_query, {"pattern": f"%{word}%"})
            items = result.fetchall()

            for item in items:
                if item.id not in seen_ids:
                    seen_ids.add(item.id)
                    found_products.append({
                        "id": item.id,
                        "name": item.name,
                        "stock_qty": item.stock_qty,
                        "unit_price": item.unit_price,
                        "category": item.category
                    })
        except Exception as e:
            logger.error(f"[SmartSearch] Error searching for '{word}': {e}")
            continue

    return found_products[:10]  # Return max 10 products


def _extract_product_names(query: str) -> List[str]:
    """Extract potential product names from query."""
    import re

    # Common words to ignore
    stop_words = {
        'show', 'me', 'the', 'stock', 'of', 'and', 'or', 'for', 'in', 'a', 'an',
        'what', 'is', 'are', 'how', 'many', 'much', 'get', 'find', 'search',
        'inventory', 'item', 'items', 'product', 'products', 'unit', 'units',
        'level', 'levels', 'quantity', 'check', 'display', 'list', 'all',
        'overview', 'health', 'status', 'summary', 'report', 'analytics',
        'low', 'out', 'high', 'top', 'best', 'worst', 'which', 'that',
        'sales', 'revenue', 'trend', 'trends', 'monthly', 'daily', 'weekly',
        'compare', 'comparison', 'versus', 'total', 'average', 'current'
    }

    # Skip extraction for overview/general queries
    overview_patterns = ['overview', 'health', 'status', 'summary', 'all items', 'all products']
    if any(p in query.lower() for p in overview_patterns):
        return []

    # Skip extraction for low stock queries
    if 'low' in query.lower() and 'stock' in query.lower():
        return []

    # Split by common delimiters
    parts = re.split(r'[,\s]+and\s+|[,\s]+or\s+|,\s*', query.lower())

    products = []
    for part in parts:
        # Clean up
        words = part.strip().split()
        # Filter out stop words and keep potential product names
        name_words = [w for w in words if w not in stop_words and len(w) > 1]
        if name_words:
            products.append(' '.join(name_words))

    # Filter out empty strings, very short results, and single question marks
    products = [p for p in products if len(p) > 2 and p != '?' and not p.endswith('?')]

    return products[:5]  # Limit to 5 products


async def _get_product_stock_visualization(
    product_names: List[str],
    db: AsyncSession
) -> Dict[str, Any]:
    """Get visualization for specific products."""
    from sqlalchemy import text

    metrics = []
    chart_data = []

    for name in product_names:
        # Search for product (case-insensitive partial match)
        query = text("""
            SELECT id, name, stock_qty, unit_price, category
            FROM items
            WHERE LOWER(name) LIKE :pattern
            LIMIT 5
        """)

        result = await db.execute(query, {"pattern": f"%{name.lower()}%"})
        items = result.fetchall()

        for item in items:
            stock_qty = float(item.stock_qty) if item.stock_qty else 0
            unit_price = float(item.unit_price) if item.unit_price else 0
            metrics.append({
                "title": item.name,
                "value": f"{stock_qty:.0f} units",
                "subtitle": f"${unit_price:.2f} each"
            })
            chart_data.append({
                "name": item.name[:20],
                "value": stock_qty,
                "price": unit_price
            })

    charts = []
    if chart_data:
        charts.append({
            "type": "bar",
            "title": "Stock Levels",
            "data": chart_data,
            "dataKey": "value",
            "xAxisKey": "name"
        })

    return {"metrics": metrics, "charts": charts}


async def _get_low_stock_visualization(db: AsyncSession) -> Dict[str, Any]:
    """Get low stock items visualization."""
    from sqlalchemy import text

    # Using stock_qty <= 10 as threshold since there's no reorder_level column
    query = text("""
        SELECT id, name, stock_qty, unit_price, category
        FROM items
        WHERE stock_qty <= 10
        ORDER BY stock_qty ASC
        LIMIT 10
    """)

    result = await db.execute(query)
    items = result.fetchall()

    metrics = [
        {"title": "Low Stock Items", "value": str(len(items)), "status": "warning"}
    ]

    chart_data = [
        {"name": item.name[:15], "value": float(item.stock_qty), "threshold": 10}
        for item in items
    ]

    charts = []
    if chart_data:
        charts.append({
            "type": "bar",
            "title": "Low Stock Items",
            "data": chart_data,
            "dataKey": "value",
            "xAxisKey": "name",
            "color": "#EF4444"
        })

    return {"metrics": metrics, "charts": charts}


async def _get_top_stock_visualization(db: AsyncSession) -> Dict[str, Any]:
    """Get top items by stock value."""
    from sqlalchemy import text

    query = text("""
        SELECT name, stock_qty, unit_price, (stock_qty * unit_price) as total_value
        FROM items
        ORDER BY total_value DESC
        LIMIT 10
    """)

    result = await db.execute(query)
    items = result.fetchall()

    total_value = sum(item.total_value for item in items)

    metrics = [
        {"title": "Top 10 Value", "value": f"${total_value:,.2f}"}
    ]

    chart_data = [
        {"name": item.name[:15], "value": float(item.total_value)}
        for item in items
    ]

    charts = []
    if chart_data:
        charts.append({
            "type": "bar",
            "title": "Top Items by Stock Value",
            "data": chart_data,
            "dataKey": "value",
            "xAxisKey": "name",
            "formatValue": "currency"
        })

    return {"metrics": metrics, "charts": charts}


async def _get_inventory_overview_visualization(db: AsyncSession) -> Dict[str, Any]:
    """Get general inventory overview."""
    try:
        data = await get_inventory_analytics(session=db)

        summary = data.get("summary", {})
        category_breakdown = data.get("category_breakdown", [])

        metrics = [
            {"title": "Total Items", "value": str(summary.get("total_items", 0))},
            {"title": "Total Value", "value": f"${summary.get('total_inventory_value', 0):,.2f}"},
            {"title": "Out of Stock", "value": str(summary.get("out_of_stock_count", 0)), "status": "danger" if summary.get("out_of_stock_count", 0) > 0 else "success"},
            {"title": "Low Stock", "value": str(summary.get("low_stock_count", 0)), "status": "warning" if summary.get("low_stock_count", 0) > 0 else "success"},
        ]

        chart_data = [
            {"name": cat.get("category", "Unknown")[:15], "value": cat.get("total_value", 0)}
            for cat in category_breakdown[:8]
        ]

        charts = []
        if chart_data:
            charts.append({
                "type": "bar",
                "title": "Inventory Value by Category",
                "data": chart_data,
                "dataKey": "value",
                "xAxisKey": "name",
                "formatValue": "currency"
            })

        return {"metrics": metrics, "charts": charts}
    except Exception as e:
        logger.error(f"Error in inventory overview: {e}")
        return {"metrics": [], "charts": []}


async def _get_sales_trend_visualization(db: AsyncSession) -> Dict[str, Any]:
    """Get sales trend visualization."""
    try:
        data = await get_sales_trends(days=30, session=db)

        summary = data.get("summary", {})
        daily_trends = data.get("daily_trends", [])

        metrics = [
            {"title": "Total Sales (30d)", "value": f"${summary.get('total_sales', 0):,.2f}"},
            {"title": "Avg Daily", "value": f"${summary.get('average_daily_sales', 0):,.2f}"},
        ]

        chart_data = [
            {"name": t.get("date", "")[-5:], "value": t.get("sales", 0)}
            for t in daily_trends[-30:]
        ]

        charts = []
        if chart_data:
            charts.append({
                "type": "line",
                "title": "Sales Trend (Last 30 Days)",
                "data": chart_data,
                "dataKey": "value",
                "xAxisKey": "name",
                "formatValue": "currency"
            })

        return {"metrics": metrics, "charts": charts}
    except Exception as e:
        logger.error(f"Error in sales trend: {e}")
        return {"metrics": [], "charts": []}


async def _get_top_sales_visualization(db: AsyncSession) -> Dict[str, Any]:
    """Get top selling products."""
    try:
        now = datetime.utcnow()
        data = await get_sales_by_month(year=now.year, month=now.month, session=db)

        top_products = data.get("top_products", [])[:5]

        metrics = [
            {"title": p.get("name", "Unknown")[:20], "value": f"${p.get('revenue', 0):,.2f}"}
            for p in top_products[:3]
        ]

        chart_data = [
            {"name": p.get("name", "Unknown")[:15], "value": p.get("revenue", 0)}
            for p in top_products
        ]

        charts = []
        if chart_data:
            charts.append({
                "type": "bar",
                "title": "Top Products by Revenue",
                "data": chart_data,
                "dataKey": "value",
                "xAxisKey": "name",
                "formatValue": "currency"
            })

        return {"metrics": metrics, "charts": charts}
    except Exception as e:
        logger.error(f"Error in top sales: {e}")
        return {"metrics": [], "charts": []}


async def _get_sales_overview_visualization(db: AsyncSession) -> Dict[str, Any]:
    """Get sales overview with chart."""
    try:
        now = datetime.utcnow()
        data = await get_sales_by_month(year=now.year, month=now.month, session=db)

        summary = data.get("summary", {})
        top_products = data.get("top_products", [])[:5]

        metrics = [
            {"title": "Total Sales", "value": f"${summary.get('total_sales', 0):,.2f}"},
            {"title": "Transactions", "value": str(summary.get("total_transactions", 0))},
            {"title": "Avg Transaction", "value": f"${summary.get('average_transaction_value', 0):,.2f}"},
        ]

        # Always include a chart for sales
        charts = []
        if top_products:
            chart_data = [
                {"name": p.get("name", "Unknown")[:15], "value": p.get("revenue", 0)}
                for p in top_products
            ]
            charts.append({
                "type": "bar",
                "title": "Top Products by Revenue",
                "data": chart_data,
                "dataKey": "value",
                "xAxisKey": "name",
                "formatValue": "currency"
            })

        return {"metrics": metrics, "charts": charts}
    except Exception as e:
        logger.error(f"Error in sales overview: {e}")
        return {"metrics": [], "charts": []}


def _parse_response_for_visualization(response_text: str) -> Dict[str, Any]:
    """Parse AI response text to extract visualization data as fallback."""
    import re

    metrics = []
    chart_data = []

    # Pattern: "ProductName" has X units / stock quantity of X
    patterns = [
        r'"([^"]+)"\s+has\s+(?:a\s+)?(?:stock\s+)?(?:quantity\s+of\s+)?\*?\*?(\d+)\s*(?:units?)?\*?\*?',
        r'\*\*([^*]+)\*\*[:\s]+\*?\*?(\d+)\s*(?:units?)?\*?\*?',
        r'([A-Z][a-zA-Z\s]+?):\s*(\d+)\s*(?:units?|pcs?|items?)',
    ]

    found = set()
    for pattern in patterns:
        for match in re.finditer(pattern, response_text, re.IGNORECASE):
            name = match.group(1).strip()
            value = int(match.group(2))

            if name.lower() not in found and len(name) > 2:
                found.add(name.lower())
                metrics.append({
                    "title": name,
                    "value": f"{value} units"
                })
                chart_data.append({
                    "name": name[:15],
                    "value": value
                })

    charts = []
    if chart_data:
        charts.append({
            "type": "bar",
            "title": "Stock Levels",
            "data": chart_data,
            "dataKey": "value",
            "xAxisKey": "name"
        })

    return {"metrics": metrics, "charts": charts}
