# Data Extraction from AI Responses

> This reference explains the regex patterns and strategies for extracting visualizable data from AI agent responses.

---

## Core Principle

**NEVER generate fake data. ONLY extract data that actually exists in the AI response text.**

The visualization should be a direct reflection of what the AI said - not a guess or approximation.

---

## Extraction Strategy

```
AI Response Text
       │
       ▼
┌─────────────────────────────┐
│  Pattern Matching Pipeline  │
├─────────────────────────────┤
│ 1. Total/Count Numbers      │
│ 2. Named Items + Values     │
│ 3. Currency/Price Data      │
│ 4. Percentage Values        │
│ 5. Date/Time Series         │
└─────────────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│    Data Validation          │
├─────────────────────────────┤
│ - Remove duplicates         │
│ - Skip generic words        │
│ - Validate ranges           │
│ - Limit results             │
└─────────────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│    Chart Type Selection     │
├─────────────────────────────┤
│ - 1 item → Metrics only     │
│ - 2-5 items → Bar chart     │
│ - 6+ items → Horizontal bar │
│ - Time data → Line chart    │
│ - Distribution → Pie chart  │
└─────────────────────────────┘
       │
       ▼
   Chart-Ready JSON
```

---

## Pattern Library

### Pattern 1: Total/Count Numbers

Extracts summary totals from AI responses.

**Examples that should match:**
- "There is a total of **50** items"
- "There are 25 records in the database"
- "Total: 100"
- "Count: 75"
- "I found 30 products"

```python
total_patterns = [
    # "total of X items/products/records"
    r'total\s+of\s+\*?\*?(\d+)\s*\*?\*?\s*(item|product|record|row|entr)',

    # "there is/are X items"
    r'(?:there\s+(?:is|are)|have)\s+\*?\*?(\d+)\s*\*?\*?\s*(item|product|record)',

    # "count: X" or "total: X"
    r'(?:count|total)[:\s]+\*?\*?(\d+)\*?\*?',

    # "X items found/total"
    r'\*?\*?(\d+)\*?\*?\s+(?:item|product|record)s?\s+(?:in|found|total)',

    # "found X results"
    r'found\s+\*?\*?(\d+)\*?\*?\s+result',
]
```

**Usage:**
```python
for pattern in total_patterns:
    match = re.search(pattern, response_text, re.IGNORECASE)
    if match:
        total = int(match.group(1))
        metrics.append({
            "title": "Total",
            "value": str(total),
            "status": "success" if total > 0 else "warning"
        })
        break  # Only capture first total
```

---

### Pattern 2: Named Items with Values

Extracts item-value pairs for chart data.

**Examples that should match:**
- `"Rice" has stock quantity of **50**`
- `**Product A**: 100 units`
- `• Apples: 25`
- `| Product Name | 50 | $10.00 |`

```python
item_patterns = [
    # "Name" has (stock) quantity of X (units)
    r'["\']([^"\']+)["\']\s+has\s+(?:a\s+)?(?:stock\s+)?(?:quantity\s+of\s+)?\*?\*?(\d+)',

    # **Name**: X units
    r'\*\*([^*]+)\*\*[:\s]+\*?\*?(\d+)\s*\*?\*?\s*(?:unit|stock|quantit)?',

    # Bullet: Name: X units
    r'^[•\-\*]?\s*([A-Za-z][A-Za-z\s]{2,30})[:\s]+(\d+)\s*(?:unit|item|stock|pcs?)?',

    # name: "X", quantity: Y (JSON-like)
    r'name[:\s]+["\']?([^"\',:]+)["\']?[,\s]+(?:quantity|stock|count)[:\s]+(\d+)',

    # Table row: | Name | Value |
    r'\|\s*([A-Za-z][A-Za-z\s]{2,25})\s*\|\s*(\d+)\s*\|',
]
```

**Usage with validation:**
```python
found_items = {}

# Words to skip (not real item names)
skip_words = {
    'the', 'item', 'product', 'total', 'count', 'stock', 'quantity',
    'database', 'table', 'result', 'row', 'record', 'value', 'name',
    'items', 'products', 'results', 'rows', 'records'
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

        # Avoid duplicates (case-insensitive)
        name_key = name.lower()
        if name_key not in found_items:
            found_items[name_key] = {"name": name, "value": value}

# Limit to top 10
chart_data = list(found_items.values())[:10]
```

---

### Pattern 3: Currency/Price Values

Extracts monetary values.

**Examples that should match:**
- `$25.99`
- `price: $100`
- `total value: $1,500.00`
- `cost: 75.50`

