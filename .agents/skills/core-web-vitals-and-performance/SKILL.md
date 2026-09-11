---
name: core-web-vitals-and-performance
description: High-performance engineering, Core Web Vitals (LCP, INP, CLS) optimization, browser rendering profiling, bundle tree-shaking, memory leak prevention, and database query optimization. Activate whenever optimizing speed, profiling latency, reducing bundle size, or scaling data throughput.
---

# Core Web Vitals & Performance Engineering

This skill governs high-throughput, low-latency execution across both frontend rendering pipelines and backend data layers. The standard is sub-50ms interaction responses and near-perfect Web Vitals.

---

## 1. Core Web Vitals (CWV) Targets & Fixes

* **Largest Contentful Paint (LCP < 2.5s, target < 1.2s):**
  * Prioritize the LCP element with `fetchpriority="high"`.
  * Preload critical hero images or fonts in `<head>`.
  * Eliminate render-blocking stylesheets and unneeded third-party scripts.
* **Interaction to Next Paint (INP < 200ms, target < 50ms):**
  * Break heavy CPU tasks into chunks using `scheduler.yield()` or `requestIdleCallback()`.
  * Offload heavy computations (image processing, sorting large datasets) to Web Workers.
  * Avoid expensive synchronous re-renders on every keystroke in inputs.
* **Cumulative Layout Shift (CLS < 0.1, target 0):**
  * Always specify explicit `width` and `height` (or `aspect-ratio`) on all `<img>`, `<video>`, and iframe elements.
  * Reserve space for dynamic ad banners or async widgets with CSS `min-height` or skeleton placeholders.
  * Use `font-display: optional` or modern metric overrides (`size-adjust`) to eliminate FOYT/FOUT layout jumps.

---

## 2. Frontend Bundle & Memory Optimization

* **Code Splitting & Dynamic Imports:**
  * Lazy load non-critical routes and heavy modals via dynamic `import()`.
  * Tree-shake large packages (e.g. import `lodash-es/debounce` or native JavaScript instead of importing entire utility libraries).
* **DOM Node Management:**
  * Use virtualized lists (e.g. TanStack Virtual) when rendering lists with more than 100 items.
  * Clean up event listeners, intervals, and AbortControllers in component unmount lifecycles to prevent memory leaks.

---

## 3. Database & Backend Throughput

* **Eliminate N+1 Queries:**
  * Always use eager loading, joins, or dataloaders (`batching`) instead of firing queries inside loops.
* **Database Indexing:**
  * Verify `EXPLAIN ANALYZE` on frequent queries. Ensure foreign keys, search filters, and sort columns are indexed.
* **Aggressive Caching Strategies:**
  * Implement Stale-While-Revalidate (SWR) for read-heavy public APIs.
  * Utilize Redis or in-memory caches for computationally heavy aggregations.
