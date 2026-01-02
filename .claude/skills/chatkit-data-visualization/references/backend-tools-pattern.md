# Backend Tools Pattern for Data Visualization

> This reference explains how to create backend tools that return visualization-ready data for any domain.

---

## Overview

When building visualization features, your backend needs:
1. **Domain Tools** - Functions that fetch/process data from your data source
2. **Visualization Endpoint** - POST endpoint that extracts data from AI response
3. **MCP Server Integration** - If using MCP for tool calling

---

## Pattern 1: Direct Analytics Tools

These tools are called directly (not via AI agent) for specific visualizations:

```python
# backend/app/routers/your_domain_analytics.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from datetime import datetime

from app.database import get_db
from app.models import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/your-domain", tags=["your-domain"])


@router.get("/overview")
async def get_overview_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get overview data with chart-ready structure.
    Returns metrics and visualizations for dashboard.
    """
    try:
        # Fetch your domain data
        # Example: sales, inventory, patients, transactions, etc.
        data = await fetch_your_domain_data(db, current_user.id)

        # Transform to visualization format
        summary = data.get("summary", {})

        # Prepare metrics cards
        metrics = [
            {
                "title": "Total Items",
                "value": str(summary.get("total", 0)),
                "icon": "package"
            },
            {
                "title": "Total Value",
                "value": f"${summary.get('value', 0):,.2f}",
                "icon": "dollar"
            },
            {
                "title": "Active",
                "value": str(summary.get("active", 0)),
                "icon": "check",
                "status": "success"
            },
            {
                "title": "Alerts",
                "value": str(summary.get("alerts", 0)),
                "icon": "alert",
                "status": "warning" if summary.get("alerts", 0) > 0 else "success"
            },
        ]

        # Prepare chart data
        category_data = data.get("by_category", [])
        category_chart = [
            {"label": item.get("name", "Unknown"), "value": item.get("value", 0)}
            for item in category_data[:8]
        ]

        trend_data = data.get("trends", [])
        trend_chart = [
            {"label": t.get("date", "")[-5:], "value": t.get("value", 0)}
            for t in trend_data[-30:]
        ]

        return {
            "success": True,
            "metrics": metrics,
            "visualizations": [
                {
                    "type": "bar-chart",
                    "title": "Value by Category",
                    "data": category_chart,
                    "formatValue": "currency"
                },
                {
                    "type": "line-chart",
                    "title": "Daily Trend",
                    "data": trend_chart,
                    "formatValue": "number"
                }
            ],
            "raw_data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Pattern 2: MCP Server Tools

If using MCP for AI agent tool calling:

```python
# backend/app/mcp_server/tools_your_domain.py

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.mcp_server.utils import mcp_error_handler


@mcp_error_handler()
async def get_domain_summary(
    session: AsyncSession,
    user_id: Optional[int] = None,
    days: int = 30
) -> dict:
    """
    Get summary data for your domain.

    Args:
        session: Database session
        user_id: User ID for data scoping
        days: Number of days to analyze

    Returns:
        Dictionary with summary, items, and trends
    """
    from sqlalchemy import select, func
    from app.models import YourModel

    # Build query with user scope
    query = select(YourModel)
    if user_id:
        query = query.where(YourModel.user_id == user_id)

    # Date filter
    start_date = datetime.utcnow() - timedelta(days=days)
    query = query.where(YourModel.created_at >= start_date)

    result = await session.execute(query)
    items = result.scalars().all()

    # Calculate summary
    total_value = sum(item.value for item in items)
    total_count = len(items)

    # Group by category
    category_breakdown = {}
    for item in items:
        cat = item.category or "Uncategorized"
        if cat not in category_breakdown:
            category_breakdown[cat] = {"count": 0, "value": 0}
        category_breakdown[cat]["count"] += 1
        category_breakdown[cat]["value"] += item.value

    # Return structured data
    return {
        "period": {
            "days": days,
            "start": start_date.isoformat(),
            "end": datetime.utcnow().isoformat()
        },
        "summary": {
            "total_count": total_count,
            "total_value": round(total_value, 2),
            "average_value": round(total_value / max(total_count, 1), 2)
        },
        "category_breakdown": [
            {
                "category": cat,
                "count": data["count"],
                "value": round(data["value"], 2)
            }
            for cat, data in sorted(
                category_breakdown.items(),
                key=lambda x: x[1]["value"],
                reverse=True
            )
        ],
        "generated_at": datetime.utcnow().isoformat()
    }


