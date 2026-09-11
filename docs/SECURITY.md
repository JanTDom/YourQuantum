# SECURITY.md — Security Architecture

**Status:** PLANNED · **Last updated:** 2026-09-09

---

## Trust Boundaries

| Entity | Trust Level | Rationale |
|--------|------------|-----------|
| Authenticated user | Partially trusted | Valid session, but input is untrusted |
| User-supplied data | Untrusted | Must be validated and sanitised |
| LLM output | Untrusted | Hallucinations, prompt injection |
| Solver output | Partially trusted | Verify independently |
| QPU results | Partially trusted | Verify constraints independently |
| Admin | Trusted (elevated) | Must still be audited |
| External APIs | Untrusted at transport | Validate responses |

---

## Input Validation

- Every external input (HTTP body, query params, file upload, webhook) is
  validated against a strict schema (Zod / Pydantic) before reaching domain logic.
- LLM-generated structured data (Problem IR drafts) is re-validated against the
  IR schema before use — the LLM is not trusted to produce valid schemas.
- File uploads: type checked by magic bytes, size limited, scanned for known
  malicious patterns. No execution of uploaded files.

---

## Secrets Management

- No secrets (API keys, tokens, passwords, QPU credentials) in code, docs,
  comments, environment files committed to VCS, or project memory.
- Secrets are loaded at runtime from environment variables or a secret manager.
- Logs must not contain secrets or PII. Structured logging with allowlist fields.

---

## Code Execution Isolation

- Worker processes execute solver code in isolated environments (container or
  sandbox) with:
  - No network access (unless the solver specifically requires it and it is
    whitelisted per solver).
  - Filesystem access limited to a job-specific scratch directory.
  - CPU and memory limits enforced by the container runtime.
  - Wall-time timeout with SIGKILL fallback.
- User prompts NEVER result in arbitrary code execution. The solver selection
  and configuration is determined by the Router from the Problem IR — not by
  parsing user-supplied code strings.

---

## QPU Cost Controls

- No QPU call without showing the user a cost estimate first.
- No QPU call without explicit user approval for that specific job.
- Total QPU spend per user per period is configurable and enforced.
- QPU job IDs and costs are recorded and auditable.

---

## Client Isolation

- Each user's problem data, results, and history are isolated.
- No cross-user data leakage through shared caches, logs, or worker state.
- Shared infrastructure (queue, cache) uses per-tenant namespacing.

---

## Authentication & Authorisation

- All API endpoints require authentication.
- Authorisation checks at the use-case layer, not only at the transport layer.
- Principle of least privilege: each component has only the permissions it needs.
- Session tokens: short-lived, revocable.

---

## Dependency Security

- Dependencies are pinned to exact versions.
- `npm audit` / `pip-audit` runs in CI; high/critical vulnerabilities block merge.
- No new dependency added without explicit justification and licence check.

---

## What This System Will NOT Do

- Execute arbitrary code supplied in a user prompt.
- Weaken security constraints based on a model's suggestion.
- Store user problem data in shared global memory accessible to other users.
- Make paid external API calls (including QPU) without user approval.
