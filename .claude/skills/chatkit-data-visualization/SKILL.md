# ChatKit Data Visualization Skill

> **Purpose**: Add interactive data visualizations (charts, graphs, metrics) to any ChatKit-based agent system. This skill enables AI responses to automatically generate visual representations of data for any domain/problem.

---

## Overview

This skill provides a **reusable pattern** for implementing data visualizations in ChatKit-based systems. It works for **ANY problem domain** - not just inventory/analytics. Whether you're building a finance dashboard, healthcare analytics, or any data-driven application, this pattern applies.

**What This Skill Enables:**
1. AI agent responds with text containing data
2. System automatically extracts numerical data from response
3. Charts/graphs are rendered alongside the text response
4. User sees both conversational answer AND visual representation

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────┐    ┌─────────────────────────────────┐  │
│  │      ChatKit Widget     │    │     Visualization Panel         │  │
│  │                         │    │                                 │  │
│  │  User: "Show me sales"  │    │  ┌─────────────────────────┐    │  │
│  │                         │    │  │   Metrics Cards          │    │  │
│  │  AI: "Here are your     │    │  │   $15K  |  150  |  25%   │    │  │
│  │  sales for December..." │    │  └─────────────────────────┘    │  │
│  │                         │    │                                 │  │
│  │                         │    │  ┌─────────────────────────┐    │  │
│  │                         │    │  │   Bar/Line/Pie Chart    │    │  │
│  │                         │    │  │   ████████ Product A     │    │  │
│  │                         │    │  │   ██████   Product B     │    │  │
│  │                         │    │  └─────────────────────────┘    │  │
│  └─────────────────────────┘    └─────────────────────────────────┘  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND FLOW                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. User sends query via ChatKit                                     │
│                    │                                                  │
│                    ▼                                                  │
│  2. ChatKit Server routes to AI Agent                                │
│                    │                                                  │
│                    ▼                                                  │
│  3. Agent calls tools (MCP/function_tool)                            │
│                    │                                                  │
│                    ▼                                                  │
│  4. Agent generates text response with data                          │
│                    │                                                  │
│                    ▼                                                  │
│  5. Response streams back to frontend                                │
│                    │                                                  │
│                    ▼                                                  │
│  6. Frontend captures response text                                  │
│                    │                                                  │
│                    ▼                                                  │
│  7. POST /visualize with {query, response_text}                      │
│                    │                                                  │
│                    ▼                                                  │
│  8. Extract real data from response text                             │
│                    │                                                  │
│                    ▼                                                  │
│  9. Return chart-ready JSON                                          │
│                    │                                                  │
│                    ▼                                                  │
│  10. Frontend renders charts with Recharts                           │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Critical Rules

### Data Extraction Rules (MUST FOLLOW)

| Rule | Description |
|------|-------------|
| NEVER fake data | Only extract data that exists in AI response |
| Parse response text | Use regex to find numbers, items, prices, percentages |
| Return empty if no data | If no visualizable data found, return empty arrays |
| Match agent's answer | Charts must reflect exactly what the AI said |
| Handle edge cases | Empty datasets, single items, malformed numbers |

### Chart Type Selection

| Data Shape | Best Chart | Example |
|------------|------------|---------|
| 1 item | Metrics card only | "Total: 50 units" |
| 2-5 items | Bar chart | Top 5 products |
| 6+ items | Horizontal bar | Category breakdown |
| Time series | Line chart | Daily/weekly trends |
| Distribution | Pie chart | Percentage breakdown |
| Comparison | Grouped bar | Period vs period |

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend Charts | Recharts | React charting library |
| Frontend Container | Next.js page | Split-panel layout |
| Backend Endpoint | FastAPI | POST /visualize |
| Data Extraction | Python regex | Parse AI response |
| Chat Widget | OpenAI ChatKit | Pure vanilla JS |

---

## Reference Files

When implementing visualization, read the relevant reference files:

| If the task involves... | Read this file |
|------------------------|----------------|
| Backend tools, data fetching, MCP tools | `references/backend-tools-pattern.md` |
| Frontend dashboard, React components | `references/frontend-dashboard-pattern.md` |
| Data extraction from AI responses | `references/visualization-extraction.md` |
| Adding visualization button to ChatKit | `references/chatkit-button-integration.md` |

