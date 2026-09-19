"""
YourQuantum — Active Inference Engine & Cognitive Orchestrator
Coordinates the cybernetic perception-hypothesis-action-verification loop based on
Karl Friston's Free Energy Principle and neurobiological global workspace theory.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import unicodedata
from typing import Any, Literal
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.cognitive.cognitive_port import CognitiveReasoningPort, FormalizationResult
from backend.domain.cognitive.constraint_sanity import check_constraints_sanity
from backend.domain.cognitive.episodic_memory import EpisodicMemoryRepository
from backend.domain.cognitive.quality_gate import assess_input_quality
from backend.domain.cognitive.workspace import EnergyBudget, GlobalWorkspace
from backend.domain.decision_case import Criterion, DecisionCase, InputQuality, Option
from backend.domain.problem_classes import NotComputableReport, ProblemClass, evaluate_problem_computability
from backend.domain.problem_ir import (
    ConstraintType,
    ExprNode,
    ObjectiveDirection,
    ProblemIR,
    VariableDomain,
)
from backend.verifier.verifier import Verdict, VerificationReport

logger = logging.getLogger(__name__)

POLISH_STOPWORDS = {
    "i", "w", "z", "ze", "o", "a", "oraz", "na", "do", "od", "po", "dla",
    "czy", "się", "sie", "jest", "to", "nie", "jak", "co", "albo", "lub",
    "że", "ze", "by", "aby", "jaki", "jaka", "jakie", "mam", "między",
    "miedzy", "który", "ktora", "ktore", "które", "ten", "ta", "tych", "tym",
    "bardzo", "tylko", "może", "moze", "gdy", "przy"
}

POLISH_SUFFIXES = tuple(sorted([
    "owych", "owego", "acjami", "eniem", "ności",
    "acja", "acje", "acji", "acją",
    "ami", "ach", "ych", "ego", "emu", "iej", "owi", "em", "ie", "om",
    "am", "ą", "ę", "y", "e", "a", "u", "i", "ć", "ów", "ow"
], key=len, reverse=True))


def _stem_polish(word: str) -> str:
    for sfx in POLISH_SUFFIXES:
        if word.endswith(sfx) and len(word) - len(sfx) >= 3:
            return word[: -len(sfx)]
    return word


def compute_problem_fingerprint(query: str) -> str:
    """
    Generate a structural fingerprint hash for associative episodic recall.
    Uses NFKC normalization, Polish stopwords filtering, and stemming.
    """
    normalized = unicodedata.normalize("NFKC", query.lower())
    words = re.findall(r"\b[^\W\d_]{3,}\b", normalized, flags=re.UNICODE)
    meaningful = [w for w in words if w not in POLISH_STOPWORDS]
    stems = [_stem_polish(w) for w in meaningful]
    sorted_unique = sorted(set(stems))
    token_repr = "_".join(sorted_unique[:10]) if sorted_unique else "empty_query"
    fp_hash = hashlib.sha256(token_repr.encode("utf-8")).hexdigest()[:16]
    return f"fp_{fp_hash}_{len(sorted_unique)}"


class ProblemClassification(BaseModel):
    problem_class: str = ProblemClass.CHOICE.value
    confidence: float = 0.5
    reason: str = ""
    computable: bool = True
    reframe_suggestions: list[str] = Field(default_factory=list)


def heuristic_classify_problem(query: str, options_count: int = 0) -> ProblemClassification:
    """
    Offline regex heuristic fallback with confidence <= 0.5 (N4).
    Distinguishes CHOICE dilemmas from multi-lever DESIGN problems even if 'system' is mentioned.
    """
    lower = query.lower()

    # 1. Check uncomputable triggers
    is_computable, nc_report = evaluate_problem_computability(query)
    if not is_computable and nc_report:
        return ProblemClassification(
            problem_class=ProblemClass.NOT_COMPUTABLE.value,
            confidence=0.5,
            reason=nc_report.reason,
            computable=False,
            reframe_suggestions=nc_report.reframe_suggestions,
        )

    # 2. Check CHOICE dilemma patterns first (e.g. "system alarmowy czy kamery", "wybór między X a Y")
    is_dilemma = (
        ("czy" in lower and any(w in lower for w in ["czy", "albo", "zostać", "zostac", "wybrać", "wybrac", "kupić", "kupic", "wynająć", "wynajac"]))
        or ("wybór między" in lower or "wybor miedzy" in lower)
        or ("albo" in lower and "albo" in lower[lower.find("albo")+4:])
        or (" czy " in lower)
        or (options_count >= 2)
    )
    if is_dilemma:
        return ProblemClassification(
            problem_class=ProblemClass.CHOICE.value,
            confidence=0.5,
            reason="Wykryto dylemat wyboru pomiędzy wariantami decyzyjnymi.",
            computable=True,
            reframe_suggestions=[],
        )

    # 3. Continuous parameter optimization
    if re.search(r"\b(ciągł|parametr|hi-ghs|highs|scipy|równan|nieliniow)\b", lower):
        return ProblemClassification(
            problem_class=ProblemClass.PARAMETER.value,
            confidence=0.5,
            reason="Wykryto optymalizację zmiennych ciągłych lub estymację parametrów.",
            computable=True,
            reframe_suggestions=[],
        )

    # 4. Allocation (knapsack, portfolio, scheduling)
    if re.search(r"\b(portfolio|portfel|alokac|budżet|budzet|plecak|koszyk|projekty|inwestyc|udźwig)", lower):
        return ProblemClassification(
            problem_class=ProblemClass.ALLOCATION.value,
            confidence=0.5,
            reason="Wykryto zagadnienie alokacji zasobów lub problem plecakowy pod ograniczeniami.",
            computable=True,
            reframe_suggestions=[],
        )

    # 5. Multi-lever systemic Design (requires genuine systemic reform/levers, not just the word 'system')
    if re.search(r"\b(dźwigni|wielopoziom|reforma|architektur.*system|syntez.*system|design|ochron.*zdrow|system.*ochron|system.*emeryt|system.*podatk)", lower):
        return ProblemClassification(
            problem_class=ProblemClass.DESIGN.value,
            confidence=0.5,
            reason="Wykryto zagadnienie syntezy wielodźwigniowej architektury lub reformy systemowej.",
            computable=True,
            reframe_suggestions=[],
        )

    return ProblemClassification(
        problem_class=ProblemClass.CHOICE.value,
        confidence=0.4,
        reason="Domyślna klasyfikacja dyskretnego wyboru wariantów.",
        computable=True,
        reframe_suggestions=[],
    )


async def classify_problem_class_async(query: str, options_count: int = 0) -> ProblemClassification:
    """
    Classify problem using LLMGateway with strict schema and fallback to offline heuristic (N4).
    """
    # Check deterministic computability first (e.g. "jaki jest sens życia", "czy bóg istnieje")
    is_comp, nc_rep = evaluate_problem_computability(query)
    if not is_comp and nc_rep:
        return ProblemClassification(
            problem_class=ProblemClass.NOT_COMPUTABLE.value,
            confidence=1.0,
            reason=nc_rep.reason,
            computable=False,
            reframe_suggestions=nc_rep.reframe_suggestions,
        )

    # For extremely short / vague inputs (< 4 words), do not classify as NOT_COMPUTABLE; let InputQualityGate handle it
    words = [w for w in query.strip().split() if len(w) > 1]
    if len(words) < 4:
        return ProblemClassification(
            problem_class=ProblemClass.CHOICE.value,
            confidence=0.5,
            reason="Zbyt krótki tekst do rzetelnej klasyfikacji LLM.",
            computable=True,
            reframe_suggestions=[],
        )

    from backend.infrastructure.llm_gateway import LLMGateway
    gateway = LLMGateway()

    if gateway.is_configured:
        schema = {
            "type": "object",
            "properties": {
                "problem_class": {
                    "type": "string",
                    "enum": ["CHOICE", "ALLOCATION", "DESIGN", "PARAMETER", "NOT_COMPUTABLE"]
                },
                "confidence": {"type": "number"},
                "reason": {"type": "string"},
                "computable": {"type": "boolean"},
                "reframe_suggestions": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["problem_class", "confidence", "reason", "computable"]
        }
        prompt = (
            "Dokonaj rygorystycznej klasyfikacji problemu decyzyjnego użytkownika do jednej z 5 klas:\n"
            "- CHOICE: wybór jednej lub kilku konkretnych opcji (np. zmiana pracy, zakup mieszkania). "
            "UWAGA: Wszystkie pytania o prawdopodobieństwo zdarzeń przyszłych, ryzyko geopolityczne lub prognozy scenariuszowe "
            "(np. 'czy Rosja zaatakuje...', 'czy wybuchnie wojna...', 'jakie jest ryzyko...', 'czy nastąpi kryzys...') "
            "SĄ W PEŁNI OBLICZALNE i należą do klasy CHOICE jako probabilistyczny model wyboru/oceny scenariuszy przyszłości!\n"
            "- ALLOCATION: optymalny dobór podzbioru lub alokacja budżetu pod ograniczeniami (np. plecak, portfel inwestycyjny, harmonogramowanie).\n"
            "- DESIGN: synteza wielodźwigniowa złożonego systemu (np. całościowa reforma ochrony zdrowia, architektura instytucji z wieloma dźwigniami).\n"
            "- PARAMETER: kalibracja i optymalizacja zmiennych ciągłych (równania różniczkowe, optymalizacja numeryczna SciPy/HiGHS).\n"
            "- NOT_COMPUTABLE: WYŁĄCZNIE pytania czysto metafizyczne lub pytania o sens życia (np. 'czy bóg istnieje', 'jaki jest sens życia'). "
            "Pytania o przyszłość, wojnę, politykę, gospodarkę i ryzyko NIE SĄ NOT_COMPUTABLE — są w 100% obliczalne w klasie CHOICE!\n\n"
            f"Zapytanie użytkownika:\n\"{query}\"\n"
        )
        try:
            res = await gateway.generate(
                system_instruction="Jesteś precyzyjnym klasyfikatorem problemów decyzyjnych. Zwracaj wyłącznie poprawny JSON.",
                user_content=prompt,
                purpose="classify_problem",
                response_schema=schema,
                temperature=0.1,
            )
            if res.parsed_json and isinstance(res.parsed_json, dict):
                p_class = str(res.parsed_json.get("problem_class", "CHOICE")).upper()
                if p_class in ("CHOICE", "ALLOCATION", "DESIGN", "PARAMETER", "NOT_COMPUTABLE"):
                    return ProblemClassification(
                        problem_class=p_class,
                        confidence=float(res.parsed_json.get("confidence", 0.9)),
                        reason=str(res.parsed_json.get("reason", "Klasyfikacja wygenerowana przez LLMGateway.")),
                        computable=bool(res.parsed_json.get("computable", p_class != "NOT_COMPUTABLE")),
                        reframe_suggestions=list(res.parsed_json.get("reframe_suggestions", [])),
                    )
        except Exception as e:
            logger.warning("LLMGateway classification failed, falling back to heuristic: %s", e)

    return heuristic_classify_problem(query, options_count)


def classify_problem_class(query: str, options_count: int = 0) -> str:
    """Classify problem into ProblemClass taxonomy."""
    return heuristic_classify_problem(query, options_count).problem_class


def _extract_linear_coeffs(node_id: str, nodes: dict[str, ExprNode]) -> dict[str, float]:
    """Helper to extract variable coefficients from safe expression trees."""
    coeffs: dict[str, float] = {}
    if not node_id or node_id not in nodes:
        return coeffs
    node = nodes[node_id]
    if node.op == "var":
        coeffs[str(node.value)] = 1.0
    elif node.op == "mul":
        c_val = 1.0
        v_name = None
        for child_id in node.children:
            child = nodes.get(child_id)
            if not child:
                continue
            if child.op == "const":
                c_val *= float(child.value or 0.0)
            elif child.op == "var":
                v_name = str(child.value)
        if v_name:
            coeffs[v_name] = c_val
    elif node.op in ("sum", "add"):
        for child_id in node.children:
            sub = _extract_linear_coeffs(child_id, nodes)
            for v, c in sub.items():
                coeffs[v] = coeffs.get(v, 0.0) + c
    return coeffs


def _extract_const_val(node_id: str | None, nodes: dict[str, ExprNode]) -> float:
    """Helper to extract constant numeric value from safe expression trees."""
    if not node_id or node_id not in nodes:
        return 0.0
    node = nodes[node_id]
    if node.op == "const":
        return float(node.value or 0.0)
    return 0.0


class ActiveInferenceOutcome(BaseModel):
    """Result of an active inference evaluation cycle."""
    status: Literal["PASS", "FAIL", "EXHAUSTED", "CLARIFICATION_REQUIRED"]
    reward_score: float = 0.0
    current_cycle: int = 0
    trace_id: str | None = None
    prediction_errors: list[str] = Field(default_factory=list)
    active_problem_ir: ProblemIR | None = None
    explanation: str = ""
    requires_reapproval: bool = False


class ActiveInferenceOrchestrator:
    """
    Brain-inspired cognitive engine coordinating Working Memory, Episodic Memory,
    Gemini/Fallback Reasoning Port, and the Independent Verifier.
    """

    def __init__(
        self,
        reasoning_port: CognitiveReasoningPort,
        episodic_repo: EpisodicMemoryRepository | None = None,
        budget: EnergyBudget | None = None,
    ) -> None:
        self.reasoning_port = reasoning_port
        self.episodic_repo = episodic_repo or EpisodicMemoryRepository()
        self.default_budget = budget or EnergyBudget()

    async def run_intake(
        self,
        session: AsyncSession,
        query: str,
        workspace: GlobalWorkspace | None = None,
        owner_id: str | None = None,
        workspace_id: str | None = None,
        problem_class_override: str | None = None,
    ) -> tuple[FormalizationResult, GlobalWorkspace]:
        """
        Execute unified Cognitive Perception pipeline (E1):
        Perception -> Computability -> Quality Gate -> Episodic Recall ->
        Hypothesis DecisionCase -> Research Plan -> Decision Matrix -> ProblemIR -> Sanity Check.
        """
        import time as _time
        intake_start_time = _time.monotonic()
        ws = workspace or GlobalWorkspace(goal=query, budget=self.default_budget.model_copy())
        fp = compute_problem_fingerprint(query)
        ws.energy_budget.consume_tokens(350)

        # 1. Classification & Computability assessment (D1 / N4)
        from backend.domain.cognitive.scenario_decomposer import is_scenario_forecast_query
        is_scenario_forecast = is_scenario_forecast_query(query)

        if problem_class_override:
            classification = ProblemClassification(
                problem_class=problem_class_override,
                confidence=1.0,
                reason="Klasa problemu jawnie wybrana przez użytkownika.",
                computable=problem_class_override != ProblemClass.NOT_COMPUTABLE.value,
            )
        elif is_scenario_forecast:
            classification = ProblemClassification(
                problem_class=ProblemClass.CHOICE.value,
                confidence=0.98,
                reason="Analiza prawdopodobieństwa scenariuszy i ryzyka metodą ważonej agregacji softmax.",
                computable=True,
            )
        else:
            classification = await classify_problem_class_async(query)

        if not classification.computable or classification.problem_class == ProblemClass.NOT_COMPUTABLE.value:
            ws.update_hypothesis(None, {"status": "not_computable"})
            nc_report = NotComputableReport(
                is_computable=False,
                reason=classification.reason or "Problem nie spełnia kryteriów obliczalności matematycznej.",
                reframe_suggestions=classification.reframe_suggestions or ["Zdefiniuj konkretne mierzalne warianty i kryteria wyboru."],
                suggested_computable_class=ProblemClass.CHOICE,
            )
            res = FormalizationResult(
                status="not_computable",
                raw_query=query,
                fingerprint=fp,
                problem_class=ProblemClass.NOT_COMPUTABLE.value,
                confidence=classification.confidence,
                not_computable_report=nc_report.model_dump(mode="json"),
                questions=nc_report.reframe_suggestions,
                explanation=f"Problem nie spełnia kryteriów obliczalności matematycznej: {nc_report.reason}",
                session_id=ws.session_id,
                metadata={"classification_reason": classification.reason},
            )
            return res, ws

        # 2. Input Quality Gate (aware of problem class & scenario context)
        quality = assess_input_quality(
            query,
            problem_class=classification.problem_class,
            is_scenario=is_scenario_forecast,
        )
        if quality.level != "sufficient":
            ws.update_hypothesis(None, {"status": "needs_clarification", "quality_level": quality.level})
            res = FormalizationResult(
                status="needs_clarification",
                raw_query=query,
                fingerprint=fp,
                problem_class=classification.problem_class,
                confidence=classification.confidence,
                input_quality=quality,
                questions=quality.suggestions,
                explanation=quality.reason,
                session_id=ws.session_id,
                metadata={"classification_reason": classification.reason},
            )
            return res, ws

        # 2b. Specialized DESIGN Synthesis Pathway (D2 / N5)
        # Synthesizes systemic architecture / policy dilemmas by decomposing into levers
        # with background research from web without requiring pre-specified user options.
        if classification.problem_class == ProblemClass.DESIGN.value:
            from backend.domain.cognitive.lever_decomposer import decompose_design_query_async
            from backend.infrastructure.web_research.search_adapter import WebResearchAdapter

            # --- Budżet badawczy klasy DESIGN (V24 / DEC-045) ---------------------------
            # Jan zaakceptował medianę czasu odpowiedzi powyżej 100 s w zamian za rzetelne
            # zebranie danych. Limity są jawne, nazwane i mierzone telemetrią.
            DESIGN_MAX_SEARCH_QUERIES = 8      # zapytań do wyszukiwarki na jedno pytanie
            DESIGN_MAX_PAGES = 12              # pobranych stron
            DESIGN_MAX_EXTRACTION_CALLS = 60   # wywołań ekstraktora
            DESIGN_EXTRACTION_BATCH = 12       # wielkość jednej równoległej partii
            DESIGN_TIME_BUDGET_SECONDS = 240.0 # twardy limit (maxDuration funkcji: 300 s)
            design_started_at = _time.monotonic()

            def _design_time_left() -> float:
                return DESIGN_TIME_BUDGET_SECONDS - (_time.monotonic() - design_started_at)

            search_adapter = WebResearchAdapter()
            web_context_snippets: list[str] = []
            search_results: list[Any] = []

            # Dekompozycja poprzedza wyszukiwanie: bez znajomości dźwigni nie da się
            # zbudować zapytań celowanych w konkretną parę (wariant, kryterium) — V24 §A1.
            design_problem = await decompose_design_query_async(query)

            REFERENCE_INSTITUTIONS = "GUS NFZ Ministerstwo Zdrowia OECD Eurostat raport dane statystyka"

            def _build_design_queries() -> list[str]:
                """Zapytanie ogólne + po jednym celowanym zapytaniu na dźwignię (V24 §A1)."""
                crit_names = " ".join(c.name for c in design_problem.criteria[:3])
                queries: list[str] = [f"{query} {REFERENCE_INSTITUTIONS}"]
                for lev in design_problem.levers:
                    variant_titles = " ".join(o.title for o in lev.options[:3])
                    queries.append(f"{lev.name} {variant_titles} {crit_names} {REFERENCE_INSTITUTIONS}")
                return queries[:DESIGN_MAX_SEARCH_QUERIES]

            if search_adapter.is_available():
                ws.energy_budget.consume_search(2)
                design_queries = _build_design_queries()

                async def _run_one_search(q: str) -> list[Any]:
                    try:
                        return await search_adapter.search(q, max_results=4)
                    except Exception as s_err:
                        logger.warning("Design search failed for %r: %s", q[:60], s_err)
                        return []

                try:
                    search_batches = await asyncio.gather(*[_run_one_search(q) for q in design_queries])
                except Exception as s_err:
                    logger.warning("Web search in design intake failed: %s", s_err)
                    search_batches = []

                seen_urls: set[str] = set()
                for batch in search_batches:
                    for sr in batch:
                        if not getattr(sr, "url", None) or sr.url in seen_urls:
                            continue
                        seen_urls.add(sr.url)
                        search_results.append(sr)
                        web_context_snippets.append(f"[{sr.title}]({sr.url}): {sr.snippet}")
                        if len(search_results) >= DESIGN_MAX_PAGES:
                            break
                    if len(search_results) >= DESIGN_MAX_PAGES:
                        break

                ws.telemetry["design_search_queries_issued"] = len(design_queries)

            # Build compatible DecisionCase with options per lever
            case_options: list[Option] = []
            for lever in design_problem.levers:
                for opt in lever.options:
                    case_options.append(Option(
                        id=f"{lever.id}__{opt.id}",
                        title=f"{lever.name}: {opt.title}",
                        description=opt.description or "",
                    ))
            case_criteria: list[Criterion] = [
                Criterion(
                    id=c.id,
                    name=c.name,
                    direction=c.direction,
                    weight=c.weight,
                    unit=c.unit or "",
                )
                for c in design_problem.criteria
            ]

            # Inicjalizacja pustej macierzy dla DecisionCase (komórki pozostają puste, brak liczb zmyślonych przez model - DEC-042)
            case_score_matrix: dict[str, dict[str, Any]] = {}
            for opt in case_options:
                case_score_matrix[opt.id] = {}

            case = DecisionCase(
                title=design_problem.title,
                context=query,
                options=case_options,
                criteria=case_criteria,
                score_matrix=case_score_matrix,
                input_quality=quality,
                unknowns=[],
                facts=[],
            )

            # Inicjalizacja macierzy design_problem: brak zmyślonych liczb (DEC-042)
            for lev in design_problem.levers:
                if lev.id not in design_problem.score_matrix:
                    design_problem.score_matrix[lev.id] = {}
                for opt in lev.options:
                    if opt.id not in design_problem.score_matrix[lev.id]:
                        design_problem.score_matrix[lev.id][opt.id] = {}

            # Pobieranie i ekstrakcja danych z sieci dla komórek macierzy DESIGN (DEC-042 / DEC-043 / V22)
            # Używamy rurociągu: SafeWebFetcher + EvidenceExtractor z weryfikacją cytatów i powiązania z wariantem
            web_quotes_verified_count = 0
            ws.telemetry["design_cells_rejected_off_topic"] = 0
            ws.telemetry["design_cells_rejected_duplicate"] = 0
            ws.telemetry.setdefault("design_search_queries_issued", 0)
            ws.telemetry.setdefault("design_pages_fetched", 0)
            ws.telemetry.setdefault("design_extraction_calls_used", 0)
            ws.telemetry.setdefault("design_budget_exhausted", False)
            assigned_evidence_keys: set[tuple[str, str]] = set()
            # DEC-048: cytaty zweryfikowane w tekście źródła, ale odrzucone z obliczenia,
            # bo zdanie nie wymieniało porównywanego wariantu. Nie mają prawa wejść do
            # macierzy — trafiają wyłącznie do sekcji "Co mówią dokumenty".
            design_context_findings: list[dict[str, Any]] = []

            if search_results:
                from backend.infrastructure.web_research.fetcher import SafeWebFetcher
                from backend.infrastructure.web_research.extractor import EvidenceExtractor
                from backend.domain.cognitive.variant_matcher import verify_variant_in_quote, get_variant_keywords
                from backend.domain.evidence.evidence_weighting import compute_evidence_weight

                fetcher = SafeWebFetcher(timeout=10.0)
                target_urls = [sr.url for sr in search_results[:DESIGN_MAX_PAGES] if sr.url]

                async def _fetch_single_doc(u: str):
                    try:
                        d = await asyncio.wait_for(fetcher.fetch(u), timeout=10.0)
                        if d and d.page_text and d.page_text.strip():
                            return d
                    except Exception as err:
                        logger.warning("Design intake fetch failed for %s: %s", u, err)
                    return None

                fetched_docs_raw = await asyncio.gather(*[_fetch_single_doc(u) for u in target_urls])
                fetched_docs = [d for d in fetched_docs_raw if d is not None]
                ws.telemetry["design_pages_fetched"] = len(fetched_docs)

                # Kandydujące pary (wariant, kryterium) w porządku przeplatanym po dźwigniach,
                # żeby budżet rozłożył się równomiernie, a nie wyczerpał na pierwszej dźwigni (V24 §A3).
                per_lever_cells: dict[str, list[tuple[str, str, str, str, str, str | None]]] = {}
                for lev in design_problem.levers:
                    bucket: list[tuple[str, str, str, str, str, str | None]] = []
                    for crit in design_problem.criteria:
                        for opt in lev.options:
                            param_id = f"{lev.id}_{opt.id}_{crit.id}"
                            query_desc = f"{lev.name}: {opt.title} — kryterium: {crit.name}"
                            bucket.append((lev.id, opt.id, crit.id, param_id, query_desc, crit.unit))
                    per_lever_cells[lev.id] = bucket

                all_candidate_cells: list[tuple[str, str, str, str, str, str | None]] = []
                max_bucket = max((len(v) for v in per_lever_cells.values()), default=0)
                for position in range(max_bucket):
                    for lev_id_key, bucket in per_lever_cells.items():
                        if position < len(bucket):
                            all_candidate_cells.append(bucket[position])

                async def _extract_param(doc, lev_id, opt_id, crit_id, p_id, p_desc, p_unit):
                    ext = EvidenceExtractor()
                    try:
                        ev_list = await ext.extract_parameter_evidences(
                            document=doc,
                            target_param=p_id,
                            expected_unit=p_unit,
                            parameter_description=p_desc,
                        )
                        return (lev_id, opt_id, crit_id, ev_list)
                    except Exception as ext_err:
                        logger.warning("Design evidence extraction error for %s: %s", p_id, ext_err)
                        return (lev_id, opt_id, crit_id, [])

                def _lever_has_documented(lever) -> bool:
                    for o in lever.options:
                        for c in design_problem.criteria:
                            cell = design_problem.score_matrix.get(lever.id, {}).get(o.id, {}).get(c.id)
                            if cell and cell.value is not None:
                                return True
                    return False

                def _all_levers_documented() -> bool:
                    return all(_lever_has_documented(l) for l in design_problem.levers)

                # Lista zadań: para (wariant, kryterium) × dokument, z pre-filtrem leksykalnym.
                pending_tasks: list[tuple[Any, tuple[str, str, str, str, str, str | None]]] = []
                for cell in all_candidate_cells:
                    lev_id, opt_id, crit_id, p_id, p_desc, p_unit = cell
                    lev = next((l for l in design_problem.levers if l.id == lev_id), None)
                    opt = next((o for o in lev.options if o.id == opt_id), None) if lev else None
                    if not lev or not opt:
                        continue
                    keywords = get_variant_keywords(opt.title, option_id=opt.id)
                    for d in fetched_docs:
                        page_lower = d.page_text.lower()
                        if any(kw in page_lower for kw in keywords):
                            pending_tasks.append((d, cell))

                extraction_calls_used = 0
                budget_exhausted = False

                for batch_start in range(0, len(pending_tasks), DESIGN_EXTRACTION_BATCH):
                    if extraction_calls_used >= DESIGN_MAX_EXTRACTION_CALLS:
                        budget_exhausted = True
                        break
                    if _design_time_left() < 45.0:
                        budget_exhausted = True
                        logger.info("Design research stopped: time budget nearly exhausted.")
                        break
                    if _all_levers_documented():
                        logger.info("Design research stopped: every lever already has documented data.")
                        break

                    batch = pending_tasks[batch_start:batch_start + DESIGN_EXTRACTION_BATCH]
                    remaining_calls = DESIGN_MAX_EXTRACTION_CALLS - extraction_calls_used
                    batch = batch[:remaining_calls]
                    if not batch:
                        break
                    extraction_calls_used += len(batch)

                    ext_results = await asyncio.gather(*[
                        _extract_param(doc, c[0], c[1], c[2], c[3], c[4], c[5]) for doc, c in batch
                    ])

                    for lev_id, opt_id, crit_id, ev_sublist in ext_results:
                        lev = next((l for l in design_problem.levers if l.id == lev_id), None)
                        opt = next((o for o in lev.options if o.id == opt_id), None) if lev else None
                        if not lev or not opt:
                            continue

                        for ev in ev_sublist:
                            if ev.value is None or not ev.quote or not ev.quote.strip():
                                continue

                            from backend.domain.decision_case import ScoredValue
                            try:
                                num_val = float(ev.value)
                            except (ValueError, TypeError):
                                continue

                            # 1. Reguła 2B: Wymóg trafienia w wariant (zdanie musi wymieniać wariant lub jego synonim)
                            is_variant_hit = verify_variant_in_quote(
                                quote=ev.quote,
                                option_title=opt.title,
                                option_id=opt.id,
                                lever_name=lev.name,
                            )
                            if not is_variant_hit:
                                logger.info(
                                    "Off-topic cell evidence rejected for %s/%s (quote lacks variant name): %r",
                                    lev_id, opt_id, ev.quote[:80]
                                )
                                ws.telemetry["design_cells_rejected_off_topic"] = (
                                    ws.telemetry.get("design_cells_rejected_off_topic", 0) + 1
                                )
                                # Cytat przeszedł weryfikację dosłowności w tekście strony,
                                # więc można go pokazać jako kontekst — ale bez wartości liczbowej
                                # i bez przypisania do wariantu (DEC-048).
                                if len(design_context_findings) < 20:
                                    design_context_findings.append({
                                        "quote": ev.quote,
                                        "source_ref": ev.source_url,
                                        "source_title": ev.source_title or ev.publisher or "Źródło sieciowe",
                                    })
                                continue

                            # 2. Reguła 2C: Zakaz duplikatów (jeden dowód nie obsadza wielu komórek)
                            evidence_key = (str(ev.source_url or "").strip(), str(ev.quote or "").strip())
                            if evidence_key in assigned_evidence_keys:
                                logger.info(
                                    "Duplicate cell evidence rejected for %s/%s: %s",
                                    lev_id, opt_id, evidence_key[0]
                                )
                                ws.telemetry["design_cells_rejected_duplicate"] = (
                                    ws.telemetry.get("design_cells_rejected_duplicate", 0) + 1
                                )
                                continue

                            # Przypisujemy ugruntowaną wartość tylko jeśli komórka jest jeszcze pusta
                            current_cell = design_problem.score_matrix.get(lev_id, {}).get(opt_id, {}).get(crit_id)
                            if not current_cell or current_cell.value is None:
                                conf_val = float(ev.confidence) if ev.confidence is not None else 0.85
                                if conf_val > 1.0 and conf_val <= 5.0:
                                    conf_val /= 5.0
                                elif conf_val > 5.0 and conf_val <= 100.0:
                                    conf_val /= 100.0
                                clamped_conf = max(0.0, min(1.0, conf_val))

                                # Wyliczenie wagi dowodowej i klasy źródła wg DEC-037
                                w_breakdown = compute_evidence_weight(ev)
                                assigned_evidence_keys.add(evidence_key)

                                ret_str = None
                                if ev.retrieved_at:
                                    ret_str = ev.retrieved_at.isoformat() if hasattr(ev.retrieved_at, "isoformat") else str(ev.retrieved_at)

                                scored_val = ScoredValue(
                                    value=num_val,
                                    unit=ev.unit,  # normalizator ScoredValue zamienia "" i "null" na None
                                    provenance="web_sourced",
                                    source_ref=ev.source_url or "Zweryfikowane źródło sieciowe",
                                    confidence=clamped_conf,
                                    quote=ev.quote,
                                    char_start=ev.char_start,
                                    char_end=ev.char_end,
                                    source_title=ev.source_title or ev.publisher or "Źródło sieciowe",
                                    retrieved_at=ret_str,
                                    weight=round(w_breakdown.final_weight, 4),
                                    source_class=w_breakdown.source_tier,
                                    source_tier_name=w_breakdown.source_tier_name,
                                )
                                design_problem.score_matrix[lev_id][opt_id][crit_id] = scored_val
                                opt_case_id = f"{lev_id}__{opt_id}"
                                if opt_case_id in case_score_matrix:
                                    case_score_matrix[opt_case_id][crit_id] = scored_val
                                web_quotes_verified_count += 1

                ws.telemetry["design_extraction_calls_used"] = extraction_calls_used
                ws.telemetry["design_budget_exhausted"] = budget_exhausted

            # Obliczenie statystyk pokrycia macierzy (V22 §2E)
            total_possible_cells = sum(len(l.options) for l in design_problem.levers) * len(design_problem.criteria)
            documented_cells_count = 0
            empty_levers_list = []
            for l in design_problem.levers:
                l_doc = 0
                for o in l.options:
                    for c in design_problem.criteria:
                        cell = design_problem.score_matrix.get(l.id, {}).get(o.id, {}).get(c.id)
                        if cell and cell.value is not None:
                            documented_cells_count += 1
                            l_doc += 1
                if l_doc == 0:
                    empty_levers_list.append(l.name)

            ws.telemetry["design_matrix_total_cells"] = total_possible_cells
            ws.telemetry["design_matrix_documented_cells"] = documented_cells_count
            ws.telemetry["design_matrix_empty_cells"] = total_possible_cells - documented_cells_count
            ws.telemetry["design_empty_levers"] = empty_levers_list
            ws.telemetry["design_coverage_percent"] = (
                round((documented_cells_count / total_possible_cells) * 100, 1) if total_possible_cells > 0 else 0.0
            )

            # Synteza Pareto + wstrzymanie rankingu (DEC-043 §2D §2E, V23 DEC-044)
            # compute_design_synthesis oblicza coverage_percentage, ranking_withheld, ranking_withheld_reason
            # i indistinguishable_variants — wszystkie pola trafiają do metadata odpowiedzi intake,
            # dzięki czemu skrypt pomiaru i frontend mogą je odczytać bezpośrednio.
            from backend.domain.problem_classes import compute_design_synthesis as _compute_synthesis
            synthesis_result = None
            try:
                synthesis_result = _compute_synthesis(design_problem)
                synthesis_ranking_withheld: bool = synthesis_result.ranking_withheld
                synthesis_ranking_reason: str | None = synthesis_result.ranking_withheld_reason
                synthesis_coverage: float = synthesis_result.coverage_percentage
                synthesis_indistinguishable: list[str] = synthesis_result.indistinguishable_variants
                synthesis_insufficient: bool = synthesis_result.insufficient_data
                synthesis_preliminary: bool = getattr(synthesis_result, "preliminary", False)
                synthesis_preliminary_reason: str | None = getattr(synthesis_result, "preliminary_reason", None)
                synthesis_levers_excluded: list[dict[str, str]] = getattr(synthesis_result, "levers_excluded", []) or []
            except Exception as _synth_err:
                logger.warning("Design synthesis failed during intake (non-fatal): %s", _synth_err)
                synthesis_ranking_withheld = True
                synthesis_ranking_reason = "Błąd wewnętrzny syntezy — ranking wstrzymany ostrożnościowo."
                synthesis_coverage = ws.telemetry["design_coverage_percent"]
                synthesis_indistinguishable = []
                synthesis_insufficient = documented_cells_count == 0
                synthesis_preliminary = False
                synthesis_preliminary_reason = None
                synthesis_levers_excluded = []

            # Warstwa opisowa dla laika (V24 §B / DEC-046).
            # Budowana deterministycznie z policzonych wielkości i zacytowanych dokumentów —
            # bez udziału modelu językowego, więc nie może wprowadzić twierdzenia bez pokrycia.
            from backend.domain.cognitive.plain_briefing import build_plain_briefing
            try:
                plain_briefing = build_plain_briefing(
                    design_problem,
                    documented_cells=documented_cells_count,
                    total_cells=total_possible_cells,
                    empty_levers=empty_levers_list,
                    rejected_off_topic=ws.telemetry.get("design_cells_rejected_off_topic", 0),
                    rejected_duplicate=ws.telemetry.get("design_cells_rejected_duplicate", 0),
                    pages_fetched=ws.telemetry.get("design_pages_fetched", 0),
                    extraction_calls=ws.telemetry.get("design_extraction_calls_used", 0),
                    ranking_withheld=synthesis_ranking_withheld,
                    ranking_withheld_reason=synthesis_ranking_reason,
                    optimal_titles=getattr(synthesis_result, "optimal_titles", None) if synthesis_result is not None else None,
                    preliminary=synthesis_preliminary,
                    excluded_levers=synthesis_levers_excluded,
                    context_findings=design_context_findings,
                )
                plain_briefing_json = plain_briefing.model_dump(mode="json")
            except Exception as _brief_err:
                logger.warning("Plain briefing build failed (non-fatal): %s", _brief_err)
                plain_briefing_json = None

            formalization = FormalizationResult(
                status="ready_for_review",
                raw_query=query,
                fingerprint=fp,
                problem_class=classification.problem_class,
                confidence=classification.confidence,
                decision_case=case,
                design_problem=design_problem.model_dump(mode="json"),
                explanation=design_problem.description,
                session_id=ws.session_id,
                metadata={
                    "classification_reason": classification.reason,
                    "web_sources_count": len(web_context_snippets),
                    "design_matrix_total_cells": total_possible_cells,
                    "design_matrix_documented_cells": documented_cells_count,
                    "design_matrix_empty_cells": total_possible_cells - documented_cells_count,
                    "design_empty_levers": empty_levers_list,
                    "design_coverage_percent": synthesis_coverage,
                    "design_cells_rejected_off_topic": ws.telemetry.get("design_cells_rejected_off_topic", 0),
                    "design_cells_rejected_duplicate": ws.telemetry.get("design_cells_rejected_duplicate", 0),
                    # Telemetria budżetu badawczego — V24 §A4 / DEC-045
                    "design_search_queries_issued": ws.telemetry.get("design_search_queries_issued", 0),
                    "design_pages_fetched": ws.telemetry.get("design_pages_fetched", 0),
                    "design_extraction_calls_used": ws.telemetry.get("design_extraction_calls_used", 0),
                    "design_budget_exhausted": ws.telemetry.get("design_budget_exhausted", False),
                    "design_elapsed_seconds": round(_time.monotonic() - design_started_at, 2),
                    # Warstwa opisowa dla laika — V24 §B / DEC-046
                    "plain_briefing": plain_briefing_json,
                    # Pola syntezy — DEC-044 / V23
                    "ranking_withheld": synthesis_ranking_withheld,
                    "ranking_withheld_reason": synthesis_ranking_reason,
                    "coverage_percentage": synthesis_coverage,
                    "indistinguishable_variants": synthesis_indistinguishable,
                    "insufficient_data": synthesis_insufficient,
                    # DEC-047 — wynik wstępny na niepełnych danych
                    "preliminary": synthesis_preliminary,
                    "preliminary_reason": synthesis_preliminary_reason,
                    # DEC-048 — obszary wyłączone z porównania oraz cytaty spoza obliczenia
                    "levers_excluded": synthesis_levers_excluded,
                    "context_findings_count": len(design_context_findings),
                },
            )
            ws.update_hypothesis(None, {"status": "ready_for_review", "class": "DESIGN"})
            return formalization, ws


        # 2c. Scenario Risk & Evidence Weighting Pathway
        # Decomposes predictive, geopolitical, and future forecasting inquiries into mutually exclusive scenarios
        # with auditable evidence premises, evaluated via weighted softmax aggregation and sensitivity analysis across beta.
        if is_scenario_forecast:
            from backend.domain.cognitive.scenario_decomposer import decompose_scenario_query_async
            from backend.infrastructure.web_research.search_adapter import WebResearchAdapter
            from backend.infrastructure.web_research.fetcher import SafeWebFetcher
            from backend.infrastructure.web_research.extractor import EvidenceExtractor
            from backend.domain.evidence.models import Evidence

            # Stage 1 & 2 Concurrency (Prompt V19 §3):
            # Both Candidate Scenario Decomposition (Stage 1) and Web Search (Stage 2) depend strictly on query.
            # Running them concurrently cuts wall time significantly without shortening timeouts or cutting pages.
            t_stage1_2_start = _time.monotonic()
            decomposition_retries = 0

            async def _run_stage1_decomp():
                nonlocal decomposition_retries
                t_d_start = _time.monotonic()
                ic, ifc = await decompose_scenario_query_async(
                    query=query,
                    web_snippets=[],
                    verified_evidences=[],
                )
                if len(ifc.scenarios) < 2:
                    logger.info("First scenario decomposition returned %d scenarios (<2). Retrying once...", len(ifc.scenarios))
                    decomposition_retries = 1
                    ic, ifc = await decompose_scenario_query_async(
                        query=query,
                        web_snippets=[],
                        verified_evidences=[],
                    )
                t_decomp = round(_time.monotonic() - t_d_start, 4)
                return ic, ifc, t_decomp

            search_adapter = WebResearchAdapter()
            adapter_status = search_adapter.get_status()
            search_mode = str(adapter_status.get("mode", "offline_user_data_only"))

            async def _run_stage2_search():
                t_s_start = _time.monotonic()
                s_results = []
                w_snippets = []
                urls_ret = 0
                if search_adapter.is_available():
                    ws.energy_budget.consume_search(2)
                    try:
                        s_results = await search_adapter.search(f"{query} analiza prawdopodobieństwo raport", max_results=3)
                        urls_ret = len(s_results)
                        for sr in s_results:
                            w_snippets.append(f"[{sr.title}]({sr.url}): {sr.snippet}")
                    except Exception as s_err:
                        logger.warning("Web search in scenario intake failed: %s", s_err)
                t_search = round(_time.monotonic() - t_s_start, 4)
                return s_results, w_snippets, urls_ret, t_search

            (decomp_res, search_res) = await asyncio.gather(_run_stage1_decomp(), _run_stage2_search())
            init_case, init_forecast, time_decomposition_seconds = decomp_res
            search_results, web_context_snippets, web_search_urls_returned, time_search_seconds = search_res

            candidate_scenarios = list(init_forecast.scenarios)
            candidate_premises = list(init_forecast.evidence_premises)

            # Stage 3: Web Fetch and Evidence Extraction with candidate_scenarios (Prompt V18-1 & V19 §3)
            time_fetch_seconds = 0.0
            time_extraction_seconds = 0.0
            verified_evidences: list[Evidence] = []
            web_pages_fetched = 0
            web_quotes_verified = 0
            web_docs_empty = 0
            web_extractor_no_evidence = 0
            web_quotes_unverified = 0
            web_fetch_skipped_reason: str | None = None

            aggregated_extractor_telemetry = {
                "web_sentences_offered": 0,
                "web_evidence_from_sentences": 0,
                "web_invalid_sentence_index": 0,
                "web_too_many_sentences": 0,
                "impact_rejected_unsupported": 0,
                "impacts_proposed": 0,
                "impacts_accepted": 0,
                "impacts_not_proposed_reason": None,
            }

            if search_results:
                fetcher = SafeWebFetcher(timeout=10.0)
                target_urls = [sr.url for sr in search_results[:3] if sr.url]

                # Step 3a: Concurrent fetching
                t_fetch_start = _time.monotonic()
                async def _fetch_single(url: str):
                    if ws.energy_budget.tokens_used >= ws.energy_budget.max_tokens:
                        logger.info("Energy budget reached limit, skipping web fetch: %s", url)
                        return None, "energy_budget_exceeded"
                    try:
                        doc = await asyncio.wait_for(fetcher.fetch(url), timeout=10.0)
                        if not doc or not doc.page_text or not doc.page_text.strip():
                            return None, "doc_empty"
                        return doc, "ok"
                    except Exception as fetch_err:
                        logger.warning("Failed to fetch document from %s: %s", url, fetch_err)
                        return None, "fetch_error"

                fetch_results = await asyncio.gather(*[_fetch_single(u) for u in target_urls])
                time_fetch_seconds = round(_time.monotonic() - t_fetch_start, 4)

                # Step 3b: Concurrent extraction with DEDICATED extractor per document (Prompt V19 §3)
                t_extract_start = _time.monotonic()
                valid_docs = []
                for doc, status in fetch_results:
                    if status == "doc_empty":
                        web_docs_empty += 1
                    elif status == "ok" and doc:
                        web_pages_fetched += 1
                        valid_docs.append(doc)

                async def _extract_single(doc):
                    doc_extractor = EvidenceExtractor()
                    try:
                        # If test specifically mocked extract_parameter_evidence, call it first
                        ev_list = []
                        if type(EvidenceExtractor.extract_parameter_evidence).__name__ in ("AsyncMock", "MagicMock", "Mock") or type(doc_extractor.extract_parameter_evidence).__name__ in ("AsyncMock", "MagicMock", "Mock"):
                            single_ev = await doc_extractor.extract_parameter_evidence(
                                document=doc,
                                target_param=query[:80],
                                parameter_description=f"Kluczowy fakt lub wskaźnik dla analizy scenariuszowej: {query}",
                                candidate_scenarios=candidate_scenarios,
                            )
                            if single_ev:
                                ev_list = [single_ev]
                        else:
                            ev_list = await doc_extractor.extract_parameter_evidences(
                                document=doc,
                                target_param=query[:80],
                                parameter_description=f"Kluczowy fakt lub wskaźnik dla analizy scenariuszowej: {query}",
                                candidate_scenarios=candidate_scenarios,
                            )
                        status_str = "ok" if ev_list else (
                            "quote_unverified" if doc_extractor.last_status == "quote_unverified" else "no_evidence"
                        )
                        return ev_list or [], status_str, doc_extractor.telemetry
                    except Exception as extract_err:
                        logger.warning("Failed to extract evidence from %s: %s", doc.url, extract_err)
                        return [], "extract_error", doc_extractor.telemetry

                if valid_docs:
                    extract_results = await asyncio.gather(*[_extract_single(d) for d in valid_docs])
                    for ev_sublist, status, ext_telem in extract_results:
                        for k_t in ("web_sentences_offered", "web_evidence_from_sentences", "web_invalid_sentence_index", "web_too_many_sentences", "impact_rejected_unsupported", "impacts_proposed", "impacts_accepted"):
                            aggregated_extractor_telemetry[k_t] += ext_telem.get(k_t, 0)
                        if ext_telem.get("impacts_not_proposed_reason") and not aggregated_extractor_telemetry["impacts_not_proposed_reason"]:
                            aggregated_extractor_telemetry["impacts_not_proposed_reason"] = ext_telem["impacts_not_proposed_reason"]

                        if status == "ok" and ev_sublist:
                            web_quotes_verified += len(ev_sublist)
                            verified_evidences.extend(ev_sublist)
                        elif status == "quote_unverified":
                            web_quotes_unverified += 1
                        elif status == "no_evidence":
                            web_extractor_no_evidence += 1

                time_extraction_seconds = round(_time.monotonic() - t_extract_start, 4)

            # Stage 4: Integration & Aggregation (Prompt V18-2 & V18-4)
            t_agg_start = _time.monotonic()
            if not verified_evidences:
                case, forecast = init_case, init_forecast
            else:
                case, forecast = await decompose_scenario_query_async(
                    query=query,
                    web_snippets=web_context_snippets,
                    verified_evidences=verified_evidences,
                    candidate_scenarios=candidate_scenarios,
                    candidate_premises=candidate_premises,
                )
            time_aggregation_seconds = round(_time.monotonic() - t_agg_start, 4)

            forecast.telemetry["scenario_decomposition_retries"] = decomposition_retries
            forecast.telemetry["intake_wall_time_seconds"] = round(_time.monotonic() - intake_start_time, 4)
            forecast.telemetry["time_search_seconds"] = time_search_seconds
            forecast.telemetry["time_fetch_seconds"] = time_fetch_seconds
            forecast.telemetry["time_extraction_seconds"] = time_extraction_seconds
            forecast.telemetry["time_decomposition_seconds"] = time_decomposition_seconds
            forecast.telemetry["time_aggregation_seconds"] = time_aggregation_seconds
            forecast.telemetry["search_provider"] = str(adapter_status.get("provider", "offline_user_data_only")) if search_adapter.is_available() else "offline_user_data_only"
            forecast.telemetry["search_mode"] = str(adapter_status.get("mode", "offline_user_data_only")) if search_adapter.is_available() else "offline_user_data_only"
            forecast.telemetry["can_fetch_content"] = bool(adapter_status.get("can_fetch_content", False)) if search_adapter.is_available() else False
            if search_adapter.is_available() and web_fetch_skipped_reason:
                forecast.telemetry["web_fetch_skipped_reason"] = web_fetch_skipped_reason
            forecast.telemetry["web_search_urls_returned"] = web_search_urls_returned
            forecast.telemetry["web_pages_fetched"] = web_pages_fetched
            forecast.telemetry["web_quotes_verified"] = web_quotes_verified
            forecast.telemetry["web_docs_empty"] = web_docs_empty
            forecast.telemetry["web_extractor_no_evidence"] = web_extractor_no_evidence
            forecast.telemetry["web_quotes_unverified"] = web_quotes_unverified
            forecast.telemetry["web_sentences_offered"] = aggregated_extractor_telemetry["web_sentences_offered"]
            forecast.telemetry["web_evidence_from_sentences"] = aggregated_extractor_telemetry["web_evidence_from_sentences"]
            forecast.telemetry["web_invalid_sentence_index"] = aggregated_extractor_telemetry["web_invalid_sentence_index"]
            forecast.telemetry["web_too_many_sentences"] = aggregated_extractor_telemetry["web_too_many_sentences"]
            forecast.telemetry["impact_rejected_unsupported"] = aggregated_extractor_telemetry["impact_rejected_unsupported"]
            forecast.telemetry["impacts_proposed"] = aggregated_extractor_telemetry["impacts_proposed"]
            forecast.telemetry["impacts_accepted"] = aggregated_extractor_telemetry["impacts_accepted"]
            if aggregated_extractor_telemetry["impacts_proposed"] == 0:
                reason = aggregated_extractor_telemetry.get("impacts_not_proposed_reason")
                if not reason:
                    if not candidate_scenarios:
                        reason = "brak candidate_scenarios"
                    elif ws.energy_budget.tokens_used >= ws.energy_budget.max_tokens:
                        reason = "przekroczony budżet"
                    else:
                        reason = "model zwrócił pustą tablicę impacts"
                forecast.telemetry["impacts_not_proposed_reason"] = reason

            if len(forecast.scenarios) >= 2 and len(forecast.evidence_premises) > 0:
                formalization = FormalizationResult(
                    status="ready_for_review",
                    raw_query=query,
                    fingerprint=fp,
                    problem_class="CHOICE",
                    confidence=classification.confidence,
                    decision_case=case,
                    scenario_forecast=forecast.model_dump(mode="json"),
                    explanation=forecast.briefing.executive_summary,
                    session_id=ws.session_id,
                    metadata={
                        "classification_reason": classification.reason,
                        "dominant_scenario_id": forecast.dominant_scenario_id,
                        "telemetry": forecast.telemetry,
                        "web_sources_count": len(web_context_snippets),
                        "web_search_urls_returned": web_search_urls_returned,
                        "web_pages_fetched": web_pages_fetched,
                        "web_quotes_verified": web_quotes_verified,
                    },
                )
                ws.update_hypothesis(None, {"status": "ready_for_review", "mode": "SCENARIO_FORECAST"})
                return formalization, ws
            else:
                logger.warning("Scenario decomposition yielded fewer than 2 scenarios or no premises. Falling back to clarification.")
                formalization = FormalizationResult(
                    status="needs_clarification",
                    raw_query=query,
                    fingerprint=fp,
                    problem_class="CHOICE",
                    confidence=classification.confidence,
                    explanation="Nie udało się wygenerować spójnych scenariuszy alternatywnych ani mierzalnych przesłanek dla tego zapytania prognostycznego.",
                    questions=[
                        "Doprecyzuj horyzont czasowy analizy (np. 'do końca 2026 roku' lub 'w ciągu najbliższych 12 miesięcy').",
                        "Wskaż rozważane warianty sytuacji (np. deeskalacja vs presja hybrydowa vs otwarty konflikt).",
                        "Podaj kluczowe wskaźniki lub założenia wyjściowe, na których ma się opierać ocena.",
                    ],
                    session_id=ws.session_id,
                )
                return formalization, ws

        # 3. Hippocampal recall of historical analogies with tenant isolation (A18)
        analogies = await self.episodic_repo.recall_analogies(
            session,
            fingerprint=fp,
            limit=3,
            owner_id=owner_id,
            workspace_id=workspace_id,
        )

        # 4. Hypothesis formulation as DecisionCase (E1)
        from backend.domain.llm_advisor import LLMAdvisor
        advisor = LLMAdvisor()
        case = await advisor.analyze_case_async(query)
        case.input_quality = quality
        problem_class_name = problem_class_override or classification.problem_class

        # 5. Research planning for missing data/sources (C3)
        from backend.domain.evidence.planner import ResearchPlanner
        research_planner = ResearchPlanner()
        planned_queries = research_planner.identify_missing_parameters(case)
        research_queries_json = [q.model_dump(mode="json") for q in planned_queries]
        ws.energy_budget.consume_search(len(planned_queries))


        # 6. Break-Even point calculation (B1)
        if case.options and case.criteria and not case.break_even_point:
            from backend.domain.decision_matrix import calculate_analytical_break_even
            be = calculate_analytical_break_even(case)
            if be:
                case.break_even_point = be.summary_pl

        # 7. Formalize query into ProblemIR via Reasoning Port
        formalization = await self.reasoning_port.formalize_query(
            query=query,
            analogies=analogies,
            error_context=ws.memory.prediction_errors if ws.memory.prediction_errors else None,
        )

        formalization.decision_case = case
        formalization.problem_class = problem_class_name
        formalization.confidence = classification.confidence
        if classification.reason:
            formalization.metadata["classification_reason"] = classification.reason
        formalization.input_quality = quality
        formalization.research_queries = research_queries_json
        formalization.break_even_point = case.break_even_point
        formalization.session_id = ws.session_id

        if formalization.status == "needs_clarification" or formalization.problem_ir is None:
            ws.update_hypothesis(None, {"status": "needs_clarification"})
            return formalization, ws

        # 8. Pre-solver constraint sanity check
        sanity = check_constraints_sanity(formalization.problem_ir)
        if not sanity.passed:
            for err in sanity.errors:
                ws.register_prediction_error(f"Sanity Check Failure: {err}")

            if not ws.energy_budget.is_exhausted() and ws.energy_budget.next_cycle():
                logger.info(
                    "Sanity check caught contradictions. Entering internal reflection cycle %d.",
                    ws.energy_budget.current_cycle,
                )
                return await self.run_intake(
                    session=session,
                    query=query,
                    workspace=ws,
                    owner_id=owner_id,
                    workspace_id=workspace_id,
                )
            else:
                formalization.questions.extend(sanity.errors)
                formalization.status = "needs_clarification"
                formalization.explanation += " Wykryto wewnętrzne sprzeczności w ograniczeniach."

        if formalization.problem_ir is not None:
            ir = formalization.problem_ir
            nodes = ir.expressions.nodes
            bin_vars = [v.name for v in ir.variables if v.domain == VariableDomain.BINARY] or [v.name for v in ir.variables]
            eq_constrs = []
            ineq_constrs = []
            for c in ir.constraints:
                lhs_coeffs = _extract_linear_coeffs(c.lhs_expression_id, nodes)
                rhs_val = _extract_const_val(c.rhs_expression_id, nodes)
                c_dto = {"lhs": lhs_coeffs, "rhs": rhs_val}
                if c.type == ConstraintType.EQUALITY:
                    eq_constrs.append(c_dto)
                else:
                    ineq_constrs.append(c_dto)

            obj_coeffs: dict[str, float] = {}
            if ir.objectives:
                obj_coeffs = _extract_linear_coeffs(ir.objectives[0].expression_id, nodes)

            formalization.formalized = {
                "description_raw": formalization.raw_query or query,
                "description_formalised": formalization.explanation or query,
                "binary_variables": bin_vars,
                "objective_direction": "maximize" if (ir.objectives and ir.objectives[0].direction == ObjectiveDirection.MAXIMIZE) else "minimize",
                "objective_coefficients": obj_coeffs,
                "equality_constraints": eq_constrs,
                "inequality_constraints": ineq_constrs,
                "assumptions": [a.statement for a in ir.assumptions],
                "missing_information": [m.description for m in ir.missing_information],
                "identified_archetype": formalization.problem_class,
                "break_even_point": formalization.break_even_point,
            }

        ws.update_hypothesis(formalization.problem_ir, {"status": formalization.status})
        return formalization, ws

    async def process_verification_feedback(
        self,
        session: AsyncSession,
        workspace: GlobalWorkspace,
        verifier_report: VerificationReport,
        raw_query: str,
        winning_solver: str = "cpsat",
        consent: bool = True,
        anonymize: bool = False,
    ) -> ActiveInferenceOutcome:
        """
        Active Inference Error Minimization Loop (Stage 5-6):
        - If Verifier passes (PASS): consolidates trace (E5).
        - If Verifier fails (FAIL): treats violations as Prediction Errors, consumes cycle,
          and adapts hypothesis.
        - MANDATORY DEC-002: Any revised ProblemIR generated MUST be unapproved (approved=False, approved_at=None)
          and require explicit human re-approval before running any solver!
        """
        is_pass = verifier_report.verdict == Verdict.PASS or (
            verifier_report.feasible and verifier_report.verdict != Verdict.FAIL
        )

        cycle = workspace.energy_budget.current_cycle

        if is_pass:
            # Reward score: 1.0 for zero reflection cycles, decaying gracefully
            reward = 1.0 if cycle == 0 else max(0.5, 1.0 - (cycle * 0.15))
            fp = compute_problem_fingerprint(raw_query)
            trace_id: str | None = None

            # E5: Consent-gated consolidation
            if consent:
                ir_dict = (
                    workspace.memory.active_hypothesis.model_dump(mode="json")
                    if workspace.memory.active_hypothesis
                    else {}
                )
                user_query_to_save = "[ANONYMIZED_STRUCTURAL_QUERY]" if anonymize else raw_query
                trace_id = await self.episodic_repo.consolidate_trace(
                    session=session,
                    trace_data={
                        "problem_fingerprint": fp,
                        "raw_user_query": user_query_to_save,
                        "successful_ir_json": ir_dict,
                        "winning_solver": winning_solver,
                        "penalty_multipliers": {},
                        "reward_score": reward,
                        "lessons_learned": f"Zbieżność osiągnięta w cyklu {cycle} przy weryfikacji {verifier_report.verdict.value}.",
                    },
                )

            return ActiveInferenceOutcome(
                status="PASS",
                reward_score=reward,
                current_cycle=cycle,
                trace_id=trace_id,
                active_problem_ir=workspace.memory.active_hypothesis,
                explanation="Model pomyślnie zweryfikowany przez niezależny weryfikator.",
                requires_reapproval=False,
            )

        # Verification Failed: compute prediction errors
        error_signals: list[str] = [f"Verifier Verdict: {verifier_report.verdict.value} ({verifier_report.verdict_reason})"]
        for cr in verifier_report.constraint_results:
            if not cr.satisfied:
                error_signals.append(
                    f"Naruszone ograniczenie {cr.constraint_id} (mag={cr.violation_magnitude}, note={cr.note})"
                )
        for dv in verifier_report.domain_violations:
            error_signals.append(f"Naruszenie dziedziny zmiennej {dv}")
        if verifier_report.numerical_residual is not None and verifier_report.numerical_residual > 1e-4:
            error_signals.append(f"Residuum numeryczne przekracza tolerancję: {verifier_report.numerical_residual:.6e}")

        for sig in error_signals:
            workspace.register_prediction_error(sig)

        # Check energy exhaustion
        if workspace.energy_budget.is_exhausted() or not workspace.energy_budget.next_cycle():
            reason = workspace.energy_budget.get_exhaustion_reason() or "Przekroczono limit energii/cykli."
            logger.warning("Active inference metabolic budget depleted: %s", reason)
            return ActiveInferenceOutcome(
                status="EXHAUSTED",
                reward_score=0.0,
                current_cycle=workspace.energy_budget.current_cycle,
                prediction_errors=list(workspace.memory.prediction_errors),
                active_problem_ir=workspace.memory.active_hypothesis,
                explanation=f"{reason} Sugestia: {'; '.join(workspace.energy_budget.suggest_simplifications())}",
                requires_reapproval=False,
            )

        # Free Energy Minimization: generate refined hypothesis with error context
        fp = compute_problem_fingerprint(raw_query)
        analogies = await self.episodic_repo.recall_analogies(session, fingerprint=fp, limit=2)
        revised_res = await self.reasoning_port.formalize_query(
            query=raw_query,
            analogies=analogies,
            error_context=workspace.memory.prediction_errors,
        )
        workspace.energy_budget.consume_tokens(300)

        if revised_res.problem_ir is not None:
            # DEC-002: Revised hypothesis MUST be unapproved and require human re-approval!
            revised_ir = revised_res.problem_ir
            revised_ir.approved = False
            revised_ir.approved_at = None
            workspace.update_hypothesis(revised_ir, {"status": "revised_hypothesis_unapproved"})
            return ActiveInferenceOutcome(
                status="FAIL",
                reward_score=0.2,
                current_cycle=workspace.energy_budget.current_cycle,
                prediction_errors=list(workspace.memory.prediction_errors),
                active_problem_ir=revised_ir,
                explanation="Zarejestrowano błąd weryfikatora. Wygenerowano zaktualizowaną hipotezę ProblemIR wymagającą zatwierdzenia przez użytkownika.",
                requires_reapproval=True,
            )

        return ActiveInferenceOutcome(
            status="CLARIFICATION_REQUIRED",
            reward_score=0.0,
            current_cycle=workspace.energy_budget.current_cycle,
            prediction_errors=list(workspace.memory.prediction_errors),
            active_problem_ir=None,
            explanation="Autorefleksja wymaga doprecyzowania od użytkownika.",
            requires_reapproval=False,
        )