# Register with MCP server
# backend/app/mcp_server/server.py

from fastmcp import FastMCP
from app.mcp_server.tools_your_domain import get_domain_summary

server = FastMCP("Your Domain MCP")

@server.tool()
async def domain_summary(days: int = 30, user_id: int = None) -> dict:
    """Get summary for your domain data."""
    async with async_session() as session:
        return await get_domain_summary(
            session=session,
            user_id=user_id,
            days=days
        )
```

---

## Pattern 3: Visualization Endpoint

The key endpoint that extracts data from AI responses:

```python
# backend/app/routers/your_domain_analytics.py

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import re
import logging

logger = logging.getLogger(__name__)


class VisualizeRequest(BaseModel):
    """Request model for visualization endpoint."""
    query: str
    response_text: Optional[str] = None
    user_id: Optional[int] = None


@router.post("/visualize")
async def get_visualization(
    request: VisualizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    AI-POWERED VISUALIZATION ENDPOINT

    CRITICAL RULES:
    1. Only extract data that exists in response_text
    2. NEVER generate fake/placeholder data
    3. Return empty arrays if no visualizable data found
    4. Charts must match exactly what the AI said
    """
    try:
        query = request.query
        response_text = request.response_text or ""

        logger.info(f"[Visualize] Query: {query[:50]}...")
        logger.info(f"[Visualize] Response length: {len(response_text)}")

        # Extract data from AI response
        viz_data = extract_visualization_from_response(query, response_text)

        # If no data found, return empty
        if not viz_data.get("metrics") and not viz_data.get("charts"):
            return {
                "success": True,
                "query": query,
                "metrics": [],
                "charts": [],
                "message": "No numerical data to visualize"
            }

        return {
            "success": True,
            "query": query,
            **viz_data
        }

    except Exception as e:
        logger.error(f"Visualization error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "metrics": [],
            "charts": []
        }


def extract_visualization_from_response(
    query: str,
    response_text: str
) -> Dict[str, Any]:
    """
    Parse AI response to extract REAL data for visualization.

    STRATEGY:
    1. Use regex to find numerical patterns
    2. Identify data type (counts, prices, quantities, percentages)
    3. Create appropriate visualization type
    4. Return ONLY data from response - NEVER fake data
    """
    metrics: List[Dict] = []
    chart_data: List[Dict] = []

    if not response_text or len(response_text) < 10:
        return {"metrics": [], "charts": []}

    # =========================================
    # PATTERN 1: Total/Summary Numbers
    # =========================================
    # Matches: "total of 50 items", "there are 25 records"
    total_patterns = [
        r'total\s+of\s+\*?\*?(\d+)\s*\*?\*?\s*(item|product|record|row|entr)',
        r'(?:there\s+(?:is|are)|have)\s+\*?\*?(\d+)\s*\*?\*?',
        r'(?:count|total)[:\s]+\*?\*?(\d+)\*?\*?',
        r'\*?\*?(\d+)\*?\*?\s+(?:item|product|record)s?\s+(?:in|found|total)',
    ]

    for pattern in total_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            total = int(match.group(1))
            metrics.append({
                "title": "Total",
                "value": str(total),
                "status": "success" if total > 0 else "warning"
            })
            break

    # =========================================
    # PATTERN 2: Named Items with Values
    # =========================================
    # Matches: '"Rice" has quantity of 50', '**Product**: 100 units'
    item_patterns = [
        r'["\']([^"\']+)["\']\s+has\s+(?:a\s+)?(?:stock\s+)?(?:quantity\s+of\s+)?\*?\*?(\d+)',
        r'\*\*([^*]+)\*\*[:\s]+\*?\*?(\d+)\s*\*?\*?',
        r'^[•\-\*]?\s*([A-Za-z][A-Za-z\s]{2,30})[:\s]+(\d+)\s*(?:unit|item)?',
        r'\|\s*([A-Za-z][A-Za-z\s]{2,25})\s*\|\s*(\d+)\s*\|',
    ]

    found_items = {}
    skip_words = {
        'the', 'item', 'product', 'total', 'count', 'stock',
        'database', 'table', 'result', 'row', 'record', 'value'
    }

    for pattern in item_patterns:
        for match in re.finditer(pattern, response_text, re.IGNORECASE | re.MULTILINE):
            name = match.group(1).strip('*').strip()
            value = int(match.group(2))

            # Validate name
            if len(name) < 2 or len(name) > 50:
                continue
            if name.lower() in skip_words:
                continue

            name_key = name.lower()
            if name_key not in found_items:
                found_items[name_key] = {"name": name, "value": value}

    # Add to chart data
    for item in list(found_items.values())[:10]:
        chart_data.append(item)
        metrics.append({
            "title": item["name"],
            "value": f"{item['value']} units"
        })

    # =========================================
    # PATTERN 3: Currency/Price Values
    # =========================================
    # Matches: "$25.99", "price: $100"
    price_patterns = [
        r'(?:price|cost|value|total)[:\s]+\$?\s?(\d+(?:\.\d{2})?)',
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

    # Add price metrics
    for i, price in enumerate(prices_found[:3]):
        metrics.append({
            "title": f"Price {i+1}" if len(prices_found) > 1 else "Price",
            "value": f"${price:,.2f}"
        })

    # =========================================
    # PATTERN 4: Percentage Values
    # =========================================
    # Matches: "50%", "growth: 25%"
    pct_pattern = r'(\d+(?:\.\d+)?)\s*%'
    percentages = []

    for match in re.finditer(pct_pattern, response_text):
        try:
            pct = float(match.group(1))
            if 0 <= pct <= 100 and pct not in percentages:
                percentages.append(pct)
        except:
            continue

    for pct in percentages[:2]:
        metrics.append({
            "title": "Percentage",
            "value": f"{pct:.1f}%"
        })

    # =========================================
    # BUILD CHARTS (only if real data exists)
    # =========================================
    charts = []

    if chart_data and len(chart_data) >= 2:
        # Determine best chart type
        if len(chart_data) <= 5:
            chart_type = "bar"
        else:
            chart_type = "bar"  # Horizontal bar for many items

        charts.append({
            "type": chart_type,
            "title": "Data Overview",
            "data": chart_data,
            "dataKey": "value",
            "xAxisKey": "name"
        })

    return {
        "metrics": metrics,
        "charts": charts,
        "data_extracted": len(found_items) > 0
    }
```

---

## Response Format Standards

### Metrics Format

```json
{
  "title": "Total Sales",
  "value": "$15,000",
  "icon": "dollar",
  "status": "success",
  "subtitle": "This month"
}
```

**Status Options:**
- `success` - Green indicator
- `warning` - Yellow indicator
- `danger` - Red indicator
- `neutral` - Gray indicator (default)

### Chart Format

```json
{
  "type": "bar",
  "title": "Top Products",
  "data": [
    {"name": "Product A", "value": 150},
    {"name": "Product B", "value": 100}
  ],
  "dataKey": "value",
  "xAxisKey": "name",
  "formatValue": "currency"
}
```

**Chart Types:**
- `bar` - Vertical or horizontal bar chart
- `line` - Line chart for trends
- `pie` - Pie chart for distribution

**Format Values:**
- `currency` - Display as $X,XXX.XX
- `number` - Display as X,XXX
- `percentage` - Display as X%

---

## Error Handling

```python
from app.mcp_server.utils import mcp_error_handler

@mcp_error_handler()
async def your_tool_function(...):
    """
    The decorator handles:
    - Database errors
    - Validation errors
    - Timeout errors
    - Returns structured error response
    """
    pass
```

---

## User Data Scoping

ALWAYS filter data by user_id:

```python
# In every query
query = select(Model).where(Model.user_id == user_id)

# In tool parameters
async def get_data(session, user_id: Optional[int] = None):
    if user_id:
        query = query.where(Model.user_id == user_id)
```

---

## Best Practices

1. **Always validate input ranges** - Dates, limits, pagination
2. **Use async/await** - All database operations should be async
3. **Return consistent format** - Same structure for success/error
4. **Log for debugging** - Log queries and response lengths
5. **Handle empty data** - Return valid empty arrays, not null
6. **Limit results** - Use [:10] or similar to prevent huge responses
7. **Round numbers** - Use `round(value, 2)` for currency/decimals
