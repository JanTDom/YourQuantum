---
name: yq-product-engineering
description: >-
  Use this skill when building or modifying the YourQuantum frontend or backend
  product: problem intake UI, IR review and approval flow, result presentation,
  API routes, authentication, or deployment. Activate when implementing
  user-facing features or server-side application code. This skill keeps the
  product focused on the problem and result, not on circuit diagrams or
  quantum mechanics education. Every user-facing path must be verified in a
  real browser before being declared done.
---

# yq-product-engineering — Product Frontend and Backend

## Input

- Feature specification (from `docs/BUILD_SPEC.md` or a specific task).
- Current architecture (from `docs/ARCHITECTURE.md`).
- Capability status (from `docs/CAPABILITIES.md`).

## Procedure

### 1. Read Product Definition

Read `docs/PRODUCT.md` before writing any user-facing code.
The product is problem-centric: users see their problem and result.

### 2. Frontend Principles

**Problem-first UI:**
- The primary screen is the problem intake form and the result display.
- Circuit diagrams, qubit counts, and Hamiltonian matrices are hidden by default.
  They may be available in a "Technical details" expandable — never the default view.

**Three mandatory UI states (always implement all three):**
- Loading: progress indicator with estimated time if available.
- Empty / waiting: clear next action for the user.
- Error: human-readable message + specific next step + ability to retry.

**Accessibility (WCAG 2.2 AA baseline):**
- Full keyboard navigation.
- Visible `:focus-visible` ring on all interactive elements.
- Semantic HTML5 (`<main>`, `<nav>`, `<dialog>`, `<button>`, etc.).
- ARIA labels on all icon-only controls.
- `prefers-reduced-motion` respected.

**Verification verdict always visible:**
- Every result card shows the verification verdict (PASS / FAIL / PARTIAL).
- The limitations list is always visible, not hidden behind a "details" toggle.
- Do not merge PARTIAL into a generic "success" state.

### 3. Backend Principles

**Transport layer (API):**
- All routes require authentication.
- All request bodies validated with Zod/Pydantic before reaching handlers.
- Rate limiting enforced at the transport layer.
- No business logic in route handlers.

**Application layer (use-cases):**
- Each use-case is a pure function of validated input → result.
- Use-cases do not access the database directly — they use repository interfaces.
- All use-cases return typed result objects (not raw HTTP responses).

**Domain layer:**
- Domain objects are immutable.
- Solver calls go through the capability registry (not hardcoded).
- The Verifier is always called before a result is returned.

**Infrastructure layer:**
- Database migrations are versioned and deterministic.
- Queue jobs are idempotent.
- All external API calls have timeouts.

### 4. Full Browser Path Verification

For every user-facing feature, verify the complete path in a real browser:

1. Start from the entry point (URL or navigation action).
2. Exercise all three UI states (loading, empty/error, success).
3. Verify keyboard navigation through the entire flow.
4. Confirm the verification verdict is displayed.
5. Record the test in `docs/memory/CURRENT_STATE.md`.

A feature is NOT done until this verification is recorded.

### 5. Performance

- No blocking operations on the main thread.
- Solver jobs run in worker processes, never in the API request handler.
- Long-running jobs report progress via SSE or polling endpoint.
- Bundle size budget: defined in BUILD_SPEC when available.

## Required Output

- Implemented, tested, and browser-verified feature.
- Updated `docs/CAPABILITIES.md` status.
- Updated `docs/memory/CURRENT_STATE.md` with verification record.

## Abort Conditions

- If a feature requires displaying circuit diagrams as the primary result view,
  push back and redesign as a "technical details" optional view.
- If a solver result bypasses the Verifier, reject the implementation.
- If the three UI states are not all implemented, the feature is incomplete.

## What This Skill Does NOT Do

- Does not transform the application into a quantum circuit editor.
- Does not accept "works on my machine" as browser verification.
- Does not skip the Verifier integration in any result display path.
