#!/usr/bin/env bash
# scripts/check_v4.sh — Mechaniczne bramki weryfikacyjne dla YourQuantum V4
# Wymóg: sekcja 6 promptu korygującego V4

set -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FAIL_COUNT=0

function report_gate() {
    local gate_id="$1"
    local status="$2"
    local msg="$3"
    if [ "$status" = "PASS" ]; then
        echo "[$gate_id] PASS: $msg"
    else
        echo "[$gate_id] FAIL: $msg"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

echo "=== YOURQUANTUM V4 MECHANICAL GATES CHECK ==="
echo "Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
echo "Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
echo "----------------------------------------------"

# G-R1a: grep -rE "stat\.gov\.pl|nfz\.gov\.pl|who\.int|oecd\.org" frontend/src = 0 trafień
R1A_HITS=$(grep -rE "stat\.gov\.pl|nfz\.gov\.pl|who\.int|oecd\.org" frontend/src 2>/dev/null | wc -l | tr -d ' ')
if [ "$R1A_HITS" -eq 0 ]; then
    report_gate "G-R1a" "PASS" "0 trafień domen w frontend/src"
else
    report_gate "G-R1a" "FAIL" "Znaleziono $R1A_HITS wystąpień domen w frontend/src"
fi

# G-R1b: grep -rn "getDesignFixture(" frontend/src/components/RecommendationView.tsx = 0
R1B_HITS=$(grep -rn "getDesignFixture(" frontend/src/components/RecommendationView.tsx 2>/dev/null | wc -l | tr -d ' ')
if [ "$R1B_HITS" -eq 0 ]; then
    report_gate "G-R1b" "PASS" "getDesignFixture nie występuje w RecommendationView.tsx"
else
    report_gate "G-R1b" "FAIL" "Znaleziono $R1B_HITS wywołań getDesignFixture w RecommendationView.tsx"
fi

# G-R1c: każdy URL w tests/fixtures/design/healthcare_pl.json zaczyna się od https://example.test/; plik zawiera "synthetic_test_data": true
FIXTURE_PATH="tests/fixtures/design/healthcare_pl.json"
if [ -f "$FIXTURE_PATH" ]; then
    HAS_SYNTHETIC=$(grep -n '"synthetic_test_data": true' "$FIXTURE_PATH" 2>/dev/null | wc -l | tr -d ' ')
    NON_EXAMPLE_URLS=$(grep -oE 'https?://[^"]+' "$FIXTURE_PATH" 2>/dev/null | grep -v '^https://example\.test' | wc -l | tr -d ' ')
    if [ "$HAS_SYNTHETIC" -ge 1 ] && [ "$NON_EXAMPLE_URLS" -eq 0 ]; then
        report_gate "G-R1c" "PASS" "healthcare_pl.json jest syntetyczny i zawiera wyłącznie adresy https://example.test"
    else
        report_gate "G-R1c" "FAIL" "healthcare_pl.json narusza regułę syntetyczności (has_synthetic=$HAS_SYNTHETIC, non_example_urls=$NON_EXAMPLE_URLS)"
    fi
else
    report_gate "G-R1c" "FAIL" "Brak pliku $FIXTURE_PATH"
fi

# G-R2: git grep -n secret zwraca wyłącznie docs/SECURITY.md, docs/memory/LESSONS.md, docs/BUILD_SPEC_V*.md, docs/REPORT_V*.md
TARGET_SECRET="A132""a132"
R2_INVALID_HITS=$(git grep -n "$TARGET_SECRET" 2>/dev/null \
    | grep -vE '^(\./)?docs/SECURITY\.md:' \
    | grep -vE '^(\./)?docs/memory/LESSONS\.md:' \
    | grep -vE '^(\./)?docs/BUILD_SPEC_V[0-9]+\.md:' \
    | grep -vE '^(\./)?docs/REPORT_V[0-9]+\.md:' \
    | wc -l | tr -d ' ')
if [ "$R2_INVALID_HITS" -eq 0 ]; then
    report_gate "G-R2" "PASS" "Brak hasła master poza dokumentami audytowymi"
else
    report_gate "G-R2" "FAIL" "Znaleziono $R2_INVALID_HITS niedozwolonych wystąpień sekretu master w repo"
fi

# G-R3: grep -n 'getenv("YQ_SIGNING_KEY", "' backend = 0 i grep -n 'getenv("YQ_MASTER_API_SECRET", "' backend = 0
R3_SIGNING=$(grep -rn 'getenv("YQ_SIGNING_KEY", "' backend 2>/dev/null | wc -l | tr -d ' ')
R3_MASTER=$(grep -rn 'getenv("YQ_MASTER_API_SECRET", "' backend 2>/dev/null | wc -l | tr -d ' ')
if [ "$R3_SIGNING" -eq 0 ] && [ "$R3_MASTER" -eq 0 ]; then
    report_gate "G-R3" "PASS" "Zero wartości domyślnych dla YQ_SIGNING_KEY i YQ_MASTER_API_SECRET"
else
    report_gate "G-R3" "FAIL" "Wykryto domyślne sekrety: signing=$R3_SIGNING, master=$R3_MASTER"
fi

# G-R4: każda ścieżka w backtickach w docs/memory/CURRENT_STATE.md, docs/CAPABILITIES.md, docs/memory/DECISIONS.md istnieje na dysku
python3 -c "
import re, sys, os

docs = ['docs/memory/CURRENT_STATE.md', 'docs/CAPABILITIES.md', 'docs/memory/DECISIONS.md']
pattern = re.compile(r'\`([A-Za-z0-9_./-]+\.(?:py|ts|tsx|md|json|sh|yml|txt)|Dockerfile)\`')
missing = []

for doc in docs:
    if not os.path.isfile(doc):
        continue
    with open(doc, 'r', encoding='utf-8') as f:
        content = f.read()
    matches = pattern.findall(content)
    for m in matches:
        if m.startswith('http') or '*' in m or m.startswith('v0.') or m.startswith('0.'):
            continue
        if not os.path.exists(m):
            missing.append(f'{doc} references missing: {m}')

if missing:
    for item in missing[:5]:
        print(item, file=sys.stderr)
    sys.exit(1)
sys.exit(0)
" 2>/dev/null
if [ $? -eq 0 ]; then
    report_gate "G-R4" "PASS" "Wszystkie ścieżki w dokumentacji istnieją na dysku"
else
    report_gate "G-R4" "FAIL" "Wykryto nieistniejące ścieżki w dokumentacji"
fi

# G-R5: grep -nE "\?\? 1|isVerified \? 0 : 1" frontend/src/components/EvidenceDrawer.tsx = 0
R5_HITS=$(grep -nE "\?\? 1|isVerified \? 0 : 1" frontend/src/components/EvidenceDrawer.tsx 2>/dev/null | wc -l | tr -d ' ')
if [ "$R5_HITS" -eq 0 ]; then
    report_gate "G-R5" "PASS" "Brak domyślnych zmyślonych wartości w EvidenceDrawer.tsx"
else
    report_gate "G-R5" "FAIL" "Znaleziono $R5_HITS zmyślonych domyślnych wartości w EvidenceDrawer.tsx"
fi

# G-R6: grep -n "google.com/search" backend/infrastructure/web_research/search_adapter.py = 0; grep -n "page_text=text" backend/infrastructure/web_research/search_adapter.py = 0
R6_URL_HITS=$(grep -n "google.com/search" backend/infrastructure/web_research/search_adapter.py 2>/dev/null | wc -l | tr -d ' ')
R6_TEXT_HITS=$(grep -n "page_text=text" backend/infrastructure/web_research/search_adapter.py 2>/dev/null | wc -l | tr -d ' ')
if [ "$R6_URL_HITS" -eq 0 ] && [ "$R6_TEXT_HITS" -eq 0 ]; then
    report_gate "G-R6" "PASS" "search_adapter.py nie traktuje tekstu modelu jako strony i nie używa google.com/search"
else
    report_gate "G-R6" "FAIL" "search_adapter.py narusza R6 (google_url_hits=$R6_URL_HITS, text_as_page_hits=$R6_TEXT_HITS)"
fi

# G-N1a: istnieją: Dockerfile, docker-compose.yml, requirements-api.txt, requirements-worker.txt
if [ -f "Dockerfile" ] && [ -f "docker-compose.yml" ] && [ -f "requirements-api.txt" ] && [ -f "requirements-worker.txt" ]; then
    report_gate "G-N1a" "PASS" "Wszystkie pliki kontenera i rozdzielonych zależności istnieją"
else
    report_gate "G-N1a" "FAIL" "Brak któregoś z plików: Dockerfile, docker-compose.yml, requirements-api.txt, requirements-worker.txt"
fi

# G-N1b: requirements-api.txt nie zawiera ortools, qiskit, scipy
if [ -f "requirements-api.txt" ]; then
    N1B_HITS=$(grep -iE "ortools|qiskit|scipy" requirements-api.txt 2>/dev/null | wc -l | tr -d ' ')
    if [ "$N1B_HITS" -eq 0 ]; then
        report_gate "G-N1b" "PASS" "requirements-api.txt jest lekki (brak ciężkich pakietów solverów)"
    else
        report_gate "G-N1b" "FAIL" "requirements-api.txt zawiera zakazane pakiety numeryczne ($N1B_HITS)"
    fi
else
    report_gate "G-N1b" "FAIL" "Brak pliku requirements-api.txt"
fi

# G-N1c: docs/memory/CURRENT_STATE.md zawiera blok ```json z surową odpowiedzią produkcyjnego health/solvers zawierającą pole "available"
python3 -c "
import sys, re
with open('docs/memory/CURRENT_STATE.md', 'r', encoding='utf-8') as f:
    text = f.read()
pattern = re.compile(r'\`\`\`json\s*\{.*?\"available\".*?\}\s*\`\`\`', re.DOTALL)
if pattern.search(text):
    sys.exit(0)
sys.exit(1)
" 2>/dev/null
if [ $? -eq 0 ]; then
    report_gate "G-N1c" "PASS" "CURRENT_STATE.md zawiera surową odpowiedź z polem available"
else
    report_gate "G-N1c" "FAIL" "Brak surowej odpowiedzi health/solvers z polem available w CURRENT_STATE.md"
fi

# G-N2a: grep -n "len(self.criteria) == 0" backend/domain/decision_case.py ≥ 1
N2A_HITS=$(grep -n "len(self.criteria) == 0" backend/domain/decision_case.py 2>/dev/null | wc -l | tr -d ' ')
if [ "$N2A_HITS" -ge 1 ]; then
    report_gate "G-N2a" "PASS" "decision_case.py posiada bramkę blokującą przy 0 kryteriach"
else
    report_gate "G-N2a" "FAIL" "Brak sprawdzenia len(self.criteria) == 0 w decision_case.py"
fi

# G-N2b: grep -rn "score_matrix" frontend/src/components/CaseWorkspace.tsx ≥ 1
N2B_HITS=$(grep -rn "score_matrix" frontend/src/components/CaseWorkspace.tsx 2>/dev/null | wc -l | tr -d ' ')
if [ "$N2B_HITS" -ge 1 ]; then
    report_gate "G-N2b" "PASS" "CaseWorkspace.tsx zawiera edytor macierzy score_matrix"
else
    report_gate "G-N2b" "FAIL" "Brak score_matrix w CaseWorkspace.tsx"
fi

# G-N3: grep -rn "researchEvidence(" frontend/src/components frontend/src/App.tsx ≥ 1
N3_HITS=$(grep -rn "researchEvidence(" frontend/src/components frontend/src/App.tsx 2>/dev/null | wc -l | tr -d ' ')
if [ "$N3_HITS" -ge 1 ]; then
    report_gate "G-N3" "PASS" "Frontend wywołuje researchEvidence"
else
    report_gate "G-N3" "FAIL" "Brak wywołań researchEvidence w frontend/src/components lub frontend/src/App.tsx"
fi

# G-N4: grep -n "problem_class_override" backend/api/cognitive_routes.py frontend/src/api.ts ≥ 1 w każdym
N4_BE=$(grep -n "problem_class_override" backend/api/cognitive_routes.py 2>/dev/null | wc -l | tr -d ' ')
N4_FE=$(grep -n "problem_class_override" frontend/src/api.ts 2>/dev/null | wc -l | tr -d ' ')
if [ "$N4_BE" -ge 1 ] && [ "$N4_FE" -ge 1 ]; then
    report_gate "G-N4" "PASS" "problem_class_override zaimplementowany w backendzie i frontendzie"
else
    report_gate "G-N4" "FAIL" "Brak problem_class_override (backend: $N4_BE, frontend: $N4_FE)"
fi

# G-N5: istnieje backend/domain/cognitive/lever_decomposer.py i frontend/src/components/DesignWorkspace.tsx
if [ -f "backend/domain/cognitive/lever_decomposer.py" ] && [ -f "frontend/src/components/DesignWorkspace.tsx" ]; then
    report_gate "G-N5" "PASS" "lever_decomposer.py i DesignWorkspace.tsx istnieją"
else
    report_gate "G-N5" "FAIL" "Brak lever_decomposer.py lub DesignWorkspace.tsx"
fi

# G-N6: grep -rnE "httpx\.(post|Client\()" backend/domain = 0
N6_HITS=$(grep -rnE "httpx\.(post|Client\()" backend/domain 2>/dev/null | wc -l | tr -d ' ')
if [ "$N6_HITS" -eq 0 ]; then
    report_gate "G-N6" "PASS" "Zero wywołań httpx.post/Client w backend/domain"
else
    report_gate "G-N6" "FAIL" "Znaleziono $N6_HITS zakazanych wywołań httpx w backend/domain"
fi

# G-N7: grep -n "approved=True" backend/api/universal_engine.py = 0; grep -n "ProblemRouter" backend/api/universal_engine.py ≥ 1
N7_APP=$(grep -n "approved=True" backend/api/universal_engine.py 2>/dev/null | wc -l | tr -d ' ')
N7_ROUTER=$(grep -n "ProblemRouter" backend/api/universal_engine.py 2>/dev/null | wc -l | tr -d ' ')
if [ "$N7_APP" -eq 0 ] && [ "$N7_ROUTER" -ge 1 ]; then
    report_gate "G-N7" "PASS" "universal_engine.py nie omija approved=False i używa ProblemRouter"
else
    report_gate "G-N7" "FAIL" "universal_engine.py narusza N7 (approved_true_hits=$N7_APP, router_hits=$N7_ROUTER)"
fi

# G-N8: grep -rni "halucynac" frontend/src backend/api/help_service.py = 0
N8_HITS=$(grep -rni "halucynac" frontend/src backend/api/help_service.py 2>/dev/null | wc -l | tr -d ' ')
if [ "$N8_HITS" -eq 0 ]; then
    report_gate "G-N8" "PASS" "Zero niedozwolonego copy o halucynacjach"
else
    report_gate "G-N8" "FAIL" "Znaleziono $N8_HITS wystąpień słowa halucynac w UI / help service"
fi

# G-N9: grep -n 'schema_version: str = "0.3"' backend/domain/problem_ir.py = 1
N9_HITS=$(grep -n 'schema_version: str = "0.3"' backend/domain/problem_ir.py 2>/dev/null | wc -l | tr -d ' ')
if [ "$N9_HITS" -eq 1 ]; then
    report_gate "G-N9" "PASS" "Problem IR schema version podniesione do 0.3"
else
    report_gate "G-N9" "FAIL" "Problem IR schema version nie jest 0.3 (hits=$N9_HITS)"
fi

# G-N11: istnieje frontend/e2e/v4-real-backend.spec.ts; playwright.config.ts zawiera webServer
N11_E2E_EXISTS=0
[ -f "frontend/e2e/v4-real-backend.spec.ts" ] && N11_E2E_EXISTS=1
N11_WEBSERVER=$(grep -n "webServer" frontend/playwright.config.ts 2>/dev/null | wc -l | tr -d ' ')
if [ "$N11_E2E_EXISTS" -eq 1 ] && [ "$N11_WEBSERVER" -ge 1 ]; then
    report_gate "G-N11" "PASS" "E2E z realnym backendem uvicorn i webServer w playwright.config.ts"
else
    report_gate "G-N11" "FAIL" "Brak v4-real-backend.spec.ts lub webServer w playwright.config.ts"
fi

# G-N10: istnieje docs/REPORT_V4.md i zawiera wiersze dla wszystkich ID: R1–R6, N1–N11
if [ -f "docs/REPORT_V4.md" ]; then
    MISSING_IDS=0
    for id in R1 R2 R3 R4 R5 R6 N1 N2 N3 N4 N5 N6 N7 N8 N9 N10 N11; do
        if ! grep -q "$id" docs/REPORT_V4.md 2>/dev/null; then
            MISSING_IDS=$((MISSING_IDS + 1))
        fi
    done
    if [ "$MISSING_IDS" -eq 0 ]; then
        report_gate "G-N10" "PASS" "REPORT_V4.md zawiera wszystkie wymagane ID"
    else
        report_gate "G-N10" "FAIL" "REPORT_V4.md nie zawiera wszystkich ID (brak $MISSING_IDS)"
    fi
else
    report_gate "G-N10" "FAIL" "Brak pliku docs/REPORT_V4.md"
fi

# G-DOCS: python3 scripts/check_doc_citations.py kończy się kodem 0
DOCS_OUTPUT=$(python3 scripts/check_doc_citations.py 2>&1)
DOCS_STATUS=$?
if [ "$DOCS_STATUS" -eq 0 ]; then
    report_gate "G-DOCS" "PASS" "Wszystkie przywołania linii w dokumentacji trafiają w kod"
else
    report_gate "G-DOCS" "FAIL" "Wykryto nieaktualne przywołania w dokumentacji"
    echo "$DOCS_OUTPUT"
fi

# G-EVID: python3 scripts/check_report_evidence.py kończy się kodem 0
EVID_OUTPUT=$(python3 scripts/check_report_evidence.py 2>&1)
EVID_STATUS=$?
if [ "$EVID_STATUS" -eq 0 ]; then
    report_gate "G-EVID" "PASS" "Raporty zweryfikowane pod kątem autentyczności dowodów"
else
    report_gate "G-EVID" "FAIL" "Wykryto sfabrykowane dowody lub nieprawdziwe czasy w raportach"
    echo "$EVID_OUTPUT"
fi


# G-TESTS: pytest -q kończy się kodem 0; npm run build kończy się kodem 0
echo "Sprawdzanie testów pytest i kompilacji frontendu..."
PYTEST_STATUS=0
.venv/bin/pytest -q tests/ >/dev/null 2>&1 || PYTEST_STATUS=$?
BUILD_STATUS=0
(cd frontend && npm run build >/dev/null 2>&1) || BUILD_STATUS=$?

if [ "$PYTEST_STATUS" -eq 0 ] && [ "$BUILD_STATUS" -eq 0 ]; then
    report_gate "G-TESTS" "PASS" "pytest i npm run build kończą się kodem 0"
else
    report_gate "G-TESTS" "FAIL" "Testy lub build nie przeszły (pytest=$PYTEST_STATUS, build=$BUILD_STATUS)"
fi

echo "----------------------------------------------"
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "WYNIK KOŃCOWY: WSZYSTKIE BRAMKI ZIELONE (PASS)"
    exit 0
else
    echo "WYNIK KOŃCOWY: $FAIL_COUNT BRAMEK CZERWONYCH (FAIL)"
    exit 1
fi
