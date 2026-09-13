#!/usr/bin/env bash
# validate-structure.sh — YourQuantum project structure validator
# Usage: bash scripts/validate-structure.sh
# Returns exit code 0 if all checks pass, 1 if any fail.

set -euo pipefail

PASS=0
FAIL=0
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

check_file() {
    local path="$ROOT/$1"
    if [ -f "$path" ]; then
        echo "  PASS  $1"
        ((PASS++)) || true
    else
        echo "  FAIL  $1  [FILE MISSING]"
        ((FAIL++)) || true
    fi
}

check_skill() {
    local skill="$1"
    local skill_path="$ROOT/.agents/skills/$skill/SKILL.md"
    if [ -f "$skill_path" ]; then
        # Verify frontmatter name and description fields exist
        if grep -q "^name:" "$skill_path" && grep -q "^description:" "$skill_path"; then
            echo "  PASS  .agents/skills/$skill/SKILL.md  [frontmatter OK]"
            ((PASS++)) || true
        else
            echo "  FAIL  .agents/skills/$skill/SKILL.md  [missing frontmatter fields]"
            ((FAIL++)) || true
        fi
    else
        echo "  FAIL  .agents/skills/$skill/SKILL.md  [FILE MISSING]"
        ((FAIL++)) || true
    fi
}

check_no_secrets() {
    local path="$ROOT/$1"
    if [ -f "$path" ]; then
        # Look for common secret patterns (API keys, tokens, passwords)
        if grep -qiE '(api_key|apikey|secret|password|token|credential)\s*[:=]\s*["\x27][^"\x27]{8,}' "$path" 2>/dev/null; then
            echo "  FAIL  $1  [POSSIBLE SECRET DETECTED — review manually]"
            ((FAIL++)) || true
        else
            echo "  PASS  $1  [no obvious secrets]"
            ((PASS++)) || true
        fi
    fi
}

echo "=================================================="
echo "  YourQuantum — Structure Validation"
echo "  Root: $ROOT"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="
echo ""

echo "── Core rules ────────────────────────────────────"
check_file "AGENTS.md"

echo ""
echo "── Documentation ─────────────────────────────────"
check_file "docs/PRODUCT.md"
check_file "docs/BUILD_SPEC.md"
check_file "docs/ARCHITECTURE.md"
check_file "docs/PROBLEM_IR.md"
check_file "docs/QUANTUM_CORE.md"
check_file "docs/VERIFICATION.md"
check_file "docs/BENCHMARK_PROTOCOL.md"
check_file "docs/SECURITY.md"
check_file "docs/CAPABILITIES.md"
check_file "docs/SOURCES.md"

echo ""
echo "── Memory ────────────────────────────────────────"
check_file "docs/memory/INDEX.md"
check_file "docs/memory/CURRENT_STATE.md"
check_file "docs/memory/DECISIONS.md"
check_file "docs/memory/LESSONS.md"

echo ""
echo "── Benchmarks ────────────────────────────────────"
check_file "benchmarks/README.md"

echo ""
echo "── Skills ────────────────────────────────────────"
check_skill "yq-context"
check_skill "yq-formalizer"
check_skill "yq-architect"
check_skill "yq-classical-solvers"
check_skill "yq-quantum-core"
check_skill "yq-routing-and-decomposition"
check_skill "yq-verifier"
check_skill "yq-benchmark"
check_skill "yq-data-io"
check_skill "yq-product-engineering"
check_skill "yq-security"
check_skill "yq-learning"

echo ""
echo "── Skill name uniqueness ─────────────────────────"
NAMES=$(grep -rh "^name:" "$ROOT/.agents/skills/" 2>/dev/null | sort)
UNIQUE_NAMES=$(echo "$NAMES" | sort -u)
if [ "$NAMES" = "$UNIQUE_NAMES" ]; then
    echo "  PASS  All skill names are unique"
    ((PASS++)) || true
else
    echo "  FAIL  Duplicate skill names detected:"
    echo "$NAMES" | sort | uniq -d
    ((FAIL++)) || true
fi

echo ""
echo "── Secret scan ───────────────────────────────────"
check_no_secrets "AGENTS.md"
check_no_secrets "docs/PRODUCT.md"
check_no_secrets "docs/ARCHITECTURE.md"
check_no_secrets "docs/memory/CURRENT_STATE.md"
check_no_secrets "docs/memory/DECISIONS.md"
check_no_secrets "docs/memory/LESSONS.md"

echo ""
echo "── Cross-reference checks ────────────────────────"
# Check that AGENTS.md references the key memory docs
if grep -q "docs/memory/INDEX.md" "$ROOT/AGENTS.md"; then
    echo "  PASS  AGENTS.md references docs/memory/INDEX.md"
    ((PASS++)) || true
else
    echo "  FAIL  AGENTS.md does not reference docs/memory/INDEX.md"
    ((FAIL++)) || true
fi

if grep -q "docs/memory/CURRENT_STATE.md" "$ROOT/AGENTS.md"; then
    echo "  PASS  AGENTS.md references docs/memory/CURRENT_STATE.md"
    ((PASS++)) || true
else
    echo "  FAIL  AGENTS.md does not reference docs/memory/CURRENT_STATE.md"
    ((FAIL++)) || true
fi

echo ""
echo "── Documentation referenced paths check (R4) ─────"
DOC_PATHS_FAIL=0
for doc in "docs/memory/CURRENT_STATE.md" "docs/CAPABILITIES.md"; do
    if [ -f "$ROOT/$doc" ]; then
        paths=$(grep -oE '\`[A-Za-z0-9_./-]+\.(py|ts|tsx|md|json|sh|yml|txt)\`|\`Dockerfile\`' "$ROOT/$doc" | tr -d '`' || true)
        for p in $paths; do
            if [[ "$p" =~ ^http ]] || [[ "$p" =~ \* ]] || [[ "$p" =~ ^v?[0-9]+\. ]]; then
                continue
            fi
            if [ -e "$ROOT/$p" ]; then
                ((PASS++)) || true
            else
                echo "  FAIL  $doc references missing path: $p"
                ((FAIL++)) || true
                DOC_PATHS_FAIL=1
            fi
        done
    fi
done
if [ "$DOC_PATHS_FAIL" -eq 0 ]; then
    echo "  PASS  All backtick filepaths in CURRENT_STATE.md and CAPABILITIES.md exist on disk"
    ((PASS++)) || true
fi

echo ""
echo "=================================================="
echo "  Results: $PASS passed, $FAIL failed"
echo "=================================================="

if [ "$FAIL" -gt 0 ]; then
    exit 1
else
    echo "  All checks passed."
    exit 0
fi
