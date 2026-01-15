# Feature Specification: Dashboard UX Improvements

**Feature ID**: 015-dashboard-ux-improvements
**Feature Branch**: `feat/dashboard-ux-improvements`
**Created**: 2025-01-16
**Version**: v1.0
**Status**: Draft
**Type**: UI/UX Enhancement (No Backend Changes)

## Executive Summary

Enhance the existing dashboard UI/UX to improve user engagement, feature adoption, and overall user experience. Based on UX research and industry best practices for 2025, this specification outlines improvements including onboarding checklists, KPI summary widgets, interactive card CTAs, microinteractions, progressive disclosure, and contextual tooltips.

**Key Constraint**: All existing business logic remains unchanged. This is purely a presentation layer enhancement.

---

## User Scenarios & Testing

### User Story 1 - New User: Guided Onboarding (Priority: P1)

As a new user who just connected my database, I want to see a clear checklist of next steps so that I know exactly what to do to get value from the platform.

**Why this priority**: P1 - Research shows 80% users abandon apps because they don't know how to use them. Onboarding checklists increase feature adoption by 42%.

**Independent Test**: Can be tested by logging in as a new user with `schema_query_only` connection and verifying the checklist appears with accurate completion states.

**Acceptance Scenarios**:

1. **Given** I'm a new user with `schema_query_only` connection, **When** I land on the dashboard, **Then** I see an onboarding checklist showing my progress (e.g., "2 of 4 steps completed")
2. **Given** I have connected my database but haven't used AI Agent, **When** I view the checklist, **Then** "Connect Database" shows as complete (checkmark) and "Ask your first AI question" shows as pending
3. **Given** I click on a pending checklist item, **When** I click, **Then** I'm navigated to the relevant feature (e.g., clicking "Ask AI question" takes me to Schema Agent)
4. **Given** I complete all checklist items, **When** I return to dashboard, **Then** the checklist shows "All set!" or collapses to a minimal congratulatory state
5. **Given** I want to dismiss the checklist, **When** I click "Dismiss" or "Hide", **Then** the checklist collapses but can be expanded again via a small icon

---

### User Story 2 - Returning User: Quick Stats Overview (Priority: P1)

As a returning user, I want to see key metrics at a glance so that I immediately understand the state of my data and recent activity.

**Why this priority**: P1 - KPI widgets provide instant value visibility. Users should see value within 3 seconds of landing.

**Independent Test**: Can be tested by logging in with an active connection and verifying stats row shows accurate counts from existing data.

**Acceptance Scenarios**:

1. **Given** I have a `schema_query_only` connection with discovered schema, **When** I land on dashboard, **Then** I see a stats row showing: Tables count, Tools connected count
2. **Given** my schema has 15 tables, **When** I view the stats row, **Then** "Tables" widget shows "15" with the label "Tables Discovered"
3. **Given** I have 3 MCP connectors connected, **When** I view the stats row, **Then** "Tools Connected" widget shows "3"
4. **Given** data is loading, **When** stats are being fetched, **Then** each stat widget shows a subtle skeleton/shimmer animation
5. **Given** I click on a stat widget (e.g., "Tables"), **When** I click, **Then** I'm navigated to the relevant detail page (Schema Connect page)

---

### User Story 3 - User: Clear Feature Card Actions (Priority: P2)

As a user viewing feature cards, I want clear action buttons on each card so that I know exactly what I can do and where to click.

**Why this priority**: P2 - Cards without explicit CTAs reduce click-through rates. Users should see actionable buttons, not just informational text.

**Independent Test**: Can be tested by viewing the dashboard and verifying each feature card has a visible action button with appropriate label.

**Acceptance Scenarios**:

1. **Given** I'm viewing the AI Agent card, **When** I look at the card, **Then** I see a prominent "Open Chat" button (not just the card being clickable)
2. **Given** I'm viewing the Scheduler card, **When** I look at the card, **Then** I see a "View Tasks" or "Create Task" button
3. **Given** a feature requires schema to be ready first, **When** schema is not ready, **Then** the button shows "Setup Required" in a disabled/muted state with tooltip explaining why
4. **Given** I hover over a card, **When** hovering, **Then** the card shows a subtle lift effect (shadow increase) and the button becomes more prominent
5. **Given** the AI Agent card is the primary action, **When** I view all cards, **Then** the AI Agent card has a visually distinct style (primary color border/background) to indicate it's the main feature