---

## Quick Implementation Guide

### Step 1: Create Visualization Endpoint

```python
# backend/app/routers/your_domain.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import re

router = APIRouter(prefix="/your-domain", tags=["your-domain"])

class VisualizeRequest(BaseModel):
    query: str
    response_text: Optional[str] = None
    user_id: Optional[int] = None

@router.post("/visualize")
async def visualize_data(request: VisualizeRequest) -> Dict[str, Any]:
    """
    Extract visualization data from AI response.

    CRITICAL: Only return data that exists in response_text.
    NEVER generate fake/placeholder data.
    """
    query = request.query
    response_text = request.response_text or ""

    # Extract data using regex patterns
    viz_data = extract_visualization_data(query, response_text)

    if not viz_data.get("metrics") and not viz_data.get("charts"):
        return {
            "success": True,
            "metrics": [],
            "charts": [],
            "message": "No numerical data to visualize"
        }

    return {
        "success": True,
        "query": query,
        **viz_data
    }


def extract_visualization_data(query: str, response_text: str) -> Dict[str, Any]:
    """
    Parse AI response to extract real data for visualization.
    """
    metrics = []
    chart_data = []

    if not response_text or len(response_text) < 10:
        return {"metrics": [], "charts": []}

    # Pattern 1: Total/Count numbers
    total_patterns = [
        r'total\s+of\s+\*?\*?(\d+)\s*\*?\*?\s*(item|record|entr)',
        r'(?:there\s+(?:is|are)|have)\s+\*?\*?(\d+)\s*\*?\*?',
        r'(?:count|total)[:\s]+\*?\*?(\d+)\*?\*?',
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

    # Pattern 2: Named items with values
    item_patterns = [
        r'["\']([^"\']+)["\']\s+has\s+(?:quantity\s+of\s+)?\*?\*?(\d+)',
        r'\*\*([^*]+)\*\*[:\s]+\*?\*?(\d+)\s*\*?\*?',
        r'^[•\-\*]?\s*([A-Za-z][A-Za-z\s]{2,30})[:\s]+(\d+)',
    ]

    found_items = {}
    for pattern in item_patterns:
        for match in re.finditer(pattern, response_text, re.IGNORECASE | re.MULTILINE):
            name = match.group(1).strip('*').strip()
            value = int(match.group(2))

            skip_words = {'the', 'item', 'total', 'count', 'database', 'table'}
            if len(name) < 2 or len(name) > 50 or name.lower() in skip_words:
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

    # Pattern 3: Currency values
    price_pattern = r'\$(\d+(?:\.\d{2})?)'
    for match in re.finditer(price_pattern, response_text):
        try:
            price = float(match.group(1))
            if price > 0:
                metrics.append({
                    "title": "Price",
                    "value": f"${price:,.2f}"
                })
                break
        except:
            continue

    # Build charts
    charts = []
    if len(chart_data) >= 2:
        charts.append({
            "type": "bar",
            "title": "Data Overview",
            "data": chart_data,
            "dataKey": "value",
            "xAxisKey": "name"
        })

    return {
        "metrics": metrics,
        "charts": charts
    }
```

### Step 2: Create Frontend Dashboard

