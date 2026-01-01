# Theming Reference

> Guide for theming OpenAI ChatKit using official CSS variables and configuration.

---

## Theme Configuration

### Basic Theme Setting

```typescript
chatkit.setOptions({
  theme: 'light',  // 'light' or 'dark'
});
```

### System Theme (Auto)

```typescript
// Detect system preference
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

chatkit.setOptions({
  theme: prefersDark ? 'dark' : 'light',
});

// Listen for changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
  chatkit.setOptions({
    theme: e.matches ? 'dark' : 'light',
  });
});
```

---

## CSS Variables (Official)

ChatKit exposes CSS variables for customization. Override these in your CSS:

### Color Variables

```css
openai-chatkit {
  /* Primary colors */
  --chatkit-primary: #0066ff;
  --chatkit-primary-hover: #0052cc;

  /* Background colors */
  --chatkit-bg: #ffffff;
  --chatkit-bg-secondary: #f5f5f5;
  --chatkit-bg-tertiary: #eeeeee;

  /* Text colors */
  --chatkit-text: #1a1a1a;
  --chatkit-text-secondary: #666666;
  --chatkit-text-muted: #999999;

  /* Border colors */
  --chatkit-border: #e0e0e0;
  --chatkit-border-focus: #0066ff;

  /* Message colors */
  --chatkit-user-message-bg: #0066ff;
  --chatkit-user-message-text: #ffffff;
  --chatkit-assistant-message-bg: #f5f5f5;
  --chatkit-assistant-message-text: #1a1a1a;

  /* Status colors */
  --chatkit-success: #00cc66;
  --chatkit-error: #ff3333;
  --chatkit-warning: #ffcc00;
}
```

### Dark Theme Override

```css
openai-chatkit[data-theme="dark"] {
  --chatkit-bg: #1a1a1a;
  --chatkit-bg-secondary: #2a2a2a;
  --chatkit-bg-tertiary: #333333;

  --chatkit-text: #ffffff;
  --chatkit-text-secondary: #cccccc;
  --chatkit-text-muted: #888888;

  --chatkit-border: #444444;

  --chatkit-assistant-message-bg: #2a2a2a;
  --chatkit-assistant-message-text: #ffffff;
}
```

---

## Container Styling

### Floating Widget

```css
.chatkit-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 384px;       /* 96 * 4 = 384px (w-96 in Tailwind) */
  height: 500px;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  z-index: 50;
}

openai-chatkit {
  width: 100%;
  height: 100%;
  display: block;
}
```

### Full Page

```css
.chatkit-fullpage {
  width: 100vw;
  height: 100vh;
}
```

### Sidebar

```css
.chatkit-sidebar {
  position: fixed;
  right: 0;
  top: 0;
  width: 400px;
  height: 100vh;
  border-left: 1px solid var(--chatkit-border);
}
```

---

## Brand Customization

### Custom Primary Color

```css
openai-chatkit {
  --chatkit-primary: #6366f1;         /* Indigo */
  --chatkit-primary-hover: #4f46e5;
  --chatkit-user-message-bg: #6366f1;
}
```

### Custom Font

```css
openai-chatkit {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

### Custom Border Radius

```css
openai-chatkit {
  --chatkit-radius: 8px;
  --chatkit-radius-lg: 12px;
  --chatkit-radius-full: 9999px;
}
```

---

## Component-Specific Styling

### Header

```css
openai-chatkit::part(header) {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
}
```

### Composer (Input Area)

```css
openai-chatkit::part(composer) {
  border-top: 1px solid var(--chatkit-border);
  padding: 12px 16px;
}

openai-chatkit::part(composer-input) {
  border-radius: 8px;
  border: 1px solid var(--chatkit-border);
}
```

### Messages

```css
openai-chatkit::part(message-user) {
  background: var(--chatkit-user-message-bg);
  color: var(--chatkit-user-message-text);
  border-radius: 12px 12px 4px 12px;
}

openai-chatkit::part(message-assistant) {
  background: var(--chatkit-assistant-message-bg);
  color: var(--chatkit-assistant-message-text);
  border-radius: 12px 12px 12px 4px;
}
```

### Start Screen

```css
openai-chatkit::part(start-screen) {
  text-align: center;
  padding: 32px;
}

openai-chatkit::part(start-greeting) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 16px;
}

openai-chatkit::part(prompt-button) {
  background: var(--chatkit-bg-secondary);
  border: 1px solid var(--chatkit-border);
  border-radius: 8px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

openai-chatkit::part(prompt-button):hover {
  background: var(--chatkit-bg-tertiary);
}
```

### Disclaimer

```css
openai-chatkit::part(disclaimer) {
  font-size: 0.75rem;
  color: var(--chatkit-text-muted);
  text-align: center;
  padding: 8px;
}
```

---

## Responsive Design

### Mobile Optimization

```css
@media (max-width: 640px) {
  .chatkit-container {
    position: fixed;
    inset: 0;
    width: 100%;
    height: 100%;
    border-radius: 0;
  }
}
```

### Tablet

```css
@media (min-width: 641px) and (max-width: 1024px) {
  .chatkit-container {
    width: 420px;
    height: 600px;
  }
}
```

---

## Animation Customization

```css
openai-chatkit {
  /* Message animation */
  --chatkit-message-animation: fadeIn 0.2s ease-out;

  /* Loading indicator */
  --chatkit-loading-animation: pulse 1.5s infinite;

  /* Transition speed */
  --chatkit-transition: 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
```

---

## Toggle Button Styling

The toggle button is NOT part of ChatKit - style it yourself:

```css
.chatkit-toggle {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #0066ff;
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 102, 255, 0.4);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s, box-shadow 0.2s;
  z-index: 50;
}

.chatkit-toggle:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 102, 255, 0.5);
}

.chatkit-toggle:active {
  transform: scale(0.95);
}
```

---

## Theme Presets

### Modern Blue

```css
openai-chatkit {
  --chatkit-primary: #3b82f6;
  --chatkit-primary-hover: #2563eb;
  --chatkit-user-message-bg: #3b82f6;
  --chatkit-radius: 12px;
}
```

### Elegant Purple

```css
openai-chatkit {
  --chatkit-primary: #8b5cf6;
  --chatkit-primary-hover: #7c3aed;
  --chatkit-user-message-bg: #8b5cf6;
}
```

### Professional Gray

```css
openai-chatkit {
  --chatkit-primary: #374151;
  --chatkit-primary-hover: #1f2937;
  --chatkit-user-message-bg: #374151;
}
```

### Vibrant Gradient

```css
openai-chatkit::part(header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

---

## Important Rules

1. **Use CSS variables** - Never target internal ChatKit classes directly
2. **Use ::part()** - For component-specific styling where supported
3. **Avoid !important** - Work with the cascade, not against it
4. **Test both themes** - Ensure customizations work in light and dark
5. **Mobile first** - Test responsive behavior thoroughly
6. **Respect defaults** - Only override what's necessary

---

## Common Mistakes

### DON'T: Target internal elements

```css
/* BAD - Internal structure may change */
.chatkit-message-bubble { ... }
```

### DO: Use CSS variables

```css
/* GOOD - Stable API */
openai-chatkit {
  --chatkit-user-message-bg: #6366f1;
}
```

### DON'T: Override everything

```css
/* BAD - Heavy-handed */
openai-chatkit * {
  font-family: Arial !important;
}
```

### DO: Target specific parts

```css
/* GOOD - Surgical */
openai-chatkit {
  font-family: 'Inter', sans-serif;
}
```