---

### User Story 4 - User: Responsive Feedback (Priority: P2)

As a user interacting with the dashboard, I want immediate visual feedback on my actions so that I feel confident the system is responding.

**Why this priority**: P2 - Microinteractions make dashboards feel polished and professional. They reassure users that actions were registered.

**Independent Test**: Can be tested by clicking buttons and verifying visual feedback (hover states, click animations, loading states).

**Acceptance Scenarios**:

1. **Given** I hover over a clickable card, **When** my mouse enters the card area, **Then** the card subtly lifts (translateY -2px) with increased shadow
2. **Given** I click a button, **When** I press down, **Then** the button shows a brief scale-down effect (0.98) before returning to normal
3. **Given** I click "Manage All Tools", **When** I click, **Then** a brief ripple or highlight effect confirms my click before navigation
4. **Given** data is loading in Connected Tools section, **When** loading, **Then** individual tool cards show staggered fade-in animation (not all at once)
5. **Given** a health check is running on a connector, **When** checking, **Then** the status icon shows a subtle pulse animation

---

### User Story 5 - New User: Focused Initial Experience (Priority: P3)

As a new user, I want to focus on the most important feature first so that I'm not overwhelmed by too many options.

**Why this priority**: P3 - Progressive disclosure reduces cognitive load. New users should focus on 1-3 key actions initially.

**Independent Test**: Can be tested by logging in as a new user and verifying the AI Agent card is visually emphasized while secondary features are de-emphasized.

**Acceptance Scenarios**:

1. **Given** I'm a new user (no queries made yet), **When** I view the feature cards, **Then** the AI Agent card is visually prominent (highlighted border, larger, or positioned first)
2. **Given** secondary features exist (Scheduler, Dev Tools), **When** viewing as new user, **Then** these cards appear slightly muted or with a "Coming up next" indicator
3. **Given** I've used the AI Agent at least once, **When** I return to dashboard, **Then** all cards show with equal visual weight (progressive unlock)
4. **Given** I hover over a muted secondary card, **When** hovering, **Then** it becomes fully visible with a tooltip: "Complete AI Agent setup first" or similar guidance

---

### User Story 6 - User: Contextual Help (Priority: P3)

As a user, I want contextual help tooltips so that I can understand features without leaving the dashboard.

**Why this priority**: P3 - In-context help reduces friction. Users shouldn't need to navigate to docs for basic understanding.

**Independent Test**: Can be tested by hovering over info icons and verifying tooltips appear with helpful content.

**Acceptance Scenarios**:

1. **Given** the Schema Status indicator shows "Ready", **When** I hover over the info icon next to it, **Then** a tooltip explains: "Your database schema was discovered. You can now query your data with AI."
2. **Given** a tool shows as "Disconnected", **When** I hover over the status, **Then** a tooltip explains: "This connector lost connection. Click 'Reconnect' to restore."
3. **Given** the Read-Only banner is displayed, **When** I hover over the shield icon, **Then** a tooltip explains: "Read-only mode means we can only SELECT data, never modify your database."
4. **Given** I see the Connected Tools section header, **When** I hover over the question mark icon, **Then** a tooltip explains: "Tools extend AI capabilities. Connect Gmail to search emails, Analytics to track usage."

---

## Requirements

### Functional Requirements

#### P1 - Onboarding Checklist
- **FR-001**: Dashboard MUST display an onboarding checklist for users with `schema_query_only` connection type
- **FR-002**: Checklist MUST show completion state for each step based on existing connection/usage data
- **FR-003**: Checklist items MUST be clickable and navigate to the relevant feature page
- **FR-004**: Checklist MUST be dismissible/collapsible with state persisted in localStorage
- **FR-005**: Checklist completion state MUST be derived from existing data (no new API calls needed):
  - "Connect Database" = `connectionStatus.schema_status === 'ready'`
  - "Ask AI Question" = localStorage flag or future: query count > 0
  - "Connect a Tool" = `connectors.length > 0`
  - "Create Scheduled Task" = localStorage flag or future: task count > 0

