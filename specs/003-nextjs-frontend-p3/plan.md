# Implementation Plan: Next.js Frontend UI (Phase 3) - StoreLite IMS

**Branch**: `003-nextjs-frontend-p3` | **Date**: 2025-12-08 | **Spec**: [spec.md](spec.md)
**Status**: Ready for Phase 0 → Phase 1 → Phase 2
**Input**: Feature specification + Constitution alignment check

## Summary

Build a production-ready Next.js 14+ frontend with TypeScript for StoreLite IMS inventory and billing system. The frontend provides two core user interfaces:

1. **Admin Page** (`/admin`) – Inventory management CRUD: add items, view searchable table, update price/stock
2. **POS Page** (`/pos`) – Point-of-sale billing: search items, build cart, generate printable invoices

The frontend integrates seamlessly with existing FastAPI backend (Phase 2) and applies 3 critical resilience patterns: auto-retry with user feedback, real-time stock monitoring, and user-friendly error handling. All code follows TDD principles and Constitution standards (Separation of Concerns, Contract-First APIs, Local-First Development).

---

## Technical Context

**Language/Version**: TypeScript 5.x with Node.js 18+
**Primary Dependencies**:
- Next.js 14+ (App Router)
- React 18+
- Tailwind CSS
- TypeScript for type safety
- Axios or native fetch for API calls
- React Hook Form or built-in form handling

**Storage**: N/A (frontend stateless; data persists in PostgreSQL via FastAPI)
**Testing**: Jest + React Testing Library (optional for Phase 3; consider for Phase 3.5)
**Target Platform**: Desktop (1920x1080, 1366x768) + Tablet (iPad) browsers; mobile optional
**Project Type**: Web (SPA with Server-Side Rendering via Next.js)
**Performance Goals**:
- Page load < 3 seconds (SC-009)
- Search filters update < 1 second (SC-002)
- Bill total calculation real-time (< 100ms)

**Constraints**:
- No external payment processing (Phase 4+)
- No authentication required (Phase 3 is open; auth in future phase)
- Real-time stock sync via polling (not WebSockets; keep simple)
- Offline capability not required for Phase 3

**Scale/Scope**:
- Single storefront (multi-store deferred to Phase 5+)
- Typical small store: 100-500 items, 50-100 bills/day
- 2 main pages + landing page

---

## Constitution Check

**GATE 1: Separation of Concerns** ✅ PASS
- Frontend code isolated in `/frontend` directory
- No imports from backend code; pure API-based integration
- Separate `package.json` and dependencies from backend

**GATE 2: Test-Driven Development** ⚠️ PARTIAL (frontend tests optional Phase 3, required Phase 3.5+)
- Backend (FastAPI Phase 2) tested first; frontend validates against working API
- Manual testing sufficient for Phase 3 MVP; automated testing deferred to follow-up

**GATE 3: Phased Implementation** ✅ PASS
- Phase 3 depends on Phase 2 (FastAPI) being complete and tested
- Frontend does not re-implement backend logic; only consumes API

**GATE 4: Database-First Design** ✅ PASS
- Frontend treats PostgreSQL (via FastAPI) as source of truth
- No local data duplication; API calls always fresh
- Bill generation triggers server-side stock deduction

**GATE 5: Contract-First APIs** ✅ PASS
- All API endpoints documented in Phase 2 spec
- Frontend strictly adheres to documented request/response contracts
- No dynamic/undocumented API usage

**GATE 6: Local-First Development** ✅ PASS
- Frontend runs on `localhost:3000`
- Backend on `localhost:8000` (configurable via `.env.local`)
- No cloud dependencies during development

**GATE 7: Simplicity Over Abstraction** ✅ PASS
- Direct API calls using fetch/Axios; no complex middleware layers
- Component structure mirrors page structure (simple 1:1 mapping)
- No custom state management libraries (Context API sufficient for Phase 3)

**GATE 8: Observability by Default** ✅ PASS
- Console logging for API calls, errors, user actions
- Error boundary implementation for graceful failure handling
- Structured error messages displayed to user

