# Tasks: Dashboard UX Improvements

**Feature ID**: 015-dashboard-ux-improvements
**Version**: v1.4
**Created**: 2025-01-16
**Updated**: 2025-01-16
**Branch**: `feat/dashboard-ux-improvements`

## Change History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2025-01-16 | Initial 12 tasks for Phases 1-4 |
| v1.1 | 2025-01-16 | Added Phase 5: Quick Wins (5 new tasks) |
| v1.2 | 2025-01-16 | Added Phase 6: Recent Activity Panel (2 new tasks) |
| v1.3 | 2025-01-16 | Added Phase 7: Interactive Onboarding Tour (2 new tasks) |
| v1.4 | 2025-01-16 | Added Phase 8: Customizable Dashboard Widgets (3 new tasks) |

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
**Priority**: P1 | **Effort**: Low | **Status**: [x] Completed (v1.0)

**Description**: Verify build passes and create PR.

**Acceptance Criteria**:
- [x] `npm run build` passes with no errors
- [x] No TypeScript errors
- [x] No ESLint errors
- [x] All changes committed
- [x] Pushed to `feat/dashboard-ux-improvements` branch
- [x] PR created with link to spec

---

## Phase 5: Quick Wins (v1.1 Addition)

### Task 5.1: Add Checklist Inline Action Buttons
**Priority**: P1 | **Effort**: Low | **Status**: [ ] Pending

**Description**: Add contextual action buttons to each checklist item (e.g., "Open Chat", "Connect Tools").

**Files**:
- MODIFY: `frontend/app/dashboard/components/OnboardingChecklist.tsx`

**Acceptance Criteria**:
- [ ] Each checklist step has an action button on the right side
- [ ] "Connect your database" → "View Schema" button
- [ ] "Ask your first AI question" → "Open Chat" button
- [ ] "Connect a tool" → "Connect Tools" button
- [ ] "Create a scheduled task" → "Create Task" button
- [ ] Buttons navigate to corresponding pages on click
- [ ] Buttons styled consistently (outline style, small size)
- [ ] Dark mode support

**Implementation Notes**:
```tsx
// Add to each step in the checklist
<div className="flex items-center justify-between">
  <div className="flex items-center space-x-3">
    {/* Existing checkbox and label */}
  </div>
  <button
    onClick={() => router.push(step.route)}
    className="text-xs px-3 py-1 rounded border border-emerald-300
               text-emerald-600 hover:bg-emerald-50 dark:border-emerald-700
               dark:text-emerald-400 dark:hover:bg-emerald-900/30 transition-colors"
  >
    {step.actionLabel}
  </button>
</div>
```

---

### Task 5.2: Implement Auto-collapse for Completed Checklist
**Priority**: P1 | **Effort**: Low | **Status**: [ ] Pending

**Description**: Auto-collapse the checklist to minimal state when all 4 steps are completed.

**Files**:
- MODIFY: `frontend/app/dashboard/components/OnboardingChecklist.tsx`

**Acceptance Criteria**:
- [ ] Checklist auto-collapses when `completedCount === 4`
- [ ] Collapsed state shows: "All set! ✓ You've completed setup"
- [ ] Expand button available to show full checklist
- [ ] Auto-collapse respects user's previous dismiss preference
- [ ] Smooth collapse/expand animation

**Implementation Notes**:
```tsx
const allCompleted = completedCount === 4;
const [isExpanded, setIsExpanded] = useState(!allCompleted);

// Show minimal view when all done
if (allCompleted && !isExpanded) {
  return (
    <div className="bg-emerald-50 dark:bg-emerald-900/30 rounded-xl p-4 flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <CheckCircle2 className="h-5 w-5 text-emerald-600" />
        <span className="font-medium text-emerald-700 dark:text-emerald-300">All set!</span>
        <span className="text-sm text-emerald-600 dark:text-emerald-400">You've completed setup</span>
      </div>
      <button onClick={() => setIsExpanded(true)} className="text-sm text-emerald-600">
        Show details
      </button>
    </div>
  );
}
```

