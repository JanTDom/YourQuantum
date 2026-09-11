---
name: yq-data-io
description: >-
  Use this skill when implementing or reviewing data ingestion, validation,
  unit normalisation, missing-data handling, versioning, or export in
  YourQuantum. Activate when a user uploads data, when implementing a new
  import format, when auditing data handling for security, or when designing
  the export schema for results. Data from users is always untrusted at the
  boundary.
---

# yq-data-io — Data Input/Output

## Input

- Raw user data (file upload, API payload, form input).
- Target Problem IR field(s) the data should populate.
- Import format specification (JSON, CSV, Excel, etc.).

## Procedure

### 1. Validate at the Boundary

Every incoming data item is validated BEFORE it reaches any domain logic:

```python
# Example: Zod (TypeScript) or Pydantic (Python)
schema = DataImportSchema(...)
try:
    validated = schema.parse(raw_input)
except ValidationError as e:
    return DataImportError(field_errors=e.errors(), raw_input_rejected=True)
```

Validation rules:
- Required fields must be present.
- Types must match exactly (no silent coercion of strings to numbers).
- Numeric values must be finite (reject NaN, Inf).
- String fields must meet length and character constraints.
- File uploads: check magic bytes, not just extension.

### 2. File Upload Security

- Maximum file size enforced before parsing.
- MIME type validated against allowlist by magic bytes.
- No execution of uploaded files under any circumstances.
- Uploaded files stored in isolated, job-specific scratch directory.
- Scratch directory is cleaned up after job completion.

### 3. Unit Normalisation

For every numeric field with a physical unit:
1. Detect the declared unit (from data or user specification).
2. Convert to the canonical internal unit for that quantity.
3. Record: original value, original unit, canonical value, canonical unit.
4. If unit is ambiguous or unknown: flag as `MissingInfo` in the Problem IR.

Do NOT silently assume a unit. A value of "100" without a unit is always
ambiguous.

### 4. Missing Data Handling

For each missing or null field:
- Determine the impact: `blocks_solving`, `reduces_quality`, or `minor`.
- If `blocks_solving`: add to Problem IR `MissingInfo`; do not attempt to solve.
- If `reduces_quality`: notify user and offer options (impute, exclude, stop).
- Never silently impute values that affect the objective or hard constraints.

### 5. Versioning

Each imported data set is assigned a version at import time:
- Hash of the raw data content (SHA-256).
- Import timestamp.
- Source description (filename, URL, API endpoint).

The hash and timestamp are recorded in the Problem IR's `data` field.
If the same data file is imported again with different content, it is a new
version — not an in-place update.

### 6. Export

Results are exported in the user's requested format (JSON, CSV, report).
Before export:
- Confirm the Verification Report is attached to the result.
- Include the Problem IR version in the export metadata.
- Include the limitations list in every export — not just in the UI.

## Required Output

- Validated, normalised data ready for Problem IR population.
- Or: a structured error with the specific rejected fields and reasons.

## Abort Conditions

- If file type is not in the allowlist, reject with a clear error.
- If validation fails on a required field, reject the entire import.
  Do NOT accept a partial import that silently omits a required field.
- If unit normalisation is impossible (unknown unit), flag and halt.

## What This Skill Does NOT Do

- Does not execute imported data as code.
- Does not silently impute values for missing hard-constraint data.
- Does not accept files without magic-byte validation.
- Does not store uploaded files outside the job-specific scratch directory.
