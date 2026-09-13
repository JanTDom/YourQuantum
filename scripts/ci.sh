#!/usr/bin/env bash
# ci.sh — YourQuantum V2 Continuous Integration Script
# Runs structure validation, backend test suite, frontend build, and E2E Playwright tests.
# Exit code 0 if all steps succeed, non-zero on failure.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "=========================================================="
echo "  YourQuantum V2 — Honest Engine CI Pipeline"
echo "  Root: $ROOT"
echo "=========================================================="

echo ""
echo "── Step 1: Validating Project Structure ─────────────────"
bash "$ROOT/scripts/validate-structure.sh"

echo ""
echo "── Step 2: Running Backend Test Suite (Pytest) ──────────"
cd "$ROOT"
if [ -d ".venv" ]; then
    PYTHON_EXEC=".venv/bin/pytest"
else
    PYTHON_EXEC="pytest"
fi
$PYTHON_EXEC tests/ -v

echo ""
echo "── Step 3: Frontend Typecheck & Build ───────────────────"
cd "$ROOT/frontend"
npm run build

echo ""
echo "── Step 4: Frontend E2E Playwright Verification ─────────"
cd "$ROOT/frontend"
export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH="${PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
npx playwright test e2e/v2-honest-engine.spec.ts

echo ""
echo "=========================================================="
echo "  ✓ ALL CI CHECKS PASSED: YourQuantum V2 is 100% Green!"
echo "=========================================================="