---

### Task 5.3: Add Tools Quick Actions (Reconnect Button)
**Priority**: P1 | **Effort**: Low | **Status**: [ ] Pending

**Description**: Add "Reconnect" button to disconnected tools in ConnectToolsSection.

**Files**:
- MODIFY: `frontend/app/dashboard/components/ConnectToolsSection.tsx`

**Acceptance Criteria**:
- [ ] Disconnected tools (health check failed) show "Reconnect" button
- [ ] "Reconnect" navigates to `/dashboard/settings?connector={id}`
- [ ] Healthy tools show subtle settings icon on hover
- [ ] Button styled to match error state (red/orange theme)
- [ ] Dark mode support

**Implementation Notes**:
```tsx
// For disconnected connector
{!isHealthy && (
  <Link
    href={`/dashboard/settings?connector=${connector.id}`}
    className="text-xs px-2 py-1 rounded bg-red-100 text-red-600
               hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400
               dark:hover:bg-red-900/50 transition-colors"
  >
    Reconnect
  </Link>
)}
```

---

### Task 5.4: Add "Learn More" Link to Read-Only Banner
**Priority**: P1 | **Effort**: Low | **Status**: [ ] Pending

**Description**: Add a "Learn more" link to the Read-Only security banner.

**Files**:
- MODIFY: `frontend/app/dashboard/page.tsx`

**Acceptance Criteria**:
- [ ] Read-Only banner includes "Learn more" link after the text
- [ ] Link opens documentation about read-only mode (external link or modal)
- [ ] Link styled as subtle underlined text
- [ ] Opens in new tab if external
- [ ] Dark mode support

**Implementation Notes**:
```tsx
// In the Read-Only banner section
<p className="text-sm text-blue-800 dark:text-blue-300">
  <ShieldCheck className="inline h-4 w-4 mr-1" />
  Read-only connection - Your data is safe
  <a
    href="https://docs.example.com/read-only-mode"
    target="_blank"
    rel="noopener noreferrer"
    className="ml-2 underline hover:text-blue-600 dark:hover:text-blue-200"
  >
    Learn more
  </a>
</p>
```

---

### Task 5.5: Create Floating Help Button Component
**Priority**: P1 | **Effort**: Medium | **Status**: [ ] Pending

**Description**: Add a floating help button (FAB) with dropdown menu in bottom-right corner.

**Files**:
- CREATE: `frontend/app/dashboard/components/FloatingHelpButton.tsx`
- MODIFY: `frontend/app/dashboard/page.tsx` (import and add component)

**Acceptance Criteria**:
- [ ] Floating button fixed at bottom-right (z-50)
- [ ] Button shows "?" icon
- [ ] Click opens dropdown with 3 options:
  - "Documentation" → external docs link
  - "Contact Support" → support email or form
  - "Keyboard Shortcuts" → shows shortcuts modal (optional: just placeholder)
- [ ] Dropdown closes on click outside or Escape
- [ ] Smooth open/close animation
- [ ] Dark mode support
- [ ] Mobile responsive (smaller button on mobile)

**Implementation Notes**:
```tsx
// FloatingHelpButton.tsx
'use client';

import { useState, useRef, useEffect } from 'react';
import { HelpCircle, ExternalLink, Mail, Keyboard } from 'lucide-react';

export default function FloatingHelpButton() {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={ref} className="fixed bottom-6 right-6 z-50">
      {/* Dropdown */}
      {isOpen && (
        <div className="absolute bottom-14 right-0 w-48 bg-white dark:bg-gray-800
                        rounded-lg shadow-lg border border-gray-200 dark:border-gray-700
                        py-2 animate-fade-in-up">
          <a href="#" className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200
                                 hover:bg-gray-100 dark:hover:bg-gray-700">
            <ExternalLink className="h-4 w-4 mr-2" />
            Documentation
          </a>
          <a href="mailto:support@example.com" className="flex items-center px-4 py-2 text-sm
                                 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
            <Mail className="h-4 w-4 mr-2" />
            Contact Support
          </a>
          <button className="flex items-center w-full px-4 py-2 text-sm text-gray-700
                             dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
            <Keyboard className="h-4 w-4 mr-2" />
            Keyboard Shortcuts
          </button>
        </div>
      )}

      {/* FAB Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-12 h-12 rounded-full bg-emerald-600 text-white shadow-lg
                   hover:bg-emerald-700 hover:shadow-xl transition-all duration-200
                   flex items-center justify-center click-feedback"
        aria-label="Help menu"
      >
        <HelpCircle className="h-6 w-6" />
      </button>
    </div>
  );
}
```

