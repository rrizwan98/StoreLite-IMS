# Implementation Plan: Dashboard UX Improvements

**Feature ID**: 015-dashboard-ux-improvements
**Version**: v1.0
**Created**: 2025-01-16

---

## Architecture Overview

This is a **frontend-only** enhancement. No backend changes required.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Dashboard Page                           │
│                    (page.tsx - existing)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           OnboardingChecklist (NEW)                      │   │
│  │  - Derives state from connectionStatus + localStorage    │   │
│  │  - Clickable items navigate to features                  │   │
│  │  - Dismissible, persisted                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              KPIStatsRow (NEW)                           │   │
│  │  - Tables count from schema                              │   │
│  │  - Tools connected from connectors                       │   │
│  │  - Schema status indicator                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            Feature Cards (ENHANCED)                      │   │
│  │  - Explicit CTA buttons                                  │   │
│  │  - Hover microinteractions                               │   │
│  │  - AI Agent primary emphasis                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │        ConnectToolsSection (MINOR UPDATES)               │   │
│  │  - Staggered animation on load                           │   │
│  │  - Tooltip on section header                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │          Read-Only Banner (TOOLTIP ADDED)                │   │
│  │  - Info icon with security explanation                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

All data comes from **existing sources** - no new API calls:

```
┌─────────────────────┐
│     useAuth()       │
│  connectionStatus   │──────┬──────> Onboarding Checklist
│                     │      │        - schema_status
│                     │      │        - connection_type
└─────────────────────┘      │
                             │
┌─────────────────────┐      │
│   getConnectors()   │──────┼──────> KPI Stats Row
│   (existing API)    │      │        - connectors.length
└─────────────────────┘      │
                             │
┌─────────────────────┐      │
│    localStorage     │──────┴──────> Checklist state
│  (browser storage)  │               - dismissed flag
│                     │               - first_query_done
└─────────────────────┘
```

---

## Component Design

### 1. OnboardingChecklist.tsx

```typescript
interface OnboardingChecklistProps {
  connectionStatus: ConnectionStatus;
  connectorsCount: number;
  onNavigate: (route: string) => void;
}

interface ChecklistItem {
  id: string;
  label: string;
  isComplete: boolean;
  route: string;
  icon: React.ReactNode;
}

// Checklist items derived from props (no API calls)
const getChecklistItems = (props): ChecklistItem[] => [
  {
    id: 'connect_db',
    label: 'Connect your database',
    isComplete: props.connectionStatus?.schema_status === 'ready',
    route: ROUTES.SCHEMA_CONNECT,
    icon: <Database />,
  },
  {
    id: 'first_query',
    label: 'Ask your first AI question',
    isComplete: localStorage.getItem('first_ai_query_done') === 'true',
    route: ROUTES.SCHEMA_AGENT,
    icon: <MessageSquare />,
  },
  // ... more items
];
```

**Key Decisions**:
- State derived at render time (not stored in component state)
- localStorage for non-API trackable items
- Collapse/expand controlled via local state + localStorage persistence

---

### 2. KPIStatsRow.tsx

```typescript
interface KPIStatsRowProps {
  tablesCount: number | null;  // null = loading
  toolsConnected: number | null;
  schemaStatus: 'ready' | 'pending' | 'error' | null;
  onStatClick: (statType: string) => void;
}

interface StatWidget {
  value: number | string;
  label: string;
  icon: React.ReactNode;
  route: string;
  color: 'emerald' | 'purple' | 'blue';
}
```

**Key Decisions**:
- Horizontal row layout on desktop, stack on mobile
- Skeleton loading state (not spinner) for each widget
- Click navigates to relevant detail page

---

### 3. Feature Card Enhancements (inline in page.tsx)

Instead of creating a separate component, enhance existing cards inline:

```tsx
// BEFORE: Card with implicit click
<Link href={ROUTES.SCHEMA_AGENT}>
  <div className="bg-white rounded-xl ...">
    <div className="text-4xl mb-4">icon</div>
    <h2>AI Agent</h2>
    <p>Description</p>
  </div>
</Link>

// AFTER: Card with explicit CTA
<div className="bg-white rounded-xl group hover:-translate-y-0.5 transition-all ...">
  <div className="text-4xl mb-4">icon</div>
  <h2>AI Agent</h2>
  <p>Description</p>
  <Link href={ROUTES.SCHEMA_AGENT}>
    <button className="mt-4 w-full bg-emerald-600 text-white py-2 rounded-lg
                       hover:bg-emerald-700 active:scale-[0.98] transition-all">
      Open Chat
    </button>
  </Link>
</div>
```