```tsx
// frontend/app/your-domain/page.tsx

'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import Script from 'next/script';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

interface MetricData {
  title: string;
  value: string;
  status?: 'success' | 'warning' | 'danger';
}

interface ChartConfig {
  type: 'bar' | 'line' | 'pie';
  title: string;
  data: Array<{ name: string; value: number }>;
  dataKey: string;
  xAxisKey: string;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

export default function YourDomainPage() {
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [charts, setCharts] = useState<ChartConfig[]>([]);
  const [isChatkitLoaded, setIsChatkitLoaded] = useState(false);
  const [lastQuery, setLastQuery] = useState<string>('');
  const [isLoadingViz, setIsLoadingViz] = useState(false);
  const chatkitRef = useRef<HTMLElement | null>(null);

  // Fetch visualization data
  const fetchVisualization = useCallback(async (query: string, responseText?: string) => {
    if (!query) return;

    setIsLoadingViz(true);

    try {
      const response = await fetch('/api/your-domain/visualize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          response_text: responseText || '',
        })
      });

      const data = await response.json();

      if (data.success) {
        setMetrics(data.metrics || []);
        setCharts(data.charts || []);
        setLastQuery(query);
      }
    } catch (error) {
      console.error('Failed to fetch visualization:', error);
    } finally {
      setIsLoadingViz(false);
    }
  }, []);

  // Configure ChatKit
  useEffect(() => {
    if (!isChatkitLoaded) return;

    const chatkit = chatkitRef.current as any;
    if (!chatkit?.setOptions) return;

    let currentQuery = '';

    chatkit.setOptions({
      api: {
        url: '/api/agent/chatkit',
        fetch: async (url: string, options: RequestInit) => {
          const body = JSON.parse(options.body as string);

          // Capture user query
          if (body.params?.input?.content) {
            const inputText = body.params.input.content.find(
              (c: any) => c.type === 'input_text'
            )?.text;
            if (inputText) currentQuery = inputText;
          }

          const response = await fetch(url, options);

          // Clone to read for visualization
          const cloned = response.clone();
          const reader = cloned.body?.getReader();

          if (reader && currentQuery) {
            const decoder = new TextDecoder();
            let responseText = '';

            (async () => {
              while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                  if (line.startsWith('data: ')) {
                    try {
                      const data = JSON.parse(line.slice(6));
                      // Capture text deltas
                      if (data.type === 'assistant_message.content_part.text_delta') {
                        responseText += data.delta;
                      }
                      // When response complete, fetch visualization
                      if (data.type === 'thread.item.done' &&
                          data.item?.type === 'assistant_message') {
                        setTimeout(() => {
                          fetchVisualization(currentQuery, responseText);
                        }, 200);
                      }
                    } catch {}
                  }
                }
              }
            })();
          }

          return response;
        },
      },
      theme: 'light',
      header: { enabled: true, title: { text: 'AI Assistant' } },
      startScreen: {
        greeting: 'Ask me anything! Charts will appear automatically.',
        prompts: [
          { label: 'Overview', prompt: 'Show me an overview' },
          { label: 'Trends', prompt: 'Show me trends' },
        ],
      },
    });
  }, [isChatkitLoaded, fetchVisualization]);

  // Render chart based on type
  const renderChart = (chart: ChartConfig, index: number) => {
    switch (chart.type) {
      case 'bar':
        return (
          <div key={index} className="bg-white rounded-lg p-4 border">
            <h4 className="font-semibold mb-3">{chart.title}</h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chart.data} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey={chart.xAxisKey} width={80} />
                <Tooltip />
                <Bar dataKey={chart.dataKey}>
                  {chart.data.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      // Add line, pie cases similarly...
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        onLoad={() => setIsChatkitLoaded(true)}
      />

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="h-[calc(100vh-180px)] flex gap-4">
          {/* Left: ChatKit */}
          <div className="w-1/2 bg-white rounded-lg border overflow-hidden">
            <div className="bg-blue-600 text-white px-4 py-3">
              <h2 className="font-semibold">AI Assistant</h2>
            </div>
            <div className="flex-1">
              <openai-chatkit
                ref={chatkitRef as any}
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          </div>

          {/* Right: Visualizations */}
          <div className="w-1/2 bg-white rounded-lg border overflow-hidden">
            <div className="bg-purple-600 text-white px-4 py-3">
              <h2 className="font-semibold">Visualizations</h2>
              <p className="text-xs text-purple-100">
                {lastQuery ? `Query: "${lastQuery}"` : 'Charts from your data'}
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {isLoadingViz ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin h-8 w-8 border-b-2 border-purple-600" />
                </div>
              ) : charts.length === 0 && metrics.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500">Charts appear here automatically</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Metrics Cards */}
                  {metrics.length > 0 && (
                    <div className="grid grid-cols-2 gap-3">
                      {metrics.map((m, i) => (
                        <div key={i} className="p-4 rounded-lg border bg-white">
                          <div className="text-xs text-gray-500">{m.title}</div>
                          <div className="text-xl font-bold">{m.value}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Charts */}
                  {charts.map((chart, i) => renderChart(chart, i))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
```