#### P1 - KPI Summary Stats
- **FR-006**: Dashboard MUST display a stats summary row above feature cards
- **FR-007**: Stats row MUST show: Tables Discovered (from schema), Tools Connected (from connectors)
- **FR-008**: Each stat widget MUST be clickable and navigate to its detail page
- **FR-009**: Stats MUST show loading skeleton while data is being fetched
- **FR-010**: Stats data MUST be derived from existing API responses (no new endpoints)

#### P2 - Card CTAs
- **FR-011**: Each feature card MUST have an explicit action button with clear label
- **FR-012**: AI Agent card button: "Open Chat" (primary style)
- **FR-013**: Scheduler card button: "View Tasks" or "Create Task"
- **FR-014**: Connection card button: "View Schema"
- **FR-015**: Developer Tools card button: "Manage Agents"
- **FR-016**: Disabled state buttons MUST show tooltip explaining why (e.g., "Discover schema first")
- **FR-017**: AI Agent card MUST have visual distinction (primary color border) as the main feature

#### P2 - Microinteractions
- **FR-018**: Cards MUST have hover lift effect (translateY: -2px, shadow increase)
- **FR-019**: Buttons MUST have click feedback (scale: 0.98 briefly)
- **FR-020**: Loading states MUST use skeleton/shimmer animations instead of spinners where appropriate
- **FR-021**: Tool cards in Connected Tools MUST animate in with staggered fade effect
- **FR-022**: Health check status MUST show pulse animation while checking

#### P3 - Progressive Disclosure
- **FR-023**: For new users (no AI queries yet), AI Agent card SHOULD be visually emphasized
- **FR-024**: Secondary features MAY appear slightly muted for new users with unlock hint
- **FR-025**: After first AI query, all cards SHOULD show with equal visual weight

#### P3 - Contextual Tooltips
- **FR-026**: Schema Status indicator MUST have info icon with explanatory tooltip
- **FR-027**: Tool connection status MUST have tooltip explaining current state
- **FR-028**: Read-Only banner MUST have tooltip explaining security implications
- **FR-029**: Connected Tools section header MAY have tooltip explaining purpose

### Non-Functional Requirements

- **NFR-001**: All animations MUST respect `prefers-reduced-motion` media query
- **NFR-002**: Tooltips MUST be accessible via keyboard (Tab + focus)
- **NFR-003**: All new UI elements MUST support dark mode
- **NFR-004**: Page load time MUST NOT increase by more than 100ms due to these changes
- **NFR-005**: No new API endpoints required - all data derived from existing responses

---

## Technical Approach

### Components to Create

```
frontend/app/dashboard/components/
├── OnboardingChecklist.tsx      # P1 - New component
├── KPIStatsRow.tsx              # P1 - New component
├── FeatureCard.tsx              # P2 - Refactored existing card pattern
├── AnimatedCard.tsx             # P2 - Wrapper for microinteractions
├── Tooltip.tsx                  # P3 - Reusable tooltip (or use shadcn)
└── ConnectToolsSection.tsx      # Existing - minor updates
```

### Data Sources (No New APIs)

| Data Point | Source | Existing? |
|------------|--------|-----------|
| Tables count | `connectionStatus` or schema discovery response | Yes |
| Tools connected | `connectors.length` from `getConnectors()` | Yes |
| Schema status | `connectionStatus.schema_status` | Yes |
| MCP status | `connectionStatus.mcp_status` | Yes |
| Connector health | `checkConnectorHealth()` | Yes |

### State Management

- Onboarding checklist completion: Derived from existing state + localStorage for non-API items
- Dismissed state: localStorage (`dashboard_checklist_dismissed`)
- No new React context or global state required

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: New users can identify their next action within 5 seconds of landing (via checklist)
- **SC-002**: Users can see key stats (tables, tools) without scrolling on desktop
- **SC-003**: Feature card click-through rate increases (measurable via analytics if added)
- **SC-004**: Time to first AI query decreases for new users (guided by checklist)
- **SC-005**: All animations complete within 300ms for smooth feel
- **SC-006**: Zero accessibility violations on new components (axe-core audit)
- **SC-007**: Dark mode fully functional on all new components