**GATE RESULT**: ✅ **APPROVED** – Phase 3 frontend aligns with all 8 Constitution principles.

---

## Project Structure

### Documentation (this feature)

```text
specs/003-nextjs-frontend-p3/
├── spec.md              # Feature specification (COMPLETED)
├── plan.md              # This file (CURRENT)
├── research.md          # Phase 0 output (PENDING - will be created during implementation)
├── data-model.md        # Phase 1 output (PENDING)
├── quickstart.md        # Phase 1 output (PENDING)
├── contracts/           # Phase 1 output - API contracts (PENDING)
│   ├── items.openapi.json
│   └── bills.openapi.json
├── checklists/
│   └── requirements.md   # Quality validation (COMPLETED)
└── tasks.md             # Phase 2 output from /sp.tasks (PENDING)
```

### Source Code Structure

```text
frontend/                           # New directory for Phase 3
├── app/                            # Next.js App Router
│   ├── layout.tsx                  # Root layout with navigation
│   ├── page.tsx                    # Landing page (optional)
│   ├── admin/
│   │   ├── layout.tsx              # Admin-specific layout
│   │   └── page.tsx                # Inventory management page
│   ├── pos/
│   │   ├── layout.tsx              # POS-specific layout
│   │   └── page.tsx                # Billing/POS page
│   └── globals.css                 # Global styles (Tailwind)
├── components/                     # Reusable React components
│   ├── admin/
│   │   ├── AddItemForm.tsx         # Form to add new item
│   │   ├── ItemsTable.tsx          # Inventory table with search/filter
│   │   ├── EditItemModal.tsx       # Modal to edit item
│   │   └── ItemActions.tsx         # Edit/Delete buttons
│   ├── pos/
│   │   ├── ItemSearch.tsx          # Search box with dropdown
│   │   ├── BillItems.tsx           # Bill items table (editable quantities)
│   │   ├── BillSummary.tsx         # Subtotal and Grand Total
│   │   ├── GenerateBillButton.tsx  # Submit button
│   │   └── InvoiceView.tsx         # Print-ready invoice
│   └── shared/
│       ├── Header.tsx              # App header
│       ├── Navigation.tsx          # Navigation menu
│       ├── LoadingSpinner.tsx      # Loading indicator
│       ├── ErrorBoundary.tsx       # Error fallback
│       ├── SuccessToast.tsx        # Success notifications
│       └── ErrorMessage.tsx        # Error message display
├── lib/                            # Utilities and API client
│   ├── api.ts                      # API client with retry logic
│   ├── hooks.ts                    # Custom React hooks (useItems, useBill, etc.)
│   ├── types.ts                    # TypeScript interfaces (Item, Bill, etc.)
│   ├── validation.ts               # Form validation rules
│   └── constants.ts                # App constants (API URLs, categories, etc.)
├── styles/                         # CSS modules (if needed alongside Tailwind)
├── public/                         # Static assets (logos, icons)
├── .env.local.example              # Example environment variables
├── package.json                    # Frontend dependencies
├── package-lock.json
├── tsconfig.json                   # TypeScript configuration
├── next.config.js                  # Next.js configuration
├── tailwind.config.js              # Tailwind CSS configuration
└── README.md                       # Frontend setup guide
```

**Structure Decision**: Web application (Option 2) selected. Frontend and backend are completely separated, following Constitution Principle I (Separation of Concerns). Frontend in `/frontend` uses only documented FastAPI endpoints; no code imports from `/backend`.

---

## Architecture Overview

### High-Level Data Flow

```
User (Browser)
    ↓
Next.js Frontend (React Components)
    ↓ (API Calls via fetch/Axios)
FastAPI Backend (Phase 2)
    ↓
PostgreSQL Database
    ↑
(Updates returned, displayed in UI)
```

### Component Hierarchy

**Admin Page** (`/admin`):
```
AdminLayout
├── Header
├── AddItemForm (input fields + submit button)
├── Filters (name search + category dropdown)
├── ItemsTable (results with Edit/Delete buttons)
│   └── EditItemModal (form for price/stock update)
└── ErrorBoundary + LoadingSpinner
```

