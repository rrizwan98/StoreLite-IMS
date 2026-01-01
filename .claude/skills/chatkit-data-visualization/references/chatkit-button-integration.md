# ChatKit Button Integration Guide

> This reference explains how to add custom action buttons (like "Use Analytics") to ChatKit that trigger specific agent behaviors.

---

## Overview

There are multiple ways to add action buttons to ChatKit:
1. **Start Screen Prompts** - Built-in ChatKit feature
2. **Custom Toolbar Buttons** - Above/below ChatKit
3. **Tool Prefix Injection** - Modify message before sending
4. **Floating Action Button** - Overlay on ChatKit

---

## Method 1: Start Screen Prompts (Recommended)

The simplest way - uses ChatKit's built-in `prompts` feature.

```typescript
chatkit.setOptions({
  startScreen: {
    greeting: 'How can I help you today?',
    prompts: [
      {
        label: 'Use Analytics',  // Button text shown to user
        prompt: '[TOOL:analytics] Show me analytics overview'  // Sent to agent
      },
      {
        label: 'Generate Report',
        prompt: '[TOOL:reports] Generate a comprehensive report'
      },
      {
        label: 'Stock Check',
        prompt: 'Show me current stock levels'
      },
      {
        label: 'Sales Trend',
        prompt: '[TOOL:analytics] Show me sales trend for this month'
      },
    ],
  },
});
```

**How it works:**
- Buttons appear on the start screen
- When clicked, the `prompt` text is sent as user message
- Backend agent sees the full text including `[TOOL:xxx]` prefix

**Backend handling:**
```python
# In your agent's instructions
SYSTEM_PROMPT = """
When the user message starts with [TOOL:analytics],
you MUST use the analytics tools to answer their question.
Extract the actual query from after the prefix.

When the user message starts with [TOOL:reports],
you MUST use the report generation tools.
"""

# Or detect programmatically
async def handle_message(message: str):
    if message.startswith('[TOOL:analytics]'):
        query = message.replace('[TOOL:analytics]', '').strip()
        return await run_analytics_agent(query)
    elif message.startswith('[TOOL:reports]'):
        query = message.replace('[TOOL:reports]', '').strip()
        return await run_reports_agent(query)
    else:
        return await run_default_agent(message)
```

---

## Method 2: Custom Toolbar Buttons

Add a toolbar with buttons outside ChatKit that inject messages.