```python
price_patterns = [
    # "price/cost/value: $X.XX"
    r'(?:price|cost|value|total)[:\s]+\$?\s?(\d+(?:,\d{3})*(?:\.\d{2})?)',

    # "$X.XX" standalone
    r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',

    # "X.XX dollars"
    r'(\d+(?:\.\d{2})?)\s*dollars?',
]

prices_found = []
for pattern in price_patterns:
    for match in re.finditer(pattern, response_text, re.IGNORECASE):
        try:
            # Remove commas and convert
            price_str = match.group(1).replace(',', '')
            price = float(price_str)
            if price > 0 and price not in prices_found:
                prices_found.append(price)
        except:
            continue

# Add to metrics (limit to 3)
for i, price in enumerate(prices_found[:3]):
    metrics.append({
        "title": f"Price {i+1}" if len(prices_found) > 1 else "Price",
        "value": f"${price:,.2f}"
    })
```

---

### Pattern 4: Percentage Values

Extracts percentage data.

**Examples that should match:**
- `50%`
- `growth: 25%`
- `increased by 15.5%`
- `completion rate: 75%`

```python
percentage_patterns = [
    # "X%" basic
    r'(\d+(?:\.\d+)?)\s*%',

    # "X percent"
    r'(\d+(?:\.\d+)?)\s*percent',
]

percentages = []
for pattern in percentage_patterns:
    for match in re.finditer(pattern, response_text, re.IGNORECASE):
        try:
            pct = float(match.group(1))
            # Validate range
            if 0 <= pct <= 100 and pct not in percentages:
                percentages.append(pct)
        except:
            continue

# Add to metrics (limit to 2)
for pct in percentages[:2]:
    metrics.append({
        "title": "Percentage",
        "value": f"{pct:.1f}%"
    })
```

---

### Pattern 5: Date/Time Series

Extracts date-based data for line charts.

**Examples that should match:**
- `2025-01-15: 500`
- `January 15: $1,200`
- `01/15: 75 units`

```python
date_patterns = [
    # YYYY-MM-DD: Value
    r'(\d{4}-\d{2}-\d{2})[:\s]+\$?(\d+(?:\.\d{2})?)',

    # Month Day: Value
    r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2})[:\s]+\$?(\d+(?:\.\d{2})?)',

    # MM/DD: Value
    r'(\d{1,2}/\d{1,2})[:\s]+\$?(\d+(?:\.\d{2})?)',
]

time_series = []
for pattern in date_patterns:
    for match in re.finditer(pattern, response_text, re.IGNORECASE):
        date_str = match.group(1)
        value = float(match.group(2))
        time_series.append({"date": date_str, "value": value})

# If time series data found, create line chart
if len(time_series) >= 2:
    charts.append({
        "type": "line",
        "title": "Trend Over Time",
        "data": [{"name": d["date"], "value": d["value"]} for d in time_series],
        "dataKey": "value",
        "xAxisKey": "name"
    })
```

---

## Domain-Specific Pattern Extensions

### Healthcare Domain

```python
healthcare_patterns = [
    # "X patients"
    r'\*?\*?(\d+)\*?\*?\s+patient',

    # Diagnosis: Count
    r'([A-Za-z][A-Za-z\s]{2,30})\s+(?:cases?|diagnosis|diagnosed)[:\s]+(\d+)',

    # Blood pressure: X/Y
    r'blood\s+pressure[:\s]+(\d+)/(\d+)',

    # Temperature: X.X F/C
    r'temperature[:\s]+(\d+(?:\.\d+)?)\s*[FC°]',
]
```

### Finance Domain

```python
finance_patterns = [
    # Revenue: $X
    r'(?:revenue|income|earnings)[:\s]+\$(\d+(?:,\d{3})*(?:\.\d{2})?)',

    # Stock: X.XX (change)
    r'([A-Z]{2,5})[:\s]+\$?(\d+(?:\.\d{2})?)',

    # ROI: X%
    r'(?:ROI|return)[:\s]+(\d+(?:\.\d+)?)\s*%',

    # Quarter results
    r'Q([1-4])[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
]
```

### E-commerce Domain

```python
ecommerce_patterns = [
    # X orders
    r'\*?\*?(\d+)\*?\*?\s+orders?',

    # Product: X sold
    r'([A-Za-z][A-Za-z\s]{2,30})[:\s]+(\d+)\s+sold',

    # Cart value: $X
    r'(?:cart|order)\s+(?:value|total)[:\s]+\$(\d+(?:\.\d{2})?)',

    # Conversion: X%
    r'(?:conversion|rate)[:\s]+(\d+(?:\.\d+)?)\s*%',
]
```

---

## Complete Extraction Function