---

## Visual Reference

### Proposed Layout (schema_query_only user)

```
+------------------------------------------------------------------+
| HEADER: StoreLite | User | Theme Toggle | Logout                  |
+------------------------------------------------------------------+
|                                                                  |
| [Onboarding Checklist - Collapsible]                            |
| +--------------------------------------------------------------+ |
| | Get Started (2/4 complete)                          [Dismiss] | |
| | [x] Connect your database                                     | |
| | [ ] Ask your first AI question  -----> Click to go            | |
| | [x] Connect a tool (Gmail, etc.)                              | |
| | [ ] Create a scheduled task     -----> Click to go            | |
| +--------------------------------------------------------------+ |
|                                                                  |
| [KPI Stats Row]                                                  |
| +----------------+  +-------------------+  +------------------+  |
| | 12             |  | 3                 |  | Ready            |  |
| | Tables         |  | Tools Connected   |  | Schema Status    |  |
| +----------------+  +-------------------+  +------------------+  |
|                                                                  |
| [Feature Cards - 4 columns]                                      |
| +-------------+ +-------------+ +-------------+ +-------------+  |
| | AI Agent    | | Scheduler   | | Connection  | | Dev Tools   |  |
| | [icon]      | | [icon]      | | [icon]      | | [icon]      |  |
| | Ask questions| Schedule tasks| View schema  | | Publish agents|
| |             | |             | |             | |             |  |
| | [Open Chat] | | [View Tasks]| | [View]      | | [Manage]    |  |
| +-------------+ +-------------+ +-------------+ +-------------+  |
|                                                                  |
| [Connected Tools Section] - Existing with minor updates          |
|                                                                  |
| [Read-Only Banner with tooltip]                                  |
+------------------------------------------------------------------+
```

---

## Implementation Priority Order

| Phase | Component | Effort | Files Changed |
|-------|-----------|--------|---------------|
| **Phase 1** | KPI Stats Row | Low | `page.tsx`, new `KPIStatsRow.tsx` |
| **Phase 1** | Onboarding Checklist | Medium | `page.tsx`, new `OnboardingChecklist.tsx` |
| **Phase 2** | Card CTAs & Styling | Low | `page.tsx` (inline changes) |
| **Phase 2** | Microinteractions | Medium | CSS/Tailwind utilities, card wrappers |
| **Phase 3** | Progressive Disclosure | Medium | `page.tsx`, conditional styling |
| **Phase 3** | Contextual Tooltips | Low | Add Tooltip component or shadcn |

---

## Out of Scope

- Backend API changes
- New database tables/columns
- Authentication/authorization changes
- Analytics tracking implementation (can be added later)
- Mobile-specific optimizations
- A/B testing infrastructure

---

## Dependencies

- Existing `connectionStatus` from `useAuth()` hook
- Existing `getConnectors()` and `getAllTools()` APIs
- Existing Tailwind CSS and dark mode setup
- Optional: shadcn/ui Tooltip component (or create custom)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Animation jank on low-end devices | Low | Medium | Use CSS transforms (GPU accelerated), respect reduced-motion |
| Tooltip accessibility issues | Low | High | Use semantic HTML, aria-describedby, keyboard navigation |
| localStorage quota exceeded | Very Low | Low | Store minimal data (booleans only) |
| Dark mode contrast issues | Medium | Medium | Test all components in both themes before merge |

---

## References

- [Dashboard UX Best Practices 2025 - Medium](https://medium.com/@allclonescript/20-best-dashboard-ui-ux-design-principles-you-need-in-2025-30b661f2f795)
- [SaaS Onboarding Patterns - UXCam](https://uxcam.com/blog/saas-onboarding-best-practices/)
- [Card UI Design Best Practices - Eleken](https://www.eleken.co/blog-posts/card-ui-examples-and-best-practices-for-product-owners)
- [Microinteractions in Dashboard Design - Fuselab](https://fuselabcreative.com/top-dashboard-design-trends-2025/)