---

## Task Summary

| Phase | Task | Priority | Effort | Status | Dependencies |
|-------|------|----------|--------|--------|--------------|
| 1 | 1.1 KPI Stats Row | P1 | Low | ✅ Done | None |
| 1 | 1.2 Onboarding Checklist | P1 | Medium | ✅ Done | None |
| 1 | 1.3 Integrate P1 Components | P1 | Low | ✅ Done | 1.1, 1.2 |
| 2 | 2.1 Microinteraction CSS | P2 | Low | ✅ Done | None |
| 2 | 2.2 Feature Card CTAs | P2 | Low | ✅ Done | 2.1 |
| 2 | 2.3 Staggered Animations | P2 | Medium | ✅ Done | 2.1 |
| 3 | 3.1 Tooltip Component | P3 | Low | ✅ Done | None |
| 3 | 3.2 Add Tooltips | P3 | Low | ✅ Done | 3.1 |
| 3 | 3.3 Progressive Disclosure | P3 | Medium | ✅ Done | None |
| 4 | 4.1 Dark Mode Verification | P1 | Low | ✅ Done | All above |
| 4 | 4.2 Accessibility Audit | P1 | Low | ✅ Done | All above |
| 4 | 4.3 Build & PR | P1 | Low | ✅ Done | All above |
| 5 | 5.1 Checklist Action Buttons | P1 | Low | ✅ Done | 1.2 |
| 5 | 5.2 Auto-collapse Checklist | P1 | Low | ✅ Done | 1.2 |
| 5 | 5.3 Tools Quick Actions | P1 | Low | ✅ Done | None |
| 5 | 5.4 Read-Only Learn More | P1 | Low | ✅ Done | None |
| 5 | 5.5 Floating Help Button | P1 | Medium | ✅ Done | None |
| 6 | 6.1 Recent Activity Panel | P1 | Medium | ✅ Done | None |
| 6 | 6.2 Integrate Activity Panel | P1 | Low | ✅ Done | 6.1 |
| 7 | 7.1 Onboarding Tour Component | P1 | Medium | ✅ Done | None |
| 7 | 7.2 Integrate Tour + Replay | P1 | Low | ✅ Done | 7.1 |
| **8** | **8.1 Widget Config Hook** | **P2** | **Medium** | ⏳ Pending | None |
| **8** | **8.2 Customize Dashboard Modal** | **P2** | **Medium** | ⏳ Pending | 8.1 |
| **8** | **8.3 Integrate Widget System** | **P2** | **Low** | ⏳ Pending | 8.1, 8.2 |

---

## Phase 6: Recent Activity Panel (v1.2 Addition - COMPLETED)

### Task 6.1: Create RecentActivityPanel Component
**Priority**: P1 | **Effort**: Medium | **Status**: [x] Done

**Description**: Create a component that displays recent user activities aggregated from existing API data.

**Files**:
- CREATE: `frontend/app/dashboard/components/RecentActivityPanel.tsx`

**Acceptance Criteria**:
- [ ] Component fetches data from existing APIs (getScheduledTasks, getConnectors)
- [ ] Shows last 5-10 activities sorted by timestamp (most recent first)
- [ ] Each activity shows: icon, description, relative time ("2 hours ago")
- [ ] Activities color-coded: success (green), error (red), info (blue)
- [ ] Loading skeleton while fetching
- [ ] Empty state when no activities
- [ ] Click activity navigates to relevant page
- [ ] Dark mode support