```tsx
// frontend/components/ChatWithToolbar.tsx

'use client';

import { useEffect, useRef, useState } from 'react';

interface ToolButton {
  id: string;
  label: string;
  icon: string;
  prefix: string;
  color: string;
}

const TOOL_BUTTONS: ToolButton[] = [
  {
    id: 'analytics',
    label: 'Use Analytics',
    icon: '📊',
    prefix: '[TOOL:analytics]',
    color: 'bg-blue-100 text-blue-800 hover:bg-blue-200'
  },
  {
    id: 'reports',
    label: 'Generate Report',
    icon: '📄',
    prefix: '[TOOL:reports]',
    color: 'bg-green-100 text-green-800 hover:bg-green-200'
  },
  {
    id: 'search',
    label: 'Deep Search',
    icon: '🔍',
    prefix: '[TOOL:search]',
    color: 'bg-purple-100 text-purple-800 hover:bg-purple-200'
  },
];

export default function ChatWithToolbar() {
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [isChatkitLoaded, setIsChatkitLoaded] = useState(false);
  const chatkitRef = useRef<HTMLElement | null>(null);

  // Configure ChatKit with tool prefix injection
  useEffect(() => {
    if (!isChatkitLoaded) return;

    const chatkit = chatkitRef.current as any;
    if (!chatkit?.setOptions) return;

    chatkit.setOptions({
      api: {
        url: '/api/agent/chatkit',
        fetch: async (url: string, options: RequestInit) => {
          const body = JSON.parse(options.body as string);

          // INJECT TOOL PREFIX if tool is selected
          if (selectedTool && body.params?.input?.content) {
            const inputContent = body.params.input.content;
            for (const item of inputContent) {
              if (item.type === 'input_text' && item.text) {
                // Only add prefix if not already present
                if (!item.text.startsWith('[TOOL:')) {
                  const tool = TOOL_BUTTONS.find(t => t.id === selectedTool);
                  if (tool) {
                    item.text = `${tool.prefix} ${item.text}`;
                  }
                }
              }
            }
          }

          return fetch(url, {
            ...options,
            body: JSON.stringify(body),
          });
        },
      },
      // ... other options
    });
  }, [isChatkitLoaded, selectedTool]);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex gap-2 p-3 bg-gray-100 border-b">
        <span className="text-sm text-gray-500 mr-2 self-center">Tools:</span>
        {TOOL_BUTTONS.map((tool) => (
          <button
            key={tool.id}
            onClick={() => setSelectedTool(
              selectedTool === tool.id ? null : tool.id
            )}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
              selectedTool === tool.id
                ? `${tool.color} ring-2 ring-offset-1`
                : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
            }`}
          >
            <span className="mr-1">{tool.icon}</span>
            {tool.label}
          </button>
        ))}
        {selectedTool && (
          <span className="text-xs text-gray-400 self-center ml-2">
            Tool active - messages will use {selectedTool}
          </span>
        )}
      </div>

      {/* ChatKit */}
      <div className="flex-1">
        <openai-chatkit
          ref={chatkitRef as any}
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    </div>
  );
}
```

---

## Method 3: Floating Action Button (FAB)

Add a floating button overlay on ChatKit.

```tsx
// frontend/components/ChatWithFAB.tsx

'use client';

import { useState, useRef } from 'react';