---

## Adding "Use [Feature]" Button to ChatKit

To add a button like "Use Analytics" that triggers specific tool behavior:

### Option 1: Start Screen Prompts

```typescript
chatkit.setOptions({
  startScreen: {
    greeting: 'How can I help you today?',
    prompts: [
      {
        label: 'Use Analytics',  // Button text
        prompt: '[TOOL:analytics] Show me analytics overview'  // Prefix for agent
      },
      {
        label: 'Use Reports',
        prompt: '[TOOL:reports] Generate a report'
      },
    ],
  },
});
```

### Option 2: Tool Prefix Injection

Frontend injects tool prefix before sending to backend:

```typescript
// In ChatKit fetch interceptor
if (selectedTool === 'analytics') {
  body.messages[body.messages.length - 1].content =
    `[TOOL:analytics] ${body.messages[body.messages.length - 1].content}`;
}
```

Backend agent detects prefix:

```python
@function_tool
def analytics_tool(query: str) -> str:
    """Use this tool when user asks about analytics."""
    # Tool implementation
    pass

# In agent instructions
SYSTEM_PROMPT = """
When user message starts with [TOOL:analytics],
always use the analytics_tool first.
"""
```

### Option 3: Custom Button Outside ChatKit

Add buttons above/below ChatKit that trigger specific queries:

```tsx
<div className="flex gap-2 mb-2">
  <button
    onClick={() => sendQuery('[TOOL:analytics] Show analytics')}
    className="px-3 py-1 bg-blue-100 text-blue-800 rounded"
  >
    Use Analytics
  </button>
  <button
    onClick={() => sendQuery('[TOOL:reports] Generate report')}
    className="px-3 py-1 bg-green-100 text-green-800 rounded"
  >
    Use Reports
  </button>
</div>
```

---

## Checklist for Adding Visualization to Any Problem

- [ ] **Backend**: Create `/your-domain/visualize` POST endpoint
- [ ] **Backend**: Implement `extract_visualization_data()` with domain-specific patterns
- [ ] **Backend**: Ensure data extraction ONLY uses response text (no fake data)
- [ ] **Frontend**: Create split-panel page with ChatKit + visualization panel
- [ ] **Frontend**: Implement `fetchVisualization()` callback
- [ ] **Frontend**: Add stream reader to capture response text
- [ ] **Frontend**: Render metrics cards and charts with Recharts
- [ ] **Frontend**: Add loading states and empty state messaging
- [ ] **Agent**: Ensure agent returns data in parseable format (markdown with numbers)
- [ ] **Testing**: Verify charts match exactly what AI says in response

---

## Common Mistakes to Avoid

1. **Generating fake data** - NEVER create placeholder data for visualization
2. **Not capturing response text** - Must clone response stream to read
3. **Wrong chart type** - Match chart type to data structure
4. **Missing loading states** - Show spinners during data fetch
5. **Not handling empty data** - Return empty arrays, not null
6. **Hardcoded domains** - Make patterns configurable for any domain
7. **Blocking main response** - Visualization fetch should be async/non-blocking

---

## Integration with Existing ChatKit Skill

This skill extends the `openai-chatkit-ui` skill. Read that skill first for:
- ChatKit web component setup
- Backend ChatKitServer implementation
- PostgreSQL persistence
- Streaming workflow events

Then add visualization layer on top using this skill.

---

## Domain Customization

To adapt for your specific domain:

1. **Modify regex patterns** in `extract_visualization_data()` to match your data format
2. **Update chart titles** to reflect your domain terminology
3. **Add domain-specific metrics** (e.g., healthcare: "Patients", finance: "Revenue")
4. **Configure start screen prompts** for common domain queries
5. **Adjust color schemes** to match your brand/domain

---

## Dependencies

### Python (Backend)
```
fastapi
pydantic
# Plus your existing agent dependencies
```

### JavaScript (Frontend)
```json
{
  "recharts": "^2.x",
  "next": "^14.x"
}
```

### ChatKit CDN
```
https://cdn.platform.openai.com/deployments/chatkit/chatkit.js
```
