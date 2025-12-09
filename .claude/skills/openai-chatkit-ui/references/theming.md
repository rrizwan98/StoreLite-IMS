# ChatKit Theming (Official Options Only)

Style ChatKit using ONLY official CSS variables and configuration options.

## CSS Variables (Complete List)

```css
openai-chatkit {
  /* === COLORS === */
  --ck-accent-color: #2563EB;           /* Primary action color */
  --ck-accent-color-hover: #1d4ed8;     /* Hover state */
  --ck-background-color: #ffffff;        /* Main background */
  --ck-surface-color: #f9fafb;          /* Cards, inputs background */
  --ck-border-color: #e5e7eb;           /* Borders */
  --ck-text-color: #1f2937;             /* Primary text */
  --ck-text-secondary-color: #6b7280;   /* Secondary text */
  --ck-error-color: #ef4444;            /* Error states */
  --ck-success-color: #22c55e;          /* Success states */
  
  /* === SPACING === */
  --ck-radius: 8px;                     /* Border radius */
  --ck-spacing-xs: 4px;
  --ck-spacing-sm: 8px;
  --ck-spacing-md: 16px;
  --ck-spacing-lg: 24px;
  
  /* === TYPOGRAPHY === */
  --ck-font-family: system-ui, -apple-system, sans-serif;
  --ck-font-size-sm: 14px;
  --ck-font-size-md: 16px;
  --ck-font-size-lg: 18px;
  
  /* === DIMENSIONS === */
  height: 600px;
  width: 400px;
  max-width: 100%;
}
```

## Dark Mode

```css
/* Auto dark mode based on system preference */
@media (prefers-color-scheme: dark) {
  openai-chatkit {
    --ck-background-color: #1a1a1a;
    --ck-surface-color: #2d2d2d;
    --ck-border-color: #404040;
    --ck-text-color: #ffffff;
    --ck-text-secondary-color: #a0a0a0;
  }
}

/* Or set via JavaScript */
chatkit.setOptions({
  theme: {
    colorScheme: 'dark',  // 'light', 'dark', 'auto'
  },
});
```

## Density Options

```javascript
chatkit.setOptions({
  theme: {
    density: 'normal',  // 'compact', 'normal', 'spacious'
  },
});
```

| Density | Use Case |
|---------|----------|
| `compact` | Mobile, sidebars, limited space |
| `normal` | Default, most applications |
| `spacious` | Desktop, reading-focused |

## Brand Colors Example

```css
/* Brand: Blue */
openai-chatkit.brand-blue {
  --ck-accent-color: #2563EB;
  --ck-accent-color-hover: #1d4ed8;
}

/* Brand: Green */
openai-chatkit.brand-green {
  --ck-accent-color: #16a34a;
  --ck-accent-color-hover: #15803d;
}

/* Brand: Purple */
openai-chatkit.brand-purple {
  --ck-accent-color: #9333ea;
  --ck-accent-color-hover: #7e22ce;
}
```

## JavaScript Theme Configuration

```javascript
chatkit.setOptions({
  theme: {
    colorScheme: 'light',
    accentColor: '#2563EB',
    
    // Grayscale customization
    grayscale: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
    },
    
    // Surface colors
    surface: {
      background: '#ffffff',
      foreground: '#f9fafb',
      border: '#e5e7eb',
    },
  },
});
```

## Responsive Sizing

```css
/* Mobile */
@media (max-width: 640px) {
  openai-chatkit {
    height: 100vh;
    width: 100vw;
    --ck-radius: 0;
  }
}

/* Tablet */
@media (min-width: 641px) and (max-width: 1024px) {
  openai-chatkit {
    height: 500px;
    width: 350px;
  }
}

/* Desktop */
@media (min-width: 1025px) {
  openai-chatkit {
    height: 600px;
    width: 400px;
  }
}
```

## Embedding Layouts

### Sidebar Chat

```html
<div class="app-layout">
  <main class="content">
    <!-- Your app content -->
  </main>
  <aside class="chat-sidebar">
    <openai-chatkit></openai-chatkit>
  </aside>
</div>

<style>
  .app-layout {
    display: flex;
    height: 100vh;
  }
  .content {
    flex: 1;
  }
  .chat-sidebar {
    width: 400px;
    border-left: 1px solid #e5e7eb;
  }
  .chat-sidebar openai-chatkit {
    height: 100%;
    width: 100%;
  }
</style>
```

### Floating Widget

```html
<button id="chat-toggle">Chat</button>
<div id="chat-container" class="hidden">
  <openai-chatkit></openai-chatkit>
</div>

<style>
  #chat-container {
    position: fixed;
    bottom: 80px;
    right: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    border-radius: 12px;
    overflow: hidden;
  }
  #chat-container.hidden {
    display: none;
  }
  #chat-container openai-chatkit {
    height: 500px;
    width: 380px;
  }
  #chat-toggle {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 24px;
    background: #2563EB;
    color: white;
    border: none;
    border-radius: 24px;
    cursor: pointer;
  }
</style>

<script>
  document.getElementById('chat-toggle').onclick = () => {
    document.getElementById('chat-container').classList.toggle('hidden');
  };
</script>
```

### Fullscreen Modal

```html
<div id="chat-modal" class="modal hidden">
  <div class="modal-content">
    <button class="close-btn">&times;</button>
    <openai-chatkit></openai-chatkit>
  </div>
</div>

<style>
  .modal {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  .modal.hidden {
    display: none;
  }
  .modal-content {
    background: white;
    border-radius: 12px;
    position: relative;
    overflow: hidden;
  }
  .modal-content openai-chatkit {
    height: 80vh;
    width: 600px;
    max-width: 90vw;
  }
  .close-btn {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 10;
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
  }
</style>
```

## DO NOT

❌ Override internal ChatKit styles with `!important`
❌ Use browser dev tools to find and override internal classes
❌ Inject custom CSS into ChatKit shadow DOM
❌ Replace ChatKit components with custom implementations

## DO

✅ Use only documented CSS variables
✅ Use only documented JavaScript options
✅ Wrap ChatKit in container elements for layout
✅ Use media queries on container, not internal elements