**Key Decisions**:
- Keep changes inline (no new component) for simplicity
- Use Tailwind's `group` for coordinated hover effects
- `active:scale-[0.98]` for click feedback

---

### 4. Microinteractions (CSS/Tailwind)

Add utility classes to existing elements:

```css
/* Card hover lift */
.card-hover {
  @apply hover:-translate-y-0.5 hover:shadow-lg transition-all duration-200;
}

/* Button click feedback */
.btn-click {
  @apply active:scale-[0.98] transition-transform duration-100;
}

/* Staggered fade-in animation */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in-up {
  animation: fadeInUp 0.3s ease-out forwards;
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  .card-hover,
  .btn-click,
  .animate-fade-in-up {
    animation: none;
    transform: none;
    transition: none;
  }
}
```

---

### 5. Tooltip Component

Option A: Use shadcn/ui Tooltip (if available)
Option B: Create simple custom tooltip:

```tsx
interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

const Tooltip = ({ content, children, position = 'top' }: TooltipProps) => (
  <div className="relative group">
    {children}
    <div className={`
      absolute hidden group-hover:block group-focus-within:block
      px-3 py-2 text-sm bg-gray-900 text-white rounded-lg
      whitespace-nowrap z-50
      ${positionClasses[position]}
    `}>
      {content}
    </div>
  </div>
);
```

**Decision**: Check if shadcn/ui already installed. If yes, use it. If no, create simple custom tooltip.

---

## Implementation Phases

### Phase 1: P1 Features (KPI Stats + Onboarding)

**Files to modify/create**:
1. `frontend/app/dashboard/components/KPIStatsRow.tsx` - NEW
2. `frontend/app/dashboard/components/OnboardingChecklist.tsx` - NEW
3. `frontend/app/dashboard/page.tsx` - Add new components

**Order**:
1. Create KPIStatsRow (simpler, fewer dependencies)
2. Create OnboardingChecklist (depends on understanding localStorage pattern)
3. Integrate into page.tsx
4. Test with existing connection types

---

### Phase 2: P2 Features (CTAs + Microinteractions)

**Files to modify**:
1. `frontend/app/dashboard/page.tsx` - Enhance feature cards
2. `frontend/app/dashboard/components/ConnectToolsSection.tsx` - Add animations
3. `frontend/app/globals.css` or Tailwind config - Add animation utilities

**Order**:
1. Add microinteraction CSS utilities
2. Update feature cards with CTAs and hover effects
3. Add staggered animations to ConnectToolsSection
4. Test all interactions

---

### Phase 3: P3 Features (Progressive Disclosure + Tooltips)

**Files to modify/create**:
1. `frontend/components/ui/Tooltip.tsx` - NEW (or use shadcn)
2. `frontend/app/dashboard/page.tsx` - Add tooltips, progressive styling
3. `frontend/app/dashboard/components/ConnectToolsSection.tsx` - Add tooltips

**Order**:
1. Implement/import Tooltip component
2. Add tooltips to status indicators
3. Implement progressive disclosure logic
4. Final accessibility audit

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Animation jank | Use `transform` only (GPU accelerated), test on low-end device |
| Dark mode issues | Test each component in both modes before committing |
| localStorage conflicts | Use namespaced keys: `ims_dashboard_*` |
| Tooltip accessibility | Include `aria-describedby`, test keyboard navigation |

---

## Testing Strategy

### Manual Testing Checklist

- [ ] New user sees onboarding checklist
- [ ] Checklist items navigate correctly
- [ ] Checklist can be dismissed and stays dismissed
- [ ] KPI stats show correct counts
- [ ] KPI stats are clickable
- [ ] Cards show hover lift effect
- [ ] Buttons show click feedback
- [ ] Tooltips appear on hover
- [ ] All features work in dark mode
- [ ] Reduced motion preference respected
- [ ] Keyboard navigation works for tooltips

### Automated Testing

- Unit tests for OnboardingChecklist state derivation
- Accessibility audit with axe-core
- Visual regression testing (optional)

---

## Definition of Done

- [ ] All P1 requirements implemented and tested
- [ ] All P2 requirements implemented and tested
- [ ] All P3 requirements implemented and tested
- [ ] Dark mode verified
- [ ] Accessibility audit passed
- [ ] Code reviewed
- [ ] Build passes (`npm run build`)
- [ ] Pushed to feature branch
- [ ] PR created with spec reference