**POS Page** (`/pos`):
```
POSLayout
├── Header
├── ItemSearch (search box + dropdown results)
├── BillItems (table with quantity inputs)
│   └── Actions (delete button per row)
├── BillSummary (subtotal + total)
├── GenerateBillButton
├── InvoiceView (conditional: shown after bill generated)
│   ├── PrintButton
│   └── NewBillButton
└── ErrorBoundary + LoadingSpinner + Real-time Stock Monitor
```

### API Integration Points

**Items Endpoints** (from FastAPI Phase 2):
- `POST /items` → Add new item (admin)
- `GET /items` → List items with optional filters (admin + pos)
- `GET /items/{id}` → Get single item (internal)
- `PUT /items/{id}` → Update item (admin)

**Bills Endpoints** (from FastAPI Phase 2):
- `POST /bills` → Create bill + deduct stock (pos)
- `GET /bills/{id}` → Retrieve bill for invoice (pos)

**Error Handling & Retries**:
- Implement in `lib/api.ts` wrapper around fetch/Axios
- Auto-retry logic: 3 attempts with exponential backoff
- Manual retry button offered to user after auto-retry exhaustion
- User-friendly error messages mapped from backend error codes

**Stock Monitoring** (for POS page):
- Background polling every 5-10 seconds (configurable)
- Check stock levels of items currently in bill
- Display warning overlay if item becomes unavailable (quantity = 0)
- Validation occurs at bill generation, not before

---

## Technology Decisions & Rationale

| Decision | Choice | Rationale | Alternatives Rejected |
|----------|--------|-----------|----------------------|
| **Framework** | Next.js 14+ (App Router) | Modern, production-ready, built-in SSR, easy API routes if needed | Vite/React (no SSR), Create React App (older pattern) |
| **Language** | TypeScript | Type safety prevents bugs; Constitution Principle VIII (Observability) – types help debugging | Plain JavaScript (runtime errors harder to catch) |
| **Styling** | Tailwind CSS | Utility-first, fast development, low CSS overhead | Bootstrap (heavier), CSS modules (more boilerplate) |
| **HTTP Client** | Axios with wrapper | Simple, built-in retry support via interceptors, promise-based | Fetch only (more verbose retry logic), GraphQL client (overkill) |
| **State Management** | React Context API (built-in) | Sufficient for Phase 3; minimal boilerplate following Principle VII (Simplicity) | Redux (overkill for 2 pages), Zustand (premature abstraction) |
| **Form Handling** | React Hook Form or controlled inputs | Minimal dependencies, strong integration with validation libraries | Formik (heavier), Uncontrolled inputs (harder validation) |
| **Testing** | Manual + Jest/RTL (deferred to Phase 3.5) | Phase 3 is MVP; FastAPI backend tested first (Principle II TDD) | Skip testing entirely (risky for production) |
| **Real-Time Updates** | Polling (5-10s intervals) | Keeps architecture simple; no WebSocket infrastructure (Principle VI Local-First) | WebSockets (adds complexity), Server-Sent Events (overkill) |
| **Print Format** | Browser native `window.print()` | No external library dependency; users control print settings (Principle VII Simplicity) | jsPDF (adds library), Custom CSS print media only (limited UX) |

---

## Key Implementation Patterns

### Pattern 1: API Client with Auto-Retry

```typescript
// lib/api.ts
class APIClient {
  async request(method: string, endpoint: string, data?: any, retries = 3) {
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const response = await fetch(`${API_URL}${endpoint}`, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: data ? JSON.stringify(data) : undefined,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
      } catch (error) {
        if (attempt === retries - 1) throw error; // Last attempt failed
        await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1))); // Backoff
      }
    }
  }
}
```

### Pattern 2: Real-Time Stock Monitoring (POS Page)

