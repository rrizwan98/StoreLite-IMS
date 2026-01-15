# Tasks: Dashboard UX Improvements

**Feature ID**: 015-dashboard-ux-improvements
**Version**: v1.0
**Created**: 2025-01-16
**Branch**: `feat/dashboard-ux-improvements`

---

## Phase 1: P1 Features (High Impact)

### Task 1.1: Create KPI Stats Row Component
**Priority**: P1 | **Effort**: Low | **Status**: [ ] Pending

**Description**: Create a new component that displays key metrics at the top of the dashboard.

**Files**:
- CREATE: `frontend/app/dashboard/components/KPIStatsRow.tsx`

**Acceptance Criteria**:
- [ ] Component accepts `tablesCount`, `toolsConnected`, `schemaStatus` props
- [ ] Shows 3 stat widgets in horizontal row
- [ ] Each widget shows: value, label, icon
- [ ] Skeleton loading state when value is null
- [ ] Click on widget navigates to detail page
- [ ] Responsive: horizontal on desktop, stack on mobile
- [ ] Dark mode support

**Implementation Notes**:
```typescript
// Props interface
interface KPIStatsRowProps {
  tablesCount: number | null;
  toolsConnected: number | null;
  schemaStatus: 'ready' | 'pending' | 'error' | null;
}

// Data derivation (in parent):
// tablesCount = connectionStatus?.tables?.length || 0
// toolsConnected = connectors.length
// schemaStatus = connectionStatus?.schema_status
```

---

### Task 1.2: Create Onboarding Checklist Component
**Priority**: P1 | **Effort**: Medium | **Status**: [ ] Pending

**Description**: Create a checklist component showing user's onboarding progress.

**Files**:
- CREATE: `frontend/app/dashboard/components/OnboardingChecklist.tsx`

**Acceptance Criteria**:
- [ ] Shows 4 checklist items with completion state
- [ ] Completion derived from existing data (no new APIs)
- [ ] Clicking pending item navigates to feature
- [ ] Dismiss button collapses checklist
- [ ] Dismissed state persisted in localStorage
- [ ] Expand button to show again after dismiss
- [ ] Progress indicator (e.g., "2/4 complete")
- [ ] Dark mode support

**Checklist Items**:
1. "Connect your database" - `connectionStatus.schema_status === 'ready'`
2. "Ask your first AI question" - `localStorage.getItem('ims_first_ai_query')`
3. "Connect a tool" - `connectors.length > 0`
4. "Create a scheduled task" - `localStorage.getItem('ims_first_task_created')`

**localStorage Keys**:
- `ims_dashboard_checklist_dismissed`: boolean
- `ims_first_ai_query`: 'true' | null
- `ims_first_task_created`: 'true' | null

---

### Task 1.3: Integrate P1 Components into Dashboard
**Priority**: P1 | **Effort**: Low | **Status**: [ ] Pending

**Description**: Add KPIStatsRow and OnboardingChecklist to the main dashboard page.

**Files**:
- MODIFY: `frontend/app/dashboard/page.tsx`

**Acceptance Criteria**:
- [ ] OnboardingChecklist appears above feature cards (for `schema_query_only` users)
- [ ] KPIStatsRow appears between checklist and feature cards
- [ ] Data passed correctly from existing state
- [ ] No new API calls added
- [ ] Layout looks balanced with new components

**Integration Points**:
```tsx
// In schema_query_only section, before feature cards:
<OnboardingChecklist
  connectionStatus={connectionStatus}
  connectorsCount={connectors.length}
  onNavigate={(route) => router.push(route)}
/>

<KPIStatsRow
  tablesCount={connectionStatus?.schema_summary?.tables_count || null}
  toolsConnected={connectors.length}
  schemaStatus={connectionStatus?.schema_status}
/>

// Existing feature cards below...
```

---

## Phase 2: P2 Features (Professional Polish)

### Task 2.1: Add Microinteraction CSS Utilities
**Priority**: P2 | **Effort**: Low | **Status**: [ ] Pending

**Description**: Add Tailwind utilities for hover and click animations.

**Files**:
- MODIFY: `frontend/app/globals.css` OR `frontend/tailwind.config.ts`

**Acceptance Criteria**:
- [ ] Card hover lift effect class available
- [ ] Button click feedback class available
- [ ] Staggered fade-in animation available
- [ ] Pulse animation for loading states
- [ ] All animations respect `prefers-reduced-motion`

**CSS to Add**:
```css
/* globals.css */
@layer utilities {
  .hover-lift {
    @apply hover:-translate-y-0.5 hover:shadow-lg transition-all duration-200;
  }

  .click-feedback {
    @apply active:scale-[0.98] transition-transform duration-100;
  }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in-up {
  animation: fadeInUp 0.3s ease-out forwards;
}

@media (prefers-reduced-motion: reduce) {
  .hover-lift, .click-feedback, .animate-fade-in-up {
    animation: none !important;
    transform: none !important;
    transition: none !important;
  }
}
```