```python
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def extract_visualization_from_response(
    query: str,
    response_text: str,
    domain: str = "general"
) -> Dict[str, Any]:
    """
    Extract visualization data from AI response.

    Args:
        query: Original user query (for context)
        response_text: Full AI response text
        domain: Domain for specialized patterns

    Returns:
        Dict with metrics and charts arrays
    """
    metrics: List[Dict] = []
    chart_data: List[Dict] = []

    if not response_text or len(response_text) < 10:
        logger.info("Response too short for visualization")
        return {"metrics": [], "charts": []}

    logger.info(f"Extracting from: {response_text[:100]}...")

    # =====================
    # 1. TOTAL/COUNT
    # =====================
    total_patterns = [
        r'total\s+of\s+\*?\*?(\d+)\s*\*?\*?\s*(item|product|record|row|entr)',
        r'(?:there\s+(?:is|are)|have)\s+\*?\*?(\d+)\s*\*?\*?',
        r'(?:count|total)[:\s]+\*?\*?(\d+)\*?\*?',
    ]

    total_found = None
    for pattern in total_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            total_found = int(match.group(1))
            metrics.append({
                "title": "Total",
                "value": str(total_found),
                "status": "success" if total_found > 0 else "warning"
            })
            break

    # =====================
    # 2. NAMED ITEMS
    # =====================
    item_patterns = [
        r'["\']([^"\']+)["\']\s+has\s+(?:quantity\s+of\s+)?\*?\*?(\d+)',
        r'\*\*([^*]+)\*\*[:\s]+\*?\*?(\d+)\s*\*?\*?',
        r'^[•\-\*]?\s*([A-Za-z][A-Za-z\s]{2,30})[:\s]+(\d+)',
    ]

    skip_words = {
        'the', 'item', 'product', 'total', 'count', 'stock',
        'database', 'table', 'result', 'row', 'record', 'value'
    }

    found_items = {}
    for pattern in item_patterns:
        for match in re.finditer(pattern, response_text, re.IGNORECASE | re.MULTILINE):
            name = match.group(1).strip('*').strip()
            value = int(match.group(2))

            if len(name) < 2 or len(name) > 50:
                continue
            if name.lower() in skip_words:
                continue

            name_key = name.lower()
            if name_key not in found_items:
                found_items[name_key] = {"name": name, "value": value}

    for item in list(found_items.values())[:10]:
        chart_data.append(item)
        metrics.append({
            "title": item["name"],
            "value": f"{item['value']} units"
        })

    # =====================
    # 3. CURRENCY
    # =====================
    price_pattern = r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
    prices = []
    for match in re.finditer(price_pattern, response_text):
        try:
            price = float(match.group(1).replace(',', ''))
            if price > 0 and price not in prices:
                prices.append(price)
        except:
            continue

    for price in prices[:3]:
        metrics.append({
            "title": "Price",
            "value": f"${price:,.2f}"
        })

    # =====================
    # 4. PERCENTAGES
    # =====================
    pct_pattern = r'(\d+(?:\.\d+)?)\s*%'
    for match in re.finditer(pct_pattern, response_text):
        try:
            pct = float(match.group(1))
            if 0 <= pct <= 100:
                metrics.append({
                    "title": "Percentage",
                    "value": f"{pct:.1f}%"
                })
                break
        except:
            continue

    # =====================
    # BUILD CHARTS
    # =====================
    charts = []

    if len(chart_data) >= 2:
        charts.append({
            "type": "bar",
            "title": "Data Overview",
            "data": chart_data,
            "dataKey": "value",
            "xAxisKey": "name"
        })

    logger.info(f"Extracted: {len(metrics)} metrics, {len(charts)} charts")

    return {
        "metrics": metrics,
        "charts": charts,
        "data_extracted": len(found_items) > 0 or total_found is not None
    }
```

---

## Testing Extraction

```python
# Test cases
test_cases = [
    {
        "response": 'There is a total of **5** items in your inventory. "Rice" has 50 units.',
        "expected_metrics": 2,  # Total + Rice
        "expected_charts": 0,   # Only 1 item, no chart
    },
    {
        "response": '**Apples**: 25 units\n**Oranges**: 30 units\n**Bananas**: 20 units',
        "expected_metrics": 3,
        "expected_charts": 1,  # Bar chart
    },
    {
        "response": 'Total sales: $15,000. Growth rate: 25%.',
        "expected_metrics": 2,  # Price + Percentage
        "expected_charts": 0,
    },
]

for i, test in enumerate(test_cases):
    result = extract_visualization_from_response("test", test["response"])
    assert len(result["metrics"]) == test["expected_metrics"], f"Test {i} failed: metrics"
    assert len(result["charts"]) == test["expected_charts"], f"Test {i} failed: charts"
    print(f"Test {i} passed!")
```

---

## Best Practices

1. **Always use `re.IGNORECASE`** - AI responses may have varying case
2. **Use `re.MULTILINE`** for bullet points - Matches `^` at line starts
3. **Limit results** - Use slicing `[:10]` to prevent overwhelming charts
4. **Validate ranges** - Check percentages are 0-100, prices are positive
5. **Skip generic words** - Maintain a list of non-item words
6. **Handle markdown** - Patterns should handle `**bold**` markers
7. **Deduplicate** - Use dictionary keys to avoid duplicate items
8. **Log extraction** - Log what was found for debugging