```typescript
// In POSLayout component
useEffect(() => {
  const interval = setInterval(async () => {
    const itemIds = bill.items.map(item => item.id);
    const currentStocks = await api.checkStock(itemIds);
    const unavailable = currentStocks.filter(s => s.stock === 0);
    if (unavailable.length > 0) setWarning(`${unavailable[0].name} is out of stock`);
  }, 10000); // Poll every 10 seconds
  return () => clearInterval(interval);
}, [bill.items]);
```

### Pattern 3: User-Friendly Error Mapping

```typescript
// lib/api.ts
const ERROR_MESSAGES = {
  'VALIDATION_ERROR': 'Please check your input and try again',
  'INSUFFICIENT_STOCK': 'Not enough stock available for this item',
  'ITEM_NOT_FOUND': 'Item no longer exists',
  'SERVER_ERROR': 'System error, please try again later',
  'NETWORK_ERROR': 'Connection lost, retrying...',
};

function mapError(backendError: string | number): string {
  return ERROR_MESSAGES[backendError] || 'Something went wrong';
}
```

### Pattern 4: Form Validation (Client-Side)

```typescript
// lib/validation.ts
export const validateItem = (item: ItemForm): Record<string, string> => {
  const errors: Record<string, string> = {};
  if (!item.name.trim()) errors.name = 'Item name is required';
  if (item.unit_price <= 0) errors.unit_price = 'Price must be greater than 0';
  if (item.stock_qty < 0) errors.stock_qty = 'Stock cannot be negative';
  return errors;
};
```

---

## Development Workflow

### Getting Started (Local Development)

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Create environment file
cp .env.local.example .env.local
# Edit .env.local: set NEXT_PUBLIC_API_URL=http://localhost:8000

# 4. Start development server
npm run dev
# Accessible at http://localhost:3000

# 5. Verify FastAPI backend is running
# Should be at http://localhost:8000/docs
```

### Build & Production

```bash
# Build for production
npm run build

# Start production server
npm run start

# Run linting/type checking
npm run lint
npm run type-check
```

### File Organization for Development

1. **Component creation**: Follow `components/[domain]/[ComponentName].tsx` pattern
2. **API calls**: All HTTP requests go through `lib/api.ts`
3. **Type definitions**: Add to `lib/types.ts` (never duplicate across components)
4. **Environment variables**: Use `NEXT_PUBLIC_*` prefix for client-side vars (visible in browser)

---

## Success Criteria & Validation

From the specification, Phase 3 will be **complete** when:

### Functional Validation
- ✅ Admin page allows adding items via form; item appears in table
- ✅ Admin page filters by name and category work
- ✅ Admin page edit modal updates price/stock
- ✅ POS page search finds items and shows in dropdown
- ✅ POS page selected items appear in bill with quantities
- ✅ POS page totals calculate correctly (line totals + grand total)
- ✅ POS page "Generate Bill" creates invoice record and shows print-ready view
- ✅ Invoice print layout is clean and suitable for receipt/A4 paper

### Performance Validation
- ✅ Pages load in <3 seconds on standard connection (SC-009)
- ✅ Search/filter updates show results in <1 second (SC-002)
- ✅ Bill total updates real-time as quantities change

### Resilience Validation
- ✅ API failures trigger auto-retry with visible "Retrying..." status (3 attempts max)
- ✅ Manual "Retry" button appears after auto-retry exhaustion
- ✅ Stock levels monitored in background on POS page; warning shown if item becomes unavailable
- ✅ Error messages are user-friendly; no technical stack traces shown

### Code Quality Validation
- ✅ Code follows Constitution standards (Separation of Concerns, Local-First, Contract-First)
- ✅ No hardcoded secrets in code; `.env.local` used for configuration
- ✅ TypeScript strict mode enabled; all types defined
- ✅ Components are small, focused, and reusable

---

## Dependencies & Prerequisites

**MUST be operational before Phase 3 implementation begins:**

1. **Phase 2 FastAPI Backend** ✅ REQUIRED
   - All endpoints tested and working
   - Available at `http://localhost:8000`
   - Swagger docs at `http://localhost:8000/docs`

