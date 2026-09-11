---
name: creative-web-craftsmanship
description: Master-grade frontend engineering and creative web design. Enforces Awwwards/FWA-level visual aesthetics, modern CSS (Anchor positioning, View Transitions, Container Queries, Scroll-driven animations, OKLCH), fluid typography, bespoke layouts, micro-interactions, and high-performance rendering. Activate whenever designing or building web user interfaces, landing pages, interactive apps, and component libraries.
---

# Creative Web Craftsmanship — Elite Frontend Standard

This skill establishes the highest echelon of frontend engineering and creative web direction. It transforms web development from sterile, template-driven assembly into bespoke digital craftsmanship with award-winning visual impact, fluid motion physics, and flawless accessibility.

---

## 1. Creative Direction & Anti-Template Philosophy

* **The Anti-Generic Imperative:**
  * Ban default AI tropes: No cookie-cutter centered hero with two pill buttons; no monotonous 3-column card grids with icons in colored squares; no meaningless blurred gradient blobs.
  * Every interface must establish a distinct visual identity:
    * **Editorial / Publication:** Sharp typography, asymmetrical multi-column grids, exquisite whitespace, hairline rules, pull quotes.
    * **High-Tech / Precision Instrument:** Monospace accents, dense tabular data, high-contrast indicators, micro-badges, subtle scanlines or geometric guides.
    * **Warm Humanist / Crafted:** Tactile card elevations, organic curves, rich ink tones, paper textures, humanist sans-serifs or modern serifs.
    * **Cinematic / Immersive:** Deep dark mode, subtle atmospheric grain, dynamic lighting/vignettes, spotlight hover effects, dimensional layered depth.
* **Content-Informed Layouts:**
  * The structure must emerge from the specific product story, data shape, and user tasks — never force content into a generic pre-made skeleton.
  * Use **Bento Grids with Intentional Scale**: Hero feature spans 2x2 or 2x1 with high visual density; secondary features offer interactive previews; tertiary items provide concise statistics or status signals.

---

## 2. Cutting-Edge CSS & Modern Layout Standards (2025/2026)

* **CSS Anchor Positioning (`anchor-name` / `position-anchor`):**
  * Use native anchor positioning for tooltips, floating menus, popovers, and contextual badges to eliminate brittle manual bounding box math and resize listeners.
* **Popover API & Dialogs:**
  * Leverage native `<dialog>` and `popover="auto"` attributes for top-layer rendering, native focus trapping, backdrop blur, and light-dismiss without massive JS overhead.
* **View Transitions API (SPA & Multi-Page):**
  * Seamless state and page morphing using `document.startViewTransition()`. Pair with `@view-transition` and named elements (`view-transition-name`) to create fluid morphs between list cards and detail views.
* **Scroll-Driven & Scroll-Reveals:**
  * Implement zero-CPU hardware-accelerated animations using CSS `animation-timeline: view()` and `animation-timeline: scroll()` with `animation-range: entry 10% cover 40%`.
* **Discrete Transitions with `@starting-style`:**
  * Animate elements entering and exiting the top layer (`display: none` / `popover` / `<dialog>`) using `@starting-style` and `transition-behavior: allow-discrete`.
* **Container Queries (`@container`):**
  * Design components that react to their parent container's inline width rather than the viewport. A card in a 300px sidebar renders compact; the same card in an 800px column renders an expanded rich layout.
* **Subgrid & Modern Grid:**
  * Use `grid-template-rows: subgrid` to align card headers, bodies, and footers across uneven grid items automatically.
* **Perceptual Color Space (OKLCH):**
  * All design tokens must use `oklch(lightness chroma hue / alpha)` to guarantee predictable contrast, perceptually uniform palette stepping, and vibrant accents without muddy blends.

---

## 3. Typographic Hierarchy & Fluid Scales

* **Fluid Type Scale with `clamp()`:**
  * Never use static pixel font sizes that break between desktop and mobile. Calculate fluid bounds:
    ```css
    --font-display: clamp(2.5rem, 1.8rem + 3.5vw, 5.5rem);
    --font-h1: clamp(2rem, 1.5rem + 2.5vw, 3.75rem);
    --font-h2: clamp(1.5rem, 1.2rem + 1.5vw, 2.5rem);
    --font-body: clamp(0.9375rem, 0.9rem + 0.2vw, 1.125rem);
    ```
* **Optical Tracking & Micro-Typography:**
  * Display titles (`> 32px`): Negative tracking (`letter-spacing: -0.025em` to `-0.04em`) with tight line-height (`1.05` to `1.15`).
  * Body copy (`15px - 18px`): Normal tracking with generous line-height (`1.55` to `1.7`) and max line length of 65 characters (`max-w-prose`).
  * All-caps / Monospace labels: Generous tracking (`letter-spacing: 0.06em` to `0.1em`), small caps (`font-variant-caps: all-small-caps`), smaller size (`0.75rem` to `0.8125rem`).

---

## 4. Tactile Micro-Interactions & Motion Dynamics

* **Physics-Based Spring Response:**
  * Replace static linear/ease transitions on interactive elements with spring physics.
  * **Buttons & Clicks:** Subtle scale-down on active (`scale(0.97)`), fast return spring (`stiffness: 450`, `damping: 25`).
  * **Card Hover States:** Gentle physical elevation, subtle border glow tracking the cursor (`radial-gradient` following pointer coordinates), and smooth background shift.
* **Loading & Skeleton Artistry:**
  * Eliminate jarring spinners. Replace with shimmer skeletons that match the exact typography and layout of the incoming data, or subtle pulsating indeterminate progress lines along top borders.
* **Sound & Haptics (When Applicable):**
  * Subtle, opt-in audio/haptic feedback on major actions (e.g. success confirmation, toggling critical modes).

---

## 5. Web Accessibility (WCAG 2.2 AA / AAA Baseline)

* **Keyboard Navigation First:**
  * Every interactive element is reachable via <kbd>Tab</kbd> and activates with <kbd>Enter</kbd> / <kbd>Space</kbd>.
  * Visible, high-contrast focus rings using `:focus-visible` (never remove outline without providing a distinct custom focus indicator).
* **Motion Sensitivity:**
  * Respect `@media (prefers-reduced-motion: reduce)`. Gracefully degrade complex transforms to simple, non-jarring crossfades.
* **Semantic ARIA Contracts:**
  * Use native HTML5 landmarks (`<main>`, `<nav>`, `<aside>`, `<header>`, `<footer>`).
  * Dynamic status updates announced via `role="status"` or `aria-live="polite"`.

---

## 6. Frontend Production Checklist

- [ ] Distinct, non-generic art direction with deliberate color palette (`oklch`) and typography scale (`clamp`).
- [ ] Responsive without layout breaks across 320px (compact mobile) to 2560px (ultra-wide).
- [ ] Zero layout shifts (CLS < 0.05); critical images sized with `aspect-ratio` and modern formats (`avif`, `webp`).
- [ ] 60+ FPS fluid micro-interactions with hardware-accelerated transforms (`translate3d`, `scale`, `opacity`).
- [ ] All interactive states styled: `default`, `hover`, `focus-visible`, `active`, `disabled`, `loading`.
