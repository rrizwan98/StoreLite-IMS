---
name: openai-chatkit-ui
description: >
  Connect AI agents to frontend UI using OpenAI ChatKit SDK. Use this skill when
  integrating agents with web interfaces, embedding chat UI, connecting ChatKit
  to OpenAI Agents SDK backend, or adding chat functionality to existing apps.
  IMPORTANT: Uses ONLY pure official ChatKit components (web component or vanilla JS).
  NO custom UI code, NO React-specific code. Triggers include: ChatKit, chat UI,
  agent UI, embed chat, connect agent to frontend, agent interface, chat widget.
---

# OpenAI ChatKit UI Integration

Connect your OpenAI Agents SDK backend to a frontend using **pure official ChatKit components only**.

## Critical Rules (MUST FOLLOW)

1. **PURE CHATKIT ONLY** - Use only official `<openai-chatkit>` web component
2. **NO CUSTOM UI** - Never write custom chat UI code
3. **NO REACT CODE** - Avoid React-specific implementations (use vanilla JS)
4. **LATEST DOCS FIRST** - Always fetch latest documentation before implementing
5. **OFFICIAL COMPONENTS** - Only use components from `@openai/chatkit`

## Why Pure ChatKit?

| Benefit | Explanation |
|---------|-------------|
| Easy Upgrades | Just update npm package, no custom code to maintain |
| Official Support | Bug fixes and features from OpenAI |
| Consistency | Same behavior across all projects |
| Less Code | Drop-in component, minimal integration |

## Fetch Latest Documentation (REQUIRED)

Before ANY ChatKit implementation, fetch current docs:

**Context7 MCP (Preferred):**
```
context7: resolve chatkit-js
context7: resolve chatkit-python
```

**Web Search (Fallback):**
```
OpenAI ChatKit JS documentation latest 2025
OpenAI ChatKit web component vanilla JS
ChatKit Python SDK latest
```

**Official Documentation URLs:**
- ChatKit JS: `https://openai.github.io/chatkit-js/`
- ChatKit Python: `https://openai.github.io/chatkit-python/`
- API Reference: `https://platform.openai.com/docs/api-reference/chatkit`
- Guide: `https://platform.openai.com/docs/guides/chatkit`

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR FRONTEND                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           <openai-chatkit> Web Component              │  │
│  │         (Pure Official ChatKit - NO CUSTOM UI)        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP (Client Token)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  YOUR BACKEND (Python)                      │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  Session API    │    │  OpenAI Agents SDK              │ │
│  │  /api/session   │───▶│  (Your Agent Logic)             │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│                              │                               │
│                              ▼                               │
│                    ┌─────────────────┐                       │
│                    │  MCP Servers    │                       │
│                    │  (FastMCP)      │                       │
│                    └─────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Frontend (Vanilla JS Only)

```bash
npm install @openai/chatkit
```

### Backend (Python)

```bash
pip install chatkit openai openai-agents fastapi
```

## Pure Vanilla JS Implementation (REQUIRED PATTERN)

### HTML Setup

```html
<!DOCTYPE html>
<html>
<head>
  <title>Agent Chat</title>
  <script type="module">
    import '@openai/chatkit';
  </script>
  <style>
    openai-chatkit {
      /* Use CSS variables for theming - NO custom CSS */
      --ck-accent-color: #2563EB;
      --ck-radius: 8px;
      height: 600px;
      width: 400px;
    }
  </style>
</head>
<body>
  <openai-chatkit id="chat"></openai-chatkit>
  
  <script type="module">
    const chatkit = document.getElementById('chat');
    
    // Configure with self-hosted backend
    chatkit.setOptions({
      api: {
        url: '/api/chat',           // Your backend endpoint
        domainKey: 'your-domain',   // Optional: for hosted backend
        
        // For self-hosted: custom fetch for auth
        fetch: async (url, options) => {
          const token = await getAuthToken(); // Your auth logic
          return fetch(url, {
            ...options,
            headers: {
              ...options.headers,
              'Authorization': `Bearer ${token}`,
            },
          });
        },
      },
      
      // Theme (use only official options)
      theme: {
        colorScheme: 'light',  // 'light', 'dark', 'auto'
        accentColor: '#2563EB',
      },
      
      // Start screen
      startScreen: {
        greeting: 'Hello! How can I help you?',
        prompts: [
          { text: 'What can you do?', prompt: 'What are your capabilities?' },
          { text: 'Help me get started', prompt: 'Help me get started' },
        ],
      },
    });
    
    // Event handlers (official events only)
    chatkit.addEventListener('message', (e) => {
      console.log('Message:', e.detail);
    });
    
    chatkit.addEventListener('error', (e) => {
      console.error('ChatKit error:', e.detail);
    });
  </script>
</body>
</html>
```

## Backend Integration with OpenAI Agents SDK

See `references/backend-integration.md` for:
- FastAPI session endpoint
- ChatKit Python SDK setup
- Connecting to OpenAI Agents SDK
- MCP server integration

## Theming (Official CSS Variables Only)

```css
openai-chatkit {
  /* Colors */
  --ck-accent-color: #2563EB;
  --ck-background-color: #ffffff;
  --ck-text-color: #1a1a1a;
  
  /* Spacing */
  --ck-radius: 8px;
  --ck-density: normal;  /* 'compact', 'normal', 'spacious' */
  
  /* Dimensions */
  height: 100%;
  width: 100%;
  max-width: 800px;
}
```

## Domain Allowlist (CRITICAL)

Before deployment, add your domain to OpenAI's allowlist:

1. Go to OpenAI Dashboard → Settings → ChatKit
2. Add your domain (e.g., `chat.example.com`)
3. Include `localhost` for development

**Without this step, ChatKit will show a blank screen!**

## File Structure

```
your-project/
├── frontend/
│   ├── index.html           # ChatKit web component
│   └── chatkit.js           # Minimal config only
├── backend/
│   ├── main.py              # FastAPI app
│   ├── session.py           # ChatKit session handling
│   └── agent.py             # OpenAI Agents SDK
└── .env
```

## Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# ChatKit (for hosted backend)
CHATKIT_WORKFLOW_ID=wf_...

# Your Backend
BACKEND_URL=http://localhost:8000
```

## What NOT To Do

❌ **Never write custom chat UI components**
❌ **Never use React-specific ChatKit bindings** (`@openai/chatkit-react`)
❌ **Never override ChatKit's internal styles**
❌ **Never implement custom message rendering**
❌ **Never build custom input/composer components**

## What TO Do

✅ **Use `<openai-chatkit>` web component directly**
✅ **Configure via `setOptions()` only**
✅ **Theme via official CSS variables only**
✅ **Handle events via official event listeners**
✅ **Integrate backend via official API patterns**

## Upgrade Process

When ChatKit updates:

```bash
# 1. Update package
npm update @openai/chatkit

# 2. Check changelog for breaking changes
# https://github.com/openai/chatkit-js/releases

# 3. Test - should work without code changes
npm run dev
```

This is why we use pure ChatKit - upgrades are seamless!