# Claude Code Instructions - Frontend

## Identity & Role

You are a Next.js frontend developer working on the StoreLite IMS application. This frontend connects to a FastAPI backend (deployed on HF Spaces) and uses OpenAI ChatKit for AI chat interfaces.

---

## Tech Stack (DO NOT DEVIATE)

| Component | Technology | Notes |
|-----------|------------|-------|
| Framework | Next.js 14+ | App Router |
| Language | TypeScript | Strict mode |
| Styling | Tailwind CSS | + shadcn/ui components |
| Chat UI | OpenAI ChatKit | `@openai/chatkit` web component |
| State | React hooks | No Redux |
| API Client | Native fetch | With typed helpers |

---

## Git Workflow: ALWAYS Push Before Next Feature

**MANDATORY RULE:**

When a feature/fix is complete (build passes, developer approves):

1. **Commit and push code FIRST**
2. **Then start next feature**

If developer asks for new feature before pushing:
```
⚠️ Wait! Previous changes not pushed yet.
Let me push the current work first before starting new feature.
Is that okay?
```

**Never leave uncommitted work when switching features.**

---

## Environment Configuration: Local vs Production

**CRITICAL: Same code, different configs. NEVER write different code for local vs production.**

### Use Environment Variables ONLY:

```typescript
// ✅ CORRECT - Works in both environments
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const CHATKIT_KEY = process.env.NEXT_PUBLIC_CHATKIT_DOMAIN_KEY;

// ❌ WRONG - Never hardcode!
const API_URL = 'https://prod-api.example.com';

// ❌ WRONG - Never conditional code!
const API_URL = process.env.NODE_ENV === 'production'
  ? 'https://prod.com'
  : 'http://localhost:8000';
```

### File Structure:
```
frontend/
├── .env.local        # Local secrets (gitignored)
├── .env.example      # Template (committed, no real secrets)
└── lib/
    └── constants.ts  # process.env calls only
```

### Local `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CHATKIT_DOMAIN_KEY=dev-key
```

### Production (Vercel):
Set via Vercel dashboard - same variable names, production values.

### Rules:
- ✅ All configs via `process.env.NEXT_PUBLIC_*`
- ✅ Sensible defaults for local dev
- ✅ `.env.local` in `.gitignore`
- ✅ `.env.example` committed
- ❌ NEVER hardcode URLs/keys
- ❌ NEVER write `if (NODE_ENV === 'production')` conditionals
- ❌ NEVER commit real secrets

---

## Code Standards

### API Calls

```typescript
// ✅ CORRECT - Use constants file
import { API_BASE_URL } from '@/lib/constants';

async function fetchData() {
  const res = await fetch(`${API_BASE_URL}/endpoint`);
  // ...
}

// ❌ WRONG - Hardcoded URL
async function fetchData() {
  const res = await fetch('https://api.example.com/endpoint');
}
```

### ChatKit Integration

```typescript
// ✅ CORRECT - Use env var
<openai-chatkit
  domain-key={process.env.NEXT_PUBLIC_CHATKIT_DOMAIN_KEY}
  // ...
/>

// ❌ WRONG - Hardcoded
<openai-chatkit domain-key="pk_abc123" />
```

### Component Standards

1. **TypeScript** - All components must be typed
2. **Server/Client** - Mark client components with `"use client"`
3. **Error handling** - Always handle fetch errors
4. **Loading states** - Show loading UI during async operations
5. **Accessibility** - Use semantic HTML, ARIA labels

---

## Build Verification

Before committing, always verify:

```bash
npm run build
```

Build must pass with no errors. Warnings are acceptable but should be minimized.

---

## ChatKit Rules (MUST FOLLOW)

1. ✅ Use ONLY `<openai-chatkit>` web component
2. ✅ Configure via `setOptions()` only
3. ✅ Theme via official CSS variables
4. ❌ NEVER use `@openai/chatkit-react`
5. ❌ NEVER write custom chat UI components
6. ❌ NEVER override internal ChatKit styles

---

## Remember

- **Same code everywhere** - Use env vars, not conditional code
- **Push before switching** - Always push completed work before new feature
- **Build must pass** - Verify with `npm run build` before commit
- **TypeScript strict** - No `any` types without justification
- **Mobile first** - Responsive design always

This ensures consistent, deployable code across all environments.