**Activity Types**:
| Type | Source | Icon | Color |
|------|--------|------|-------|
| Task Created | ScheduledTask.created_at | CalendarPlus | Blue |
| Task Completed | ScheduledTask.executed_at + status=completed | CheckCircle | Green |
| Task Failed | ScheduledTask.executed_at + status=failed | XCircle | Red |
| Connector Added | Connector.created_at | Plug | Blue |
| Connector Verified | Connector.last_verified_at | CheckCircle | Green |

**Implementation Notes**:
```typescript
interface Activity {
  id: string;
  type: 'task_created' | 'task_completed' | 'task_failed' | 'connector_added' | 'connector_verified';
  title: string;
  description?: string;
  timestamp: Date;
  route?: string;
}

// Aggregate from existing APIs
const activities: Activity[] = [
  ...tasksToActivities(scheduledTasks),
  ...connectorsToActivities(connectors),
].sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime()).slice(0, 10);
```

---

### Task 6.2: Integrate RecentActivityPanel into Dashboard
**Priority**: P1 | **Effort**: Low | **Status**: [x] Done

**Description**: Add RecentActivityPanel to the dashboard page below KPI stats.

**Files**:
- MODIFY: `frontend/app/dashboard/page.tsx`

**Acceptance Criteria**:
- [ ] Panel appears below KPI stats row for schema_query_only users
- [ ] Data passed from existing state/API calls
- [ ] No new API calls added (reuse existing data)
- [ ] Layout balanced with other components

**Integration Point**:
```tsx
{/* After KPIStatsRow */}
<RecentActivityPanel
  scheduledTasks={tasks}
  connectors={connectors}
  className="mt-6"
/>
```

---

## Phase 7: Interactive Onboarding Tour (v1.3 Addition)

### Task 7.1: Create OnboardingTour Component
**Priority**: P1 | **Effort**: Medium | **Status**: [x] Done

**Description**: Create a custom onboarding tour component with spotlight and tooltip functionality.

**Files**:
- CREATE: `frontend/app/dashboard/components/OnboardingTour.tsx`

**Acceptance Criteria**:
- [ ] Tour starts automatically for new users (after 1s delay)
- [ ] Spotlight overlay highlights target element
- [ ] Tooltip shows title, description, step progress
- [ ] Navigation: Back, Next, Skip, Finish buttons
- [ ] Skip shows confirmation dialog
- [ ] Completion sets localStorage flag
- [ ] Smooth animations between steps
- [ ] Dark mode support
- [ ] Keyboard accessible (Escape to close)

**Tour Steps Configuration**:
```typescript
const TOUR_STEPS = [
  {
    target: '[data-tour="ai-agent-card"]',
    title: 'AI Agent',
    description: 'Start here! Ask questions about your data in natural language.',
    position: 'right',
  },
  {
    target: '[data-tour="kpi-stats"]',
    title: 'Quick Stats',
    description: 'See an overview of your connected tables and tools.',
    position: 'bottom',
  },
  {
    target: '[data-tour="connected-tools"]',
    title: 'Connected Tools',
    description: 'Extend AI capabilities by connecting Gmail, Slack, and more.',
    position: 'top',
  },
  {
    target: '[data-tour="scheduler-card"]',
    title: 'Scheduler',
    description: 'Automate recurring queries on a schedule.',
    position: 'left',
  },
  {
    target: '[data-tour="help-button"]',
    title: 'Need Help?',
    description: 'Find documentation, support, and keyboard shortcuts here.',
    position: 'top',
  },
];
```

**localStorage Keys**:
- `ims_onboarding_tour_completed`: 'true' | null
- `ims_onboarding_tour_skipped`: 'true' | null

---

### Task 7.2: Integrate Tour and Add Replay Option
**Priority**: P1 | **Effort**: Low | **Status**: [x] Done

**Description**: Add tour component to dashboard and replay option in help menu.

**Files**:
- MODIFY: `frontend/app/dashboard/page.tsx` (add data-tour attributes, import tour)
- MODIFY: `frontend/app/dashboard/components/FloatingHelpButton.tsx` (add replay option)