export default function ChatWithFAB() {
  const [showToolMenu, setShowToolMenu] = useState(false);
  const chatkitRef = useRef<HTMLElement | null>(null);

  // Send message programmatically
  const sendToolMessage = (toolPrefix: string, defaultQuery: string) => {
    const chatkit = chatkitRef.current as any;
    if (!chatkit) return;

    // Use ChatKit's sendMessage method if available
    // Or inject into the input field
    const message = `${toolPrefix} ${defaultQuery}`;

    // Method 1: If ChatKit exposes sendMessage
    if (chatkit.sendMessage) {
      chatkit.sendMessage(message);
    }
    // Method 2: Dispatch custom event
    else {
      const event = new CustomEvent('chatkit-send', {
        detail: { message }
      });
      window.dispatchEvent(event);
    }

    setShowToolMenu(false);
  };

  return (
    <div className="relative h-full">
      {/* ChatKit */}
      <openai-chatkit
        ref={chatkitRef as any}
        style={{ width: '100%', height: '100%' }}
      />

      {/* FAB */}
      <div className="absolute bottom-20 right-4">
        {/* Tool Menu */}
        {showToolMenu && (
          <div className="absolute bottom-full right-0 mb-2 bg-white rounded-lg shadow-xl border p-2 min-w-[180px]">
            <button
              onClick={() => sendToolMessage('[TOOL:analytics]', 'Show analytics')}
              className="w-full text-left px-3 py-2 rounded hover:bg-blue-50 flex items-center"
            >
              <span className="mr-2">📊</span>
              Use Analytics
            </button>
            <button
              onClick={() => sendToolMessage('[TOOL:reports]', 'Generate report')}
              className="w-full text-left px-3 py-2 rounded hover:bg-green-50 flex items-center"
            >
              <span className="mr-2">📄</span>
              Generate Report
            </button>
            <button
              onClick={() => sendToolMessage('[TOOL:search]', 'Deep search')}
              className="w-full text-left px-3 py-2 rounded hover:bg-purple-50 flex items-center"
            >
              <span className="mr-2">🔍</span>
              Deep Search
            </button>
          </div>
        )}

        {/* FAB Button */}
        <button
          onClick={() => setShowToolMenu(!showToolMenu)}
          className={`w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all ${
            showToolMenu
              ? 'bg-gray-600 text-white rotate-45'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>
    </div>
  );
}
```

---

## Method 4: Backend Tool Routing

Configure your agent to automatically use specific tools based on query patterns.

```python
# backend/app/agents/tool_router.py

from typing import Optional, Callable
import re

class ToolRouter:
    """Route messages to appropriate tools based on patterns."""

    def __init__(self):
        self.routes: list[tuple[str, str, Callable]] = []

    def register(self, prefix: str, tool_name: str, handler: Callable):
        """Register a tool route."""
        self.routes.append((prefix, tool_name, handler))

    def route(self, message: str) -> tuple[str, Optional[str], Callable]:
        """
        Route message to appropriate handler.

        Returns:
            Tuple of (cleaned_message, tool_name, handler)
        """
        for prefix, tool_name, handler in self.routes:
            if message.startswith(prefix):
                cleaned = message.replace(prefix, '').strip()
                return cleaned, tool_name, handler

        # Default route
        return message, None, self.default_handler

    def default_handler(self, message: str):
        """Default message handler."""
        pass


# Usage in ChatKit server
router = ToolRouter()
router.register('[TOOL:analytics]', 'analytics', analytics_agent.run)
router.register('[TOOL:reports]', 'reports', reports_agent.run)
router.register('[TOOL:search]', 'search', search_agent.run)


async def handle_user_message(message: str, context: dict):
    cleaned_msg, tool_name, handler = router.route(message)

    if tool_name:
        logger.info(f"Routing to {tool_name} tool: {cleaned_msg}")
        return await handler(cleaned_msg, context)
    else:
        return await default_agent.run(message, context)
```

---

## Agent Instructions for Tool Prefixes

Add these instructions to your agent's system prompt:

```python
SYSTEM_PROMPT = """
You are an AI assistant with access to specialized tools.

## Tool Activation Prefixes

When the user's message starts with a tool prefix, you MUST use that specific tool:

1. `[TOOL:analytics]` - Use analytics/visualization tools
   - Call: sales_by_month, compare_periods, sales_trends, inventory_analytics
   - Always include numerical data in your response for visualization

2. `[TOOL:reports]` - Use report generation tools
   - Call: generate_report, export_data, create_summary
   - Provide structured output suitable for PDF/Excel

3. `[TOOL:search]` - Use deep search tools
   - Call: semantic_search, full_text_search, filter_search
   - Search across all available data sources

## Response Format for Visualization

When using analytics tools, format your response to enable visualization:

- Use **bold** for item names: **Product Name**: 50 units
- Include totals: "There is a total of **X** items"
- Include prices with $: Total value: $1,500.00
- Include percentages: Growth rate: 25%

This formatting allows the visualization system to extract data for charts.

## Example Interactions

User: [TOOL:analytics] Show me sales trend
You: *Call sales_trends tool* Here are the sales trends...
     **Rice**: 500 units sold
     **Flour**: 350 units sold
     Total sales: $15,000

User: [TOOL:reports] Generate inventory report
You: *Call generate_report tool* I've generated the inventory report...
"""
```

---

## Complete Integration Example

```tsx
// frontend/app/dashboard/page.tsx - Complete example with all methods

'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import Script from 'next/script';
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';

// Tool definitions
const TOOLS = [
  { id: 'analytics', label: 'Analytics', icon: '📊', prefix: '[TOOL:analytics]' },
  { id: 'reports', label: 'Reports', icon: '📄', prefix: '[TOOL:reports]' },
  { id: 'search', label: 'Search', icon: '🔍', prefix: '[TOOL:search]' },
];

export default function DashboardPage() {
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [charts, setCharts] = useState([]);
  const [isLoaded, setIsLoaded] = useState(false);
  const chatkitRef = useRef<HTMLElement | null>(null);

  // Fetch visualization after response
  const fetchVisualization = useCallback(async (query: string, responseText: string) => {
    const res = await fetch('/api/visualize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, response_text: responseText }),
    });
    const data = await res.json();
    if (data.success) setCharts(data.charts || []);
  }, []);

  // Configure ChatKit
  useEffect(() => {
    if (!isLoaded) return;

    const chatkit = chatkitRef.current as any;
    if (!chatkit?.setOptions) return;

    let currentQuery = '';

    chatkit.setOptions({
      api: {
        url: '/api/agent/chatkit',
        fetch: async (url, options) => {
          const body = JSON.parse(options.body as string);

          // Capture query
          if (body.params?.input?.content) {
            const inputText = body.params.input.content.find(
              (c: any) => c.type === 'input_text'
            )?.text;
            if (inputText) currentQuery = inputText;
          }

          // INJECT TOOL PREFIX
          if (selectedTool && body.params?.input?.content) {
            const tool = TOOLS.find(t => t.id === selectedTool);
            if (tool) {
              for (const item of body.params.input.content) {
                if (item.type === 'input_text' && !item.text.startsWith('[TOOL:')) {
                  item.text = `${tool.prefix} ${item.text}`;
                }
              }
            }
          }

          const response = await fetch(url, {
            ...options,
            body: JSON.stringify(body),
          });

          // Read stream for visualization
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
                for (const line of chunk.split('\n')) {
                  if (line.startsWith('data: ')) {
                    try {
                      const data = JSON.parse(line.slice(6));
                      if (data.type === 'assistant_message.content_part.text_delta') {
                        responseText += data.delta;
                      }
                      if (data.type === 'thread.item.done' && data.item?.type === 'assistant_message') {
                        fetchVisualization(currentQuery, responseText);
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
      startScreen: {
        greeting: 'Select a tool or ask anything!',
        prompts: TOOLS.map(t => ({
          label: `${t.icon} ${t.label}`,
          prompt: `${t.prefix} Show me ${t.id} overview`,
        })),
      },
    });
  }, [isLoaded, selectedTool, fetchVisualization]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        onLoad={() => setIsLoaded(true)}
      />

      <div className="max-w-7xl mx-auto p-4">
        <div className="flex gap-4 h-[calc(100vh-2rem)]">
          {/* Left: ChatKit with Toolbar */}
          <div className="w-1/2 flex flex-col bg-white rounded-lg shadow">
            {/* Tool Toolbar */}
            <div className="flex gap-2 p-3 border-b bg-gray-50">
              {TOOLS.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => setSelectedTool(
                    selectedTool === tool.id ? null : tool.id
                  )}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium ${
                    selectedTool === tool.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {tool.icon} {tool.label}
                </button>
              ))}
            </div>

            {/* ChatKit */}
            <div className="flex-1">
              {isLoaded ? (
                <openai-chatkit
                  ref={chatkitRef as any}
                  style={{ width: '100%', height: '100%' }}
                />
              ) : (
                <div className="flex items-center justify-center h-full">
                  Loading...
                </div>
              )}
            </div>
          </div>

          {/* Right: Visualizations */}
          <div className="w-1/2 bg-white rounded-lg shadow p-4 overflow-auto">
            <h2 className="text-lg font-semibold mb-4">Visualizations</h2>
            {charts.map((chart, i) => (
              <div key={i} className="mb-4 p-4 border rounded">
                <h3 className="font-medium mb-2">{chart.title}</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={chart.data}>
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Best Practices

1. **Clear visual feedback** - Highlight active tool button
2. **Consistent prefixes** - Use `[TOOL:name]` format for easy parsing
3. **Clean messages** - Remove prefix before displaying to user
4. **Graceful fallback** - If tool fails, fall back to general agent
5. **Loading states** - Show progress when tool is processing
6. **Descriptive prompts** - Start screen prompts should be actionable