2. **PostgreSQL Database** ✅ REQUIRED
   - Schema: `items`, `bills`, `bill_items` tables created
   - Data accessible via FastAPI

3. **Node.js 18+** ✅ REQUIRED
   - npm or yarn package manager

4. **Environment Setup** ✅ REQUIRED
   - `.env.local` configured with `NEXT_PUBLIC_API_URL`
   - CORS enabled on FastAPI for `localhost:3000`

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| **FastAPI backend not ready** | Blocks all integration testing | Medium | Verify Phase 2 completion before starting Phase 3 |
| **Network latency affecting UX** | Slow search/filter (>1s) | Low | Implemented client-side debouncing on search input |
| **Real-time stock monitoring lag** | User doesn't see stock depletion until bill generation | Low | 5-10s polling interval is acceptable for small store |
| **Print layout breaks on different browsers** | Invoice unreadable on some devices | Low | Test CSS print media on Chrome, Firefox, Safari |
| **CORS errors** | Frontend can't call backend | Low | Pre-configure CORS in FastAPI `.allow_origins = ["http://localhost:3000"]` |

---

## Deferred Decisions (Post-Phase 3)

The following features are explicitly deferred to future phases and not included in Phase 3 MVP:

1. **User Authentication** (Phase 3.5+) – All users currently have access to all pages
2. **Automated Testing** (Phase 3.5+) – Manual testing sufficient for MVP; Jest/RTL setup deferred
3. **Mobile Optimization** (Phase 4+) – Desktop/tablet only for Phase 3
4. **Real-time sync** (Phase 5+) – Polling sufficient; WebSockets deferred
5. **Multi-store support** (Phase 5+) – Single store for Phase 3
6. **Payment processing** (Future) – No integration required
7. **Discount/tax calculations** (Future) – Out of scope for Phase 3

---

## Next Steps

**Phase 0**: Research & technical spike (if needed)
- Verify Next.js 14 setup + TypeScript best practices
- Test Axios interceptor patterns for retry logic
- Prototype real-time stock polling on POS page

**Phase 1**: Design & Contracts (in progress)
- ✅ Data model finalized (Item, Bill, BillItem)
- ✅ API contracts defined (from Phase 2)
- ⏳ Component hierarchy + folder structure (this document)
- ⏳ Quickstart guide + code examples

**Phase 2**: Task Breakdown (next command)
- Run `/sp.tasks` to generate detailed task list
- Tasks will be organized by user story + TDD phases (Red → Green → Refactor)
- Each task will include acceptance criteria + test examples

**Phase 3**: Implementation (after tasks)
- Follow tasks in order
- TDD workflow: write test, code, refactor
- Manual testing against FastAPI backend

---

## Appendix: Code Examples

### Example: AddItemForm Component

```typescript
// components/admin/AddItemForm.tsx
import { useState } from 'react';
import { validateItem } from '@/lib/validation';
import { api } from '@/lib/api';

export default function AddItemForm({ onItemAdded }) {
  const [form, setForm] = useState({
    name: '', category: '', unit: '', unit_price: 0, stock_qty: 0
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validateItem(form);
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }

    setLoading(true);
    try {
      const item = await api.addItem(form);
      setForm({ name: '', category: '', unit: '', unit_price: 0, stock_qty: 0 });
      onItemAdded(item);
    } catch (err) {
      setErrors({ submit: 'Failed to add item. Please try again.' });
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-md mx-auto p-4 border rounded">
      <input
        type="text" placeholder="Item Name" value={form.name}
        onChange={(e) => setForm({...form, name: e.target.value})}
        className={errors.name ? 'border-red-500' : ''}
      />
      {errors.name && <span className="text-red-500">{errors.name}</span>}
      {/* ... other fields ... */}
      <button type="submit" disabled={loading}>
        {loading ? 'Adding...' : 'Add Item'}
      </button>
    </form>
  );
}
```

---

**Plan Status**: ✅ **COMPLETE & READY FOR /sp.tasks**

This plan provides clear architecture, technology choices, and implementation patterns. Next step: generate detailed task breakdown using `/sp.tasks` command.