---

### Task 2.2: Enhance Feature Cards with CTAs
**Priority**: P2 | **Effort**: Low | **Status**: [ ] Pending

**Description**: Add explicit action buttons to each feature card.

**Files**:
- MODIFY: `frontend/app/dashboard/page.tsx`

**Acceptance Criteria**:
- [ ] AI Agent card has "Open Chat" button (primary emerald style)
- [ ] Scheduler card has "View Tasks" button
- [ ] Connection card has "View Schema" button
- [ ] Developer Tools card has "Manage Agents" button
- [ ] Disabled buttons show tooltip when schema not ready
- [ ] AI Agent card has primary visual distinction (emerald border)
- [ ] Cards use hover-lift class
- [ ] Buttons use click-feedback class

**Button Styles**:
```tsx
// Primary CTA (AI Agent)
<button className="mt-4 w-full bg-emerald-600 text-white py-2 px-4 rounded-lg
                   hover:bg-emerald-700 click-feedback font-medium">
  Open Chat
</button>

// Secondary CTA (others)
<button className="mt-4 w-full border border-gray-300 dark:border-gray-600
                   text-gray-700 dark:text-gray-200 py-2 px-4 rounded-lg
                   hover:bg-gray-50 dark:hover:bg-gray-700 click-feedback">
  View Tasks
</button>
```

---

### Task 2.3: Add Staggered Animation to Tools Section
**Priority**: P2 | **Effort**: Medium | **Status**: [ ] Pending

**Description**: Animate tool cards with staggered fade-in effect.

**Files**:
- MODIFY: `frontend/app/dashboard/components/ConnectToolsSection.tsx`

**Acceptance Criteria**:
- [ ] Tool cards animate in one by one (50ms delay between)
- [ ] Animation only plays on initial load (not re-renders)
- [ ] Health check status shows pulse animation while checking
- [ ] Animation respects reduced motion preference

**Implementation**:
```tsx
// Add animation delay based on index
{connectors.map((connector, index) => (
  <div
    key={connector.id}
    className="animate-fade-in-up"
    style={{ animationDelay: `${index * 50}ms` }}
  >
    {/* connector card content */}
  </div>
))}
```

---

## Phase 3: P3 Features (Enhanced UX)

### Task 3.1: Create or Import Tooltip Component
**Priority**: P3 | **Effort**: Low | **Status**: [ ] Pending

**Description**: Add a reusable tooltip component for contextual help.

**Files**:
- CREATE: `frontend/components/ui/Tooltip.tsx` (if not using shadcn)
- OR use existing shadcn Tooltip if available

**Acceptance Criteria**:
- [ ] Tooltip shows on hover and focus
- [ ] Supports positioning (top, bottom, left, right)
- [ ] Accessible with `aria-describedby`
- [ ] Keyboard navigable (Tab to show)
- [ ] Dark mode support
- [ ] Dismisses on Escape key

**Check first**:
```bash
# If this file exists, use shadcn Tooltip
ls frontend/components/ui/tooltip.tsx
```

---

### Task 3.2: Add Contextual Tooltips to Dashboard
**Priority**: P3 | **Effort**: Low | **Status**: [ ] Pending

**Description**: Add explanatory tooltips to status indicators and sections.

**Files**:
- MODIFY: `frontend/app/dashboard/page.tsx`
- MODIFY: `frontend/app/dashboard/components/ConnectToolsSection.tsx`

**Acceptance Criteria**:
- [ ] Schema Status indicator has info icon with tooltip
- [ ] Tool connection status has tooltip explaining state
- [ ] Read-Only banner has tooltip explaining security
- [ ] Connected Tools header has tooltip explaining purpose

**Tooltip Content**:
```tsx
// Schema Status
"Your database schema was discovered successfully. You can now query your data with AI."

// Tool Disconnected
"This connector lost connection. Click 'Manage All Tools' to reconnect."

// Read-Only Mode
"Read-only mode ensures we can only SELECT data from your database. We cannot modify, delete, or create any data."

// Connected Tools Header
"Tools extend your AI agent's capabilities. Connect Gmail to search emails, or add custom MCP servers."
```

---

### Task 3.3: Implement Progressive Disclosure for New Users
**Priority**: P3 | **Effort**: Medium | **Status**: [ ] Pending

**Description**: Visually emphasize AI Agent card for new users, de-emphasize secondary features.

**Files**:
- MODIFY: `frontend/app/dashboard/page.tsx`

