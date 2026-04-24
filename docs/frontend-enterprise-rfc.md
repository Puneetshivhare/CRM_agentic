# Frontend Enterprise RFC

## Summary
- This takeover standardizes the frontend around a single auth/session model and a shared Clay-style data workspace.
- The first implementation phase focuses on authentication, shell consistency, shared data-grid primitives, and the canonical `Prospects` and `Companies` pages.
- Backend APIs stay unchanged in this phase. Frontend architecture is the primary modernization target.

## Current-State Audit
- Auth was previously checked page-by-page using `localStorage` reads, ad-hoc redirects, and duplicated fetch logic.
- Prospects and Companies had separate table implementations with similar search, pagination, and mutation patterns.
- Mutation feedback relied on `alert()`, page reloads, or inconsistent inline handling.
- The dashboard leaned decorative rather than operational, which made it a poor standard for enterprise daily use.
- UI copy and styling had encoding artifacts and inconsistent component patterns.

## Enterprise-Readiness Gaps
- No centralized session bootstrap from `/api/auth/me`.
- No single protected app-shell boundary for dashboard routes.
- No shared table primitive for sorting, selection, toolbar actions, sticky headers, and consistent empty/loading/error states.
- No standard page-header, feedback-banner, button, input, or panel system to guide future page builds.
- Too much logic directly embedded in individual pages, increasing handoff conflict risk for parallel agents.

## Target UX Principles
- Dense, operational, and quiet by default. The UI should feel like a serious system of record, not a marketing surface.
- Tables are the primary workspace. Search, selection, sorting, row actions, and pagination must behave consistently across entity pages.
- Auth state should be invisible when healthy and graceful when broken.
- Inline feedback should replace intrusive browser alerts and page reloads.
- New pages should inherit standardized building blocks instead of inventing one-off patterns.

## Standard Page/Layout Rules
- Use the protected dashboard shell for all authenticated pages.
- Use shared `PageHeader`, `Panel`, `FeedbackBanner`, `Button`, `Input`, and `StatusBadge` primitives.
- Use the shared data-grid shell for list pages. Page-specific behavior should be expressed through column config and mutation handlers.
- Use centralized API access from `src/lib/api.ts`.
- Favor local state refresh after mutations. Avoid full page reloads.

## Workstreams
### 1. Auth / Session Shell
- Own `src/contexts`, `src/components/auth`, app root providers, and auth-aware route entrypoints.
- Keep JWT bearer-token transport for now.
- Future extension: optional migration to cookie-based auth once backend is ready.

### 2. Design System Primitives
- Own shared UI components under `src/components/ui`.
- Keep tokens and layout rules in `src/app/globals.css`.
- Future extension: move to more formal component docs or a Storybook-like preview system.

### 3. Shared Data-Grid Foundation
- Own `src/components/data-grid` and the common table interaction model.
- Future extension: inline editing, saved views, keyboard navigation, and persisted column preferences.

### 4. Prospects Workspace
- Own prospect list columns, mutation flows, exports, enrichment triggers, and prospect-specific row actions.
- Should not edit shared auth or data-grid abstractions unless needed by multiple pages.

### 5. Companies Workspace
- Own company list columns, monitoring actions, account-specific filters, and company creation flow.
- Should reuse the shared grid and shared feedback patterns without duplicating them.

### 6. Dashboard Simplification
- Keep the dashboard as a thin operational summary, not the place where unique UI patterns are invented.
- Future work can add richer analytics once the entity workspaces are stable.

## Phased Implementation Order
1. Centralize auth/session and guard the dashboard shell.
2. Establish UI primitives and shared tokens.
3. Implement shared data-grid shell and toolbar/footer patterns.
4. Migrate `Prospects` and `Companies` onto the shared grid.
5. Simplify dashboard and align login/register with the backend auth contract.
6. Expand the same pattern to campaigns, enrichment, rules, analytics, and settings.

## Parallel-Agent Ownership Guidance
- Agents working on auth should avoid editing table pages unless a shared auth contract forces it.
- Agents working on grid primitives should avoid page-specific business logic.
- Agents working on `Prospects` and `Companies` should treat shared UI and shared grid layers as external dependencies and extend them only when the change benefits multiple pages.
- Dashboard work should remain low-conflict by consuming shared components rather than redefining them.

## Next Recommended Follow-Ups
- Add stronger form validation and typed form helpers.
- Add toast infrastructure for non-blocking mutation feedback across pages.
- Add reusable query hooks or a dedicated data-fetching library once list pages expand further.
- Extend the shared grid to campaigns and enrichment execution history.