**Acceptance Criteria**:
- [ ] data-tour attributes added to target elements
- [ ] Tour component rendered in dashboard
- [ ] Help menu shows "Replay Tour" option
- [ ] Clicking "Replay Tour" clears flags and starts tour
- [ ] Tour only shows for schema_query_only users

**Integration Points**:
```tsx
// In dashboard page.tsx - add data-tour attributes
<div data-tour="ai-agent-card" className="...">
<div data-tour="kpi-stats" className="...">
<div data-tour="connected-tools" className="...">
<div data-tour="scheduler-card" className="...">
<div data-tour="help-button" className="...">

// Import and render tour
<OnboardingTour onComplete={() => setTourCompleted(true)} />

// In FloatingHelpButton.tsx - add replay option
<button onClick={handleReplayTour}>
  <Play className="h-4 w-4 mr-2" />
  Replay Tour
</button>
```

---

## Phase 8: Customizable Dashboard Widgets (v1.4 Addition)

### Task 8.1: Create Widget Configuration Hook
**Priority**: P2 | **Effort**: Medium | **Status**: [x] Done

**Description**: Create a custom React hook to manage widget visibility and order with localStorage persistence.

**Files**:
- CREATE: `frontend/app/dashboard/hooks/useWidgetConfig.ts`

**Acceptance Criteria**:
- [ ] Hook manages widget visibility states (show/hide)
- [ ] Hook manages widget order (array of widget IDs)
- [ ] Configuration persisted to localStorage (`ims_dashboard_widget_config`)
- [ ] Provides `toggleWidget()`, `reorderWidgets()`, `resetToDefault()` functions
- [ ] Loads saved config on mount, falls back to defaults if none
- [ ] TypeScript types for widget config

**Widget IDs**:
```typescript
type WidgetId = 'checklist' | 'kpiStats' | 'recentActivity' | 'featureCards' | 'connectedTools';

interface WidgetConfig {
  visibility: Record<WidgetId, boolean>;
  order: WidgetId[];
}

const DEFAULT_CONFIG: WidgetConfig = {
  visibility: {
    checklist: true,
    kpiStats: true,
    recentActivity: true,
    featureCards: true, // Always true, not toggleable
    connectedTools: true,
  },
  order: ['checklist', 'kpiStats', 'recentActivity', 'featureCards', 'connectedTools'],
};
```

**localStorage Key**: `ims_dashboard_widget_config`

---

### Task 8.2: Create Customize Dashboard Modal
**Priority**: P2 | **Effort**: Medium | **Status**: [x] Done

**Description**: Create a modal component for customizing dashboard widgets with toggles and drag-to-reorder.

**Files**:
- CREATE: `frontend/app/dashboard/components/CustomizeDashboardModal.tsx`

**Acceptance Criteria**:
- [ ] Modal opens from settings icon in dashboard
- [ ] Lists all widgets with toggle switches
- [ ] Feature Cards toggle is disabled (always visible)
- [ ] Widgets are draggable for reordering (HTML5 drag API)
- [ ] Drag handle icon visible on each widget row
- [ ] Visual feedback during drag (ghost, drop indicator)
- [ ] "Reset to Default" button at bottom
- [ ] Changes apply immediately (no save button needed)
- [ ] Dark mode support
- [ ] Accessible (keyboard navigable, ARIA labels)

**Implementation Notes**:
```tsx
// Draggable widget row
<div
  draggable
  onDragStart={(e) => handleDragStart(e, widgetId)}
  onDragOver={(e) => handleDragOver(e, widgetId)}
  onDrop={(e) => handleDrop(e, widgetId)}
  className="flex items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
>
  <GripVertical className="h-4 w-4 text-gray-400 mr-3 cursor-grab" />
  <span className="flex-1">{widget.label}</span>
  <Switch checked={visibility[widgetId]} onChange={() => toggle(widgetId)} />
</div>
```

---

### Task 8.3: Integrate Widget System into Dashboard
**Priority**: P2 | **Effort**: Low | **Status**: [x] Done