**Acceptance Criteria**:
- [ ] New user detection: `!localStorage.getItem('ims_first_ai_query')`
- [ ] AI Agent card emphasized: thicker border, slight scale, "Start here" badge
- [ ] Secondary cards (Scheduler, Dev Tools) slightly muted for new users
- [ ] After first query, all cards show equal visual weight
- [ ] Hover on muted card reveals full style

**Implementation**:
```tsx
const isNewUser = !localStorage.getItem('ims_first_ai_query');

// AI Agent card
<div className={`
  ...base styles...
  ${isNewUser ? 'ring-2 ring-emerald-500 scale-[1.02]' : ''}
`}>
  {isNewUser && (
    <span className="absolute -top-2 -right-2 bg-emerald-500 text-white text-xs px-2 py-1 rounded-full">
      Start here
    </span>
  )}
  ...
</div>

// Secondary cards
<div className={`
  ...base styles...
  ${isNewUser ? 'opacity-75 hover:opacity-100' : ''}
`}>
```

---

## Phase 4: Testing & Polish

### Task 4.1: Dark Mode Verification
**Priority**: P1 | **Effort**: Low | **Status**: [ ] Pending

**Description**: Verify all new components work correctly in dark mode.

**Acceptance Criteria**:
- [ ] KPIStatsRow renders correctly in dark mode
- [ ] OnboardingChecklist renders correctly in dark mode
- [ ] Tooltips readable in dark mode
- [ ] Animation colors appropriate for dark mode
- [ ] No contrast issues (check with browser dev tools)

---

### Task 4.2: Accessibility Audit
**Priority**: P1 | **Effort**: Low | **Status**: [ ] Pending

**Description**: Ensure all new components are accessible.

**Acceptance Criteria**:
- [ ] Run axe-core audit on dashboard page
- [ ] All tooltips have aria-describedby
- [ ] All buttons have accessible names
- [ ] Color contrast meets WCAG AA
- [ ] Keyboard navigation works for all interactive elements
- [ ] Reduced motion preference respected

**Audit Command**:
```bash
# Install axe-core if not present
npm install --save-dev @axe-core/react

# Or use browser extension
```

---

### Task 4.3: Build Verification & PR
**Priority**: P1 | **Effort**: Low | **Status**: [ ] Pending

**Description**: Verify build passes and create PR.

**Acceptance Criteria**:
- [ ] `npm run build` passes with no errors
- [ ] No TypeScript errors
- [ ] No ESLint errors
- [ ] All changes committed
- [ ] Pushed to `feat/dashboard-ux-improvements` branch
- [ ] PR created with link to spec

---

## Task Summary

| Phase | Task | Priority | Effort | Dependencies |
|-------|------|----------|--------|--------------|
| 1 | 1.1 KPI Stats Row | P1 | Low | None |
| 1 | 1.2 Onboarding Checklist | P1 | Medium | None |
| 1 | 1.3 Integrate P1 Components | P1 | Low | 1.1, 1.2 |
| 2 | 2.1 Microinteraction CSS | P2 | Low | None |
| 2 | 2.2 Feature Card CTAs | P2 | Low | 2.1 |
| 2 | 2.3 Staggered Animations | P2 | Medium | 2.1 |
| 3 | 3.1 Tooltip Component | P3 | Low | None |
| 3 | 3.2 Add Tooltips | P3 | Low | 3.1 |
| 3 | 3.3 Progressive Disclosure | P3 | Medium | None |
| 4 | 4.1 Dark Mode Verification | P1 | Low | All above |
| 4 | 4.2 Accessibility Audit | P1 | Low | All above |
| 4 | 4.3 Build & PR | P1 | Low | All above |

---

## Execution Order

```
Phase 1 (P1 - Must Have)
├── Task 1.1: KPI Stats Row
├── Task 1.2: Onboarding Checklist
└── Task 1.3: Integrate Components
    │
    ▼
Phase 2 (P2 - Polish)
├── Task 2.1: Microinteraction CSS
├── Task 2.2: Feature Card CTAs
└── Task 2.3: Staggered Animations
    │
    ▼
Phase 3 (P3 - Enhanced)
├── Task 3.1: Tooltip Component
├── Task 3.2: Add Tooltips
└── Task 3.3: Progressive Disclosure
    │
    ▼
Phase 4 (Verification)
├── Task 4.1: Dark Mode Check
├── Task 4.2: Accessibility Audit
└── Task 4.3: Build & PR
```

---

## Estimated Total Effort

| Priority | Tasks | Estimated Time |
|----------|-------|----------------|
| P1 | 3 tasks | ~2-3 hours |
| P2 | 3 tasks | ~2-3 hours |
| P3 | 3 tasks | ~2 hours |
| Testing | 3 tasks | ~1 hour |
| **Total** | **12 tasks** | **~7-9 hours** |
