# ChatKit Events and API

Official events and methods for the ChatKit web component.

## Event Listeners

### Available Events

```javascript
const chatkit = document.getElementById('chat');

// Message events
chatkit.addEventListener('message', (e) => {
  console.log('New message:', e.detail);
  // { role: 'user' | 'assistant', content: string, id: string }
});

chatkit.addEventListener('message-start', (e) => {
  console.log('Message started:', e.detail);
});

chatkit.addEventListener('message-end', (e) => {
  console.log('Message completed:', e.detail);
});

// Response events
chatkit.addEventListener('response-start', (e) => {
  console.log('Agent started responding');
});

chatkit.addEventListener('response-end', (e) => {
  console.log('Agent finished responding');
});

// Error events
chatkit.addEventListener('error', (e) => {
  console.error('ChatKit error:', e.detail);
  // { code: string, message: string }
});

// Thread events
chatkit.addEventListener('thread-change', (e) => {
  console.log('Thread changed:', e.detail);
  // { threadId: string }
});

// Tool events
chatkit.addEventListener('tool-call', (e) => {
  console.log('Tool called:', e.detail);
  // { name: string, arguments: object }
});

chatkit.addEventListener('tool-result', (e) => {
  console.log('Tool result:', e.detail);
  // { name: string, result: any }
});

// Widget events
chatkit.addEventListener('widget-action', (e) => {
  console.log('Widget action:', e.detail);
  // { action: string, data: any }
});

// Attachment events
chatkit.addEventListener('attachment-upload', (e) => {
  console.log('File uploaded:', e.detail);
  // { file: File, id: string }
});
```

## Methods

### setOptions()

Configure ChatKit:

```javascript
chatkit.setOptions({
  // API configuration
  api: {
    url: '/api/chat',
    domainKey: 'your-domain',
    
    // Custom fetch for auth
    fetch: async (url, options) => {
      return fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${token}`,
        },
      });
    },
    
    // Session refresh
    getClientSecret: async (existing) => {
      if (existing && !isExpired(existing)) {
        return existing;
      }
      const res = await fetch('/api/session');
      const { client_secret } = await res.json();
      return client_secret;
    },
  },
  
  // Theme
  theme: {
    colorScheme: 'light',
    accentColor: '#2563EB',
    density: 'normal',
  },
  
  // Header
  header: {
    title: 'Assistant',
    showTitle: true,
    icons: [
      { type: 'theme-toggle' },
      { type: 'new-thread' },
    ],
  },
  
  // Start screen
  startScreen: {
    greeting: 'Hello! How can I help?',
    prompts: [
      { text: 'Get started', prompt: 'Help me get started' },
    ],
  },
  
  // Composer
  composer: {
    placeholder: 'Type a message...',
    allowAttachments: true,
    allowedFileTypes: ['image/*', '.pdf', '.txt'],
    maxFileSize: 10 * 1024 * 1024, // 10MB
  },
  
  // Disclaimer
  disclaimer: {
    text: 'AI may make mistakes. Verify important information.',
    position: 'bottom',
  },
  
  // History
  history: {
    enabled: true,
    maxThreads: 50,
  },
  
  // Locale
  locale: 'en-US',
});
```

### sendMessage()

Send a message programmatically:

```javascript
// Simple text
chatkit.sendMessage('Hello, how are you?');

// With attachments
chatkit.sendMessage('Check this file', {
  attachments: [file],
});

// With context
chatkit.sendMessage('Analyze this', {
  context: {
    pageUrl: window.location.href,
    selectedText: getSelection().toString(),
  },
});
```

### sendAction()

Trigger widget actions:

```javascript
chatkit.sendAction({
  type: 'select_option',
  value: 'option_1',
});
```

### clearThread()

Start a new conversation:

```javascript
chatkit.clearThread();
```

### setThread()

Switch to a specific thread:

```javascript
chatkit.setThread('thread_abc123');
```

### focus()

Focus the input:

```javascript
chatkit.focus();
```

### blur()

Remove focus:

```javascript
chatkit.blur();
```

## Client Tools

Register client-side tools that ChatKit can invoke:

```javascript
chatkit.setOptions({
  tools: {
    // Tool that returns data to the model
    get_current_page: async () => {
      return {
        url: window.location.href,
        title: document.title,
        content: document.body.innerText.slice(0, 5000),
      };
    },
    
    // Tool that performs a UI action
    scroll_to_section: async ({ sectionId }) => {
      document.getElementById(sectionId)?.scrollIntoView();
      return { success: true };
    },
    
    // Tool that gets user selection
    get_selected_text: async () => {
      return { text: window.getSelection()?.toString() || '' };
    },
  },
});
```

## Client Effects

Handle effects streamed from server:

```javascript
chatkit.setOptions({
  onEffect: (effect) => {
    switch (effect.type) {
      case 'highlight_element':
        document.getElementById(effect.elementId)?.classList.add('highlight');
        break;
        
      case 'navigate':
        window.location.href = effect.url;
        break;
        
      case 'show_notification':
        showNotification(effect.message);
        break;
    }
  },
});
```

## Widget Action Handling

Handle actions from widgets:

```javascript
chatkit.setOptions({
  widgets: {
    handleAction: async (action) => {
      switch (action.type) {
        case 'open_link':
          window.open(action.url, '_blank');
          return { handled: true };
          
        case 'copy_text':
          navigator.clipboard.writeText(action.text);
          return { handled: true };
          
        case 'server_action':
          // Let server handle it
          return { handled: false };
          
        default:
          return { handled: false };
      }
    },
  },
});
```

## Complete Setup Example

```html
<!DOCTYPE html>
<html>
<head>
  <script type="module">
    import '@openai/chatkit';
  </script>
</head>
<body>
  <openai-chatkit id="chat"></openai-chatkit>
  
  <script type="module">
    const chatkit = document.getElementById('chat');
    
    // Full configuration
    chatkit.setOptions({
      api: {
        url: '/api/chat',
        fetch: async (url, opts) => {
          const token = await getToken();
          return fetch(url, {
            ...opts,
            headers: { ...opts.headers, Authorization: `Bearer ${token}` },
          });
        },
      },
      
      theme: {
        colorScheme: 'auto',
        accentColor: '#2563EB',
      },
      
      header: {
        title: 'Support Assistant',
      },
      
      startScreen: {
        greeting: 'Hi! How can I help you today?',
        prompts: [
          { text: '📦 Track order', prompt: 'Track my order' },
          { text: '🔄 Return item', prompt: 'I want to return an item' },
        ],
      },
      
      composer: {
        placeholder: 'Ask me anything...',
        allowAttachments: true,
      },
      
      tools: {
        get_current_page: async () => ({
          url: window.location.href,
        }),
      },
      
      onEffect: (effect) => {
        console.log('Effect:', effect);
      },
    });
    
    // Event listeners
    chatkit.addEventListener('message', (e) => {
      analytics.track('chat_message', e.detail);
    });
    
    chatkit.addEventListener('error', (e) => {
      console.error('Chat error:', e.detail);
    });
  </script>
</body>
</html>
```