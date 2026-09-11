---
name: editorial-typography-and-design-systems
description: Anti-generic UI design, editorial typography, modular scales, sophisticated color palettes (OKLCH), custom bento architectures, and accessible design systems. Activate whenever creating, redesigning, or refining interfaces, styling, and design foundations.
---

# Editorial Typography and Design Systems

This skill enforces intentional art direction, editorial elegance, and structural discipline in frontend interfaces. It actively prevents bland, generic AI templates in favor of tailored, publication-grade aesthetics.

---

## 1. Anti-Generic Aesthetic Imperatives

* **No Default Formulas:** Reject centered hero + two identical pill buttons + 3-card generic feature grids unless specifically requested.
* **Personality & Mood:** Each project must have a distinct visual soul (e.g. Swiss Modernist, Cyber-Technical, Luxury Editorial, Brutalist Utility, or Warm Humanist).
* **Restraint Over Clutter:** Use white space / negative space as an active architectural element. Don't crowd every pixel with cards, badges, or unnecessary borders.
* **Card Discipline:** Never nest cards inside cards inside cards. Flatten layouts using subtle surface distinctions, dividers, or whitespace grouping.

---

## 2. Typographic Architecture

* **Modular Scale:** Use a defined mathematical scale (e.g. Minor Third `1.2` for compact apps, Major Third `1.25` or Perfect Fourth `1.333` for marketing & editorial).
* **Controlled Line Length (Measure):** Cap reading copy at `45` to `75` characters per line (`max-w-prose` or `max-w-xl`). Never allow long paragraphs to stretch across full desktop widths.
* **Optical Kerning & Tracking:**
  * Tighten letter-spacing on large display headings (`letter-spacing: -0.02em` to `-0.04em`).
  * Add subtle tracking on small caps, labels, and metadata (`letter-spacing: 0.05em` to `0.1em`).
* **Leading (Line-height):** Tight leading (`1.05` to `1.2`) on large display headlines; generous leading (`1.5` to `1.7`) on body text for effortless reading.

---

## 3. Color Theory & Palette Craft

* **Modern Color Spaces:** Favor `oklch()` or `oklab` for perceptual uniformity and consistent contrast across shades.
* **60-30-10 Rule:**
  * 60% dominant neutral surface (deep ink or warm ivory, not pure `#000000` or sterile `#ffffff`).
  * 30% structural secondary tones (subtle borders, muted text, surface tiers).
  * 10% intentional accent (a single, unmistakable signature color used with purpose, not rainbow chaos).
* **Contrast & Legibility:** Meet or exceed WCAG 2.1 AA (minimum `4.5:1` for body text, `3:1` for large text). Never sacrifice readability for aesthetic minimalism.

---

## 4. Design System Tokens & Modern CSS

* **Semantic Tokens Over Arbitrary Values:**
  * Define functional tokens: `--surface-base`, `--surface-elevated`, `--text-primary`, `--text-muted`, `--border-subtle`, `--accent-primary`.
* **Container Queries & Dynamic Viewports:**
  * Build components that adapt to their container (`@container`) rather than solely relying on global screen breakpoints (`@media`).
* **State Completeness:**
  * Every interactive element must have distinct, deliberate designs for: `default`, `hover`, `focus-visible`, `active`, `disabled`, and `loading`.
