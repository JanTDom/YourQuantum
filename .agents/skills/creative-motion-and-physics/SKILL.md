---
name: creative-motion-and-physics
description: Master-level animation, spring physics, motion choreography, and tactile microinteractions. Activate whenever designing or implementing animations, transitions, gesture responses, or interactive visual polish in web and mobile applications.
---

# Creative Motion and Physics System

This skill governs high-end motion design, physical spring dynamics, seamless layout transitions, and tactile UI feedback. The goal is to elevate digital products from static screens to living, responsive instruments without sacrificing performance or accessibility.

---

## 1. Core Motion Philosophy

* **Intentionality Over Ornament:** Every animation must communicate state, spatial orientation, causality, or hierarchy. Never animate purely for the sake of movement.
* **Spring Physics Over Easing Curves:** Prefer damped harmonic oscillators (mass, stiffness, damping) over arbitrary Bézier curves like `ease-in-out`. Real objects possess inertia, tension, and resistance.
* **Respect User Preferences:** Always adhere to `prefers-reduced-motion`. When reduced motion is requested, provide instantaneous state changes or subtle opacity dissolves rather than spatial translations.

---

## 2. Spring Physics Reference Parameters

When configuring spring animations (e.g. Framer Motion, Motion One, React Spring):

* **Snappy / Interactive (Buttons, Toggles, Micro-clicks):**
  * `mass: 0.1` to `0.3`, `stiffness: 400` to `500`, `damping: 25` to `35`
  * Feeling: Immediate, crisp, zero perceived lag.
* **Natural / Physical (Modals, Drawers, Cards, Sheets):**
  * `mass: 0.8` to `1.0`, `stiffness: 250` to `320`, `damping: 28` to `36`
  * Feeling: Balanced weight, subtle settling, organic stop without excessive bouncing.
* **Gentle / Ambient (Tooltips, Dropdowns, Hover Reveals):**
  * `mass: 0.5`, `stiffness: 180`, `damping: 24`
  * Feeling: Soft, non-intrusive, polite.

---

## 3. Motion Choreography & Staggering

* **Cascading Entrances:** When rendering lists or card collections, stagger entrance animations by `25ms` to `50ms` per item. Never stagger across more than 6-8 items; cap the total duration to under `350ms`.
* **Exit Faster Than Entrance:** Exits should be 20% to 30% faster than entrances (e.g., entrance 240ms, exit 180ms) to ensure the interface feels snappy when dismissing or navigating away.
* **Spatial Continuity & FLIP:**
  * Use shared element transitions (View Transitions API or Framer Motion `layoutId`) when an element transforms from a thumbnail into a detail view.
  * Avoid jumping layouts; maintain persistent anchor points.

---

## 4. Modern Web Standards Implementation

* **CSS Scroll-Driven Animations:**
  * Use `@keyframes` bound to `animation-timeline: scroll()` or `animation-timeline: view()` for performance-critical parallax, progress indicators, and sticky headers.
* **View Transitions API:**
  * For single-page and multi-page routing, wrap state transitions with `document.startViewTransition(() => updateDOM())`.
* **GPU Acceleration:**
  * Animate only `transform` and `opacity`. Never animate `width`, `height`, `top`, `left`, `margin`, or `padding` directly to prevent layout thrashing and maintain 60/120 FPS.