**Description**: Add settings icon to dashboard header and integrate widget rendering based on configuration.

**Files**:
- MODIFY: `frontend/app/dashboard/page.tsx`

**Acceptance Criteria**:
- [ ] Settings/gear icon added to dashboard header (near title)
- [ ] Clicking icon opens CustomizeDashboardModal
- [ ] Widgets render in order specified by config
- [ ] Hidden widgets are not rendered
- [ ] Feature Cards always rendered regardless of config
- [ ] Tour still works with reordered widgets

**Integration Points**:
```tsx
// In dashboard page
const { config, toggleWidget, reorderWidgets, resetConfig } = useWidgetConfig();

// Render widgets in order
{config.order.map((widgetId) => {
  if (!config.visibility[widgetId]) return null;

  switch (widgetId) {
    case 'checklist':
      return <OnboardingChecklist key={widgetId} ... />;
    case 'kpiStats':
      return <KPIStatsRow key={widgetId} ... />;
    case 'recentActivity':
      return <RecentActivityPanel key={widgetId} ... />;
    case 'featureCards':
      return <FeatureCardsGrid key={widgetId} ... />;
    case 'connectedTools':
      return <ConnectToolsSection key={widgetId} ... />;
  }
})}
```

---

## Execution Order

```
Phase 1-4 (v1.0 - COMPLETED ✅)
├── Task 1.1: KPI Stats Row ✅
├── Task 1.2: Onboarding Checklist ✅
├── Task 1.3: Integrate Components ✅
├── Task 2.1: Microinteraction CSS ✅
├── Task 2.2: Feature Card CTAs ✅
├── Task 2.3: Staggered Animations ✅
├── Task 3.1: Tooltip Component ✅
├── Task 3.2: Add Tooltips ✅
├── Task 3.3: Progressive Disclosure ✅
├── Task 4.1: Dark Mode Check ✅
├── Task 4.2: Accessibility Audit ✅
└── Task 4.3: Build & PR ✅
    │
    ▼
Phase 5 (v1.1 - Quick Wins - COMPLETED ✅)
├── Task 5.1: Checklist Action Buttons ✅
├── Task 5.2: Auto-collapse Checklist ✅
├── Task 5.3: Tools Quick Actions ✅
├── Task 5.4: Read-Only Learn More ✅
└── Task 5.5: Floating Help Button ✅
    │
    ▼
Phase 6 (v1.2 - Recent Activity - COMPLETED ✅)
├── Task 6.1: Recent Activity Panel ✅
└── Task 6.2: Integrate Activity Panel ✅
    │
    ▼
Phase 7 (v1.3 - Onboarding Tour - COMPLETED ✅)
├── Task 7.1: Onboarding Tour Component ✅
└── Task 7.2: Integrate Tour + Replay ✅
    │
    ▼
Phase 8 (v1.4 - Widget Customization - COMPLETED ✅)
├── Task 8.1: Widget Config Hook ✅
├── Task 8.2: Customize Dashboard Modal ✅
└── Task 8.3: Integrate Widget System ✅
    │
    ▼
Build Verification & PR Update
```

---

## Estimated Total Effort

### v1.0 (Completed)

| Priority | Tasks | Status |
|----------|-------|--------|
| P1 | 3 tasks | ✅ Completed |
| P2 | 3 tasks | ✅ Completed |
| P3 | 3 tasks | ✅ Completed |
| Testing | 3 tasks | ✅ Completed |
| **Total** | **12 tasks** | **✅ Done** |

### v1.1 (Quick Wins - Pending)

| Task | Effort | Dependencies |
|------|--------|--------------|
| 5.1 Checklist Action Buttons | Low (~20 min) | None |
| 5.2 Auto-collapse Checklist | Low (~20 min) | None |
| 5.3 Tools Quick Actions | Low (~15 min) | None |
| 5.4 Read-Only Learn More | Low (~10 min) | None |
| 5.5 Floating Help Button | Medium (~30 min) | None |
| **Total Phase 5** | **~1.5-2 hours** | |
