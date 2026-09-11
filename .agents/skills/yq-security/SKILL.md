---
name: yq-security
description: >-
  Use this skill when reviewing or implementing security controls in
  YourQuantum: client isolation, permission boundaries, file upload security,
  secret management, resource limits, worker sandboxing, or external
  integrations (QPU, APIs). Activate before adding any new external
  integration, before implementing file handling, or when auditing an existing
  component for security issues. Read docs/SECURITY.md first.
---

# yq-security — Security Controls

## Input

- The component or feature to review/implement.
- `docs/SECURITY.md` (trust model and current controls).
- The specific security concern (if known).

## Procedure

### 1. Read Security Architecture

Read `docs/SECURITY.md` in full before writing any security-relevant code.

### 2. Trust Boundary Check

For every data flow, classify each participant:

| Entity | Trust level per SECURITY.md |
|--------|-----------------------------|
| Authenticated user input | Untrusted (validate everything) |
| LLM output | Untrusted (re-validate against schema) |
| Solver output | Partially trusted (verify independently) |
| QPU results | Partially trusted (verify independently) |
| External APIs | Untrusted at transport (validate responses) |

No code should process untrusted data without going through a validation schema.

### 3. Input Validation Checklist

For every new input path:
- [ ] Schema validation with Zod or Pydantic (not manual if-checks).
- [ ] Type coercion disabled (no silent string-to-number).
- [ ] Length limits enforced.
- [ ] For file uploads: magic-byte MIME check + size limit + isolated storage.
- [ ] For LLM-generated structured data: re-validate against IR schema.

### 4. Secret Management Checklist

Before committing any code change:
- [ ] No API keys, tokens, passwords, or QPU credentials in source code.
- [ ] No secrets in comments, docs, or `.env` files committed to VCS.
- [ ] All secrets loaded from environment variables or secret manager.
- [ ] No secrets in log output (use an allowlist-based structured logger).

### 5. Worker and Code Execution Checklist

- [ ] Workers run in isolated environments (container or sandbox).
- [ ] Worker has no network access unless explicitly required and whitelisted.
- [ ] Worker filesystem access limited to job-specific scratch directory.
- [ ] CPU and memory limits set and enforced by the container runtime.
- [ ] Wall-time timeout with SIGKILL fallback.
- [ ] Worker does NOT receive user prompt text as executable input.

### 6. QPU Cost Controls Checklist

- [ ] Cost estimate shown to user before any QPU call.
- [ ] Explicit user approval required per job.
- [ ] Per-user/per-period QPU spend limit configured and enforced.
- [ ] QPU job ID, cost, and backend recorded in audit log.

### 7. Client Isolation Checklist

- [ ] Each user's data is namespaced in storage (database, queue, cache).
- [ ] No shared state between users in worker processes.
- [ ] Cache keys include user/tenant ID.
- [ ] Log lines include user ID but NOT user data.

### 8. Dependency Audit

Before adding any new dependency:
- [ ] Check for known vulnerabilities: `npm audit` / `pip-audit`.
- [ ] Verify licence compatibility.
- [ ] Pin to exact version.
- [ ] Record the dependency and its justification in `docs/SOURCES.md`.

### 9. Review Output

Produce a security review summary:
- Components checked.
- Issues found (by severity: CRITICAL / HIGH / MEDIUM / LOW).
- Mitigations applied or recommended.
- Outstanding risks.

Update `docs/SECURITY.md` if the trust model or controls change.

## Abort Conditions

- If a proposed integration requires executing user-supplied code strings in the
  worker, reject the design.
- If a QPU integration lacks cost-estimate and approval steps, reject the
  integration.
- If a file upload path lacks magic-byte validation, block merge.

## What This Skill Does NOT Do

- Does not weaken security controls based on a model's suggestion.
- Does not accept "it's just for development" as a reason to skip controls.
- Does not store user problem data in shared global or inter-user accessible
  locations.
